from __future__ import annotations

import argparse
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from clients.api_football import ApiFootballClient
from config import settings
from publish.livestream import (
    bind_broadcast_to_stream,
    create_broadcast,
    find_reusable_broadcast,
    stream_health,
    transition_broadcast,
)
from scripts.stream_encoder import start_encoder

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("live_stream_immediate_test")


def _api() -> ApiFootballClient:
    return ApiFootballClient(cache_seconds=max(5, settings.LIVESTREAM_POLL_SECONDS))


def _fixture_title(fixture: dict) -> str:
    home = fixture["teams"]["home"]["name"]
    away = fixture["teams"]["away"]["name"]
    return f"{home} vs {away} | FIFA World Cup 2026 Live"


def _fixture_description(fixture: dict) -> str:
    home = fixture["teams"]["home"]["name"]
    away = fixture["teams"]["away"]["name"]
    venue = fixture["venue"]["name"] or "Venue TBC"
    round_name = fixture["league"]["round"] or "World Cup"
    kickoff = fixture["date"]
    return (
        f"Immediate livestream test for {home} vs {away}.\n\n"
        f"Competition: {fixture['league']['name']}\n"
        f"Round: {round_name}\n"
        f"Venue: {venue}\n"
        f"Kickoff: {kickoff}\n\n"
        f"{settings.BRAND_NAME} - {settings.BRAND_TAGLINE}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Test immediate YouTube livestream startup for one fixture.")
    parser.add_argument("--fixture-id", type=int, required=True, help="Fixture ID to stream immediately.")
    args = parser.parse_args()

    fixture = _api().fixture(args.fixture_id)
    title = _fixture_title(fixture)
    logger.info("Preparing immediate livestream test for fixture %s | %s", args.fixture_id, title)

    broadcast = find_reusable_broadcast(title=title, start_time=datetime.now(UTC))
    if broadcast is None:
        broadcast = create_broadcast(
            title=title,
            description=_fixture_description(fixture),
            start_time=datetime.now(UTC),
        )
    if not broadcast.bound_stream_id:
        broadcast = bind_broadcast_to_stream(broadcast.broadcast_id)

    start_encoder(args.fixture_id)

    status = stream_health()
    logger.info("YouTube stream health: %s", status)
    if status not in {"active", "ready"}:
        raise RuntimeError(f"Stream is not ingesting yet. Current status: {status}")

    try:
        transition_broadcast(broadcast.broadcast_id, "testing")
    except Exception as exc:
        logger.warning("Testing transition failed: %s", exc)
    transition_broadcast(broadcast.broadcast_id, "live")

    logger.info("Immediate livestream test is now LIVE.")
    logger.info("Broadcast ID: %s", broadcast.broadcast_id)
    logger.info("Fixture ID: %s", args.fixture_id)
    logger.info("Use normal shutdown flow later or stop encoder manually when finished testing.")


if __name__ == "__main__":
    main()
