# SPDX-FileCopyrightText: 2026 R5OS Contributors
# SPDX-License-Identifier: MIT
"""Build the R5 Operating System website into _site/.

    py tools/fetch.py   # optional: fresh What's new and pull requests from r5os
    py build.py         # writes _site/
    py -m http.server 8000 -d _site

Texts come from content.toml, pictures from screenshots/, What's new and the
pull requests from data/ (written by tools/fetch.py).
"""
from __future__ import annotations

import datetime
import hashlib
import html
import json
import pathlib
import re
import shutil
import sys
import tomllib

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "_site"
CACHE = ROOT / ".cache"
sys.path.insert(0, str(ROOT / "tools"))
import cutout  # noqa: E402

C = tomllib.loads((ROOT / "content.toml").read_text(encoding="utf-8"))
warnings: list[str] = []


def esc(s: str) -> str:
	return html.escape(s, quote=True)


def url(key_or_url: str) -> str:
	if key_or_url.startswith(("http", "/")):
		return key_or_url
	return C["site"].get(key_or_url, key_or_url)


# ------------------------------------------------------------ screenshots

SHOTS: dict[str, dict] = {}


def _render(src: pathlib.Path, spec: dict) -> tuple[str, int, int]:
	cut = spec.get("cut", True)
	area = spec.get("area")
	keep_small = spec.get("keep_small", False)
	data = src.read_bytes()
	key = hashlib.sha1(data + repr((cut, area, keep_small, 3)).encode()).hexdigest()[:16]
	ext = "webp"
	CACHE.mkdir(exist_ok=True)
	cached = CACHE / f"{key}.{ext}"
	if not cached.exists():
		im = Image.open(src)
		if area:
			w, h = im.size
			im = im.crop((int(area[0] * w), int(area[1] * h), int(area[2] * w), int(area[3] * h)))
		out = cutout.cut(im, keep_small) if cut else None
		if out is None:
			if cut:
				warnings.append(f"{src.name}: no R5 wallpaper found, showing the whole screen")
			out = im.convert("RGB")
		out.thumbnail((1600, 1600), Image.LANCZOS)
		out.save(cached, "WEBP", quality=90, method=6)
	w, h = Image.open(cached).size
	name = f"{spec['name']}-{src.stem.rsplit('-', 1)[-1]}-{key[:8]}.{ext}"
	(OUT / "shots").mkdir(parents=True, exist_ok=True)
	shutil.copyfile(cached, OUT / "shots" / name)
	return f"/shots/{name}", w, h


def load_shots() -> None:
	folder = ROOT / "screenshots"
	for spec in C.get("shot", []):
		n = spec["name"]
		src_name = spec.get("source", n)  # reuse another screenshot file
		files = {v: folder / f"{src_name}-{v}.png" for v in ("light", "dark")}
		plain = folder / f"{src_name}.png"
		found = {v: p for v, p in files.items() if p.exists()}
		if not found and plain.exists():
			found = {"light": plain}
		if not found:
			continue
		rec = dict(spec)
		for v, p in found.items():
			rec[v], rec["w"], rec["h"] = _render(p, spec)
		rec.setdefault("light", rec.get("dark"))
		rec.setdefault("dark", rec.get("light"))
		SHOTS[n] = rec


def shot(name: str, cls: str = "win", alt: str = "") -> str:
	s = SHOTS.get(name)
	if not s:
		return ""
	alt = esc(alt or s.get("caption", "").split(" — ")[0] or "R5 screenshot")
	dims = f'width="{s["w"]}" height="{s["h"]}"'
	if s["light"] == s["dark"]:
		return f'<img class="{cls}" src="{s["light"]}" {dims} alt="{alt}" loading="lazy">'
	return (f'<div class="pair {cls}-pair"><img class="{cls} d" src="{s["dark"]}" {dims} alt="{alt}" loading="lazy">'
			f'<img class="{cls} l" src="{s["light"]}" {dims} alt="" aria-hidden="true" loading="lazy"></div>')


# ------------------------------------------------------------ page frame

NAV = [("Screenshots", "/screenshots/"), ("What's new", "/whats-new/"), ("Developers", "/developers/"),
	   ("Download", "/download/")]


