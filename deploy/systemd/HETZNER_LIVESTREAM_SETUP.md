# Hetzner `systemd` Setup

This repo now supports automated YouTube live score streaming with:

- FastAPI frame server
- fixture-driven livestream controller
- headless encoder stack using `Xvfb`, `Chromium`, and `FFmpeg`

These instructions assume:

- repo path: `/opt/football-autonews`
- service user: `football`
- Python virtualenv path: `/opt/football-autonews/venv`

## 1. Install system packages

```bash
sudo apt update
sudo apt install -y python3 python3-venv ffmpeg xvfb chromium
```

## 2. Create service user

```bash
sudo useradd -r -m -d /opt/football-autonews -s /bin/bash football || true
```

## 3. Copy project

Place the repo at:

```bash
/opt/football-autonews
```

Then set ownership:

```bash
sudo chown -R football:football /opt/football-autonews
```

## 4. Create virtualenv

```bash
cd /opt/football-autonews
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Configure environment

Fill `/opt/football-autonews/.env` with at least:

```env
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
YOUTUBE_REFRESH_TOKEN=...
YOUTUBE_LIVE_STREAM_ID=...
LIVESTREAM_STREAM_KEY=...
API_FOOTBALL_KEY=...
LIVE_SCORE_TIMEZONE=UTC
LIVESTREAM_BASE_URL=http://127.0.0.1:8000
LIVESTREAM_TARGET_LEAGUE_ID=1
LIVESTREAM_TARGET_SEASON=2026
LIVESTREAM_POLL_SECONDS=30
LIVESTREAM_PREMATCH_LEAD_SECONDS=900
LIVESTREAM_POSTMATCH_GRACE_SECONDS=180
LIVESTREAM_DISPLAY=:99
LIVESTREAM_CHROMIUM_BIN=chromium
LIVESTREAM_XVFB_BIN=Xvfb
LIVESTREAM_FFMPEG_BIN=ffmpeg
```

Optional:

```env
LIVESTREAM_AUDIO_FILE=/opt/football-autonews/config/audio/bg-music.mp3
YOUTUBE_LIVE_PRIVACY_STATUS=unlisted
```

## 6. Install `systemd` units

Copy the unit files:

```bash
sudo cp deploy/systemd/football-frame.service /etc/systemd/system/
sudo cp deploy/systemd/football-live-controller.service /etc/systemd/system/
```

If your Linux username is not `football`, replace `%i` usage by concrete `User=football`, or instantiate services using your username.

Recommended simple edit:

```bash
sudo sed -i 's/User=%i/User=football/' /etc/systemd/system/football-frame.service
sudo sed -i 's/User=%i/User=football/' /etc/systemd/system/football-live-controller.service
```

## 7. Enable and start

```bash
sudo systemctl daemon-reload
sudo systemctl enable football-frame.service
sudo systemctl enable football-live-controller.service
sudo systemctl start football-frame.service
sudo systemctl start football-live-controller.service
```

## 8. Check logs

```bash
sudo systemctl status football-frame.service
sudo systemctl status football-live-controller.service
journalctl -u football-frame.service -f
journalctl -u football-live-controller.service -f
```

Encoder logs are also written to:

```bash
/opt/football-autonews/temp/livestream/
```

Files:

- `controller.log`
- `xvfb.log`
- `chromium.log`
- `ffmpeg.log`

## 9. Test safely

Before a real match:

```bash
cd /opt/football-autonews
source venv/bin/activate
python scripts/live_stream_controller.py --once
```

This checks fixture lookup and YouTube API wiring without leaving a long-running controller session.

## 10. Real runtime behavior

- frame server stays up continuously
- controller stays up continuously
- controller selects a World Cup fixture automatically
- it creates/binds a YouTube broadcast before kickoff
- when match status becomes live, it starts:
  - `Xvfb`
  - `Chromium`
  - `FFmpeg`
- when the match finishes and grace time passes, it completes the broadcast and stops the encoder stack

## Notes

- This setup is intentionally host-based, not Docker-based, because `Chromium + Xvfb + FFmpeg` is more reliable under `systemd` on Hetzner.
- Keep the YouTube reusable live stream configured in Studio and use its stream key in `LIVESTREAM_STREAM_KEY`.
