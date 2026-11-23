/* Worldmap settings – no dependencies. All text from the API is escaped before it reaches the DOM. */
'use strict';
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const NEON = ['#0A7CFF', '#FF3D9A', '#8B3DFF', '#00BFB3', '#FF8A00', '#12A84F', '#E03131', '#5C7CFA'];
const CONF = ['tief', 'mittel', 'hoch', 'bestätigt'];
const EMBED = new URLSearchParams(location.search).get('embed');
function applyTheme() { let t = 'auto'; try { t = localStorage.getItem('wm-theme') || 'auto'; } catch (e) { /* ignore */ } document.documentElement.dataset.theme = t === 'dark' || (t === 'auto' && matchMedia('(prefers-color-scheme: dark)').matches) ? 'dark' : 'light'; }
applyTheme();
window.addEventListener('storage', (e) => { if (e.key === 'wm-theme') applyTheme(); });
const st = {cfg: null, trips: [], questions: [], sort: ['start_date', -1], filter: {}, sel: new Set()};

async function api(path, opt = {}) {
  const r = await fetch(path, opt);
  const ct = r.headers.get('Content-Type') || '';
  const body = ct.includes('json') ? await r.json() : await r.text();
  if (!r.ok) throw new Error(body && body.error ? body.error : `HTTP ${r.status}`);
  return body;
}
const post = (path, data, method = 'POST') => api(path, {method, headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data ?? {})});
function toast(msg, ms = 2600) { const t = $('toast'); t.textContent = msg; t.hidden = false; clearTimeout(toast.t); toast.t = setTimeout(() => (t.hidden = true), ms); }
function paint(root = document) { root.querySelectorAll('[data-c]').forEach((el) => el.style.setProperty('--c', el.dataset.c)); }
function notifyParent(type) { try { if (EMBED && window.parent !== window) window.parent.postMessage({type: 'worldmap-' + type}, location.origin); } catch (e) { /* ignore */ } }
const fmtD = (d) => { if (!d) return ''; const [y, m, dd] = d.split('-'); return `${dd}.${m}.${y}`; };

function whoList() { return st.cfg ? [...st.cfg.persons, ...st.cfg.who_options.filter((o) => !st.cfg.persons.includes(o))] : []; }
function colorOf(who) {
  if (st.cfg && st.cfg.colors && st.cfg.colors[who]) return st.cfg.colors[who];
  const l = whoList(); const i = l.indexOf(who);
  if (i >= 0) return NEON[i % NEON.length];
  let h = 0; for (const c of String(who)) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return who ? NEON[h % NEON.length] : '#9AA0B8';
}

/* ---------- tabs ---------- */
function showTab(name) {
  document.querySelectorAll('.trpop').forEach((x) => x.remove());
  document.querySelectorAll('nav button').forEach((b) => b.classList.toggle('on', b.dataset.tab === name));
  document.querySelectorAll('.tab').forEach((t) => t.classList.toggle('on', t.id === 'tab-' + name));
  if (name === 'people') loadPeople();
  if (name === 'style') loadStyle();
  if (name === 'connectors') loadConnectors();
  if (name === 'notify') loadNotify();
  if (name === 'rules') loadRules();
  if (name === 'import') loadImports();
  if (!EMBED) history.replaceState(null, '', '#' + name);
}
$('tabs').addEventListener('click', (e) => { const b = e.target.closest('button[data-tab]'); if (b) showTab(b.dataset.tab); });

