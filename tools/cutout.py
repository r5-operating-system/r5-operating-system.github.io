# SPDX-FileCopyrightText: 2026 R5OS Contributors
# SPDX-License-Identifier: MIT
"""Cut the windows out of an R5 screenshot taken on the standard blue wallpaper.

The wallpaper is clearly blue (blue well above red). Starting at the edge of the
picture, every connected wallpaper pixel becomes transparent. What is left are
the windows, the Deskbar and the desktop icons; parts much smaller than the
biggest window (the Deskbar, icons) are dropped too.

Returns None when the picture does not look like the R5 wallpaper, so the
caller can show the whole screen instead.
"""
from __future__ import annotations

from collections import deque

from PIL import Image, ImageFilter


def _is_wallpaper(p) -> bool:
	return p[2] - p[0] >= 35


def cut(im: Image.Image, keep_small: bool = False) -> Image.Image | None:
	im = im.convert("RGB")
	w, h = im.size
	px = im.load()
	bg = bytearray(w * h)
	queue = deque()
	for x in range(w):
		queue.append((x, 0))
		queue.append((x, h - 1))
	for y in range(h):
		queue.append((0, y))
		queue.append((w - 1, y))
	while queue:
		x, y = queue.popleft()
		i = y * w + x
		if bg[i] or not _is_wallpaper(px[x, y]):
			continue
		bg[i] = 1
		if x > 0:
			queue.append((x - 1, y))
		if x < w - 1:
			queue.append((x + 1, y))
		if y > 0:
			queue.append((x, y - 1))
		if y < h - 1:
			queue.append((x, y + 1))

	if sum(bg) < w * h * 0.15:
		return None  # hardly any wallpaper: not an R5 desktop shot

	if not keep_small:
		label = [0] * (w * h)
		sizes = []
		for start in range(w * h):
			if bg[start] or label[start]:
				continue
			sizes.append(0)
			n = len(sizes)
			label[start] = n
			stack = [start]
			while stack:
				i = stack.pop()
				sizes[n - 1] += 1
				x = i % w
				for j in (i - 1 if x > 0 else -1, i + 1 if x < w - 1 else -1, i - w, i + w):
					if 0 <= j < w * h and not bg[j] and not label[j]:
						label[j] = n
						stack.append(j)
		if not sizes:
			return None
		biggest = max(sizes)
		for i in range(w * h):
			if label[i] and sizes[label[i] - 1] < biggest * 0.15:
				bg[i] = 1

	alpha = Image.frombytes("L", (w, h), bytes(0 if b else 255 for b in bg))
	alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.6))
	box = alpha.getbbox()
	if not box:
		return None
	out = im.convert("RGBA")
	out.putalpha(alpha)
	return out.crop(box)
