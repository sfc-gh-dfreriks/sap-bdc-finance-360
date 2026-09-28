#!/usr/bin/env python3
"""Capture one screenshot per application page, for the decks and the video.

Shared by the Finance 360 and Sales 360 asset builders. Point it at a running
React app and it walks the sidebar, waiting for each page's data to arrive before
it shoots.

Why this rather than pulling frames out of a recording: the Supply Chain deck
builder extracts frames from its walkthrough mp4 with ffmpeg and then crops away
browser chrome and a personal bookmarks bar. Driving the app in a clean automation
profile means there is no chrome to crop, the images are sharp rather than
video-compressed, and the same shots feed both the deck and the narrated video.

Two things that matter in practice:

  - The apps are single-page with no router — navigation is a `useState` swap
    driven by sidebar buttons, so pages are reached by clicking their label, not
    by visiting a URL.
  - Managed Google Chrome on this machine refuses automation
    ("DevTools remote debugging is disallowed by the system admin"), so this uses
    Playwright's bundled Chromium. Do not add channel="chrome".

Usage:
    python3 tools/capture_shots.py --app finance
    python3 tools/capture_shots.py --app sales --out /tmp/sales_shots
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import time

from playwright.sync_api import sync_playwright

SKILLS = pathlib.Path.home() / "Documents" / "SAP" / "SAP Skills"

APPS = {
    "finance": {
        "url": "http://localhost:5175",
        "sidebar": SKILLS / "finance_dashboard_react/client/src/components/Sidebar.tsx",
        "out": pathlib.Path("/tmp/finance_shots"),
    },
    "sales": {
        "url": "http://localhost:5176",
        "sidebar": SKILLS / "sales_360_react/client/src/components/Sidebar.tsx",
        "out": pathlib.Path("/tmp/sales_shots"),
    },
    "people": {
        "url": "http://localhost:5180",
        "sidebar": SKILLS / "people_360_react/client/src/components/Sidebar.tsx",
        "out": pathlib.Path("/tmp/people_shots"),
    },
    "spend": {
        "url": "http://localhost:5181",
        "sidebar": SKILLS / "spend_360_react/client/src/components/Sidebar.tsx",
        "out": pathlib.Path("/tmp/spend_shots"),
    },
}


def nav_items(sidebar: pathlib.Path) -> list[tuple[str, str]]:
    """Read (id, label) pairs from the sidebar nav array.

    Single-quoted in these files, so a double-quote-only pattern silently returns
    the filter labels instead of the pages.
    """
    if not sidebar.exists():
        sys.exit(f"sidebar not found: {sidebar}")
    return [(m.group(1), m.group(2)) for m in re.finditer(
        r"""id:\s*['"]([\w-]+)['"]\s*,\s*label:\s*['"]([^'"]+)['"]""",
        sidebar.read_text())]


def settle(page, timeout_ms: int = 25000) -> str:
    """Wait for the page to stop fetching and for a chart or table to exist.

    Returns a short note about what it settled on, so a page that rendered empty
    is visible in the log rather than silently shipped into a customer deck.
    """
    try:
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
    except Exception:  # noqa: BLE001
        pass
    for sel in ("svg.recharts-surface", "canvas", "table", "[class*=card]"):
        try:
            page.wait_for_selector(sel, timeout=4000, state="attached")
            return sel
        except Exception:  # noqa: BLE001
            continue
    return "nothing recognised"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", required=True, choices=sorted(APPS))
    ap.add_argument("--out", type=pathlib.Path)
    ap.add_argument("--width", type=int, default=1680)
    ap.add_argument("--height", type=int, default=1050)
    ap.add_argument("--settle", type=float, default=2.5,
                    help="extra seconds to dwell after the page settles")
    args = ap.parse_args()

    cfg = APPS[args.app]
    out = args.out or cfg["out"]
    out.mkdir(parents=True, exist_ok=True)
    items = nav_items(cfg["sidebar"])
    print(f"{args.app}: {len(items)} pages -> {out}")

    manifest = []
    with sync_playwright() as p:
        # bundled Chromium deliberately; see module docstring
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": args.width, "height": args.height},
                                device_scale_factor=2)
        page.goto(cfg["url"], wait_until="domcontentloaded", timeout=60000)
        found = settle(page)
        print(f"  landed on {cfg['url']} ({found})")
        for label in cfg.get("preclick", []):
            page.get_by_role("button", name=label, exact=True).click(timeout=15000)
            settle(page)
            print(f"  pre-click: {label}")

        for i, (pid, label) in enumerate(items):
            try:
                if i:  # first page is already showing
                    page.get_by_role("button", name=label, exact=True).click(timeout=15000)
                what = settle(page)
                time.sleep(args.settle)
                shot = out / f"{i:02d}_{pid}.png"
                page.screenshot(path=str(shot), full_page=False)
                kb = shot.stat().st_size / 1024
                manifest.append({"index": i, "id": pid, "label": label,
                                 "file": str(shot), "settled_on": what})
                print(f"  [{i + 1}/{len(items)}] {label:22s} {kb:6.0f} KB  ({what})")
            except Exception as e:  # noqa: BLE001
                print(f"  [{i + 1}/{len(items)}] {label:22s} FAILED {type(e).__name__}: "
                      f"{str(e)[:70]}")
        browser.close()

    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\ncaptured {len(manifest)}/{len(items)} -> {out}/manifest.json")
    return 0 if len(manifest) == len(items) else 1


if __name__ == "__main__":
    raise SystemExit(main())