/* ================================================================ GRID (Excel style) */
const COLS = [
  {k: 'start_date', n: 'Von', t: 'date', w: 110}, {k: 'end_date', n: 'Bis', t: 'date', w: 110},
  {k: 'destination', n: 'Ziel', w: 220}, {k: 'country', n: 'Land', w: 120},
  {k: 'who', n: 'Wer', t: 'who', w: 130}, {k: 'confidence', n: 'Sicherheit', t: 'conf', w: 110},
  {k: 'nights', n: 'Nächte', t: 'num', w: 70}, {k: 'max_km', n: 'km', t: 'num', w: 80},
  {k: 'transport', n: 'Verkehrsmittel', t: 'tr', w: 170}, {k: 'note', n: 'Notiz', w: 200}, {k: 'source', n: 'Quelle', w: 110},
];
function gridHead() {
  $('grid').tHead.innerHTML = `<tr><th class="sel"><input type="checkbox" id="selAll" aria-label="Alle auswählen"></th>${COLS.map((c) => `<th data-k="${c.k}" style="min-width:${c.w}px" class="${st.sort[0] === c.k ? (st.sort[1] > 0 ? 'asc' : 'desc') : ''}">${c.n}</th>`).join('')}</tr>
  <tr class="filters"><th></th>${COLS.map((c) => { const opts = c.t === 'who' ? [...new Set([...whoList(), ...st.trips.map((t) => t.who).filter(Boolean)])] : c.t === 'tr' ? TRANSPORT : c.t === 'conf' ? CONF : null;
    if (opts) return `<th><select data-f="${c.k}" aria-label="Filter ${c.n}"><option value="">alle</option>${opts.map((o) => `<option ${st.filter[c.k] === o ? 'selected' : ''}>${esc(o)}</option>`).join('')}</select></th>`;
    return `<th><input data-f="${c.k}" placeholder="Filter" value="${esc(st.filter[c.k] || '')}" aria-label="Filter ${c.n}"></th>`; }).join('')}</tr>`;
  $('grid').tHead.querySelectorAll('th[data-k]').forEach((th) => (th.onclick = () => { const k = th.dataset.k; st.sort = [k, st.sort[0] === k ? -st.sort[1] : 1]; gridHead(); gridBody(); }));
  $('grid').tHead.querySelectorAll('[data-f]').forEach((inp) => (inp.oninput = () => { st.filter[inp.dataset.f] = inp.value; gridBody(); }));
  $('selAll').onchange = (e) => { st.sel = e.target.checked ? new Set(visibleRows().map((t) => t.id)) : new Set(); gridBody(); };
}
function cellText(t, c) { const v = t[c.k]; if (c.t === 'date') return fmtD(v); if (c.k === 'max_km' && v != null) return String(Math.round(v)); return v ?? ''; }
function visibleRows() {
  const f = Object.entries(st.filter).filter(([, v]) => v && v.trim());
  const rows = st.trips.filter((t) => f.every(([k, v]) => { const c = COLS.find((x) => x.k === k); return String(cellText(t, c)).toLowerCase().includes(v.trim().toLowerCase()); }));
  const [k, dir] = st.sort;
  return rows.sort((a, b) => { const x = a[k] ?? '', y = b[k] ?? ''; return (typeof x === 'number' && typeof y === 'number' ? x - y : String(x).localeCompare(String(y), 'de')) * dir; });
}
function gridBody() {
  const rows = visibleRows();
  const whoOpts = [...new Set(['', ...whoList(), ...st.trips.map((t) => t.who)])];
  $('grid').tBodies[0].innerHTML = rows.map((t) => `<tr data-id="${t.id}" class="${t.status === 'ignored' ? 'ign' : ''}"><td class="sel"><input type="checkbox" ${st.sel.has(t.id) ? 'checked' : ''} aria-label="Zeile auswählen"></td>${COLS.map((c) => {
    if (c.t === 'who') return `<td><select data-k="who" data-c="${colorOf(t.who)}" class="who">${whoOpts.map((w) => `<option ${w === t.who ? 'selected' : ''} value="${esc(w)}">${esc(w || '– offen –')}</option>`).join('')}</select></td>`;
    if (c.t === 'tr') { const sel = trList(t.transport); return `<td class="trc"><button type="button" class="trbtn" data-k="transport" aria-label="Verkehrsmittel wählen">${sel.length ? sel.map((x) => `<span class="tpill">${TICON[x] || ''} ${esc(x)}</span>`).join('') : '<span class="small">wählen …</span>'}</button></td>`; }
    if (c.t === 'conf') return `<td><select data-k="confidence" class="conf-${esc(t.confidence)}">${CONF.map((x) => `<option ${x === t.confidence ? 'selected' : ''}>${x}</option>`).join('')}</select></td>`;
    return `<td contenteditable="true" spellcheck="false" data-k="${c.k}" class="${c.t === 'num' ? 'num' : ''}">${esc(cellText(t, c))}</td>`;
  }).join('')}</tr>`).join('');
  paint($('grid'));
  $('gridCount').textContent = `${rows.length} von ${st.trips.length} Reisen`;
  $('gridDel').disabled = !st.sel.size;
}
function parseCell(k, txt) {
  txt = txt.trim();
  if (k === 'start_date' || k === 'end_date') { const m = txt.match(/^(\d{1,2})\.(\d{1,2})\.(\d{4})$/); if (m) return `${m[3]}-${m[2].padStart(2, '0')}-${m[1].padStart(2, '0')}`; if (/^\d{4}-\d{2}-\d{2}$/.test(txt)) return txt; throw new Error('Datum als TT.MM.JJJJ'); }
  if (k === 'nights' || k === 'max_km') { if (!txt) return null; const n = Number(txt.replace(/['’\s]/g, '').replace(',', '.')); if (!Number.isFinite(n) || n < 0) throw new Error('Zahl erwartet'); return n; }
  return txt;
}
async function saveCell(tr, k, value, el) {
  const id = +tr.dataset.id; const t = st.trips.find((x) => x.id === id);
  try {
    const upd = await post('api/trips/' + id, {[k]: value}, 'PATCH');
    Object.assign(t, upd); el && el.classList.add('saved'); setTimeout(() => el && el.classList.remove('saved'), 700);
  } catch (e) { toast(e.message, 4000); gridBody(); }
}
$('grid').addEventListener('focusout', (e) => {
  const td = e.target.closest('td[data-k]'); if (!td) return;
  const tr = td.parentElement, t = st.trips.find((x) => x.id === +tr.dataset.id), k = td.dataset.k, c = COLS.find((x) => x.k === k);
  if (td.textContent === String(cellText(t, c))) return;
  let v; try { v = parseCell(k, td.textContent); } catch (err) { toast(err.message); td.textContent = cellText(t, c); return; }
  saveCell(tr, k, v, td);
});
$('grid').addEventListener('keydown', (e) => {
  const td = e.target.closest('td[data-k]'); if (!td) return;
  if (e.key === 'Enter') { e.preventDefault(); const tr = td.parentElement.nextElementSibling; const next = tr && tr.children[td.cellIndex]; (next || td).focus(); if (!next) td.blur(); }
  if (e.key === 'Escape') { const t = st.trips.find((x) => x.id === +td.parentElement.dataset.id); td.textContent = cellText(t, COLS.find((x) => x.k === td.dataset.k)); td.blur(); }
});
$('grid').addEventListener('change', (e) => {
  if (e.target.matches('td.sel input')) { const id = +e.target.closest('tr').dataset.id; e.target.checked ? st.sel.add(id) : st.sel.delete(id); $('gridDel').disabled = !st.sel.size; return; }
  const s = e.target.closest('select[data-k]'); if (s) { saveCell(s.closest('tr'), s.dataset.k, s.value, s); if (s.dataset.k === 'who') { s.dataset.c = colorOf(s.value); paint(s.parentElement); } }
});
/* transport: pick from a list instead of typing */
const TICON = {Auto: '🚗', Zug: '🚆', Flug: '✈️', Schiff: '⛴️', Wohnmobil: '🚐', Velo: '🚲', 'zu Fuss': '🚶', Bus: '🚌', Motorrad: '🏍️'};
function trList(v) { const parts = String(v || '').split(/\s*[·,/+]\s*/).map((x) => x.trim()).filter(Boolean);
  return parts.map((p) => TRANSPORT.find((o) => o.toLowerCase() === p.toLowerCase()) || p); }
function trPicker(btn) {
  document.querySelectorAll('.trpop').forEach((x) => x.remove());
  const tr = btn.closest('tr'), t = st.trips.find((x) => x.id === +tr.dataset.id); const chosen = new Set(trList(t.transport));
  const pop = document.createElement('div'); pop.className = 'trpop'; pop.setAttribute('role', 'dialog'); pop.setAttribute('aria-label', 'Verkehrsmittel');
  const extra = [...chosen].filter((x) => !TRANSPORT.includes(x));
  pop.innerHTML = `<div class="trgrid">${[...TRANSPORT, ...extra].map((o) => `<button type="button" class="tchip ${chosen.has(o) ? 'on' : ''}" data-v="${esc(o)}" aria-pressed="${chosen.has(o)}">${TICON[o] || '•'} ${esc(o)}</button>`).join('')}</div><div class="foot"><span class="small">mehrere möglich</span><button type="button" class="primary">Fertig</button></div>`;
  document.body.appendChild(pop); const r = btn.getBoundingClientRect(); pop.style.left = Math.min(window.innerWidth - pop.offsetWidth - 8, r.left) + 'px'; pop.style.top = Math.min(window.innerHeight - pop.offsetHeight - 8, r.bottom + 4) + 'px';
  const close = () => { pop.remove(); document.removeEventListener('mousedown', outside, true); const val = [...TRANSPORT, ...extra].filter((o) => chosen.has(o)).join(' · ');
    if (val !== (t.transport || '')) saveCell(tr, 'transport', val, null).then(() => gridBody()); };
  const outside = (e) => { if (!pop.contains(e.target)) close(); };
  pop.addEventListener('click', (e) => { const b = e.target.closest('.tchip'); if (b) { const v = b.dataset.v; chosen.has(v) ? chosen.delete(v) : chosen.add(v); b.classList.toggle('on'); b.setAttribute('aria-pressed', String(chosen.has(v))); } else if (e.target.closest('.primary')) close(); });
  pop.addEventListener('keydown', (e) => { if (e.key === 'Escape') close(); });
  setTimeout(() => document.addEventListener('mousedown', outside, true), 0); pop.querySelector('.tchip').focus();
}
$('grid').addEventListener('click', (e) => { const b = e.target.closest('.trbtn'); if (b) trPicker(b); });
/* paste rows straight from Excel / Google Sheets */
function tsvRows(text) { return text.replace(/\r/g, '').split('\n').filter((l) => l.trim()).map((l) => l.split('\t')); }
async function pasteRows(rows) {
  if (!rows.length) return;
  const looksHeader = rows[0].some((c) => /^(von|start|bis|ziel|hauptziel|destination)$/i.test(c.trim()));
  const all = looksHeader ? rows : [['Von', 'Bis', 'Ziel', 'Land', 'Wer', 'Sicherheit', 'Nächte', 'Entfernung', 'Verkehrsmittel', 'Notiz', 'Quelle'], ...rows];
  try { const r = await post('api/trips/bulk', {rows: all}); toast(`${r.trips_created} neu, ${r.trips_updated} aktualisiert${r.duplicates_in_file ? `, ${r.duplicates_in_file} doppelt` : ''}`, 4000); refresh(); } catch (e) { toast(e.message, 5000); }
}
document.addEventListener('paste', (e) => {
  const tgt = e.target instanceof Element ? e.target : null;
  if (!$('tab-trips').classList.contains('on') || (tgt && tgt.closest('td[data-k],input,textarea'))) return;
  const text = e.clipboardData.getData('text/plain'); if (!text.includes('\t')) return;
  e.preventDefault(); pasteRows(tsvRows(text));
});
$('gridPaste').onclick = () => {
  const d = $('pasteDlg');
  d.innerHTML = `<form class="dlg" method="dialog"><h2>Aus Excel einfügen</h2><p class="small">Zeilen in Excel/Google Sheets markieren, kopieren und hier einfügen. Erste Zeile mit Spaltennamen (Von, Bis, Ziel, Land, Wer …) oder genau diese Reihenfolge.</p><textarea id="pasteTxt" rows="10" class="mono" placeholder="Von&#9;Bis&#9;Ziel&#9;Land&#9;Wer"></textarea><div class="foot"><button value="cancel" class="btn">Abbrechen</button><button value="ok" class="primary">Einfügen</button></div></form>`;
  d.onclose = () => { if (d.returnValue === 'ok') pasteRows(tsvRows($('pasteTxt').value)); };
  d.returnValue = ''; d.showModal();
};
$('gridAdd').onclick = async () => {
  const today = new Date().toISOString().slice(0, 10);
  try { const t = await post('api/trips', {start_date: today, end_date: today, destination: 'Neue Reise', source: 'manual'}); st.trips.push(t); st.filter = {}; st.sort = ['id', -1]; gridHead(); gridBody(); const td = $('grid').querySelector(`tr[data-id="${t.id}"] td[data-k="destination"]`); if (td) { td.focus(); document.getSelection().selectAllChildren(td); } } catch (e) { toast(e.message); }
};
$('gridDel').onclick = async () => {
  if (!st.sel.size || !confirm(`${st.sel.size} Reise(n) löschen?`)) return;
  for (const id of st.sel) { try { await api('api/trips/' + id, {method: 'DELETE'}); } catch (e) { toast(e.message); } }
  st.sel.clear(); refresh();
};
$('gridClear').onclick = () => { st.filter = {}; gridHead(); gridBody(); };
$('gridIgnored').onchange = refresh;

/* ================================================================ QUESTIONS */
function renderQuestions() {
  const list = $('qlist');
  if (!st.questions.length) { list.innerHTML = `<div class="card"><h3>Alles beantwortet ✓</h3><p class="small">Neue Fragen erscheinen, sobald neue Reisen erkannt werden.</p>${EMBED ? '<div class="opts"><button class="primary" id="qdone">Zur Karte</button></div>' : ''}</div>`; const b = $('qdone'); if (b) b.onclick = () => notifyParent('close'); return; }
  list.innerHTML = `<p class="lead">${st.questions.length} ${st.questions.length === 1 ? 'Frage' : 'Fragen'} · Ähnliches ist zusammengefasst – eine Antwort gilt für alle.</p>` + st.questions.map((q) => {
    const group = q.trip_ids.length > 1;
    if (q.kind === 'place') return `<div class="card q" data-q="${q.id}"><h3>📍 ${esc(q.destination || 'Reise')}</h3><p>${esc(q.text)}</p>
    <div class="opts"><input class="qplace" maxlength="120" placeholder="z. B. Santorini, Costa Brava, Salou" aria-label="Ort, Insel oder Region"><button class="primary" data-place="1">Speichern</button></div>
    <div class="opts">${q.options.map((o) => `<button data-a="${esc(o)}" data-c="#8A82AA" class="meta">${esc(o)}</button>`).join('')}</div></div>`;
    return `<div class="card q" data-q="${q.id}"><h3>${group ? `<span class="status">${q.trip_ids.length}×</span>` : ''}${esc(q.destination || 'Reise')}</h3><p>${esc(q.text)}</p>
    <div class="opts">${q.options.map((o) => `<button data-a="${esc(o)}" data-c="${/^(Keine Reise|Mit Reise|Einzeln)/.test(o) ? '#8A82AA' : colorOf(o)}" class="${o === q.suggestion ? 'sug' : ''} ${/^(Keine Reise|Mit Reise|Einzeln)/.test(o) ? 'meta' : ''}">${esc(o)}</button>`).join('')}</div>
    <label class="check small"><input type="checkbox" class="remember" ${group ? 'checked' : ''}> für diesen Ort merken (künftig nicht mehr fragen)</label></div>`;
  }).join('');
  paint(list);
}
$('qlist').addEventListener('click', async (e) => {
  const b = e.target.closest('button[data-a],button[data-place]'); if (!b) return;
  const card = b.closest('[data-q]'); const id = card.dataset.q;
  const answer = b.dataset.place ? card.querySelector('.qplace').value.trim() : b.dataset.a;
  if (!answer) { toast('Bitte einen Ort eintippen'); return; }
  const rem = card.querySelector('.remember');
  try {
    const r = await post(`api/questions/${id}/answer`, {answer, remember: rem ? rem.checked : false});
    toast(r.split ? 'Einzeln gefragt' : r.merged_into ? 'Zusammengelegt' : `Gespeichert${r.trips > 1 ? ` für ${r.trips} Reisen` : ''}${r.rule ? ' · Regel gemerkt' : ''}`);
    notifyParent('changed'); refresh();
  } catch (err) { toast(err.message); }
});

$('qlist').addEventListener('keydown', (e) => { if (e.key === 'Enter' && e.target.classList.contains('qplace')) { e.preventDefault(); e.target.closest('[data-q]').querySelector('button[data-place]').click(); } });

/* ================================================================ IMPORT */
const drop = $('drop');
['dragenter', 'dragover'].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add('over'); }));
['dragleave', 'drop'].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove('over'); }));
drop.addEventListener('drop', (e) => [...e.dataTransfer.files].forEach(preview));
$('file').onchange = (e) => { [...e.target.files].forEach(preview); e.target.value = ''; };
async function upload(file, person, dry) {
  const mb = st.cfg ? st.cfg.max_upload_mb : 200;
  if (file.size > mb * 1048576) throw new Error(`Datei grösser als ${mb} MB`);
  return api(`api/import?dry_run=${dry ? 1 : 0}&person=${encodeURIComponent(person)}`, {method: 'POST', headers: {'Content-Type': 'application/octet-stream', 'X-Filename': file.name.replace(/[^\w.\-]/g, '_')}, body: file});
}
function closable(card) { const x = document.createElement('button'); x.className = 'x'; x.setAttribute('aria-label', 'Entfernen'); x.textContent = '✕'; x.onclick = () => card.remove(); card.prepend(x); }
async function preview(file) {
  const card = document.createElement('div'); card.className = 'card'; card.innerHTML = `<h3>${esc(file.name)}</h3><p class="small">wird geprüft …</p>`; $('imports').prepend(card); closable(card);
  const set = (html) => { card.innerHTML = html; closable(card); };
  try {
    const r = await upload(file, '', true);
    const cols = r.columns ? Object.entries(r.columns).map(([k, v]) => `${esc(k)} → ${esc(v)}`).join(', ') : '';
    const warn = (r.warnings || []).map((w) => `<p class="small warn">${esc(w)}</p>`).join('');
    if (r.kind === 'package') {
      const range = r.points ? `${new Date(r.first * 1000).toLocaleDateString('de-CH')} – ${new Date(r.last * 1000).toLocaleDateString('de-CH')}` : '';
      set(`<h3>${esc(file.name)} <span class="status ok">Worldmap-Paket</span></h3><p><b>${r.trips.toLocaleString('de-CH')}</b> Reisen mit „Wer war dabei“ · <b>${r.points.toLocaleString('de-CH')}</b> GPS-Positionen${range ? ' · ' + esc(range) : ''}</p>
      <p class="small">Personen: ${r.persons.map(esc).join(', ') || '–'} · Gruppen: ${r.groups.map(esc).join(', ') || '–'}</p>${r.missing.length ? `<p class="small warn">Lege zuerst unter <a href="#people">Personen &amp; Gruppen</a> an: <b>${r.missing.map(esc).join(', ')}</b> – sonst fehlen Farben und Zuordnung.</p>` : ''}${(r.warnings || []).filter((w) => !w.startsWith('not set up')).map((w) => `<p class="small warn">${esc(w)}</p>`).join('')}
      <div class="opts"><button class="primary go">Importieren</button></div>`);
    } else if (r.kind === 'trips') {
      set(`<h3>${esc(file.name)} <span class="status ok">Reiseliste</span></h3><p><b>${r.trips}</b> Reisen · ${fmtD(r.first)} – ${fmtD(r.last)} · <b>${r.located}</b> auf der Karte gefunden</p>${cols ? `<p class="small">Spalten: ${cols}</p>` : ''}${warn}
      <div class="opts"><button class="primary go">Importieren</button></div>`);
    } else {
      const range = `${new Date(r.first * 1000).toLocaleDateString('de-CH')} – ${new Date(r.last * 1000).toLocaleDateString('de-CH')}`;
      set(`<h3>${esc(file.name)} <span class="status ok">${esc(r.format)}</span></h3><p><b>${r.points.toLocaleString('de-CH')}</b> Positionen · ${esc(range)}${r.skipped ? ` · ${r.skipped} übersprungen` : ''}</p>${cols ? `<p class="small">Spalten: ${cols}</p>` : ''}${warn}
      <label class="field">Wessen Daten?<select class="who"><option value="">gemischt (Fotos: nach Kamera)</option>${(st.cfg?.persons || []).map((p) => `<option>${esc(p)}</option>`).join('')}</select></label>
      <div class="opts"><button class="primary go">Importieren</button></div>`);
    }
    card.querySelector('.go').onclick = async () => {
      const go = card.querySelector('.go'); go.disabled = true; go.textContent = 'importiere …';
      try {
        const x = await upload(file, card.querySelector('.who')?.value || '', false);
        card.querySelector('.opts').innerHTML = x.kind === 'package'
          ? `<span class="status ok">${x.trips_created || 0} Reisen neu, ${x.trips_updated || 0} aktualisiert</span> <span class="status ok">${x.new_points.toLocaleString('de-CH')} neue Positionen</span>`
          : x.kind === 'trips'
          ? `<span class="status ok">${x.trips_created} neu, ${x.trips_updated} aktualisiert${x.duplicates_in_file ? `, ${x.duplicates_in_file} doppelt in der Datei` : ''}</span>`
          : `<span class="status ok">${x.new_points.toLocaleString('de-CH')} neue Positionen</span> <span class="status">${(x.points - x.new_points).toLocaleString('de-CH')} schon vorhanden</span> ${x.rebuild ? `<span class="status">${x.rebuild.trips_created ?? 0} neue Reisen, ${x.rebuild.questions ?? 0} Fragen</span>` : ''}`;
        refresh(); loadImports();
      } catch (e) { card.querySelector('.opts').innerHTML = `<span class="status warn">${esc(e.message)}</span>`; }
    };
  } catch (e) { set(`<h3>${esc(file.name)}</h3><p><span class="status warn">${esc(e.message)}</span></p><p class="small">Erwartet wird ein Worldmap-Paket, eine Reiseliste (Spalten Von, Bis, Ziel …) oder GPS-Daten (Datum/Zeit + Breite/Länge).</p>`); }
}
async function loadImports() {
  try {
    const c = await api('api/connectors');
    $('pastImports').innerHTML = c.imports.length ? c.imports.map((i) => `<div class="card small-card" data-id="${i.id}"><button class="x" aria-label="Eintrag entfernen">✕</button><b>${esc(i.filename)}</b><p class="small">${esc(i.format)} · ${i.points.toLocaleString('de-CH')} · ${new Date(i.created_at * 1000).toLocaleString('de-CH')}</p></div>`).join('') : '<p class="small">Noch keine Importe.</p>';
    $('pastImports').querySelectorAll('.x').forEach((x) => (x.onclick = async () => { const card = x.closest('[data-id]'); try { await api('api/imports/' + card.dataset.id, {method: 'DELETE'}); card.remove(); } catch (e) { toast(e.message); } }));
  } catch (e) { /* ignore */ }
}