def page(path: str, title: str, body: str, active: str = "") -> None:
	site = C["site"]
	links = "".join(f'<a href="{h}"{" class=\"on\"" if h == active else ""}>{esc(t)}</a>' for t, h in NAV)
	links += f'<a href="{site["github"]}">GitHub</a>'
	full_title = f"{title} — {site['name']}" if title else f"{site['name']} — {site['tagline']}"
	og = SHOTS.get("hero", {}).get("dark", "")
	doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(site['description'])}">
<meta property="og:title" content="{esc(full_title)}"><meta property="og:description" content="{esc(site['description'])}">
<meta property="og:image" content="https://r5-operating-system.github.io{og}">
<link rel="icon" href="/assets/img/r5-symbol.svg" type="image/svg+xml"><link rel="icon" href="/assets/img/r5-symbol-32.png" sizes="32x32">
<link rel="preload" href="/assets/fonts/manrope-bold.ttf" as="font" type="font/ttf" crossorigin>
<link rel="stylesheet" href="/assets/site.css?v={VERSION_STAMP}">
<script>try{{if(localStorage.r5mode==='light')document.documentElement.classList.add('light')}}catch(e){{}}</script>
</head><body>
<nav><a class="brand" href="/"><img src="/assets/img/r5-symbol-64.png" alt="">{esc(site['name'])}</a><span class="sp"></span>
<div class="links">{links}</div>
<div class="mode" role="group" aria-label="Colour mode"><button data-m="dark" class="on">Dark</button><button data-m="light">Light</button></div>
<button class="menu" aria-label="Menu">☰</button></nav>
{body}
<footer><span>{esc(site['name'])} · {esc(VERSION)}</span><span class="sp"></span>
<a href="{site['github']}">GitHub</a><a href="{site['r5book']}">R5Book</a><a href="{site['github']}/blob/main/THIRD_PARTY_NOTICES.md">Credits</a>
<span>R5 code MIT · logo artwork GPL-3.0-or-later · Manrope OFL</span></footer>
<script src="/assets/site.js?v={VERSION_STAMP}"></script>
</body></html>
"""
	target = OUT / path.strip("/") / "index.html" if path != "/404" else OUT / "404.html"
	target.parent.mkdir(parents=True, exist_ok=True)
	target.write_text(doc, encoding="utf-8")


# ------------------------------------------------------------ home

def scene(sec: dict, right: bool = False) -> str:
	hint = f'<p class="hint">{sec["hint"]}</p>' if sec.get("hint") else ""
	return (f'<section class="scene{" r" if right else ""}"><div class="txt"><div class="num">{sec["kicker"]}</div>'
			f'<h2>{sec["title"]}</h2><p>{sec["text"]}</p>{hint}</div>'
			f'<div class="stage">{shot(sec["shot"])}</div></section>')


def build_home() -> None:
	h = C["home"]
	hero = h["hero"]
	extra = f'<div class="small">{shot(hero["extra"])}</div>' if hero.get("extra") and hero["extra"] in SHOTS else ""
	if hero.get("deskbar") and hero["deskbar"] in SHOTS:
		extra += f'<div class="db">{shot(hero["deskbar"])}</div>'
	body = (f'<section class="hero"><div class="txt"><div class="num">{hero["kicker"]}</div><h1>{hero["title"]}</h1>'
			f'<p>{hero["text"]}</p><span class="pill">{esc(VERSION)} · {hero["pill"]}</span></div>'
			f'<div class="stage">{shot(hero["shot"])}{extra}</div></section>')
	body += scene(h["graphics"], right=True)

	t = h["theming"]
	def chips(items: list[dict], first: bool) -> str:
		out = []
		for i, c in enumerate(items):
			s = SHOTS.get(c["shot"])
			if not s:
				warnings.append(f"Make it yours: screenshot '{c['shot']}' is missing")
				continue
			on = " on" if first and not out else ""
			quiet = " quiet" if c.get("quiet") else ""
			out.append(f'<button class="{(on + quiet).strip()}" data-light="{s["light"]}" data-dark="{s["dark"]}" '
					   f'data-cap="{esc(c["caption"])}">{esc(c["label"])}</button>')
		return "".join(out)
	first = next((SHOTS[c["shot"]] for c in t["deskbar"] if c["shot"] in SHOTS), None)
	if first:
		body += (f'<section class="theming"><div class="a-wrap"><div><div class="num">{t["kicker"]}</div>'
				 f'<h2>{t["title"]}</h2><p>{t["text"]}</p>'
				 f'<div class="chiplabel">Deskbar</div><div class="chips">{chips(t["deskbar"], True)}</div>'
				 f'<div class="chiplabel">Windows</div><div class="chips">{chips(t["windows"], False)}</div>'
				 f'<div class="cap" id="cap" aria-live="polite">{esc(t["deskbar"][0]["caption"])}</div></div>'
				 f'<div class="screen"><img id="screen" src="{first["dark"]}" width="{first["w"]}" height="{first["h"]}" '
				 f'alt="The R5 desktop"></div></div></section>')

	f = h["features"]
	items = []
	# Small pictures only once every point has one; otherwise the rows go crooked.
	all_shots = all(it.get("shot") in SHOTS for it in f["item"])
	if not all_shots:
		warnings.append("The short version: pictures stay hidden until every point has its screenshot")
	for it in f["item"]:
		thumb = f'<div class="thumb">{shot(it["shot"])}</div>' if all_shots else ""
		items.append(f'<div>{thumb}<b>{it["title"]}</b>{it["text"]}</div>')
	body += (f'<section class="features"><div class="num">{f["kicker"]}</div><h2>{f["title"]}</h2>'
			 f'<div class="grid">{"".join(items)}</div></section>')

	body += scene(h["play"])
	body += scene(h["settings"], right=True)

	strip = [shot(s["name"]) for s in C["shot"] if s.get("gallery", True) and s["name"] in SHOTS]
	if strip:
		body += (f'<section class="strip"><div class="row">{"".join(strip * 2)}</div>'
				 f'<a class="btn o" href="/screenshots/">All screenshots →</a></section>')

	n = h.get("needyou")
	if n:
		lines = "".join(f'<div class="{esc(k)}">{esc(t)}</div>' for k, t in n["log"])
		body += (f'<section class="needyou"><div class="term" aria-label="Boot log"><div class="lines">{lines}</div>'
				 f'<span class="cursor"></span></div><div><div class="num">{n["kicker"]}</div><h2>{n["title"]}</h2>'
				 f'<p>{n["text"]}</p><p><span class="soon">{n["soon"]}</span></p>'
				 f'<a class="btn" href="{C["site"]["github"]}">{n["button"]}</a></div></section>')

	e = h["end"]
	body += (f'<section class="end"><div><div class="num">{e["kicker"]}</div><h2>{e["title"]}</h2><p>{e["text"]}</p>'
			 f'<a class="btn" href="{C["site"]["github"]}">{e["button"]}</a>'
			 f'<a class="btn o" href="/whats-new/">{e["button2"]}</a></div></section>')

	page("/", "", body)


# ------------------------------------------------------------ screenshots page

def build_shots() -> None:
	s = C["screenshots"]
	tabs = '<button data-f="all" class="on">All</button>' + "".join(
		f'<button data-f="{esc(t)}">{esc(t)}</button>' for t in s["filters"])
	figs = []
	for spec in C["shot"]:
		if not spec.get("gallery", True) or spec["name"] not in SHOTS:
			continue
		cap = spec.get("caption", "")
		title, _, rest = cap.partition(" — ")
		capt = f"<b>{esc(title)}</b> — {esc(rest)}" if rest else esc(cap)
		figs.append(f'<figure data-tags="{esc(" ".join(spec.get("tags", [])))}">{shot(spec["name"])}'
					f'<figcaption>{capt}</figcaption></figure>')
	body = (f'<main class="page"><div class="num">{s["kicker"]}</div><h2>{s["title"]}</h2><p>{s["text"]}</p>'
			f'<div class="tabs">{tabs}</div><div class="gallery">{"".join(figs)}</div></main>'
			f'<div class="box"><img alt=""></div>')
	page("/screenshots/", "Screenshots", body, "/screenshots/")


# ------------------------------------------------------------ what's new

def parse_whatsnew() -> list[dict]:
	p = ROOT / "data" / "WHATSNEW"
	if not p.exists():
		warnings.append("data/WHATSNEW missing: run tools/fetch.py")
		return []
	builds, cur = [], None
	for ln in p.read_text(encoding="utf-8").splitlines():
		m = re.match(r"^R5 (\S+) Build (\d+) - (.+)$", ln.strip())
		if m:
			cur = {"version": m[1], "build": m[2], "title": m[3], "text": []}
			builds.append(cur)
		elif cur is not None and ln.strip():
			cur["text"].append(ln.strip())
	return builds


def build_whatsnew() -> None:
	w = C["whatsnew"]
	tabs = lambda on: (f'<div class="tabs"><a href="/whats-new/"{" class=\"on\"" if on == 1 else ""}>{w["tab1"]}</a>'
					   f'<a href="/whats-new/changes/"{" class=\"on\"" if on == 2 else ""}>{w["tab2"]}</a></div>')
	images = {str(k): v for k, v in w.get("images", {}).items()}
	rows = []
	for i, b in enumerate(parse_whatsnew()):
		tag = ' <span class="tag">LATEST</span>' if i == 0 else ""
		img = shot(images[b["build"]]) if b["build"] in images else ""
		text = "".join(f"<p>{esc(t)}</p>" for t in b["text"])
		rows.append(f'<div class="build" id="build-{b["build"]}"><div class="n">{b["build"]}<small>{esc(b["version"])}</small></div>'
					f'<div><h3>{esc(b["title"])}{tag}</h3>{text}</div><div>{img}</div></div>')
	first, rest = rows[:12], rows[12:]
	older = f'<details class="older"><summary>Older builds ({len(rest)})</summary>{"".join(rest)}</details>' if rest else ""
	body = (f'<main class="page"><div class="num">{w["kicker"]}</div><h2>{w["title"]}</h2><p class="lead">{w["text"]}</p>'
			f'{tabs(1)}<div class="builds">{"".join(first)}</div>{older}</main>')
	page("/whats-new/", "What's new", body, "/whats-new/")

	prs_path = ROOT / "data" / "prs.json"
	prs = json.loads(prs_path.read_text(encoding="utf-8")) if prs_path.exists() else []
	since = w.get("changes_since") or ""
	prs = [p for p in prs if p["merged"][:10] >= since]
	days: dict[str, list] = {}
	for p in prs:
		days.setdefault(p["merged"][:10], []).append(p)
	areas = sorted({p["area"] for p in prs})
	ftabs = '<button data-f="all" class="on">All</button>' + "".join(
		f'<button data-f="{esc(a.replace(" ", "-"))}">{esc(a)}</button>' for a in areas)
	out = []
	for d, ps in days.items():
		label = datetime.date.fromisoformat(d).strftime("%d %b %Y").lstrip("0")
		items = "".join(
			f'<div class="pr" data-tags="{esc(p["area"].replace(" ", "-"))}"><span class="k">{esc(p["area"])}</span>'
			f'<a href="{esc(p["url"])}">{esc(p["title"])}</a><span class="no">#{p["number"]}</span>'
			+ (f'<p>{esc(p["intro"])}</p>' if p["intro"] else "") + "</div>" for p in ps)
		out.append(f'<div class="day"><div><h4>{label}</h4><span class="hint">{len(ps)} merged</span></div><div>{items}</div></div>')
	body = (f'<main class="page"><div class="num">{w["kicker"]}</div><h2>{w["changes_title"]}</h2>'
			f'<p class="lead">{w["changes_text"]}</p>{tabs(2)}<div class="tabs">{ftabs}</div>'
			f'<div class="builds">{"".join(out)}</div></main>')
	page("/whats-new/changes/", w["changes_title"], body, "/whats-new/")


# ------------------------------------------------------------ developers, download, 404

def build_developers() -> None:
	d = C["developers"]
	cards = "".join(f'<div class="card"><h3>{c["title"]}</h3><p>{c["text"]}</p><a href="{url(c["url"])}">{c["link"]}</a></div>'
					for c in d["card"])
	kits = "".join(f"<li>{k}</li>" for k in d["kits"])
	body = (f'<main class="page"><div class="num">{d["kicker"]}</div><h2>{d["title"]}</h2><p class="lead">{d["text"]}</p>'
			f'<div class="cols">{cards}</div><h3 style="margin-top:70px;font-size:28px">{d["kits_title"]}</h3>'
			f'<ul class="kits">{kits}</ul></main>')
	page("/developers/", "Developers", body, "/developers/")


def build_download() -> None:
	d = C["download"]
	body = (f'<main class="page"><div class="num">{d["kicker"]}</div><p class="egg">{d["title"]}</p>'
			f'<p class="lead" style="margin-top:20px">{d["text"]}</p>'
			f'<a class="btn" href="{C["site"]["github"]}/releases">{d["button"]}</a>'
			f'<a class="btn o" href="/whats-new/">{d["button2"]}</a>'
			f'<div class="status"><div><b><span class="dot"></span>{d["status_label"]}</b><span>{d["status"]}</span></div></div></main>')
	page("/download/", "Download", body, "/download/")


def build_r5book() -> None:
	"""Copy the R5Book from r5os (fetched by tools/fetch.py) to /r5book/.

	Links that leave docs/r5book are fixed up: files we fetched are copied next to
	the book, Markdown and anything else point to the file on GitHub."""
	repo = ROOT / "data" / "r5os"
	src = repo / "docs" / "r5book"
	if not src.exists():
		warnings.append("R5Book not fetched: run tools/fetch.py")
		return
	dst = OUT / "r5book"
	shutil.copytree(src, dst, ignore=shutil.ignore_patterns("README.md"))
	blob = C["site"]["github"] + "/blob/main/"

	def fix(m: re.Match) -> str:
		attr, rel = m.group(1), m.group(2)
		target = (src / rel).resolve()
		try:
			inrepo = target.relative_to(repo.resolve()).as_posix()
		except ValueError:
			return m.group(0)
		if target.is_file() and target.suffix != ".md":
			out = dst / "_r5os" / inrepo
			out.parent.mkdir(parents=True, exist_ok=True)
			shutil.copyfile(target, out)
			return f'{attr}="/r5book/_r5os/{inrepo}"'
		if not target.exists():
			warnings.append(f"R5Book links to a missing file: {inrepo}")
		return f'{attr}="{blob}{inrepo}"'

	for page_file in dst.glob("*.html"):
		text = page_file.read_text(encoding="utf-8")
		new = re.sub(r'(href|src)="(\.\./[^"#?]*)"', fix, text)
		if new != text:
			page_file.write_text(new, encoding="utf-8")


def build_404() -> None:
	body = ('<main class="page"><div class="num">404</div><p class="egg">Lost?</p>'
			'<p class="lead" style="margin-top:20px">This page does not exist. Not even in Tracker.</p>'
			'<a class="btn" href="/">Back home</a></main>')
	page("/404", "Not found", body)


# ------------------------------------------------------------ main

def main() -> None:
	global VERSION, VERSION_STAMP
	vfile = ROOT / "data" / "version.json"
	v = json.loads(vfile.read_text()) if vfile.exists() else {"version": C["site"]["version"], "build": ""}
	VERSION = f"{v['version']} · Build {v['build']}" if v.get("build") else v["version"]
	VERSION_STAMP = hashlib.sha1(((ROOT / "assets" / "site.css").read_bytes()
								 + (ROOT / "assets" / "site.js").read_bytes())).hexdigest()[:8]
	if OUT.exists():
		shutil.rmtree(OUT)
	OUT.mkdir()
	shutil.copytree(ROOT / "assets", OUT / "assets")
	(OUT / ".nojekyll").write_text("")
	load_shots()
	build_home()
	build_shots()
	build_whatsnew()
	build_developers()
	build_download()
	build_r5book()
	build_404()
	for w in warnings:
		print("note:", w)
	missing = [s["name"] for s in C["shot"] if s["name"] not in SHOTS]
	if missing:
		print("screenshots not made yet:", ", ".join(missing))
	print(f"built {OUT} with {len(SHOTS)} screenshots")


VERSION = ""
VERSION_STAMP = ""
if __name__ == "__main__":
	main()
