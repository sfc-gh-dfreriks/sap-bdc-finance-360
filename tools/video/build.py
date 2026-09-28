#!/usr/bin/env python3
"""Build a narrated walkthrough video for a SAP BDC 360 application.

One builder, three domains. `--domain finance`, `--domain sales` and
`--domain people` differ only in their DOMAINS entry and their segment script; the
pipeline itself is identical, so a fix to timing or compositing lands for all at
once.

Four phases, in dependency order:

  1. narrate  synthesise per-segment audio and measure its real duration
  2. capture  drive the live app with Playwright, dwelling per measured duration
  3. cards    render the caption PNGs, now that real start offsets are known
  4. assemble ffmpeg: video + narration + overlays -> mp4

Timing is audio-led. The narration is produced first and the browser then holds
each step for exactly as long as its line takes to speak. Fixing the visuals first
and stretching audio to fit drifts within a minute and cannot be recovered.

NOTE ON PHASE ORDER: the supply-chain original listed `cards` before `capture`,
but `phase_cards` reads timeline.json and only `phase_capture` writes it, so a
clean run crashed. Capture runs second here. Do not "restore" the old order.

Usage:
    python3 tools/video/build.py --domain finance
    python3 tools/video/build.py --domain sales --voice Daniel
    python3 tools/video/build.py --domain finance --phase assemble
"""

import argparse
import importlib
import json
import pathlib
import shutil
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

HOME = pathlib.Path.home()

DOMAINS = {
    "finance": dict(
        segments="segments_finance",
        app="http://localhost:5175/",
        work=pathlib.Path("/tmp/finance_video"),
        out=HOME / "Documents" / "SAP" / "SAP_Finance_360_Walkthrough.mp4",
        title="SAP Finance 360",
        subtitle="Closing the books on SAP data that never moved",
        links=[
            ("Live application",
             "erzht4-sfsenorthamerica-dfreriks-aws1-w2.snowflakecomputing.app"),
            ("Source and documentation",
             "github.com/sfc-gh-dfreriks/sap-bdc-finance-360"),
            ("Built on",
             "SAP BDC zero-copy shares · Snowflake · Cortex Analyst"),
        ],
    ),
    "people": dict(
        segments="segments_people",
        app="http://localhost:5180/",
        work=pathlib.Path("/tmp/people_video"),
        out=HOME / "Documents" / "SAP" / "SAP_People_360_Walkthrough.mp4",
        title="SAP People 360",
        subtitle="Workforce Analytics on SAP BDC Data\nusing BDC Connect Zero Copy",
        links=[
            ("Live application",
             "irzht4-sfsenorthamerica-dfreriks-aws1-w2.snowflakecomputing.app"),
            ("Source and documentation",
             "github.com/sfc-gh-dfreriks/sap-bdc-people-360"),
            ("Built on",
             "SAP BDC zero-copy shares · Snowflake · Cortex Analyst"),
        ],
    ),
    "sales": dict(
        segments="segments_sales",
        app="http://localhost:5176/",
        work=pathlib.Path("/tmp/sales_video"),
        out=HOME / "Documents" / "SAP" / "SAP_Sales_360_Walkthrough.mp4",
        title="SAP Sales 360",
        subtitle="Pipeline, quota and forecast on live SAP data",
        links=[
            ("Live application",
             "mrzht4-sfsenorthamerica-dfreriks-aws1-w2.snowflakecomputing.app"),
            ("Source and documentation",
             "github.com/sfc-gh-dfreriks/sap-bdc-sales-360"),
            ("Built on",
             "SAP BDC data products · Snowflake · Cortex Agent"),
        ],
    ),
    "spend": dict(
        segments="segments_spend",
        app="http://localhost:5181/",
        work=pathlib.Path("/tmp/spend_video"),
        out=HOME / "Documents" / "SAP" / "SAP_Spend_360_Walkthrough.mp4",
        title="SAP Spend 360",
        subtitle="Spend Intelligence on SAP BDC Data\nusing BDC Connect Zero Copy",
        links=[
            ("Live application",
             "aszht4-sfsenorthamerica-dfreriks-aws1-w2.snowflakecomputing.app"),
            ("Source and documentation",
             "github.com/sfc-gh-dfreriks/sap-bdc-spend-360"),
            ("Built on",
             "SAP BDC zero-copy shares · Snowflake · Cortex Analyst"),
        ],
    ),
}