/* ================================================================ SETTINGS helpers */
const save = async (data, then) => { try { await post('api/connectors', data); toast('Gespeichert'); st.cfg = await api('api/config'); then && then(); } catch (e) { toast(e.message, 5000); } };
const ago = (ts) => (ts ? new Date(ts * 1000).toLocaleString('de-CH') : 'noch nie');
const lines = (id) => $(id).value.split('\n').map((s) => s.trim()).filter(Boolean);
function syncButtons(box) { box.querySelectorAll('[data-sync]').forEach((b) => (b.onclick = async () => { try { const r = await post('api/sync/' + b.dataset.sync); toast(r.started ? 'Läuft im Hintergrund …' : 'Läuft bereits'); } catch (e) { toast(e.message); } })); }

/* ================================================================ PEOPLE & GROUPS */
const PRESETS = {person: {type: 'p', label: ''}, couple: {type: 'g', label: 'Paar', all: true}, family: {type: 'g', label: 'Familie', all: true, extra: 2}, group: {type: 'g', label: ''}};
async function loadPeople() {
  const box = $('people');
  let c; try { c = await api('api/connectors'); } catch (e) { box.innerHTML = `<div class="card">${esc(e.message)}</div>`; return; }
  const ro = c.editable ? '' : '<p class="small warn keep">Speichern geht nur im Add-on (Supervisor nicht erreichbar).</p>';
  const persons = c.persons.map((p) => ({type: 'p', label: p.label, entity: p.entity || '', cams: p.camera_models || '', color: p.color || '', last: p.last_point}));
  const groups = (c.groups || []).filter((g) => !persons.some((p) => p.label === g.name)).map((g) => ({type: 'g', label: g.name, members: g.members || [], extra: g.extra || 0, color: g.color || ''}));
  const rows = [...persons, ...groups];
  const trackerOpts = (sel) => '<option value="">– kein Live-Standort –</option>' + c.trackers.map((t) => `<option value="${esc(t.entity)}" ${t.entity === sel ? 'selected' : ''}>${esc(t.name)}${t.has_gps ? '' : ' (ohne GPS)'}</option>`).join('') + (sel && !c.trackers.some((t) => t.entity === sel) ? `<option selected value="${esc(sel)}">${esc(sel)}</option>` : '');
  const pnames = () => rows.filter((r) => r.type === 'p' && r.label.trim()).map((r) => r.label.trim());
  const rowHTML = (r, i) => {
    const col = r.color || NEON[i % NEON.length];
    const head = `<select class="ty" aria-label="Art"><option value="p" ${r.type === 'p' ? 'selected' : ''}>👤 Einzelperson</option><option value="g" ${r.type === 'g' ? 'selected' : ''}>👥 Gruppe</option></select>
      <input class="nm" value="${esc(r.label)}" maxlength="40" placeholder="${r.type === 'p' ? 'Name, z. B. Alex' : 'Name, z. B. Familie'}" aria-label="Name">
      <input class="co" type="color" value="${esc(col)}" data-own="${r.color ? 1 : 0}" aria-label="Farbe" title="Eigene Farbe – ohne Wahl gilt die Farbpalette aus dem Kartenstil">`;
    const detail = r.type === 'p'
      ? `<label class="field">Live-Standort<select class="en">${trackerOpts(r.entity)}</select></label><label class="field">Kamera (für Foto-Importe)<input class="ca" value="${esc(r.cams)}" placeholder="z. B. iPhone 15"></label>${r.label ? `<p class="small keep">Letzte Position: ${esc(ago(r.last))}</p>` : ''}`
      : `<div class="field">Wer gehört dazu?<div class="chips mem">${pnames().map((n) => `<label class="chip ${(r.members || []).includes(n) ? '' : 'off'}" data-c="${colorOf(n)}"><input type="checkbox" ${(r.members || []).includes(n) ? 'checked' : ''} value="${esc(n)}" hidden><i></i>${esc(n)}</label>`).join('') || '<span class="small">Zuerst Einzelpersonen anlegen.</span>'}</div></div>
         <label class="field">+ ohne Handy (z. B. Kinder)<input class="ex" type="number" min="0" max="20" value="${r.extra || 0}"></label>`;
    return `<div class="who-row ${r.type}" data-i="${i}"><div class="who-head">${head}<button class="btn rm" type="button" aria-label="Entfernen" title="Entfernen">✕</button></div><div class="who-detail">${detail}</div></div>`;
  };
  const read = () => { box.querySelectorAll('.who-row').forEach((el) => { const r = rows[+el.dataset.i]; r.type = el.querySelector('.ty').value; r.label = el.querySelector('.nm').value; r.color = el.querySelector('.co').dataset.own === '1' ? el.querySelector('.co').value : '';
    if (el.querySelector('.en')) { r.entity = el.querySelector('.en').value; r.cams = el.querySelector('.ca').value; }
    if (el.querySelector('.mem')) { r.members = [...el.querySelectorAll('.mem input:checked')].map((x) => x.value); r.extra = +el.querySelector('.ex').value || 0; } }); };
  const draw = () => { $('wlist').innerHTML = rows.map(rowHTML).join('') || '<p class="small keep">Noch niemand – unten eine Vorlage wählen.</p>'; paint($('wlist')); };
  const h = c.home || {}, w = c.work || {};
  box.innerHTML = `
  <div class="card wide"><h3>👥 Personen &amp; Gruppen</h3>
    <p class="small">Einzelpersonen haben ein eigenes Handy (Live-Standort) oder eigene Importe. Gruppen sind die Antworten auf „Wer war dabei?“ – z. B. Paar oder Familie. Alle erscheinen oben in jeder Karte zum Antippen: eine Person zeigt alles, wo sie dabei war, eine Gruppe nur die gemeinsamen Reisen.</p>
    <details class="help"><summary>Live-Standort ohne Nabu Casa?</summary><p>Die Home-Assistant-App meldet nur, wenn das Handy Home Assistant erreicht. Ist Home Assistant nur im Heimnetz erreichbar, nimm <b>OwnTracks</b> (unter Verbindungen): es sammelt unterwegs und schickt alles zu Hause. Alternativen: VPN (WireGuard/Tailscale), Nabu Casa, oder ab und zu die Google-Zeitachse importieren.</p></details>
    <div id="wlist" class="wlist"></div>
    <div class="opts"><span class="small">Hinzufügen:</span><button class="btn" type="button" data-add="person">👤 Einzelperson</button><button class="btn" type="button" data-add="couple">👥 Paar</button><button class="btn" type="button" data-add="family">👨‍👩‍👧 Familie</button><button class="btn" type="button" data-add="group">👥 eigene Gruppe</button></div>
    <div class="opts"><button class="primary" id="saveW">Speichern</button><button class="btn" data-sync="ha">Verlauf aus HA holen</button></div>${ro}</div>
  <div class="card"><h3>🏠 Zuhause</h3>
    <p class="small">Von hier werden alle Entfernungen gemessen. Standard ist die Zuhause-Zone von Home Assistant. Der Umkreis bestimmt, was auf der Karte als „Zuhause“ zählt.</p>
    <p class="small keep">Aktuell: ${h.resolved ? 'bekannt' : 'unbekannt'} · Umkreis ${esc(h.radius_used_m)} m</p>
    <div class="prow two"><label class="field">Breitengrad (leer = Zone)<input id="hlat" inputmode="decimal" value="${h.lat ?? ''}" placeholder="aus ${esc(h.zone || 'zone.home')}"></label><label class="field">Längengrad<input id="hlon" inputmode="decimal" value="${h.lon ?? ''}"></label></div>
    <label class="field">Umkreis in Metern (0 = Radius der Zone)<input id="hrad" type="number" min="0" max="5000" step="50" value="${h.radius_m || 0}"></label>
    <label class="field">Heimatflughafen (IATA, leer = automatisch)<input id="hap" maxlength="3" autocapitalize="characters" value="${esc(h.airport || '')}" placeholder="z. B. ZRH"></label>
    <div class="opts"><button class="primary" id="saveH">Speichern</button></div></div>
  <div class="card"><h3>💼 Arbeit</h3>
    <p class="small">Die Arbeit zählt nie als Reise. Ohne Koordinaten wird sie automatisch erkannt (der Ort mit den meisten Stunden an Werktagen). Du entscheidest, ob sie auf der Karte erscheint.</p>
    <label class="check"><input type="checkbox" id="wshow" ${w.show ? 'checked' : ''}> Arbeit auf der Karte zeigen</label>
    <div class="prow two"><label class="field">Breitengrad (leer = automatisch)<input id="wlat" inputmode="decimal" value="${w.lat ?? ''}"></label><label class="field">Längengrad<input id="wlon" inputmode="decimal" value="${w.lon ?? ''}"></label></div>
    <label class="field">Umkreis in Metern<input id="wrad" type="number" min="50" max="5000" step="50" value="${w.radius_m || 300}"></label>
    <div class="opts"><button class="primary" id="saveWk">Speichern</button></div></div>`;
  draw(); infoize(box);
  box.querySelectorAll('[data-add]').forEach((b) => (b.onclick = () => { read(); const pr = PRESETS[b.dataset.add]; let label = pr.label; if (label && rows.some((r) => r.label === label)) label = '';
    rows.push({type: pr.type, label, entity: '', cams: '', color: '', members: pr.all ? pnames() : [], extra: pr.extra || 0}); draw(); const last = $('wlist').lastElementChild; if (last) last.querySelector('.nm').focus(); }));
  $('wlist').addEventListener('input', (e) => { if (e.target.matches('.co')) e.target.dataset.own = '1'; });
  $('wlist').addEventListener('change', (e) => { if (e.target.matches('.ty')) { read(); draw(); } else if (e.target.matches('.mem input')) e.target.closest('.chip').classList.toggle('off', !e.target.checked); });
  $('wlist').addEventListener('click', (e) => { if (e.target.closest('.rm')) { read(); rows.splice(+e.target.closest('.who-row').dataset.i, 1); draw(); } });
  $('saveW').onclick = () => { read();
    const ps = rows.filter((r) => r.type === 'p' && r.label.trim()), gs = rows.filter((r) => r.type === 'g' && r.label.trim());
    const names = [...ps, ...gs].map((r) => r.label.trim()); if (new Set(names).size !== names.length) return toast('Jeder Name darf nur einmal vorkommen');
    save({persons: ps.map((r) => ({label: r.label.trim(), entity: r.entity, camera_models: r.cams.trim(), color: r.color})),
      groups: gs.map((r) => ({name: r.label.trim(), members: (r.members || []).filter((m) => ps.some((p) => p.label.trim() === m)), extra: r.extra || 0, color: r.color}))}, loadPeople); };
  const num = (id) => ($(id).value.trim() === '' ? null : +$(id).value.replace(',', '.'));
  $('saveH').onclick = () => save({home_lat: num('hlat'), home_lon: num('hlon'), home_radius_m: +$('hrad').value || 0, home_airport: $('hap').value.trim().toUpperCase()}, loadPeople);
  $('saveWk').onclick = () => save({work_lat: num('wlat'), work_lon: num('wlon'), work_radius_m: +$('wrad').value || 300, show_work: $('wshow').checked}, loadPeople);
  syncButtons(box);
}
/* descriptions go behind a small (i) button so every card stays tidy */
let ibN = 0;
function infoize(root) {
  root.querySelectorAll('.card').forEach((card) => {
    const h = card.querySelector('h3'); if (!h || h.querySelector('.info')) return;
    const bits = [...card.children].filter((el) => el.matches('p.small,ol.small,ul.small,details.help') && !el.classList.contains('keep'));
    if (!bits.length) return;
    const box = document.createElement('div'); box.className = 'infobox'; box.hidden = true; box.id = 'ib-' + (++ibN);
    bits.forEach((b) => { if (b.tagName === 'DETAILS') { const sm = b.querySelector('summary'); const t = document.createElement('p'); const bb = document.createElement('b'); bb.textContent = sm.textContent; t.appendChild(bb); sm.remove(); box.appendChild(t); while (b.firstChild) box.appendChild(b.firstChild); b.remove(); } else box.appendChild(b); });
    const btn = document.createElement('button'); btn.className = 'info'; btn.type = 'button'; btn.textContent = 'i'; btn.setAttribute('aria-label', 'Erklärung'); btn.setAttribute('aria-expanded', 'false'); btn.setAttribute('aria-controls', box.id);
    btn.onclick = () => { box.hidden = !box.hidden; btn.setAttribute('aria-expanded', String(!box.hidden)); };
    h.appendChild(btn); h.after(box);
  });
}

