/* Worldmap UI – no dependencies. All text from the API is escaped before it reaches the DOM. */
'use strict';
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const NEON = ['#0A7CFF', '#FF3D9A', '#8B3DFF', '#00BFB3', '#FF8A00', '#12A84F', '#E03131', '#5C7CFA'];
const CONF = ['tief', 'mittel', 'hoch', 'bestätigt'];
const st = {cfg: null, trips: [], questions: []};

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

/* ---------- colours: persons first, then group options ---------- */
function whoList() { return st.cfg ? [...st.cfg.persons, ...st.cfg.who_options.filter((o) => !st.cfg.persons.includes(o))] : []; }
function colorOf(who) {
  const l = whoList(); const i = l.indexOf(who);
  if (i >= 0) return NEON[i % NEON.length];
  let h = 0; for (const c of String(who)) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return who ? NEON[h % NEON.length] : '#9AA0B8';
}

/* ---------- tabs ---------- */
function showTab(name) {
  document.querySelectorAll('nav button').forEach((b) => b.classList.toggle('on', b.dataset.tab === name));
  document.querySelectorAll('.tab').forEach((t) => t.classList.toggle('on', t.id === 'tab-' + name));
  if (name === 'map') reloadAtlasIfDirty();
  if (name === 'connectors') loadConnectors();
  history.replaceState(null, '', '#' + name);
}
$('tabs').addEventListener('click', (e) => { const b = e.target.closest('button[data-tab]'); if (b) showTab(b.dataset.tab); });

/* ================================================================ MAP (atlas in a same-origin frame) */
const atlas = $('atlas');
let atlasDirty = false;
function reloadAtlasIfDirty() { if (atlasDirty) { atlasDirty = false; atlas.contentWindow.location.reload(); } }
window.addEventListener('message', (e) => {
  if (e.origin !== location.origin || e.source !== atlas.contentWindow) return;
  const m = e.data || {};
  if (m.type === 'worldmap-edit' && Number.isInteger(m.id)) { const t = st.trips.find((x) => x.id === m.id); if (t) openEdit(t); }
});
function renderFilters() {
  const who = [...new Set(['', ...whoList(), ...st.trips.map((t) => t.who || '')])];
  $('tripWho').innerHTML = '<option value="">Alle</option>' + who.map((w) => `<option value="${esc(w)}">${esc(w || 'offen')}</option>`).join('');
}
async function loadStats() {
  try { const s = await api('api/stats'); const b = $('qbadge'); b.hidden = !s.open_questions; b.textContent = s.open_questions; } catch (e) { console.warn(e); }
}

/* ================================================================ TRIPS */
const fmtD = (d) => { const [y, m, dd] = d.split('-'); return `${dd}.${m}.${y}`; };
const fmtRange = (t) => (t.start_date === t.end_date ? fmtD(t.start_date) : `${fmtD(t.start_date)} – ${fmtD(t.end_date)}`);
function renderTrips() {
  const q = $('tripSearch').value.trim().toLowerCase(), w = $('tripWho').value;
  const rows = st.trips.slice().reverse().filter((t) => (!w || (t.who || '') === w) && (!q || `${t.destination} ${t.country} ${t.who} ${t.start_date} ${t.note}`.toLowerCase().includes(q)));
  $('tripTable').tBodies[0].innerHTML = rows.map((t) => `<tr data-id="${t.id}"><td>${fmtD(t.start_date)}</td><td>${fmtD(t.end_date)}</td><td>${esc(t.destination)}${t.approx ? ' <span class="status">geschätzt</span>' : ''}</td><td>${esc(t.country)}</td><td>${t.who ? `<span class="pill" data-c="${colorOf(t.who)}">${esc(t.who)}</span>` : '<span class="status warn">offen</span>'}</td><td class="conf-${esc(t.confidence)}">${esc(t.confidence)}</td><td class="num">${t.nights ?? ''}</td><td class="num">${t.max_km != null ? Math.round(t.max_km).toLocaleString('de-CH') : ''}</td><td class="small">${esc(t.source)}</td></tr>`).join('');
  paint($('tripTable'));
}
$('tripSearch').oninput = renderTrips; $('tripWho').onchange = renderTrips;
$('tripTable').addEventListener('click', (e) => { const tr = e.target.closest('tr[data-id]'); if (tr) openEdit(st.trips.find((t) => t.id === +tr.dataset.id)); });
$('rebuild').onclick = async () => { try { const r = await post('api/rebuild'); toast(r.error || `${r.trips_created} neu, ${r.trips_updated} aktualisiert, ${r.questions} Fragen`); await refresh(); } catch (e) { toast(e.message); } };

