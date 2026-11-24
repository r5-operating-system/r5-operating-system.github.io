# R5 Operating System website

The website of the R5 Operating System, published at
<https://r5-operating-system.github.io/> by GitHub Pages.
The operating system itself lives in [r5-operating-system/r5os](https://github.com/r5-operating-system/r5os).

## Zo pas je de site aan

**Teksten:** open `content.toml` op github.com, klik op het potloodje, pas de tekst aan
en klik op *Commit changes*. Binnen een paar minuten staat het op de site.

**Een screenshot toevoegen:**
1. Maak een screenshot van het hele scherm in R5, op de standaard blauwe achtergrond.
2. Geef hem een naam, bijvoorbeeld `tracker-light.png` en `tracker-dark.png`
   (of alleen `tracker.png` als er maar één is).
3. Op github.com: open de map `screenshots`, *Add file* → *Upload files*, sleep hem erin, *Commit changes*.
4. Zet in `content.toml` een blok erbij:
   ```toml
   [[shot]]
   name = "tracker"
   caption = "Tracker — your files, the way you like them."
   tags = ["Look"]
   ```
Het venster wordt automatisch uitgeknipt. Lukt dat niet (andere achtergrond),
dan toont de site het hele scherm.

**Een screenshot vervangen:** upload een nieuw bestand met precies dezelfde naam.
**Weghalen:** verwijder het bestand en het blok in `content.toml`.

**What's new** en **What have we been up to?** komen vanzelf uit r5os
(`distro/WHATSNEW` en de gemergede pull requests), elke dag en bij elke wijziging.

## Build it yourself

Needs Python 3.12 or newer and Pillow.

```sh
python tools/fetch.py          # What's new, version and pull requests from r5os (uses gh)
python build.py                # writes _site/
python -m http.server 8000 -d _site
```

`.github/workflows/pages.yml` does the same on GitHub and publishes `_site/`.

## Licences

- Site code (`build.py`, `tools/`, `assets/site.*`): MIT.
- R5 logo (`assets/img/r5-symbol*`): R5 artwork, GPL-3.0-or-later.
- Manrope (`assets/fonts/`): SIL Open Font License 1.1, see `assets/fonts/OFL.txt`.
- Screenshots show R5; they follow the licences of what they show.