/* ================================================================ MAP STYLE (with versions) */
const sty = {data: null, cur: null, saved: '', tab: 'reisen'};
const same = () => JSON.stringify(sty.cur) === sty.saved;
/* Map style: every setting of every map (stylespec.js), with the real map – your own data – as live preview */
async function loadStyle() {
  const box = $('style');
  try { sty.data = await api('api/style'); } catch (e) { box.innerHTML = `<div class="card">${esc(e.message)}</div>`; return; }
  sty.cur = JSON.parse(JSON.stringify(sty.data.style)); sty.saved = JSON.stringify(sty.cur);
  renderStyle();
}
function renderStyle() {
  const box = $('style'), c = sty.cur;
  const tabs = [['reisen', 'Reisen'], ['spuren', 'Spuren'], ['orte', 'Orte & Tage'], ['regionen', 'Regionen'], ['zeit', 'Reisefilm']];
  box.innerHTML = `<div class="style-grid">
   <div class="style-main" id="stForm">
    <div class="card">${wmModes(c)}<p class="small">Gilt für alle Karten. Personen- und Gruppenfarben stellst du unter „Personen &amp; Gruppen“ ein.</p></div>
    ${WM_SPEC.map((x) => `<div class="card">${wmSection(x, c)}</div>`).join('')}
   </div>
   <div class="style-side">
    <div class="card sticky"><h3>👀 Live auf deiner Karte <span class="status" id="stState"></span></h3>
      <div class="wseg" id="stTabs" role="tablist">${tabs.map(([k, n]) => `<button type="button" class="${k === sty.tab ? 'on' : ''}" data-tab="${k}">${n}</button>`).join('')}</div>
      <iframe id="stLive" class="stlive" title="Live-Vorschau der Karte" src="./?embed=1#${sty.tab}"></iframe>
      <p class="small">Jede Änderung siehst du sofort hier – mit deinen eigenen Reisen. Gespeichert wird erst mit „Speichern“.</p>
      <label class="field">Notiz zu dieser Version (optional)<input id="stNote" maxlength="80" placeholder="z. B. Zug gepunktet"></label>
      <div class="opts"><button class="primary" id="stSave">Speichern</button><button class="btn" id="stUndo">Verwerfen</button><button class="btn" id="stDef">Standard</button><a class="btn" href="./">Karte öffnen</a></div></div>
    <div class="card"><h3>🕘 Versionen <span class="status">${sty.data.versions.length}</span></h3>
      <p class="small">Jedes Speichern legt eine Version an (die letzten 20 bleiben). Mit „Zurück“ holst du einen früheren Stil wieder – auch das wird wieder eine Version, nichts geht verloren.</p>
      <div class="vlist">${sty.data.versions.map((v, i) => `<div class="vrow"><div><b>${esc(v.note)}</b><span class="small">${new Date(v.ts * 1000).toLocaleString('de-CH', {dateStyle: 'medium', timeStyle: 'short'})}${i === 0 ? ' · aktuell' : ''}</span></div>${i === 0 ? '' : `<button class="btn" data-restore="${v.id}">Zurück</button>`}</div>`).join('') || '<p class="small keep">Noch keine – nach dem ersten Speichern erscheinen sie hier.</p>'}</div></div>
   </div></div>`;
  wmBind($('stForm'), c, (k) => { if (k === 'map.theme') themeLocal(c.map.theme); styleChanged(); });
  $('stTabs').addEventListener('click', (e) => { const b = e.target.closest('button'); if (!b) return; sty.tab = b.dataset.tab;
    $('stTabs').querySelectorAll('button').forEach((x) => x.classList.toggle('on', x === b));
    try { $('stLive').contentWindow.location.hash = '#' + sty.tab; } catch (err) { $('stLive').src = './?embed=1#' + sty.tab; } });
  $('stLive').addEventListener('load', () => setTimeout(sendLive, 400));
  $('stSave').onclick = async () => { try { sty.data = await post('api/style', {style: sty.cur, note: $('stNote').value}); themeLocal(sty.cur.map.theme); toast('Gespeichert – neue Version angelegt'); loadStyle(); } catch (e) { toast(e.message, 5000); } };
  $('stUndo').onclick = () => loadStyle();
  $('stDef').onclick = () => { sty.cur = JSON.parse(JSON.stringify(sty.data.default)); renderStyle(); };
  box.querySelectorAll('[data-restore]').forEach((b) => (b.onclick = async () => { try { sty.data = await post('api/style/versions/' + b.dataset.restore + '/restore'); themeLocal(sty.data.style.map.theme); toast('Früherer Stil wiederhergestellt'); loadStyle(); } catch (e) { toast(e.message, 5000); } }));
  styleChanged();
}
function themeLocal(t) { try { if (t === 'auto') localStorage.removeItem('wm-theme'); else localStorage.setItem('wm-theme', t); } catch (e) { /* ignore */ } applyTheme(); }
let stRaf = 0;
function sendLive() { const f = $('stLive'); if (f && f.contentWindow) f.contentWindow.postMessage({wm: 'style', style: sty.cur}, location.origin); }
function styleChanged() { const s = $('stState'); if (s) { const ok = same(); s.textContent = ok ? 'gespeichert' : 'nicht gespeichert'; s.className = 'status ' + (ok ? 'ok' : 'warn'); }
  if (!stRaf) stRaf = requestAnimationFrame(() => { stRaf = 0; sendLive(); }); }