function openEdit(t) {
  const d = $('edit');
  const who = [...new Set([...whoList(), t.who].filter(Boolean))];
  d.innerHTML = `<form class="dlg" method="dialog"><h2>${esc(t.destination || 'Reise')}</h2><p class="small">${esc(t.reason || '')}</p>
  <div class="prow"><label class="field">Von<input name="start_date" type="date" value="${esc(t.start_date)}" required></label><label class="field">Bis<input name="end_date" type="date" value="${esc(t.end_date)}" required></label>
  <label class="field">Wer<select name="who"><option value="">offen</option>${who.map((w) => `<option ${w === t.who ? 'selected' : ''}>${esc(w)}</option>`).join('')}</select></label>
  <label class="field">Sicherheit<select name="confidence">${CONF.map((c) => `<option ${c === t.confidence ? 'selected' : ''}>${c}</option>`).join('')}</select></label></div>
  <label class="field">Ziel<input name="destination" maxlength="120" value="${esc(t.destination)}"></label>
  <div class="prow"><label class="field">Land<input name="country" maxlength="60" value="${esc(t.country)}"></label><label class="field">Verkehrsmittel<input name="transport" maxlength="80" value="${esc(t.transport)}"></label><label class="field">Fläche km<input name="radius_km" type="number" min="0" max="2000" value="${t.radius_km ?? ''}"></label></div>
  <label class="field">Notiz<textarea name="note" maxlength="1000" rows="2">${esc(t.note)}</textarea></label>
  <div class="foot"><button type="button" class="btn" id="del">Löschen</button><span><button value="cancel" class="btn">Abbrechen</button> <button value="ok" class="primary">Speichern</button></span></div></form>`;
  d.querySelector('#del').onclick = async () => { if (!confirm('Reise löschen?')) return; await api('api/trips/' + t.id, {method: 'DELETE'}); d.close(); refresh(); };
  d.onclose = async () => {
    if (d.returnValue !== 'ok') return;
    const f = new FormData(d.querySelector('form')); const data = Object.fromEntries(f.entries());
    try { await post('api/trips/' + t.id, data, 'PATCH'); toast('Gespeichert'); refresh(); } catch (e) { toast(e.message); }
  };
  d.returnValue = ''; d.showModal();
}

/* ================================================================ QUESTIONS */
function renderQuestions() {
  const list = $('qlist');
  if (!st.questions.length) { list.innerHTML = '<div class="card"><h3>Alles beantwortet ✓</h3><p class="small">Neue Fragen erscheinen, sobald neue Reisen erkannt werden.</p></div>'; return; }
  list.innerHTML = st.questions.map((q) => `<div class="card" data-q="${q.id}"><h3>${esc(q.destination || 'Reise')}</h3><p>${esc(q.text)}</p><div class="opts">${q.options.map((o) => `<button data-a="${esc(o)}" data-c="${colorOf(o)}" class="${o === q.suggestion ? 'sug' : ''}">${esc(o)}</button>`).join('')}</div></div>`).join('');
  paint(list);
}
$('qlist').addEventListener('click', async (e) => {
  const b = e.target.closest('button[data-a]'); if (!b) return;
  const id = b.closest('[data-q]').dataset.q;
  try { await post(`api/questions/${id}/answer`, {answer: b.dataset.a}); b.closest('.card').remove(); st.questions = st.questions.filter((q) => q.id !== +id); refresh(); } catch (err) { toast(err.message); }
});

