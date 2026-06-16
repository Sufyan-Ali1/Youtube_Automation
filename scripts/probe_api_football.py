"""
Probe a broad set of API-Football read endpoints and save responses to JSON.

Examples:
    .\venv\Scripts\python.exe scripts\probe_api_football.py
    .\venv\Scripts\python.exe scripts\probe_api_football.py --fixture-id 1489376 --season 2026
    .\venv\Scripts\python.exe scripts\probe_api_football.py --output temp\api_football_probe.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings


Context = dict[str, Any]


@dataclass(frozen=True)
class EndpointSpec:
    name: str
    path: str
    params_factory: Callable[[Context], dict[str, Any]]


def _today() -> str:
    return date.today().isoformat()


def _compact_params(params: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in params.items() if value not in (None, "", [])}


ENDPOINTS: list[EndpointSpec] = [
    EndpointSpec("status", "status", lambda ctx: {}),
    EndpointSpec("timezones", "timezone", lambda ctx: {}),
    EndpointSpec("countries", "countries", lambda ctx: {}),
    EndpointSpec("seasons", "leagues/seasons", lambda ctx: {}),
    EndpointSpec("leagues", "leagues", lambda ctx: {"season": ctx["season"], "current": "true"}),
    EndpointSpec("league_rounds", "fixtures/rounds", lambda ctx: {"league": ctx["league_id"], "season": ctx["season"]}),
    EndpointSpec("league_venues", "venues", lambda ctx: {"league": ctx["league_id"], "season": ctx["season"]}),
    EndpointSpec("league_teams", "teams", lambda ctx: {"league": ctx["league_id"], "season": ctx["season"]}),
    EndpointSpec("team_statistics", "teams/statistics", lambda ctx: {"league": ctx["league_id"], "season": ctx["season"], "team": ctx["team_id"]}),
    EndpointSpec("team_countries", "teams/countries", lambda ctx: {}),
    EndpointSpec("team_seasons", "teams/seasons", lambda ctx: {"team": ctx["team_id"]}),
    EndpointSpec("fixtures_by_id", "fixtures", lambda ctx: {"id": ctx["fixture_id"]}),
    EndpointSpec("fixtures_by_date", "fixtures", lambda ctx: {"date": ctx["match_date"], "league": ctx["league_id"], "season": ctx["season"]}),
    EndpointSpec("fixtures_live", "fixtures", lambda ctx: {"live": "all"}),
    EndpointSpec("fixtures_headtohead", "fixtures/headtohead", lambda ctx: {"h2h": f"{ctx['home_team_id']}-{ctx['away_team_id']}"}),
    EndpointSpec("fixture_events", "fixtures/events", lambda ctx: {"fixture": ctx["fixture_id"]}),
    EndpointSpec("fixture_lineups", "fixtures/lineups", lambda ctx: {"fixture": ctx["fixture_id"]}),
    EndpointSpec("fixture_players", "fixtures/players", lambda ctx: {"fixture": ctx["fixture_id"]}),
    EndpointSpec("fixture_statistics", "fixtures/statistics", lambda ctx: {"fixture": ctx["fixture_id"]}),
    EndpointSpec("fixture_statistics_players", "fixtures/statistics/players", lambda ctx: {"fixture": ctx["fixture_id"]}),
    EndpointSpec("standings", "standings", lambda ctx: {"league": ctx["league_id"], "season": ctx["season"]}),
    EndpointSpec("injuries", "injuries", lambda ctx: {"league": ctx["league_id"], "season": ctx["season"], "date": ctx["match_date"]}),
    EndpointSpec("predictions", "predictions", lambda ctx: {"fixture": ctx["fixture_id"]}),
    EndpointSpec("odds", "odds", lambda ctx: {"fixture": ctx["fixture_id"]}),
    EndpointSpec("odds_live", "odds/live", lambda ctx: {"fixture": ctx["fixture_id"]}),
    EndpointSpec("players", "players", lambda ctx: {"team": ctx["team_id"], "season": ctx["season"], "page": 1}),
    EndpointSpec("players_profiles", "players/profiles", lambda ctx: {"player": ctx["player_id"]}),
    EndpointSpec("players_seasons", "players/seasons", lambda ctx: {"player": ctx["player_id"]}),
    EndpointSpec("players_squads", "players/squads", lambda ctx: {"team": ctx["team_id"]}),
    EndpointSpec("players_teams", "players/teams", lambda ctx: {"player": ctx["player_id"]}),
    EndpointSpec("sidelined", "sidelined", lambda ctx: {"player": ctx["player_id"]}),
    EndpointSpec("transfers", "transfers", lambda ctx: {"player": ctx["player_id"]}),
    EndpointSpec("trophies", "trophies", lambda ctx: {"player": ctx["player_id"]}),
    EndpointSpec("coachs", "coachs", lambda ctx: {"team": ctx["team_id"]}),
    EndpointSpec("topscorers", "players/topscorers", lambda ctx: {"league": ctx["league_id"], "season": ctx["season"]}),
    EndpointSpec("topassists", "players/topassists", lambda ctx: {"league": ctx["league_id"], "season": ctx["season"]}),
    EndpointSpec("topyellowcards", "players/topyellowcards", lambda ctx: {"league": ctx["league_id"], "season": ctx["season"]}),
    EndpointSpec("topredcards", "players/topredcards", lambda ctx: {"league": ctx["league_id"], "season": ctx["season"]}),
]


class ProbeError(RuntimeError):
    pass


class ApiFootballProbe:
    def __init__(self, api_key: str, base_url: str) -> None:
        if not api_key:
            raise ProbeError("API_FOOTBALL_KEY is not set")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"x-apisports-key": self.api_key})

    def call(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        started = time.time()
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = self.session.get(url, params=_compact_params(params), timeout=30)
        elapsed_ms = round((time.time() - started) * 1000, 2)
        payload: dict[str, Any] = {
            "status_code": response.status_code,
            "elapsed_ms": elapsed_ms,
            "url": response.url,
        }
        try:
            body = response.json()
        except Exception:
            payload["ok"] = False
            payload["error"] = "non_json_response"
            payload["text"] = response.text[:2000]
            return payload

        payload["body"] = body
        payload["ok"] = response.ok and not body.get("errors")
        if body.get("errors"):
            payload["error"] = body["errors"]
        return payload


def build_context(args: argparse.Namespace) -> Context:
    return {
        "league_id": args.league_id,
        "season": args.season,
        "fixture_id": args.fixture_id,
        "team_id": args.team_id,
        "player_id": args.player_id,
        "home_team_id": args.home_team_id or args.team_id,
        "away_team_id": args.away_team_id or args.secondary_team_id,
        "secondary_team_id": args.secondary_team_id,
        "match_date": args.match_date,
    }


def run_probe(args: argparse.Namespace) -> dict[str, Any]:
    context = build_context(args)
    client = ApiFootballProbe(settings.API_FOOTBALL_KEY, settings.API_FOOTBALL_BASE_URL)

    results: list[dict[str, Any]] = []
    for spec in ENDPOINTS:
        params = _compact_params(spec.params_factory(context))
        try:
            result = client.call(spec.path, params)
        except Exception as exc:
            result = {
                "ok": False,
                "status_code": None,
                "elapsed_ms": None,
                "url": f"{settings.API_FOOTBALL_BASE_URL.rstrip('/')}/{spec.path.lstrip('/')}",
                "error": str(exc),
            }
        results.append(
            {
                "name": spec.name,
                "path": spec.path,
                "params": params,
                **result,
            }
        )

    ok_count = sum(1 for row in results if row.get("ok"))
    return {
        "generated_at": int(time.time()),
        "base_url": settings.API_FOOTBALL_BASE_URL,
        "context": context,
        "summary": {
            "total": len(results),
            "ok": ok_count,
            "failed": len(results) - ok_count,
        },
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe many API-Football endpoints and save responses.")
    parser.add_argument("--league-id", type=int, default=1, help="League id to use for league-based endpoints.")
    parser.add_argument("--season", type=int, default=2026, help="Season to use for season-based endpoints.")
    parser.add_argument("--fixture-id", type=int, default=1489376, help="Fixture id to use for fixture endpoints.")
    parser.add_argument("--team-id", type=int, default=1118, help="Primary team id to use for team/player endpoints.")
    parser.add_argument("--secondary-team-id", type=int, default=20, help="Secondary team id used for head-to-head probing.")
    parser.add_argument("--home-team-id", type=int, default=None, help="Override home team id for head-to-head endpoints.")
    parser.add_argument("--away-team-id", type=int, default=None, help="Override away team id for head-to-head endpoints.")
    parser.add_argument("--player-id", type=int, default=276, help="Player id to use for player endpoints.")
    parser.add_argument("--match-date", default=_today(), help="Date to use for date-sensitive endpoints, YYYY-MM-DD.")
    parser.add_argument(
        "--output",
        default=str(Path("temp") / "api_football_probe.json"),
        help="Output JSON report path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = run_probe(args)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved API-Football probe report to {output_path}")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