/* ================================================================ CONNECTIONS */
async function loadConnectors() {
  const box = $('conn');
  let c; try { c = await api('api/connectors'); } catch (e) { box.innerHTML = `<div class="card">${esc(e.message)}</div>`; return; }
  const src = c.points_by_source || {};
  const otRow = (o = {}) => `<div class="prow person ot"><input class="user" placeholder="Benutzer, z. B. alex" value="${esc(o.user || '')}" aria-label="Benutzer"><input class="pw" type="password" placeholder="${o.password_set ? 'Passwort (unverändert)' : 'Passwort, mind. 8 Zeichen'}" aria-label="Passwort" autocomplete="new-password"><select class="label" aria-label="Person">${(st.cfg?.persons || []).map((p) => `<option ${p === o.label ? 'selected' : ''}>${esc(p)}</option>`).join('')}</select><button class="btn rm" title="Entfernen" aria-label="Entfernen">✕</button></div>`;
  const ro = c.editable ? '' : '<p class="small warn">Speichern geht nur im Add-on (Supervisor nicht erreichbar).</p>';
  box.innerHTML = `
  <div class="card wide"><h3>👥 Personen &amp; Live-Standort <span class="status ${c.persons.length ? 'ok' : 'warn'}">${c.persons.length} Personen</span></h3>
    <p class="small keep">${c.persons.map((p) => `${esc(p.label)}: ${p.entity ? esc(p.entity) : 'ohne Live-Standort'} · zuletzt ${esc(ago(p.last_point))}`).join('<br>') || 'Noch keine Personen.'}</p>
    <div class="opts"><button class="btn" data-goto="people">Personen &amp; Gruppen bearbeiten</button><button class="btn" data-sync="ha">Verlauf aus HA holen</button></div>${ro}</div>
  <div class="card wide" id="cOT"><h3>📡 OwnTracks – live ohne Cloud <span class="status ${c.owntracks.length ? 'ok' : ''}">${(src.owntracks || 0).toLocaleString('de-CH')} Positionen</span></h3>
    <p class="small">Die kostenlose App OwnTracks (iPhone &amp; Android) speichert unterwegs und sendet, sobald das Handy wieder im Heimnetz ist. Nichts geht über das Internet.</p>
    <div id="otlist">${c.owntracks.map(otRow).join('')}</div>
    ${c.owntracks.map((o) => `<p class="small keep">${esc(o.user)} → ${esc(o.label)}: zuletzt ${esc(ago(o.last_point))}</p>`).join('')}
    <div class="opts"><button class="btn" id="addOT">+ Benutzer</button><button class="primary" id="saveOT">Speichern</button></div>
    <details class="help"><summary>So richtest du OwnTracks ein</summary><ol>
      <li>In Home Assistant: Einstellungen › Add-ons › Worldmap › Netzwerk › Port <b>8098</b> eintragen und speichern (nur im Heimnetz, nicht im Router freigeben).</li>
      <li>Hier einen Benutzer mit Passwort anlegen und der Person zuordnen.</li>
      <li>OwnTracks-App: Einstellungen › Verbindung › Modus <b>HTTP</b>, URL <code>http://IP-von-Home-Assistant:8098/pub</code>, Benutzer und Passwort eintragen.</li>
      <li>Fertig – unterwegs sammelt die App, zu Hause wird übertragen.</li></ol></details></div>
  <div class="card"><h3>🟢 Google Maps Zeitachse <span class="status">${(src.google || 0).toLocaleString('de-CH')} Positionen</span></h3>
    <p class="small">Die genaueste Quelle für die Vergangenheit. Google speichert sie nur auf dem Handy und bietet keine Schnittstelle – ab und zu exportieren und hier importieren:</p>
    <ol class="small"><li>Android: Einstellungen › Standort › Zeitachse › Exportieren</li><li>iPhone: Google Maps › Profil › Deine Zeitachse › ⋯ › Exportieren</li><li>Datei unter „Import“ ablegen – schon Vorhandenes wird nicht doppelt gespeichert.</li></ol>
    <div class="opts"><button class="btn" data-goto="import">Zum Import</button></div></div>
  <div class="card"><h3>🍎 Apple</h3>
    <p class="small">Apple gibt den Standortverlauf („Wichtige Orte“) nicht heraus. Was geht:</p>
    <ol class="small"><li><b>OwnTracks</b> oder die <b>Home-Assistant-App</b> auf dem iPhone für alles ab jetzt.</li><li><b>iCloud3</b> (HACS) liefert die Position aller Apple-Geräte als Entität – braucht die Apple-ID.</li><li><b>Fotos</b>: Aufnahmeort und -zeit der Fotos als CSV exportieren (z. B. mit exiftool) und importieren – ergibt die Reisen der Vergangenheit.</li></ol></div>
  <div class="card" id="cRoute"><h3>🛤️ Bahn- &amp; Strassennetz <span class="status ${c.routing !== 'off' ? 'ok' : ''}">${c.routing !== 'off' ? 'aktiv' : 'aus'}</span></h3>
    <p class="small">Lücken zwischen GPS-Punkten werden auf echte Bahnlinien und Strassen gelegt – direkt im Add-on, ohne Routing-Dienst. Das Netz kommt aus OpenStreetMap-Kartenkacheln, die einmal per Kachelnummer geladen und dauerhaft gespeichert werden (keine Positionen werden gesendet). Danach läuft es offline.</p>
    <p class="small keep">${c.tiles.toLocaleString('de-CH')} Kacheln gespeichert · ${(c.segments.rail || 0).toLocaleString('de-CH')} Bahn- und ${(c.segments.road || 0).toLocaleString('de-CH')} Strassenabschnitte · ${(c.segments.none || 0).toLocaleString('de-CH')} offen gelassen</p>
    <label class="field">Netz verwenden<select id="routing"><option value="tiles" ${c.routing === 'tiles' ? 'selected' : ''}>ja</option><option value="off" ${c.routing === 'off' ? 'selected' : ''}>nein</option></select></label>
    <div class="opts"><button class="primary" id="saveR">Speichern</button><button class="btn" data-sync="routes">Jetzt berechnen</button></div></div>`;
  $('addOT').onclick = () => $('otlist').insertAdjacentHTML('beforeend', otRow());
  box.querySelectorAll('#otlist').forEach((l) => l.addEventListener('click', (e) => { if (e.target.closest('.rm')) e.target.closest('.prow').remove(); }));
  $('saveOT').onclick = () => {
    const old = new Map((c.owntracks || []).map((o) => [o.user, o]));
    const rows = [...document.querySelectorAll('#otlist .ot')].map((r) => ({user: r.querySelector('.user').value.trim(), password: r.querySelector('.pw').value, label: r.querySelector('.label').value})).filter((o) => o.user);
    if (rows.some((o) => !o.password && !old.has(o.user))) return toast('Bitte ein Passwort setzen (mind. 8 Zeichen)');
    save({owntracks: rows.map((o) => (o.password ? o : {...o, keep_password: true}))}, loadConnectors);
  };
  $('saveR').onclick = () => save({routing: $('routing').value}, loadConnectors);
  syncButtons(box); infoize(box);
  box.querySelectorAll('[data-goto]').forEach((b) => (b.onclick = () => showTab(b.dataset.goto)));
}