/* ================================================================ IMPORT */
const drop = $('drop');
['dragenter', 'dragover'].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add('over'); }));
['dragleave', 'drop'].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove('over'); }));
drop.addEventListener('drop', (e) => [...e.dataTransfer.files].forEach(preview));
$('file').onchange = (e) => [...e.target.files].forEach(preview);
async function upload(file, person, dry) {
  const mb = st.cfg ? st.cfg.max_upload_mb : 200;
  if (file.size > mb * 1048576) throw new Error(`Datei grösser als ${mb} MB`);
  return api(`api/import?dry_run=${dry ? 1 : 0}&person=${encodeURIComponent(person)}`, {method: 'POST', headers: {'Content-Type': 'application/octet-stream', 'X-Filename': file.name.replace(/[^\w.\-]/g, '_')}, body: file});
}
async function preview(file) {
  const card = document.createElement('div'); card.className = 'card'; card.innerHTML = `<h3>${esc(file.name)}</h3><p class="small">wird geprüft …</p>`; $('imports').prepend(card);
  try {
    const r = await upload(file, '', true);
    const range = `${new Date(r.first * 1000).toLocaleDateString('de-CH')} – ${new Date(r.last * 1000).toLocaleDateString('de-CH')}`;
    const cols = r.columns ? Object.entries(r.columns).map(([k, v]) => `${esc(k)} → ${esc(v)}`).join(', ') : '';
    card.innerHTML = `<h3>${esc(file.name)} <span class="status ok">${esc(r.format)}</span></h3><p><b>${r.points.toLocaleString('de-CH')}</b> Positionen · ${esc(range)}${r.skipped ? ` · ${r.skipped} übersprungen` : ''}</p>${cols ? `<p class="small">Spalten: ${cols}</p>` : ''}
      <label class="field">Wessen Daten?<select class="who"><option value="">unbekannt / gemischt (Fotos)</option>${(st.cfg?.persons || []).map((p) => `<option>${esc(p)}</option>`).join('')}</select></label>
      <div class="opts"><button class="primary go">Importieren</button></div>`;
    card.querySelector('.go').onclick = async () => {
      card.querySelector('.go').disabled = true; card.querySelector('.go').textContent = 'importiere …';
      try { const x = await upload(file, card.querySelector('.who').value, false); card.querySelector('.opts').innerHTML = `<span class="status ok">${x.new_points.toLocaleString('de-CH')} neue Positionen</span> ${x.rebuild ? `<span class="status">${x.rebuild.trips_created ?? 0} neue Reisen, ${x.rebuild.questions ?? 0} Fragen</span>` : ''}`; refresh(); } catch (e) { card.querySelector('.opts').innerHTML = `<span class="status warn">${esc(e.message)}</span>`; }
    };
  } catch (e) { card.innerHTML = `<h3>${esc(file.name)}</h3><p><span class="status warn">${esc(e.message)}</span></p>`; }
}