W, H = 1600, 1000              # browser viewport
BAND = 132                     # caption band drawn BELOW the app, not over it
VH = H + BAND                  # final canvas height
FPS = 25

# Brand, matching the Word and PowerPoint deliverables and the apps.
NAVY = (27, 58, 87)
BLUE = (41, 181, 232)
WHITE = (255, 255, 255)
DIM = (176, 196, 212)

TITLE_SECS = 5.0
END_SECS = 5.5
PAD_AFTER_SPEECH = 0.55        # a beat of silence after each line

CFG = {}                       # populated by main()
NAV = {}
SEGMENTS = []


def work():
    return CFG["work"]


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def duration(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "csv=p=0", str(path)]).stdout.strip()
    return float(out)


# ------------------------------------------------------------------- 1. narrate

def phase_narrate(voice, rate):
    """Synthesise each line and measure it.

    Start offsets are deliberately NOT computed here. They come from the capture,
    because page loads and navigation cost real time that cannot be predicted;
    guessing it put the captions seconds early by the end of the original video.
    """
    d = work() / "audio"
    d.mkdir(parents=True, exist_ok=True)
    clips = []
    for seg in SEGMENTS:
        aiff = d / f"{seg['id']}.aiff"
        wav = d / f"{seg['id']}.wav"
        run(["say", "-v", voice, "-r", str(rate), "-o", str(aiff), seg["narration"]])
        # 48k stereo so every clip concatenates without resampling surprises
        run(["ffmpeg", "-y", "-v", "error", "-i", str(aiff),
             "-ar", "48000", "-ac", "2", str(wav)])
        spoken = duration(wav)
        clips.append(dict(id=seg["id"], page=seg["page"],
                          secs=round(spoken + PAD_AFTER_SPEECH, 3),
                          spoken=round(spoken, 3),
                          actions=seg["actions"], popup=seg["popup"]))
        print(f"  {seg['id']:18} {spoken:6.2f}s spoken  -> holds "
              f"{spoken + PAD_AFTER_SPEECH:5.2f}s")

    (work() / "clips.json").write_text(json.dumps(
        dict(voice=voice, rate=rate, title=TITLE_SECS, end=END_SECS,
             clips=clips), indent=2))
    spk = sum(c["secs"] for c in clips)
    print(f"\n  {len(clips)} clips · {spk:.1f}s of narration "
          f"({spk / 60:.1f} min before title and end cards)")
    return spk


def build_audio_track():
    """Lay each clip at the offset the capture actually reached.

    Built with adelay + amix rather than concat so a clip lands on its real
    timestamp; concatenating assumes the video had no unaccounted time, which it
    always does — page loads and sidebar navigation are not free.
    """
    tl = json.loads((work() / "timeline.json").read_text())
    d = work() / "audio"
    total = tl["total"]

    inputs, filt, labels = [], [], []
    for i, s in enumerate(tl["segments"]):
        inputs += ["-i", str(d / f"{s['id']}.wav")]
        ms = int(round(s["start"] * 1000))
        filt.append(f"[{i}:a]adelay={ms}|{ms}[a{i}]")
        labels.append(f"[a{i}]")
    filt.append(f"{''.join(labels)}amix=inputs={len(labels)}:"
                f"normalize=0:dropout_transition=0[mixed]")
    filt.append(f"[mixed]apad,atrim=0:{total:.3f}[out]")

    raw = work() / "narration_raw.wav"
    run(["ffmpeg", "-y", "-v", "error", *inputs,
         "-filter_complex", ";".join(filt), "-map", "[out]",
         "-ar", "48000", "-ac", "2", str(raw)])

    final = work() / "narration.wav"
    run(["ffmpeg", "-y", "-v", "error", "-i", str(raw),
         "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", str(final)])
    print(f"  narration track {duration(final):.1f}s, normalised to -16 LUFS")
    return final