/* ================================================================ NOTIFICATIONS */
async function loadNotify() {
  const box = $('notify');
  let c, svcs = [];
  try { [c, svcs] = await Promise.all([api('api/connectors'), api('api/notify_services')]); } catch (e) { box.innerHTML = `<div class="card">${esc(e.message)}</div>`; return; }
  const modes = [['off', 'nie', 'Keine Benachrichtigungen. Fragen siehst du beim Fragezeichen auf der Karte.'], ['instant', 'sofort', 'Sobald eine neue Reise erkannt ist.'], ['daily', 'täglich', 'Höchstens eine Nachricht pro Tag mit allen offenen Fragen.'], ['weekly', 'wöchentlich', 'Höchstens eine Nachricht pro Woche – empfohlen.']];
  const opts = [['', 'Hinweis in Home Assistant (Glocke)'], ...svcs.map((s) => [s, s.replace('notify.', '').replace(/^mobile_app_/, 'Handy: ').replace(/_/g, ' ')])];
  if (c.notify_service && !svcs.includes(c.notify_service)) opts.push([c.notify_service, c.notify_service + ' (nicht gefunden)']);
  box.innerHTML = `<div class="card wide"><h3>🔔 Wohin sollen die Fragen kommen?</h3>
    <div class="choice" id="nsvc">${opts.map(([v, n]) => `<button data-v="${esc(v)}" class="${v === (c.notify_service || '') ? 'on' : ''}">${esc(n)}</button>`).join('')}</div>
    ${svcs.length ? '' : '<p class="small">Keine Handys gefunden – die Home-Assistant-App installieren und anmelden, dann erscheint sie hier.</p>'}
    <h3 class="sub">Wie oft?</h3>
    <div class="choice" id="nmode">${modes.map(([v, n, d]) => `<button data-v="${v}" class="${v === c.notify_mode ? 'on' : ''}" title="${esc(d)}"><b>${n}</b><br><span class="small">${esc(d)}</span></button>`).join('')}</div>
    <p class="small">Die Nachricht nennt die Reise mit Datum, Ziel und Vorschlag; ein Tipp öffnet die Fragen in Worldmap.</p>
    <div class="opts"><button class="primary" id="saveN">Speichern</button><button class="btn" id="testN">Test senden</button></div></div>`;
  box.querySelectorAll('.choice').forEach((ch) => ch.addEventListener('click', (e) => { const b = e.target.closest('button'); if (!b) return; ch.querySelectorAll('button').forEach((x) => x.classList.toggle('on', x === b)); }));
  const val = (id) => $(id).querySelector('button.on')?.dataset.v ?? '';
  $('saveN').onclick = () => save({notify_service: val('nsvc'), notify_mode: val('nmode') || 'weekly'}, loadNotify);
  $('testN').onclick = async () => { try { await post('api/connectors', {notify_service: val('nsvc'), notify_mode: val('nmode') || 'weekly'}); await post('api/notify_test'); toast('Test gesendet'); } catch (e) { toast(e.message, 5000); } };
}

