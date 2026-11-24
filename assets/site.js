// SPDX-FileCopyrightText: 2026 R5OS Contributors
// SPDX-License-Identifier: MIT

// Dark/Light switch, remembered between pages (the <head> sets it before drawing).
const setMode = m => {
	document.documentElement.classList.toggle('light', m === 'light');
	document.querySelectorAll('.mode button').forEach(b => b.classList.toggle('on', b.dataset.m === m));
	try { localStorage.r5mode = m; } catch (e) {}
	document.dispatchEvent(new Event('r5mode'));
};
document.querySelectorAll('.mode button').forEach(b => b.onclick = () => setMode(b.dataset.m));
setMode(document.documentElement.classList.contains('light') ? 'light' : 'dark');

// Phone menu
const menu = document.querySelector('.menu');
if (menu) menu.onclick = () => document.querySelector('nav').classList.toggle('open');

// Windows rise in as their scene scrolls into view
const io = new IntersectionObserver(es => es.forEach(e => e.target.classList.toggle('in', e.isIntersecting)), {threshold: .2});
document.querySelectorAll('.scene,.hero').forEach(s => { s.classList.add('reveal'); io.observe(s); });

// Make it yours: chips swap the screen picture
const screenImg = document.getElementById('screen');
if (screenImg) {
	const chips = document.querySelectorAll('.chips button');
	let cur = document.querySelector('.chips button.on');
	const paint = () => {
		const want = document.documentElement.classList.contains('light') ? cur.dataset.light : cur.dataset.dark;
		if (screenImg.getAttribute('src') === want) return;
		screenImg.style.opacity = 0;
		setTimeout(() => { screenImg.src = want; screenImg.style.opacity = 1; }, 200);
	};
	chips.forEach(b => b.onclick = () => {
		cur = b; chips.forEach(x => x.classList.toggle('on', x === b));
		document.getElementById('cap').textContent = b.dataset.cap; paint();
	});
	document.addEventListener('r5mode', paint);
	paint();
}

// Screenshots page: filter and enlarge
document.querySelectorAll('.tabs button').forEach(b => b.onclick = () => {
	document.querySelectorAll('.tabs button').forEach(x => x.classList.toggle('on', x === b));
	document.querySelectorAll('[data-tags]').forEach(f =>
		f.style.display = b.dataset.f === 'all' || f.dataset.tags.split(' ').includes(b.dataset.f) ? '' : 'none');
});
const box = document.querySelector('.box');
if (box) {
	document.querySelectorAll('.gallery figure').forEach(f => f.onclick = () => {
		const light = document.documentElement.classList.contains('light');
		const img = f.querySelector(light ? '.l' : '.d') || f.querySelector('img');
		box.querySelector('img').src = img.src; box.classList.add('on');
	});
	box.onclick = () => box.classList.remove('on');
}