# --------------------------------------------------------------------- 2. cards

def _font(size, bold=False):
    from PIL import ImageFont
    names = (["/System/Library/Fonts/Supplemental/Arial Bold.ttf",
              "/System/Library/Fonts/Helvetica.ttc"] if bold else
             ["/System/Library/Fonts/Supplemental/Arial.ttf",
              "/System/Library/Fonts/Helvetica.ttc"])
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap(draw, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = f"{cur} {w}".strip()
        if draw.textlength(t, font=font) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def card(popup, path):
    """One caption strip, full width, sitting in the band below the app.

    Overlaying cards on top of the app was the first design and it hid whichever
    panel it landed on — and on these pages every region carries something. Giving
    captions their own band costs 132px of canvas and hides nothing.
    """
    from PIL import Image, ImageDraw
    f_title, f_fig, f_body = _font(24, True), _font(27, True), _font(17)

    img = Image.new("RGBA", (W, BAND), NAVY + (255,))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 3], fill=BLUE + (255,))          # accent rule on top
    d.rectangle([44, 26, 48, BAND - 26], fill=BLUE + (255,))

    x = 70
    d.text((x, 24), popup["title"], font=f_title, fill=WHITE)
    for i, ln in enumerate(_wrap(d, popup["body"], f_body, 880)[:2]):
        d.text((x, 60 + i * 24), ln, font=f_body, fill=DIM)

    # the figure sits right-aligned, so the eye can find it without reading
    fw = d.textlength(popup["figure"], font=f_fig)
    d.text((W - 70 - fw, 44), popup["figure"], font=f_fig, fill=BLUE)

    img.save(path)
    return img.size


def title_card(path, sub):
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (W, VH), NAVY + (255,))
    d = ImageDraw.Draw(img)
    d.text((90, 360), CFG["title"], font=_font(34, True), fill=BLUE)
    # A subtitle may carry explicit newlines to control where it breaks: the greedy
    # wrap is width-optimal but splits phrases badly ("... using BDC" / "Connect
    # Zero Copy"). Each part is still wrapped, so an over-long part cannot overflow.
    # Two lines is the ceiling — the strap line below sits at y=560.
    lines = []
    for part in CFG["subtitle"].split("\n"):
        lines.extend(_wrap(d, part, _font(52, True), 1420))
    if len(lines) > 2:
        raise SystemExit(
            f"title subtitle needs {len(lines)} lines; only 2 fit above the strap "
            f"line at y=560 — shorten it or move the break"
        )
    for i, ln in enumerate(lines):
        d.text((90, 410 + i * 62), ln, font=_font(52, True), fill=WHITE)
    d.text((90, 560), sub, font=_font(20), fill=DIM)
    d.rounded_rectangle([90, 620, 250, 624], 2, fill=BLUE + (255,))
    img.save(path)


def end_card(path):
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (W, VH), NAVY + (255,))
    d = ImageDraw.Draw(img)
    d.text((90, 330), "Explore it yourself", font=_font(44, True), fill=WHITE)
    y = 420
    for k, v in CFG["links"]:
        d.text((90, y), k, font=_font(15), fill=DIM)
        d.text((90, y + 22), v, font=_font(22, True), fill=BLUE)
        y += 78
    img.save(path)


def phase_cards():
    d = work() / "cards"
    d.mkdir(parents=True, exist_ok=True)
    tl = json.loads((work() / "timeline.json").read_text())
    for s in tl["segments"]:
        s["card"] = list(card(s["popup"], d / f"{s['id']}.png"))
    (work() / "timeline.json").write_text(json.dumps(tl, indent=2))
    mins = tl["total"] / 60
    title_card(d / "_title.png",
               f"A narrated walkthrough · {mins:.0f} minutes · "
               f"every figure computed live, not illustrative")
    end_card(d / "_end.png")
    print(f"  {len(tl['segments'])} caption cards + title + end card")


