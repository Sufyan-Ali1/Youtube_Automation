import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Paths ─────────────────────────────────────────────────────────────────────
DATABASE_DIR   = BASE_DIR / "database"
TEMP_DIR       = BASE_DIR / "temp"
VOICEOVERS_DIR = TEMP_DIR / "voiceover"
VIDEOS_DIR     = TEMP_DIR / "videos" / "final"
CLIPS_DIR      = TEMP_DIR / "videos" / "clips"

# ── Groq ─────────────────────────────────────────────────────────────────────
GROQ_API_KEY          = os.environ.get("GROQ_API_KEY", "")
GROQ_API_KEY_2        = os.environ.get("GROQ_API_KEY_2", "")
GROQ_API_KEY_3        = os.environ.get("GROQ_API_KEY_3", "")
GROQ_API_KEY_4        = os.environ.get("GROQ_API_KEY_4", "")
GROQ_API_KEY_5        = os.environ.get("GROQ_API_KEY_5", "")
GROQ_MODEL            = "llama-3.3-70b-versatile"
GROQ_VISION_MODEL     = "meta-llama/llama-4-scout-17b-16e-instruct"

# ── ElevenLabs ───────────────────────────────────────────────────────────────
ELEVENLABS_API_KEY          = os.environ.get("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID_ENGLISH = os.environ.get("ELEVENLABS_VOICE_ID_ENGLISH", "")
ELEVENLABS_VOICE_ID_YORUBA  = os.environ.get("ELEVENLABS_VOICE_ID_YORUBA", "")


# ── Twitter / X (future) ─────────────────────────────────────────────────────
TWITTER_BEARER_TOKEN   = os.environ.get("TWITTER_BEARER_TOKEN", "")

# ── Google OAuth (shared client for YouTube + Drive) ─────────────────────────
GOOGLE_CLIENT_ID     = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")

# ── YouTube ───────────────────────────────────────────────────────────────────
YOUTUBE_REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN", "")
YOUTUBE_PLAYLIST_ID   = os.environ.get("YOUTUBE_PLAYLIST_ID", "")
YOUTUBE_LIVE_STREAM_ID = os.environ.get("YOUTUBE_LIVE_STREAM_ID", "")
YOUTUBE_LIVE_PRIVACY_STATUS = os.environ.get("YOUTUBE_LIVE_PRIVACY_STATUS", "unlisted")
YOUTUBE_LIVE_CATEGORY_ID = os.environ.get("YOUTUBE_LIVE_CATEGORY_ID", "17")

# ── Buffer (future — social posting) ─────────────────────────────────────────
BUFFER_ACCESS_TOKEN        = os.environ.get("BUFFER_ACCESS_TOKEN", "")

# API-Football / API-Sports (live score scoreboard)
API_FOOTBALL_KEY        = os.environ.get("API_FOOTBALL_KEY", "")
API_FOOTBALL_BASE_URL   = os.environ.get("API_FOOTBALL_BASE_URL", "https://v3.football.api-sports.io")
LIVE_SCORE_POLL_SECONDS = int(os.environ.get("LIVE_SCORE_POLL_SECONDS", "30"))
LIVE_SCORE_TIMEZONE     = os.environ.get("LIVE_SCORE_TIMEZONE", "UTC")

# ── Livestream automation ─────────────────────────────────────────────────────
LIVESTREAM_BASE_URL = os.environ.get("LIVESTREAM_BASE_URL", "http://127.0.0.1:8000")
LIVESTREAM_FIXTURE_ID = int(os.environ.get("LIVESTREAM_FIXTURE_ID", "0"))
LIVESTREAM_TARGET_LEAGUE_ID = int(os.environ.get("LIVESTREAM_TARGET_LEAGUE_ID", "1"))
LIVESTREAM_TARGET_SEASON = int(os.environ.get("LIVESTREAM_TARGET_SEASON", "2026"))
LIVESTREAM_POLL_SECONDS = int(os.environ.get("LIVESTREAM_POLL_SECONDS", "30"))
LIVESTREAM_PREMATCH_LEAD_SECONDS = int(os.environ.get("LIVESTREAM_PREMATCH_LEAD_SECONDS", "900"))
LIVESTREAM_POSTMATCH_GRACE_SECONDS = int(os.environ.get("LIVESTREAM_POSTMATCH_GRACE_SECONDS", "180"))
LIVESTREAM_STATE_FILE = os.environ.get("LIVESTREAM_STATE_FILE", str(TEMP_DIR / "livestream_state.json"))
LIVESTREAM_CONTROLLER_STATE_FILE = os.environ.get(
    "LIVESTREAM_CONTROLLER_STATE_FILE",
    str(TEMP_DIR / "livestream_controller_state.json"),
)
LIVESTREAM_LOG_DIR = os.environ.get("LIVESTREAM_LOG_DIR", str(TEMP_DIR / "livestream"))

# Headless encoder on Hetzner/Linux
LIVESTREAM_FRAME_WIDTH = int(os.environ.get("LIVESTREAM_FRAME_WIDTH", "1080"))
LIVESTREAM_FRAME_HEIGHT = int(os.environ.get("LIVESTREAM_FRAME_HEIGHT", "1920"))
LIVESTREAM_FRAME_RATE = int(os.environ.get("LIVESTREAM_FRAME_RATE", "30"))
LIVESTREAM_DISPLAY = os.environ.get("LIVESTREAM_DISPLAY", ":99")
LIVESTREAM_CHROMIUM_BIN = os.environ.get("LIVESTREAM_CHROMIUM_BIN", "chromium")
LIVESTREAM_FFMPEG_BIN = os.environ.get("LIVESTREAM_FFMPEG_BIN", "ffmpeg")
LIVESTREAM_XVFB_BIN = os.environ.get("LIVESTREAM_XVFB_BIN", "Xvfb")
LIVESTREAM_AUDIO_FILE = os.environ.get("LIVESTREAM_AUDIO_FILE", "")
LIVESTREAM_VIDEO_BITRATE = os.environ.get("LIVESTREAM_VIDEO_BITRATE", "4500k")
LIVESTREAM_AUDIO_BITRATE = os.environ.get("LIVESTREAM_AUDIO_BITRATE", "128k")
LIVESTREAM_FFMPEG_PRESET = os.environ.get("LIVESTREAM_FFMPEG_PRESET", "veryfast")
LIVESTREAM_STREAM_KEY = os.environ.get("LIVESTREAM_STREAM_KEY", "")

# ── Google Drive ──────────────────────────────────────────────────────────────
GDRIVE_REFRESH_TOKEN = os.environ.get("GDRIVE_REFRESH_TOKEN", "")
GDRIVE_FOLDER_ID     = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "")