/* ================================================================ CONNECTORS */
async function loadConnectors() {
  const box = $('conn');
  let c; try { c = await api('api/connectors'); } catch (e) { box.innerHTML = `<div class="card">${esc(e.message)}</div>`; return; }
  const ago = (ts) => (ts ? new Date(ts * 1000).toLocaleString('de-CH') : 'noch nie');
  const src = c.points_by_source || {};
  const trackerOpts = (sel) => c.trackers.map((t) => `<option value="${esc(t.entity)}" ${t.entity === sel ? 'selected' : ''}>${esc(t.name)} (${esc(t.entity)})${t.has_gps ? '' : ' – ohne GPS'}</option>`).join('');
  const personRow = (p = {}) => `<div class="prow person"><input placeholder="Name, z. B. Alex" class="label" value="${esc(p.label || '')}" maxlength="40">${c.trackers.length ? `<select class="entity"><option value="">Entität wählen …</option>${trackerOpts(p.entity)}</select>` : `<input class="entity" placeholder="person.alex" value="${esc(p.entity || '')}">`}<input class="cams" placeholder="Kamera, z. B. iPhone 15" value="${esc(p.camera_models || '')}"><button class="btn rm" title="Entfernen">✕</button></div>`;
  const ro = c.editable ? '' : '<p class="small">Bearbeiten ist nur im Add-on möglich (Supervisor-API nicht erreichbar).</p>';
  box.innerHTML = `
  <div class="card" id="cPersons"><h3>📍 Live-Standort aus Home Assistant <span class="status ${c.persons.length ? 'ok' : 'warn'}">${c.persons.length ? c.persons.length + ' Personen' : 'nicht eingerichtet'}</span></h3>
    <p class="small">Am besten die Home-Assistant-App auf jedem Handy (iPhone und Android) mit Standort „Immer“. Die <code>person.*</code>-Entität liefert dann laufend GPS. Alternative für Apple: iCloud3 (HACS).</p>
    <div id="plist">${c.persons.map(personRow).join('')}</div>
    ${c.persons.map((p) => `<p class="small">${esc(p.label)}: letzte Position ${esc(ago(p.last_point))}</p>`).join('')}
    <div class="opts"><button class="btn" id="addP">+ Person</button><button class="primary" id="saveP">Speichern</button><button class="btn" data-sync="ha">Verlauf holen</button></div>${ro}</div>
  <div class="card" id="cPhotos"><h3>🖼️ Fotos (NAS) <span class="status ${c.photo_folders.length ? 'ok' : ''}">${(src.exif || 0).toLocaleString('de-CH')} Positionen</span></h3>
    <p class="small">Ordner unter <code>/media</code> oder <code>/share</code> (NAS über Einstellungen › System › Speicher als Netzwerkspeicher einbinden). Ordnernamen helfen beim Erkennen, wer dabei war.</p>
    <label class="field">Ordner (einer pro Zeile)<textarea id="folders" rows="2">${esc(c.photo_folders.join('\n'))}</textarea></label>
    <div class="opts"><button class="primary" id="saveF">Speichern</button><button class="btn" data-sync="photos">Jetzt scannen</button></div></div>
  <div class="card"><h3>🟢 Google Maps Zeitachse <span class="status">${(src.google || 0).toLocaleString('de-CH')} Positionen</span></h3>
    <p class="small">Google speichert die Zeitachse nur noch auf dem Handy und bietet keine Schnittstelle. Ab und zu exportieren: Android › Einstellungen › Standort › Zeitachse › Exportieren · iPhone › Google Maps › Profil › Zeitachse › ⋯ › Exportieren. Datei dann unter „Import“ ablegen.</p>
    <div class="opts"><button class="btn" data-goto="import">Zum Import</button></div></div>
  <div class="card"><h3>🍎 Apple <span class="status">${(src.ha || 0).toLocaleString('de-CH')} Live-Positionen</span></h3>
    <p class="small">Apple bietet keine Standort-API. Live: Home-Assistant-App (oben). Fotos: über iCloud-Fotos-Sync aufs NAS oder als CSV exportieren und importieren.</p></div>
  <div class="card" id="cRoute"><h3>🛣️ Routen <span class="status ${c.routing === 'osrm' ? 'ok' : ''}">${c.routing === 'osrm' ? 'aktiv' : 'aus'}</span></h3>
    <p class="small">Lücken zwischen GPS-Punkten werden auf echte Strassen gelegt (OSRM). Dabei werden Start- und Endpunkt der Lücke an den Routing-Server gesendet.</p>
    <label class="field">Routing<select id="routing"><option value="osrm" ${c.routing === 'osrm' ? 'selected' : ''}>OSRM</option><option value="off" ${c.routing === 'off' ? 'selected' : ''}>aus</option></select></label>
    <div class="opts"><button class="primary" id="saveR">Speichern</button><button class="btn" data-sync="routes">Routen jetzt suchen</button></div></div>
  <div class="card" id="cNotify"><h3>🔔 Benachrichtigungen</h3>
    <label class="field">Dienst (leer = Hinweis in Home Assistant)<input id="nsvc" placeholder="notify.mobile_app_handy" value="${esc(c.notify_service)}"></label>
    <label class="field">Wann<select id="nmode">${['off', 'instant', 'daily', 'weekly'].map((m) => `<option value="${m}" ${m === c.notify_mode ? 'selected' : ''}>${{off: 'nie', instant: 'sofort', daily: 'täglich', weekly: 'wöchentlich'}[m]}</option>`).join('')}</select></label>
    <div class="opts"><button class="primary" id="saveN">Speichern</button></div></div>
  <div class="card" id="cRules"><h3>🧠 Fragen &amp; Regeln</h3>
    <label class="field">Gruppen (Komma)<input id="whoOpts" value="${esc(c.who_options.join(', '))}"></label>
    <label class="field">Hinweise im Ordnernamen (Wort=Wer, eine pro Zeile)<textarea id="kw" rows="2" placeholder="Papa=Papa + Kinder">${esc(c.hint_keywords.join('\n'))}</textarea></label>
    <label class="field">Schulferien (YYYY-MM-DD..YYYY-MM-DD, eine pro Zeile)<textarea id="hol" rows="2">${esc(c.school_holidays.join('\n'))}</textarea></label>
    <div class="prow"><label class="field">Reise ab km<input id="minkm" type="number" min="1" max="1000" value="${c.min_trip_km}"></label><label class="field">Alltagsort ab Tagen<input id="routd" type="number" min="0" max="3650" value="${c.routine_days}" title="Orte wie die Arbeit, die man an so vielen Tagen besucht, gelten nicht als Reise"></label><label class="field">Fragen wenn unter<select id="askb">${['mittel', 'hoch', 'bestätigt'].map((x) => `<option ${x === c.ask_below ? 'selected' : ''}>${x}</option>`).join('')}</select></label></div>
    <div class="opts"><button class="primary" id="saveQ">Speichern</button><button class="btn" data-sync="rebuild">Neu erkennen</button></div></div>`;
  const lines = (id) => $(id).value.split('\n').map((s) => s.trim()).filter(Boolean);
  const save = async (data) => { try { await post('api/connectors', data); toast('Gespeichert'); st.cfg = await api('api/config'); loadConnectors(); } catch (e) { toast(e.message, 4000); } };
  $('addP').onclick = () => { $('plist').insertAdjacentHTML('beforeend', personRow()); };
  $('plist').addEventListener('click', (e) => { if (e.target.closest('.rm')) e.target.closest('.person').remove(); });
  $('saveP').onclick = () => save({persons: [...document.querySelectorAll('#plist .person')].map((r) => ({label: r.querySelector('.label').value.trim(), entity: r.querySelector('.entity').value.trim(), camera_models: r.querySelector('.cams').value.trim()})).filter((p) => p.label || p.entity)});
  $('saveF').onclick = () => save({photo_folders: lines('folders')});
  $('saveR').onclick = () => save({routing: $('routing').value});
  $('saveN').onclick = () => save({notify_service: $('nsvc').value.trim(), notify_mode: $('nmode').value});
  $('saveQ').onclick = () => save({who_options: $('whoOpts').value.split(',').map((s) => s.trim()).filter(Boolean), hint_keywords: lines('kw'), school_holidays: lines('hol'), min_trip_km: +$('minkm').value, routine_days: +$('routd').value, ask_below: $('askb').value});
  box.querySelectorAll('[data-sync]').forEach((b) => (b.onclick = async () => { try { const r = await post('api/sync/' + b.dataset.sync); toast(r.started ? 'Läuft im Hintergrund …' : 'Läuft bereits'); } catch (e) { toast(e.message); } }));
  box.querySelectorAll('[data-goto]').forEach((b) => (b.onclick = () => showTab(b.dataset.goto)));
}