/* ================================================================ RULES */
async function loadRules() {
  const box = $('rules');
  let c, rules;
  try { [c, rules] = await Promise.all([api('api/connectors'), api('api/rules')]); } catch (e) { box.innerHTML = `<div class="card">${esc(e.message)}</div>`; return; }
  const DAYS = {all: 'alle Tage', weekday: 'unter der Woche', weekend: 'am Wochenende'};
  box.innerHTML = `
  <div class="card wide"><h3>📏 Gelernte Regeln <span class="status">${rules.length}</span></h3>
    <ul class="small"><li>Ähnliche Reisen (gleicher Ort, gleiche Art Tag, gleicher Vorschlag) kommen als <b>eine</b> Frage – die Antwort gilt für alle.</li>
    <li>Jede Antwort kann als <b>Regel</b> gemerkt werden: dort und an solchen Tagen wird nie mehr gefragt.</li>
    <li>Antworten: jede Person, jede Gruppe, „Keine Reise (Alltag)“, „Mit Reise davor zusammenlegen“ und „Einzeln fragen“.</li>
    <li>Vorschläge kommen aus: wer gleichzeitig weg war, Wochenende, Schulferien, Wörter in Ordnernamen und gelernten Regeln.</li></ul><p class="small">Eine Regel sagt: „An diesem Ort, an solchen Tagen ist es immer …“. Sie entsteht, wenn du beim Beantworten einer Frage „merken“ anhakst. Mit ✕ löschst du sie wieder.</p>
    ${rules.length ? `<table class="mini"><thead><tr><th>Ort</th><th>Tage</th><th>Dann</th><th>Umkreis</th><th>angewendet</th><th></th></tr></thead><tbody>${rules.map((r) => `<tr data-id="${r.id}"><td>${esc(r.label)}</td><td>${DAYS[r.days] || esc(r.days)}</td><td>${r.action === 'ignore' ? 'keine Reise' : '<span class="pill" data-c="' + colorOf(r.value) + '">' + esc(r.value) + '</span>'}</td><td>${r.radius_km} km</td><td>${r.hits}×</td><td><button class="btn rm" aria-label="Regel löschen">✕</button></td></tr>`).join('')}</tbody></table>` : '<p class="small keep">Noch keine – sie entstehen beim Beantworten der Fragen, wenn du „merken“ anhakst.</p>'}</div>
  <div class="card" id="cTrip"><h3>🧭 Wann ist es eine Reise?</h3>
    <p class="small">Mit Übernachtung zählt es als Reise, wenn jemand weiter weg war als die erste Entfernung; ein Tagesausflug ohne Übernachtung erst ab der zweiten. Orte, die du sehr oft besuchst (Arbeit, Schule, Familie), zählen nie als Reise – so wird der Arbeitsweg nicht zur Reise.</p>
    <label class="rng"><span>mit Übernachtung ab</span><input type="range" id="minkm" min="5" max="300" step="5" value="${Math.min(300, c.min_trip_km)}"><b id="minkmV">${Math.round(c.min_trip_km)} km</b></label>
    <label class="rng"><span>Tagesausflug ab</span><input type="range" id="minday" min="10" max="400" step="10" value="${Math.min(400, c.min_day_trip_km || 100)}"><b id="mindayV">${Math.round(c.min_day_trip_km || 100)} km</b></label>
    <label class="switch" style="margin-top:10px"><input type="checkbox" id="routOn" ${c.routine_days ? 'checked' : ''}><span></span>Oft besuchte Orte nie als Reise zählen</label>
    <label class="rng" id="routRow" style="margin-top:6px"><span>ab</span><input type="range" id="routd" min="5" max="120" step="5" value="${c.routine_days || 20}"><b id="routV" class="wide-b">${c.routine_days || 20} Tagen</b></label></div>
  <div class="card" id="cAsk"><h3>💬 Wann soll ich nachfragen?</h3>
    <p class="small">Worldmap rät bei jeder Reise, wer dabei war, und weiss, wie sicher es ist. Je nach Wahl kommt eine Frage nur bei unsicheren Reisen oder bei allen.</p>
    ${'<div class="seg2" id="askb" role="radiogroup">' + [['mittel', 'nur wenn unsicher'], ['hoch', 'normal (empfohlen)'], ['bestätigt', 'bei jeder Reise']].map(([v, l]) => `<button type="button" role="radio" data-v="${v}" class="${v === c.ask_below ? 'on' : ''}" aria-checked="${v === c.ask_below}">${l}</button>`).join('') + '</div>'}</div>
  <div class="card" id="cHol"><h3>🏖️ Schulferien</h3>
    <p class="small">Reisen in den Schulferien sind eher Familienreisen – Worldmap schlägt dann „Familie“ vor.</p>
    <div id="holList" class="rowlist"></div><div class="opts"><button class="btn" id="holAdd" type="button">+ Ferien</button></div></div>
  <div class="card" id="cKw"><h3>🔤 Stichwörter</h3>
    <p class="small">Kommt ein Wort im Namen einer importierten Datei oder eines Ordners vor, wird die passende Antwort vorgeschlagen – z. B. „Skilager“ → Familie.</p>
    <div id="kwList" class="rowlist"></div><div class="opts"><button class="btn" id="kwAdd" type="button">+ Stichwort</button></div></div>
  <div class="card wide"><div class="opts"><button class="primary" id="saveQ">Speichern</button><button class="btn" data-sync="rebuild">Reisen neu erkennen</button><span class="small">Personen und Gruppen stellst du unter <a href="#people">Personen &amp; Gruppen</a> ein.</span></div></div>`;
  paint(box); infoize(box);
  box.querySelectorAll('tr[data-id] .rm').forEach((b) => (b.onclick = async () => { const tr = b.closest('tr'); try { await api('api/rules/' + tr.dataset.id, {method: 'DELETE'}); tr.remove(); } catch (e) { toast(e.message); } }));
  const holRow = (a = '', b = '') => `<div class="lrow"><input type="date" class="h1" value="${esc(a)}" aria-label="von"><span>bis</span><input type="date" class="h2" value="${esc(b)}" aria-label="bis"><button class="btn rm" type="button" aria-label="Entfernen">✕</button></div>`;
  const kwRow = (w = '', v = '') => `<div class="lrow"><input class="k1" value="${esc(w)}" placeholder="Wort, z. B. Skilager" maxlength="40" aria-label="Wort"><span>→</span><select class="k2" aria-label="Antwort">${whoList().map((o) => `<option ${o === v ? 'selected' : ''}>${esc(o)}</option>`).join('')}</select><button class="btn rm" type="button" aria-label="Entfernen">✕</button></div>`;
  $('holList').innerHTML = c.school_holidays.map((h) => holRow(...h.split('..'))).join('');
  $('kwList').innerHTML = c.hint_keywords.map((h) => kwRow(...h.split('='))).join('');
  $('holAdd').onclick = () => $('holList').insertAdjacentHTML('beforeend', holRow());
  $('kwAdd').onclick = () => $('kwList').insertAdjacentHTML('beforeend', kwRow());
  box.querySelectorAll('.rowlist').forEach((l) => l.addEventListener('click', (e) => { if (e.target.closest('.rm')) e.target.closest('.lrow').remove(); }));
  $('minkm').oninput = (e) => { $('minkmV').textContent = e.target.value + ' km'; };
  $('minday').oninput = (e) => { $('mindayV').textContent = e.target.value + ' km'; };
  $('routd').oninput = (e) => { $('routV').textContent = e.target.value + ' Tagen'; };
  const routVis = () => { $('routRow').style.opacity = $('routOn').checked ? 1 : 0.4; $('routd').disabled = !$('routOn').checked; }; $('routOn').onchange = routVis; routVis();
  let ask = c.ask_below; $('askb').onclick = (e) => { const b = e.target.closest('button'); if (!b) return; ask = b.dataset.v; $('askb').querySelectorAll('button').forEach((x) => { x.classList.toggle('on', x === b); x.setAttribute('aria-checked', String(x === b)); }); };
  $('saveQ').onclick = () => {
    const hol = [...box.querySelectorAll('#holList .lrow')].map((r) => [r.querySelector('.h1').value, r.querySelector('.h2').value]).filter(([a, b]) => a && b);
    if (hol.some(([a, b]) => b < a)) return toast('Bei den Ferien liegt „bis“ vor „von“');
    const kw = [...box.querySelectorAll('#kwList .lrow')].map((r) => [r.querySelector('.k1').value.trim(), r.querySelector('.k2').value]).filter(([a, b]) => a && b);
    save({hint_keywords: kw.map(([a, b]) => `${a}=${b}`), school_holidays: hol.map(([a, b]) => `${a}..${b}`), min_trip_km: +$('minkm').value, min_day_trip_km: +$('minday').value,
      routine_days: $('routOn').checked ? +$('routd').value : 0, ask_below: ask}, loadRules);
  };
  syncButtons(box);
}

