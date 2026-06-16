"""
Bulk clip indexer.

Scans a folder for .mp4 files, sends each to Groq Vision for a description
and keywords, then saves the result to the video_clips DB table.

Usage:
    python index_clips.py                          # index new clips only
    python index_clips.py storage/my_clips/        # custom folder
    python index_clips.py --reindex                # re-run vision on clips that failed (filename as description)
"""
import base64
import json
import logging
import sys
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("index_clips")

from config import settings
from clients.groq_client import get_groq_client
from core.database import (
    clip_exists,
    get_all_clips,
    insert_video_clip,
    update_video_clip_description,
)
from process.clip_indexer import _load_clip_info

_DETAILED_PROMPT = (
    "You are indexing football-related stock video clips for later retrieval.\n"
    "You are looking at three frames from the same clip taken at 25%, 50%, and 75%.\n"
    "Write a detailed but concise visual description that helps an editor choose the right clip.\n\n"
    "Description rules:\n"
    "- Mention the main action first.\n"
    "- If a famous public figure is clearly recognizable, include the person's name.\n"
    "- If identity is uncertain, do not guess the name.\n"
    "- Instead, describe visible traits such as clothing, team kit, posture, hairstyle, age range, or role.\n"
    "- If a stadium or location is clearly recognizable, include its name.\n"
    "- If the venue is uncertain, describe what is visible: pitch, stands, tunnel, crowd, city skyline, training ground, office, signing table, etc.\n"
    "- Mention the camera angle or shot style when useful: aerial, close-up, sideline, crowd-level, wide stadium, tracking shot, drone shot.\n"
    "- Mention notable objects or context like a contract, pen, podium, scarf, trophy, flag, bus, press backdrop, or empty seats.\n"
    "- Stay factual and visually grounded. Do not invent facts.\n"
    "- Keep the description to 1 or 2 sentences, max 45 words.\n\n"
    "Then list exactly 8 search keywords.\n\n"
    "Respond in this exact format only:\n"
    "DESCRIPTION: <description>\n"
    "KEYWORDS: <keyword1>, <keyword2>, <keyword3>, <keyword4>, <keyword5>, <keyword6>, <keyword7>, <keyword8>"
)


def _looks_like_filename(desc: str) -> bool:
    """True if the description is just the Pexels filename (vision failed at index time)."""
    return desc.startswith("pexels_") or (len(desc) < 10 and "_" in desc)


def _parse_vision_reply(text: str) -> tuple[str, str]:
    desc, kws = "", ""
    for line in text.splitlines():
        if line.startswith("DESCRIPTION:"):
            desc = line[len("DESCRIPTION:"):].strip()
        elif line.startswith("KEYWORDS:"):
            kws = line[len("KEYWORDS:"):].strip()
    return desc, kws


def _get_groq_key() -> str:
    try:
        client = get_groq_client()
        return client._keys[client._index]
    except Exception:
        return getattr(settings, "GROQ_API_KEY", "")


def _describe_frames_detailed(frames: list) -> tuple[str, str]:
    groq_key = _get_groq_key()
    if not groq_key:
        logger.warning("GROQ_API_KEY not set - skipping vision description")
        return "", ""

    content: list[dict] = []
    for image in frames:
        buf = BytesIO()
        image.convert("RGB").save(buf, format="JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode()
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
            }
        )
    content.append({"type": "text", "text": _DETAILED_PROMPT})

    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {groq_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.GROQ_VISION_MODEL,
                "messages": [{"role": "user", "content": content}],
                "max_tokens": 220,
                "temperature": 0.1,
            },
            timeout=45,
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"].strip()
        desc, kws = _parse_vision_reply(text)
        logger.info("Detailed vision: %r | kws: %r", desc, kws)
        return desc, kws
    except Exception as exc:
        logger.warning("Detailed Groq vision call failed: %s", exc)
        return "", ""


def _index_single_clip(video_path: Path, source_url: str | None = None) -> bool:
    try:
        path_str = str(video_path.resolve().relative_to(settings.BASE_DIR))
    except ValueError:
        path_str = str(video_path)

    if clip_exists(path_str):
        logger.debug("Already indexed: %s", video_path.name)
        return False

    frames, duration = _load_clip_info(video_path)
    if not frames:
        logger.warning("Frame extraction failed - skipping index for %s", video_path.name)
        return False

    print(f"    [Indexer] Describing {video_path.name} ...")
    desc, kws = _describe_frames_detailed(frames)
    if not desc:
        desc = video_path.stem
        logger.warning("Vision returned empty description - using filename as fallback")

    insert_video_clip(
        file_path=path_str,
        description=desc,
        keywords=kws,
        source="pexels",
        source_url=source_url,
        duration=duration,
        width=None,
        height=None,
    )
    print(f"    [Indexer] Saved: {desc!r}  |  keywords: {kws!r}")
    logger.info("Indexed: %s", video_path.name)
    return True