/* ================================================================ WIZARD: trip by hand */
const TRANSPORT = ['Auto', 'Zug', 'Flug', 'Schiff', 'Wohnmobil', 'Velo', 'zu Fuss'];
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
        d.close(); toast('Reise gespeichert'); refresh();
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
  render(); d.showModal();
}
function haversine(a, b, c, d) { const r = Math.PI / 180, x = Math.sin(((c - a) * r) / 2) ** 2 + Math.cos(a * r) * Math.cos(c * r) * Math.sin(((d - b) * r) / 2) ** 2; return Math.round(12742 * Math.asin(Math.sqrt(x))); }
$('addTrip').onclick = wizard;

/* ================================================================ boot */
async function refresh(initial) {
  const [trips, qs] = await Promise.all([api('api/trips'), api('api/questions')]);
  st.trips = trips; st.questions = qs;
  renderFilters(); renderTrips(); renderQuestions(); loadStats();
  if (initial !== 'boot') { atlasDirty = true; if ($('tab-map').classList.contains('on')) reloadAtlasIfDirty(); }
}
(async function boot() {
  try { st.cfg = await api('api/config'); } catch (e) { toast(e.message); }
  const tab = location.hash.slice(1); if (tab && $('tab-' + tab)) showTab(tab);
  await refresh('boot').catch((e) => toast(e.message));
})();