/* ================================================================ WIZARD: trip by hand */
const TRANSPORT = ['Auto', 'Zug', 'Bus', 'Flug', 'Schiff', 'Wohnmobil', 'Velo', 'zu Fuss'];
function wizard() {
  const d = $('wizard'); const w = {step: 0, place: null, year: new Date().getFullYear() - 1, month: '', start: '', end: '', nights: 7, who: '', transport: [], area: null, note: ''};
  const steps = ['Wohin?', 'Wann?', 'Wie lange?', 'Wer war dabei?', 'Wie seid ihr gereist?', 'Wie gross war die Gegend?', 'Passt das so?'];
  const months = ['', 'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'];
  const dates = () => {
    if (w.start) { const e = w.end || w.start; return [w.start, e, Math.max(0, Math.round((new Date(e) - new Date(w.start)) / 864e5)), 0]; }
    const m = w.month ? String(w.month).padStart(2, '0') : '07'; const s = `${w.year}-${m}-${w.month ? '01' : '15'}`;
    const e = new Date(new Date(s).getTime() + w.nights * 864e5).toISOString().slice(0, 10); return [s, e, w.nights, 1];
  };
  const body = () => {
    switch (w.step) {
      case 0: return `<input id="wq" placeholder="Ort, Insel oder Region, z. B. Korsika" autocomplete="off" value="${esc(w.place?.name || '')}"><div id="ws" class="sugg"></div>${w.place ? `<p class="small">✓ ${esc(w.place.name)}, ${esc(w.place.country)}</p>` : ''}`;
      case 1: return `<div class="prow"><label class="field">Jahr<input id="wy" type="number" min="1950" max="2100" value="${w.year}"></label><label class="field">Monat (falls bekannt)<select id="wm">${months.map((m, i) => `<option value="${i || ''}" ${String(i || '') === String(w.month) ? 'selected' : ''}>${m || 'weiss nicht'}</option>`).join('')}</select></label></div>
        <p class="small">Genaue Daten bekannt?</p><div class="prow"><label class="field">Von<input id="wst" type="date" value="${w.start}"></label><label class="field">Bis<input id="wen" type="date" value="${w.end}"></label></div>`;
      case 2: return `<div class="choice">${[[0, 'Tagesausflug'], [2, 'Wochenende'], [7, '1 Woche'], [14, '2 Wochen'], [21, '3 Wochen']].map(([n, l]) => `<button data-n="${n}" class="${w.nights === n ? 'on' : ''}">${l}</button>`).join('')}</div><label class="field">Nächte<input id="wn" type="number" min="0" max="365" value="${w.nights}"></label>${w.start ? '<p class="small">Aus den Daten berechnet.</p>' : ''}`;
      case 3: return `<div class="choice">${whoList().map((o) => `<button data-who="${esc(o)}" class="${o === w.who ? 'on' : ''}">${esc(o)}</button>`).join('')}</div><input id="wwho" placeholder="oder eigene Angabe" value="${esc(whoList().includes(w.who) ? '' : w.who)}" maxlength="60">`;
      case 4: return `<div class="choice">${TRANSPORT.map((t) => `<button data-t="${t}" class="${w.transport.includes(t) ? 'on' : ''}">${t}</button>`).join('')}</div><p class="small">Mehrfachauswahl möglich. Bei Flug zeichnet die Karte einen Bogen ab zu Hause.</p>`;
      case 5: { const reg = w.place?.radius_km; return `<div class="choice">${[[3, 'Ein Ort'], [15, 'Umgebung'], [reg || 50, reg ? `ganz ${esc(w.place.name)}` : 'Region'], [150, 'Rundreise']].map(([r, l]) => `<button data-r="${r}" class="${w.area === r ? 'on' : ''}">${l} · ${r} km</button>`).join('')}</div><p class="small">Ohne GPS-Daten zeigt die Karte eine gestrichelte Fläche – lieber zu klein als zu gross.</p>`; }
      default: { const [s, e, n, ap] = dates(); return `<p><b>${esc(w.place?.name || '?')}</b>, ${esc(w.place?.country || '')}</p><p>${fmtD(s)} – ${fmtD(e)} · ${n} Nächte${ap ? ' · <span class="status">Datum geschätzt</span>' : ''}</p><p>${esc(w.who || 'wer offen')} · ${esc(w.transport.join(' · ') || '–')} · Fläche ${w.area ?? 0} km</p><label class="field">Notiz<textarea id="wnote" rows="2" maxlength="1000">${esc(w.note)}</textarea></label>`; }
    }
  };
  const render = () => {
    d.innerHTML = `<div class="dlg"><h2>${steps[w.step]}</h2><div class="steps">${steps.map((_, i) => `<i class="${i <= w.step ? 'on' : ''}"></i>`).join('')}</div><div id="wb">${body()}</div>
    <div class="foot"><button class="btn" id="wback">${w.step ? 'Zurück' : 'Abbrechen'}</button><button class="primary" id="wnext">${w.step === steps.length - 1 ? 'Reise speichern' : 'Weiter'}</button></div></div>`;
    bind();
  };
  const collect = () => {
    if (w.step === 1) { w.year = +$('wy').value || w.year; w.month = $('wm').value; w.start = $('wst').value; w.end = $('wen').value; if (w.start && w.end && w.end < w.start) [w.start, w.end] = [w.end, w.start]; if (w.start) w.year = +w.start.slice(0, 4); }
    if (w.step === 2) w.nights = Math.max(0, +$('wn').value || 0);
    if (w.step === 3 && $('wwho').value.trim()) w.who = $('wwho').value.trim();
    if (w.step === 6) w.note = $('wnote').value;
  };
  const bind = () => {
    $('wback').onclick = () => { if (!w.step) return d.close(); collect(); w.step--; render(); };
    $('wnext').onclick = async () => {
      collect();
      if (w.step === 0 && !w.place) return toast('Bitte einen Ort aus der Liste wählen');
      if (w.step < steps.length - 1) { w.step++; if (w.step === 2 && w.start) w.nights = dates()[2]; if (w.step === 5 && w.area == null) w.area = w.place?.radius_km || 15; return render(); }
      const [s, e, n, ap] = dates(); const home = st.cfg?.home;
      const km = home ? haversine(home[0], home[1], w.place.lat, w.place.lon) : null;
      try {
        await post('api/trips', {start_date: s, end_date: e, nights: n, destination: w.place.name, country: w.place.country, who: w.who, confidence: w.who ? 'bestätigt' : 'tief', lat: w.place.lat, lon: w.place.lon, radius_km: w.area, approx: ap, transport: w.transport.join(' · '), note: w.note, source: 'manual', reason: 'von Hand erfasst', max_km: km});
        saved = true; d.close(); toast('Reise gespeichert'); notifyParent('changed'); refresh();
      } catch (err) { toast(err.message, 4000); }
    };
    const wb = $('wb');
    if (w.step === 0) {
      let tm; $('wq').focus();
      $('wq').oninput = () => { clearTimeout(tm); tm = setTimeout(async () => { const r = await api('api/places?q=' + encodeURIComponent($('wq').value)); $('ws').innerHTML = r.map((p, i) => `<button data-i="${i}">${p.kind === 'region' ? '🗺️' : '📍'} ${esc(p.name)} <span class="small">${esc(p.country)}</span></button>`).join(''); $('ws').onclick = (e) => { const b = e.target.closest('button'); if (!b) return; w.place = r[+b.dataset.i]; w.area = null; render(); }; }, 160); };
    }
    wb.querySelectorAll('[data-n]').forEach((b) => (b.onclick = () => { w.nights = +b.dataset.n; render(); }));
    wb.querySelectorAll('[data-who]').forEach((b) => (b.onclick = () => { w.who = b.dataset.who; render(); }));
    wb.querySelectorAll('[data-t]').forEach((b) => (b.onclick = () => { const t = b.dataset.t; w.transport = w.transport.includes(t) ? w.transport.filter((x) => x !== t) : [...w.transport, t]; render(); }));
    wb.querySelectorAll('[data-r]').forEach((b) => (b.onclick = () => { w.area = +b.dataset.r; render(); }));
  };
  let saved = false;
  d.onclose = () => { if (EMBED) notifyParent('close'); };
  render(); d.showModal();
}
function haversine(a, b, c, d) { const r = Math.PI / 180, x = Math.sin(((c - a) * r) / 2) ** 2 + Math.cos(a * r) * Math.cos(c * r) * Math.sin(((d - b) * r) / 2) ** 2; return Math.round(12742 * Math.asin(Math.sqrt(x))); }


/* ================================================================ boot */
async function refresh() {
  const [trips, qs] = await Promise.all([api('api/trips' + ($('gridIgnored').checked ? '?all=1' : '')), api('api/questions')]);
  st.trips = trips; st.questions = qs;
  if (!$('grid').tHead.rows.length) gridHead();
  gridBody(); renderQuestions();
}
function route() {
  const h = decodeURIComponent(location.hash.slice(1));
  const m = h.match(/^edit-(\d+)$/);
  if (m) { showTab('trips'); st.filter = {}; const t = st.trips.find((x) => x.id === +m[1]); if (t) { st.filter.destination = t.destination; gridHead(); gridBody(); } return; }
  if (h && $('tab-' + h)) showTab(h); else showTab('trips');
}
(async function boot() {
  if (EMBED) document.body.classList.add('embed', 'embed-' + EMBED);
  try { st.cfg = await api('api/config'); } catch (e) { toast(e.message); }
  await refresh().catch((e) => toast(e.message));
  if (EMBED === 'questions') { showTab('questions'); return; }
  if (EMBED === 'new') { wizard(); return; }
  route();
  window.addEventListener('hashchange', route);
})();