# ------------------------------------------------------------------- 3. capture

def phase_capture():
    import time
    from playwright.sync_api import sync_playwright
    cl = json.loads((work() / "clips.json").read_text())
    vid = work() / "raw"
    if vid.exists():
        shutil.rmtree(vid)
    vid.mkdir(parents=True)

    with sync_playwright() as pw:
        b = pw.chromium.launch(args=["--force-device-scale-factor=1"])
        ctx = b.new_context(viewport={"width": W, "height": H},
                            record_video_dir=str(vid),
                            record_video_size={"width": W, "height": H})
        pg = ctx.new_page()
        pg.goto(CFG["app"], wait_until="networkidle")
        pg.wait_for_timeout(2500)

        # t0 marks video-time zero for the timeline. Everything before it is
        # page-load noise and gets trimmed off the front in assembly.
        t0 = time.monotonic()
        pg.wait_for_timeout(int(TITLE_SECS * 1000))

        segments, cur_page = [], None
        for s in cl["clips"]:
            if s["page"] != cur_page:
                # These apps navigate by button label, not by route — the same
                # mechanism capture_shots.py uses. A reload would drop state.
                pg.get_by_role("button", name=NAV[s["page"]], exact=True).click()
                pg.wait_for_timeout(1800)
                cur_page = s["page"]

            for act in s["actions"]:
                do_action(pg, act)

            # The caption and the voice line begin now, whatever time the
            # navigation and clicks happened to consume.
            start = time.monotonic() - t0
            pg.wait_for_timeout(int(s["secs"] * 1000))
            segments.append({**s, "start": round(start, 3)})
            print(f"  {s['id']:18} {s['page']:12} starts {start:7.2f}s  "
                  f"holds {s['secs']:5.2f}s")

        pg.wait_for_timeout(int(END_SECS * 1000))
        total = time.monotonic() - t0
        path = pg.video.path()
        ctx.close()
        b.close()

    dst = work() / "screen.webm"
    shutil.move(str(pathlib.Path(path)), dst)

    raw = duration(dst)
    preroll = round(raw - total, 3)      # page-load time before t0
    (work() / "timeline.json").write_text(json.dumps(
        dict(total=round(total, 3), preroll=max(0.0, preroll),
             title=cl["title"], end=cl["end"],
             voice=cl["voice"], rate=cl["rate"], segments=segments), indent=2))
    print(f"\n  captured {raw:.1f}s · timeline {total:.1f}s · "
          f"pre-roll to trim {preroll:.1f}s")
    build_audio_track()
    return dst


def do_action(pg, act):
    """Run one scripted action."""
    kind = act[0]
    if kind == "click_text":
        pg.get_by_text(act[1], exact=False).first.click()
        pg.wait_for_timeout(700)
    elif kind == "click_button":
        pg.get_by_role("button", name=act[1], exact=False).first.click()
        pg.wait_for_timeout(1100)
    elif kind == "fill":
        pg.locator(act[1]).first.fill(act[2])
        pg.wait_for_timeout(400)
    elif kind == "press":
        pg.keyboard.press(act[1])
        pg.wait_for_timeout(600)
    elif kind == "select":
        sel = pg.locator("select").nth(act[1] if len(act) > 2 else 0)
        if sel.count():
            sel.select_option(act[-1])
        pg.wait_for_timeout(500)
    elif kind == "scroll":
        pg.mouse.wheel(0, act[1])
        pg.wait_for_timeout(600)
    elif kind == "hover":
        pg.get_by_text(act[1], exact=False).first.hover()
        pg.wait_for_timeout(600)
    elif kind == "wait":
        pg.wait_for_timeout(act[1])
    else:
        raise ValueError(f"unknown action {act!r}")


# ------------------------------------------------------------------ 4. assemble

