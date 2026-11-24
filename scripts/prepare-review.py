#!/usr/bin/env python3
"""Prepare local evidence for an independent review; never issue a visual pass."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import shutil
import subprocess


def run(args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-6000:])
    return result.stdout


def probe(ffprobe, path):
    return json.loads(run([ffprobe, "-v", "error", "-show_streams", "-show_format",
                           "-of", "json", str(path)]))


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", required=True)
    parser.add_argument("--out", required=True, help="A new directory, not an existing review")
    parser.add_argument("--framing", default=str(Path(__file__).resolve().parents[1] / "assets/framing.json"))
    parser.add_argument("--interval", type=float, default=0.5)
    parser.add_argument("--events", help="Optional JSON array of additional source times in seconds")
    args = parser.parse_args()
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        parser.error("ffmpeg and ffprobe must be installed")
    source = Path(args.video).resolve()
    if not source.is_file():
        parser.error("Video does not exist")
    if not 0.05 <= args.interval <= 10:
        parser.error("Interval must be between 0.05 and 10 seconds")
    out = Path(args.out).resolve()
    if out.exists():
        parser.error("Output already exists; choose a new review directory")
    framing_path = Path(args.framing).resolve()
    cfg = json.loads(framing_path.read_text())
    insets = cfg["normalisedSafeInsets"]
    if set(insets) != {"left", "right", "top", "bottom"}:
        parser.error("Safe insets must have left/right/top/bottom")
    if any(not 0 <= value < 1 for value in insets.values()) or insets["left"] + insets["right"] >= 1 or insets["top"] + insets["bottom"] >= 1:
        parser.error("Invalid safe insets")
    info = probe(ffprobe, source)
    video = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    if not video:
        parser.error("No video stream")
    duration = float(video.get("duration") or info["format"]["duration"])
    if duration <= 0:
        parser.error("Invalid duration")
    events = json.loads(Path(args.events).read_text()) if args.events else []
    if not isinstance(events, list) or any(isinstance(t, bool) or not isinstance(t, (int, float)) or not 0 <= t < duration for t in events):
        parser.error("Events must be an array of valid source times in seconds")
    source_hash = sha256(source)
    out.mkdir(parents=True)
    shutil.copy2(framing_path, out / "framing.json")
    source_alias = out / ("source-original" + source.suffix)
    source_alias.symlink_to(source)
    frames = out / "frames"
    frames.mkdir()
    # Review guides are burned into derivatives only. Source remains untouched.
    scale = "scale=w='min(1080,iw)':h=-2"
    guide = (f"drawbox=x=iw*{insets['left']}:y=ih*{insets['top']}:"
             f"w=iw*{1-insets['left']-insets['right']}:"
             f"h=ih*{1-insets['top']-insets['bottom']}:color=0x00DD88:t=3")
    proxy = out / "review-guides.mp4"
    run([ffmpeg, "-v", "error", "-i", str(source), "-map", "0:v:0", "-map", "0:a?",
         "-vf", scale + "," + guide, "-c:v", "libx264", "-preset", "fast", "-crf", "23",
         "-pix_fmt", "yuv420p", "-fps_mode", "passthrough", "-c:a", "aac", "-movflags", "+faststart", str(proxy)])
    proxy_info = probe(ffprobe, proxy)
    run([ffmpeg, "-v", "error", "-i", str(proxy), "-vf", f"fps=1/{args.interval}",
         str(frames / "sample-%05d.png")])
    evidence = [{"path": str(p.relative_to(out)), "nominal_time_seconds": round(i * args.interval, 4),
                 "sampling": "uniform; seek original to confirm precise issue time"}
                for i, p in enumerate(sorted(frames.glob("sample-*.png")))]
    # Include requested cut/motion events and first frame using explicit seeks.
    for i, time in enumerate(sorted(set([0.0] + events))):
        dest = frames / f"event-{i:04d}.png"
        run([ffmpeg, "-v", "error", "-ss", str(time), "-i", str(proxy),
             "-frames:v", "1", str(dest)])
        if dest.exists():
            evidence.append({"path": str(dest.relative_to(out)), "seek_time_seconds": time,
                             "sampling": "explicit seek"})
    # Select the actual final decoded frame, not duration minus an arbitrary margin.
    timeline = json.loads(run([ffprobe, "-v", "error", "-select_streams", "v:0",
                               "-show_entries", "frame=best_effort_timestamp_time",
                               "-of", "json", str(proxy)]))["frames"]
    if not timeline:
        raise RuntimeError("No decoded frame timestamps")
    last_index = len(timeline) - 1
    last_time = float(timeline[-1]["best_effort_timestamp_time"])
    last = frames / "last-frame.png"
    run([ffmpeg, "-v", "error", "-i", str(proxy), "-vf", f"select=eq(n\\,{last_index})",
         "-frames:v", "1", str(last)])
    evidence.append({"path": str(last.relative_to(out)), "seek_time_seconds": last_time,
                     "frame_index": last_index, "sampling": "actual final decoded frame"})
    if not evidence:
        raise RuntimeError("No review frames extracted")
    if sha256(source) != source_hash:
        raise RuntimeError("Source changed while preparing evidence; review this version again")
    manifest = {"source": str(source), "source_sha256": source_hash, "source_probe": info,
                "original_entry": source_alias.name,
                "review_proxy": proxy.name, "review_proxy_probe": proxy_info,
                "framing_config": "framing.json", "framing_config_sha256": sha256(out / "framing.json"),
                "duration_seconds": duration, "safe_insets": insets,
                "safe_area_basis": cfg["purpose"], "interval_seconds": args.interval,
                "frames": evidence, "visual_verdict": "pending",
                "note": "Guide preparation and decoding do not prove safe framing or visual quality. Full playback and independent inspection remain required."}
    (out / "evidence.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    checks = ["safe_area_during_motion", "subject_and_contrast", "normal_aspect_ratio",
              "phone_readability", "script_and_footage_match", "original_motion_style",
              "continuity_and_fluid_motion", "audio_and_required_deliverables"]
    report = {"source_sha256": source_hash, "reviewer": None, "independent": False,
              "full_playback_completed": False, "checks": {key: "pending" for key in checks},
              "findings": [], "checked_times": [], "verdict": "pending"}
    (out / "review.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    cards = []
    for frame in evidence:
        stamp = frame.get("seek_time_seconds", frame.get("nominal_time_seconds"))
        cards.append(f'<figure><a href="{frame["path"]}"><img loading="lazy" src="{frame["path"]}"></a><figcaption>{stamp:.3f} s · {html.escape(frame["sampling"])}</figcaption></figure>')
    page = ('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>成片复检</title>'
            '<style>body{font:16px sans-serif;margin:24px;background:#eee;color:#222}video{width:min(360px,100%)}main{display:flex;gap:16px;flex-wrap:wrap}figure{margin:0;width:240px}img{width:100%}figcaption{font-size:12px}</style>'
            f'<h1>成片独立复检：{html.escape(source.name)}</h1>'
            '<p>绿色框仅为本次安全区参考；需核对实际平台遮挡。重点的完整范围应在安全区内，背景无需留空。当前状态：待独立复检。</p>'
            f'<p><a href="{html.escape(source_alias.name)}">打开原始视频，核对真实清晰度与声音</a> · 检查副本经过压缩／缩小，不能代替原片。</p>'
            '<video controls src="review-guides.mp4"></video><main>' + ''.join(cards) + '</main></html>')
    (out / "index.html").write_text(page)
    print(json.dumps({"evidence": str(out / "evidence.json"), "review": str(out / "review.json"),
                      "frames": len(evidence), "visual_verdict": "pending"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
