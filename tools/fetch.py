# SPDX-FileCopyrightText: 2026 R5OS Contributors
# SPDX-License-Identifier: MIT
"""Fetch What's new, the version and the merged pull requests from r5os into data/.

Run by the GitHub Action before every build (and once a day). Locally:
    py tools/fetch.py
It needs the GitHub CLI (`gh`) for the pull requests. Without it, the old data/ files stay.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
REPO = "r5-operating-system/r5os"
RAW = f"https://raw.githubusercontent.com/{REPO}/main/"


def raw(path: str) -> str:
	with urllib.request.urlopen(RAW + path, timeout=30) as r:
		return r.read().decode("utf-8")


# classify_pr() and clean_body() follow scripts/generate-prs-page.py in r5os (MIT).
def classify_pr(title: str, summary: str) -> str:
	blob = f"{title} {summary}".lower()
	if any(k in blob for k in ("gpu", "vulkan", "radv", "gfx9", "teapot", "mesa", "radeon", "gart", "drm", "zink", "skia")):
		return "Graphics"
	if any(k in blob for k in ("audio", "midi", "media", "sound", "airplay", "surround", "hdmi", "latency")):
		return "Sound"
	if any(k in blob for k in ("wifi", "wi-fi", "bluetooth", "network", "ipv6", "smb", "printer")):
		return "Network"
	if any(k in blob for k in ("user", "login", "sign in", "lock", "kernel", "boot", "vbox", "virtualbox", "usb", "driver", "power")):
		return "System"
	if any(k in blob for k in ("settings", "deskbar", "tracker", "wallpaper", "notification", "display", "appearance",
			"about", "icon", "brand", "look", "theme", "window")):
		return "Desktop"
	return "Docs & more"


def clean_body(body: str, title: str) -> str:
	if not body:
		return ""
	text = body.replace(chr(92), "")  # drop markdown escapes
	text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
	text = re.sub(r"<[^>]+>", "", text)
	text = re.sub(r"🤖\s*Generated with.*", "", text, flags=re.S)
	lines = []
	for ln in text.splitlines():
		ln = ln.strip()
		low = ln.lower()
		if not ln or ln.startswith(("#", "|", "```")):
			continue
		if low.startswith(("signed-off-by:", "co-authored-by:", "reviewed-by:", "do not merge", "host test:",
				"summary", "what changes", "test plan", "tested", "how to test")):
			continue
		ln = re.sub(r"^[★*•-]\s*(\[[ x]\]\s*)?", "", ln)
		ln = re.sub(r"[`*_]", "", ln)
		ln = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", ln)
		if ln:
			lines.append(ln)
	summary = " ".join(lines)
	if len(summary) > 260:
		cut = summary[:260]
		dot = cut.rfind(". ")
		summary = cut[: dot + 1] if dot > 140 else cut.rsplit(" ", 1)[0] + "…"
	return summary


def main() -> None:
	DATA.mkdir(exist_ok=True)
	try:
		(DATA / "WHATSNEW").write_text(raw("distro/WHATSNEW"), encoding="utf-8")
		version = [ln for ln in raw("distro/VERSION").splitlines() if ln and not ln.startswith("#")][0].strip()
		build = [ln for ln in raw("distro/BUILD").splitlines() if ln and not ln.startswith("#")][0].strip()
		(DATA / "version.json").write_text(json.dumps({"version": version, "build": build}), encoding="utf-8")
		print("whatsnew + version:", version, build)
	except OSError as e:
		print("could not fetch WHATSNEW/VERSION, keeping old data:", e)

	try:
		out = subprocess.run(
			["gh", "pr", "list", "-R", REPO, "--state", "merged", "--base", "main", "--limit", "5000",
			 "--json", "number,title,mergedAt,body,url"],
			check=True, capture_output=True, text=True, encoding="utf-8").stdout
	except (OSError, subprocess.CalledProcessError) as e:
		print("could not list pull requests, keeping old data:", e)
		return
	prs = []
	for p in json.loads(out):
		intro = clean_body(p.get("body") or "", p["title"])
		prs.append({
			"number": p["number"],
			"title": p["title"],
			"merged": p["mergedAt"],
			"url": p["url"],
			"intro": intro,
			"area": classify_pr(p["title"], intro),
		})
	prs.sort(key=lambda p: p["merged"], reverse=True)
	(DATA / "prs.json").write_text(json.dumps(prs, ensure_ascii=False, indent=0), encoding="utf-8")
	print("pull requests:", len(prs))


if __name__ == "__main__":
	main()
