#!/usr/bin/env python3
"""One-time Snowsight sign-in for recording narrated videos.

Snowsight uses SSO, so the headless recorder cannot sign itself in. This opens a
visible browser, waits while you complete SSO, then saves the session cookies to
STATE so build.py can reuse them (DOMAINS[...]["storage_state"]).

The state file holds a live session: it is written to ~/.snowflake/video/ with
owner-only permissions and must never be committed.

Usage:
    python3 tools/video/snowsight_login.py
    python3 tools/video/snowsight_login.py --url https://app.snowflake.com/<org>/<account>/
"""

import argparse
import os
import pathlib
import shutil
import time

STATE = pathlib.Path.home() / ".snowflake" / "video" / "snowsight_state.json"
PROFILE = pathlib.Path.home() / ".snowflake" / "video" / "chrome_profile"
DEFAULT_URL = "https://app.snowflake.com/sfsenorthamerica/dfreriks_aws1_w2/"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--timeout", type=int, default=600, help="seconds to wait for sign-in")
    a = ap.parse_args()

    from playwright.sync_api import sync_playwright
    STATE.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(STATE.parent, 0o700)

    # Start from a clean profile every time. A profile left behind by an earlier
    # run (Chrome killed, or upgraded since) can stop Chrome attaching at all; the
    # session is saved to STATE, so nothing in the profile needs to persist.
    shutil.rmtree(PROFILE, ignore_errors=True)
    with sync_playwright() as pw:
        # Use the installed Google Chrome, not Playwright's bundled Chromium: only
        # real Chrome can reach macOS passkeys (iCloud Keychain / Touch ID), which
        # SSO may require. A dedicated profile keeps this apart from daily browsing.
        ctx = pw.chromium.launch_persistent_context(
            str(PROFILE), channel="chrome", headless=False, timeout=600_000,
            viewport={"width": 1600, "height": 1000})
        b = ctx
        pg = ctx.pages[0] if ctx.pages else ctx.new_page()
        pg.goto(a.url)
        print(f"Sign in to Snowsight in the browser window (waiting up to {a.timeout}s)...")

        deadline = time.monotonic() + a.timeout
        signed_in = False
        while time.monotonic() < deadline:
            # SSO can move the flow into a new tab, so check every open page.
            # Signed in once a page is back on app.snowflake.com with the main
            # navigation rendered (the SSO pages have neither).
            pages = [p for p in ctx.pages if not p.is_closed()]
            if not pages:
                break
            for p in pages:
                try:
                    if "app.snowflake.com" in p.url and p.get_by_role("navigation").count() > 0:
                        pg, signed_in = p, True
                        break
                except Exception:  # noqa: BLE001 - page navigating mid-check
                    pass
            if signed_in:
                break
            time.sleep(2)

        if not signed_in:
            b.close()
            raise SystemExit("Window closed or timed out before Snowsight finished loading; "
                             "nothing saved. Rerun and leave the window open until it closes itself.")

        time.sleep(4)  # let Snowsight finish setting its cookies
        ctx.storage_state(path=str(STATE))
        os.chmod(STATE, 0o600)
        b.close()
    print(f"Saved Snowsight session to {STATE}")


if __name__ == "__main__":
    main()
