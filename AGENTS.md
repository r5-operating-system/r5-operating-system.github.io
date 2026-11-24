# R5 website — rules for AI sessions

This repository is the website of the **R5 Operating System**: <https://r5-operating-system.github.io/>.
The operating system itself is `r5-operating-system/r5os` (local: `C:\Users\nickr\Projects\R5OS`). Do not change r5os from a website task.

## The owner

A product owner, not a developer. Answer in plain Dutch, short, with options and one recommendation. Tokens cost the owner money: grep instead of reading whole files, no long reports.
For a design change: show a mockup or a local preview first and ask "zo bouwen?". Do not push without an explicit OK.

## Name and honesty

- The product is **R5 Operating System**, short **R5**. Never Haiku or BeOS names or logos as the product name. "Built on Haiku" is fine as a fact.
- Only claim what ships. No download exists yet; the Download page says so. Planned work (installer, Software update, Appsolutely, cloud drives) is not mentioned unless the owner asks, and then only as "coming".
- Taglines: "Same soul. Fresh pixels." and "Yellow tabs. Modern everything."
- The site is in English. Playful and a bit cheeky, like the r5os README.
- No sentences that sound like AI filler. The owner removed "Tested on a real Ryzen 5 5625U laptop…" for that reason.

## The look (approved 24 Nov 2026, keep it)

- Concept "film": dark by default, big short headlines, one scene per screen, a Dark/Light switch top right (remembered).
- Windows cut out of real screenshots, no wallpaper. Shadow follows the background: light glow on dark, dark shadow on light.
- Home: first scene (Settings + sign-in + Deskbar), Graphics, "Make it yours" (one big screen with buttons: Deskbar Standard/Round/Pill/Bar, Windows R5/R5 Modern/Classic), "The short version" (10 points), Play, Settings, a screenshot strip, "Not out yet."
- Rejected by the owner, do not bring back: the travelling yellow tab, the credits roll, a boot intro, cut-out Deskbar shapes on a dark background (the bar disappears).
- Font Manrope (self-hosted), accent `#0084ff`, yellow tab `#ffd84d`, favicon the R5 wave pebble.

## Where things are

| What | Where |
|---|---|
| All texts, the features, the scenes, the screenshot list | `content.toml` |
| Screenshots (owner drops PNGs here) | `screenshots/<name>-light.png`, `<name>-dark.png` or `<name>.png` |
| Which screenshots are still wanted | `SCREENSHOTS-TO-MAKE.md` |
| Page layout (HTML is generated here) | `build.py` |
| Style and behaviour | `assets/site.css`, `assets/site.js` |
| Window cut-out | `tools/cutout.py` (flood fill of the blue R5 wallpaper; `area`, `keep_small`, `source`, `cut = false` per shot) |
| What's new, build number, pull requests, R5Book | fetched from r5os `main` by `tools/fetch.py` into `data/` |
| Publishing | `.github/workflows/pages.yml`: on push to `main`, daily 05:17 UTC, and by hand |

What's new is only as current as `distro/WHATSNEW` in r5os. If it is behind, that is an r5os task (new What's new section and `distro/BUILD` + 1), not a website change.

## Work loop

1. `git pull` first. Small diffs; change texts in `content.toml`, not in `build.py`.
2. Preview: `py tools/fetch.py` (only when fresh data is needed), `py build.py`, then serve `_site` on `127.0.0.1` and look at it in the browser pane, on a wide screen and at phone size (375 px), in Dark and Light.
3. Show the owner. Commit locally with the identity `r5-operating-system <232583956+nickrusman-bot@users.noreply.github.com>` and a plain-language message ("Website - what the visitor gets").
4. Ask before `git push`. After a push, the Action publishes in about two minutes; check the live page.
5. Only refresh (no change): `gh workflow run pages.yml -R r5-operating-system/r5-operating-system.github.io`, wait for the run, check the live site.

## Licences

Site code MIT (SPDX header in new files). R5 logo artwork GPL-3.0-or-later. Manrope OFL 1.1. Do not add third-party code, fonts or images without telling the owner the licence first. No external requests from the site (no Google Fonts, no trackers, no analytics) unless the owner asks.