def phase_assemble():
    """Composite screen recording + caption band + narration into the mp4.

    Each caption is fed as a LOOPED image lasting exactly its own window. A
    single-frame PNG cannot be faded: its only frame sits at PTS 0, so
    `fade=t=in:st=246` leaves that frame fully transparent and the caption never
    appears. Looping gives the fade real frames to work on, and `setpts` moves the
    clip to its slot so only its own window is ever generated.
    """
    tl = json.loads((work() / "timeline.json").read_text())
    cards = work() / "cards"
    total = tl["total"]
    pre = tl.get("preroll", 0.0)
    out = CFG["out"]

    inputs = ["-i", str(work() / "screen.webm")]
    inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{tl['title']:.3f}",
               "-i", str(cards / "_title.png")]
    inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{tl['end'] + 0.5:.3f}",
               "-i", str(cards / "_end.png")]
    for s_ in tl["segments"]:
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{s_['secs']:.3f}",
                   "-i", str(cards / f"{s_['id']}.png")]
    inputs += ["-i", str(work() / "narration.wav")]
    audio_idx = 3 + len(tl["segments"])

    fc = []
    # trim the page-load pre-roll so video time zero is timeline time zero, then
    # pad downward to make room for the caption band
    fc.append(f"[0:v]trim=start={pre:.3f},setpts=PTS-STARTPTS,"
              f"fps={FPS},scale={W}:{H},setsar=1,"
              f"pad={W}:{VH}:0:0:color=0x1B3A57[base]")
    fc.append(f"[1:v]format=rgba,fade=t=out:st={max(0.0, tl['title'] - 0.6):.3f}:"
              f"d=0.6:alpha=1[tc]")
    fc.append(f"[base][tc]overlay=0:0:enable='lt(t,{tl['title']:.3f})'[v0]")

    prev = "v0"
    for i, s_ in enumerate(tl["segments"]):
        st, dur = s_["start"], s_["secs"]
        lbl, nxt = f"c{i}", f"v{i + 1}"
        fo = max(0.0, dur - 0.4)
        fc.append(f"[{3 + i}:v]format=rgba,"
                  f"fade=t=in:st=0:d=0.3:alpha=1,"
                  f"fade=t=out:st={fo:.3f}:d=0.4:alpha=1,"
                  f"setpts=PTS+{st:.3f}/TB[{lbl}]")
        fc.append(f"[{prev}][{lbl}]overlay=0:{H}:"
                  f"enable='between(t,{st:.3f},{st + dur:.3f})'[{nxt}]")
        prev = nxt

    end_start = total - tl["end"]
    fc.append(f"[2:v]format=rgba,fade=t=in:st=0:d=0.6:alpha=1,"
              f"setpts=PTS+{end_start:.3f}/TB[ec]")
    fc.append(f"[{prev}][ec]overlay=0:0:enable='gte(t,{end_start:.3f})'[vout]")

    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-stats", *inputs,
                    "-filter_complex", ";".join(fc),
                    "-map", "[vout]", "-map", f"{audio_idx}:a",
                    "-t", f"{total:.2f}",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
                    str(out)], check=True)
    print(f"\n  wrote {out}")
    print(f"  {duration(out):.1f}s · {out.stat().st_size // 1024 // 1024} MB")


# ------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", required=True, choices=sorted(DOMAINS))
    ap.add_argument("--voice", default="Samantha")
    ap.add_argument("--rate", type=int, default=168)
    ap.add_argument("--phase", choices=["narrate", "capture", "cards", "assemble"])
    a = ap.parse_args()

    global CFG, NAV, SEGMENTS
    CFG = DOMAINS[a.domain]
    mod = importlib.import_module(CFG["segments"])
    NAV, SEGMENTS = mod.NAV, mod.SEGMENTS

    work().mkdir(parents=True, exist_ok=True)
    # capture before cards — cards needs the timeline capture writes
    phases = [a.phase] if a.phase else ["narrate", "capture", "cards", "assemble"]

    for ph in phases:
        print(f"\n=== {a.domain} · {ph} ===")
        {"narrate": lambda: phase_narrate(a.voice, a.rate),
         "capture": phase_capture,
         "cards": phase_cards,
         "assemble": phase_assemble}[ph]()


if __name__ == "__main__":
    main()