# ── Brand ─────────────────────────────────────────────────────────────────────
BRAND_NAME    = os.environ.get("BRAND_NAME", "Football Credo Hub")
BRAND_TAGLINE = os.environ.get("BRAND_TAGLINE", "Football News. Every Second.")

# ── Club colours (hex) for branding overlays ─────────────────────────────────
CLUB_COLOURS: dict[str, str] = {
    "manchester united": "#DA291C",
    "man utd":           "#DA291C",
    "chelsea":           "#034694",
    "real madrid":       "#FEBE10",
    "barcelona":         "#A50044",
    "psg":               "#004170",
    "paris saint-germain": "#004170",
    "al-nassr":          "#F5C518",
    "inter miami":       "#F7B5CD",
    "arsenal":           "#EF0107",
    "liverpool":         "#C8102E",
    "manchester city":   "#6CABDD",
    "tottenham":         "#132257",
    "juventus":          "#000000",
    "ac milan":          "#FB090B",
    "inter milan":       "#010E80",
    "atletico madrid":   "#CB3524",
    "default":           "#1A1A2E",
}

# ── Scheduler intervals (seconds) ────────────────────────────────────────────
POLL_INTERVAL_RSS = 3600  # 1 hour

# ── Daily video config ────────────────────────────────────────────────────────
BREAKING_SCORE_THRESHOLD = int(os.environ.get("BREAKING_SCORE_THRESHOLD", "100"))
MIN_STORIES_FOR_DAILY    = int(os.environ.get("MIN_STORIES_FOR_DAILY", "2"))
MAX_STORIES_FOR_DAILY    = int(os.environ.get("MAX_STORIES_FOR_DAILY", "5"))
DAILY_VIDEO_HOURS_UTC    = [9, 19]   # 9 AM and 7 PM UTC

# ── Pipeline retry config ─────────────────────────────────────────────────────
MAX_RETRIES     = 3
RETRY_BACKOFF   = 2  # exponential backoff base (seconds)