def reindex_failed(folder: Path) -> None:
    """Re-run Groq Vision on clips whose description is just their filename."""
    all_clips = get_all_clips()
    failed = [c for c in all_clips if _looks_like_filename(c["description"])]

    print(f"\nRe-index failed clips")
    print(f"  Total in DB        : {len(all_clips)}")
    print(f"  Bad descriptions   : {len(failed)}")
    print()

    if not failed:
        print("Nothing to re-index — all clips have proper descriptions.")
        return

    ok = 0
    still_fail = 0
    for i, clip in enumerate(failed, 1):
        path = Path(clip["file_path"])
        print(f"  [{i}/{len(failed)}] {path.name}")

        if not path.exists():
            print(f"    -> file missing on disk, skipping")
            still_fail += 1
            continue

        try:
            frames, _ = _load_clip_info(path)
            if not frames:
                print(f"    -> frame extraction failed")
                still_fail += 1
                continue

            desc, kws = _describe_frames_detailed(frames)
            if not desc or _looks_like_filename(desc):
                print(f"    -> vision returned empty/bad result, skipping")
                still_fail += 1
                continue

            update_video_clip_description(clip["file_path"], desc, kws)
            print(f"    -> {desc!r}")
            ok += 1

        except Exception as exc:
            logger.warning("Failed: %s — %s", path.name, exc)
            still_fail += 1

    print(f"\nDone — updated: {ok}  |  still failed: {still_fail}")


def index_new(folder: Path) -> None:
    """Index .mp4 files in folder that aren't in the DB yet."""
    mp4s = sorted(folder.rglob("*.mp4"))
    if not mp4s:
        print(f"No .mp4 files found in {folder}")
        return

    already_indexed = {r["file_path"] for r in get_all_clips()}
    pending = [p for p in mp4s if str(p) not in already_indexed]

    print(f"\nClip indexer")
    print(f"  Folder         : {folder}")
    print(f"  Total .mp4     : {len(mp4s)}")
    print(f"  Already in DB  : {len(already_indexed)}")
    print(f"  To index       : {len(pending)}\n")

    if not pending:
        print("Nothing to do — all clips already indexed.")
        return

    ok = 0
    fail = 0
    for i, path in enumerate(pending, 1):
        print(f"  [{i}/{len(pending)}] {path.name}")
        try:
            success = _index_single_clip(video_path=path, source_url=None)
            if success:
                ok += 1
            else:
                fail += 1
                print(f"    -> skipped")
        except Exception as exc:
            fail += 1
            logger.warning("Failed: %s — %s", path.name, exc)

    print(f"\nDone — indexed: {ok}  |  failed/skipped: {fail}")


def _keywords_to_list(keywords: str) -> list[str]:
    return [kw.strip() for kw in keywords.split(",") if kw.strip()]


def describe_to_json(folder: Path, output_path: Path) -> None:
    """Describe .mp4 files in folder and save results to a JSON file."""
    mp4s = sorted(folder.rglob("*.mp4"))
    if not mp4s:
        print(f"No .mp4 files found in {folder}")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    results = []
    existing_by_path = {}
    if output_path.exists():
        try:
            existing = json.loads(output_path.read_text(encoding="utf-8"))
            existing_by_path = {
                item.get("file_path"): item
                for item in existing.get("clips", [])
                if item.get("status") == "ok"
            }
        except Exception as exc:
            logger.warning("Could not read existing JSON for resume: %s", exc)

    print("\nClip JSON indexer")
    print(f"  Folder      : {folder}")
    print(f"  Total .mp4  : {len(mp4s)}")
    print(f"  Output JSON : {output_path}\n")

    for i, path in enumerate(mp4s, 1):
        print(f"  [{i}/{len(mp4s)}] {path.name}")
        existing_item = existing_by_path.get(str(path))
        if existing_item:
            results.append(existing_item)
            print("    -> already described, keeping existing result")
            continue

        item = {
            "file_name": path.name,
            "file_path": str(path),
            "size_bytes": path.stat().st_size,
            "duration_seconds": None,
            "description": "",
            "keywords": [],
            "status": "failed",
            "error": "",
        }

        try:
            frames, duration = _load_clip_info(path)
            item["duration_seconds"] = round(duration, 2) if duration is not None else None

            if not frames:
                item["error"] = "frame_extraction_failed"
                print("    -> frame extraction failed")
            else:
                desc, kws = _describe_frames_detailed(frames)
                item["description"] = desc or path.stem
                item["keywords"] = _keywords_to_list(kws)
                item["status"] = "ok" if desc else "fallback"
                print(f"    -> {item['description']!r}")

        except Exception as exc:
            item["error"] = str(exc)
            logger.warning("Failed: %s â€” %s", path.name, exc)

        results.append(item)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "folder": str(folder),
        "total": len(results),
        "ok": sum(1 for item in results if item["status"] == "ok"),
        "fallback": sum(1 for item in results if item["status"] == "fallback"),
        "failed": sum(1 for item in results if item["status"] == "failed"),
        "clips": results,
    }
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nDone - saved JSON: {output_path}")


def main() -> None:
    reindex = "--reindex" in sys.argv
    json_output = None
    if "--json-output" in sys.argv:
        idx = sys.argv.index("--json-output")
        try:
            json_output = Path(sys.argv[idx + 1])
        except IndexError:
            print("Missing path after --json-output")
            sys.exit(1)

    args = []
    skip_next = False
    for arg in sys.argv[1:]:
        if skip_next:
            skip_next = False
            continue
        if arg == "--json-output":
            skip_next = True
            continue
        if not arg.startswith("--"):
            args.append(arg)

    folder = Path(args[0]) if args else settings.CLIPS_DIR

    if not folder.exists() and not reindex:
        print(f"Folder not found: {folder}")
        sys.exit(1)

    if json_output is not None:
        describe_to_json(folder, json_output)
    elif reindex:
        reindex_failed(folder)
    else:
        index_new(folder)


if __name__ == "__main__":
    main()
