/* Worldmap – every map setting in one list, shared by the map's 🎨 drawer and the settings page.
   Field: [key, type, label, extra, info]
   type: r = range [min, max, step, unit], s = segmented [[value, label]...], b = switch, c = colour ('' = automatic) */
'use strict';
const DASH_OPTS = [['solid', 'durchgezogen'], ['dashed', 'gestrichelt'], ['dotted', 'gepunktet'], ['longdash', 'lang'], ['dashdot', 'Strich-Punkt'], ['sparse', 'locker']];
const WM_SPEC = [
  {id: 'trips', tabs: ['reisen'], icon: '🧭', title: 'Reisen-Karte', fields: [
    ['trips.arc_height', 'r', 'Höhe der Flugbögen', [0.3, 2.5, 0.1, '×']],
    ['trips.line_width', 'r', 'Linienbreite', [0.5, 3, 0.1, '×']],
    ['trips.dot_size', 'r', 'Grösse der Ziel-Punkte', [0.5, 2.5, 0.1, '×']],
    ['trips.labels', 's', 'Namen der Ziele', [['all', 'alle'], ['normal', 'normal'], ['few', 'nur grosse'], ['off', 'keine']]],
    ['trips.label_size', 'r', 'Schriftgrösse', [0.7, 1.8, 0.05, '×']],
    ['trips.airports', 'b', 'Flughafen-Schilder (IATA)'],
  ]},
  {id: 'est', tabs: ['reisen', 'zeit'], icon: '🛣️', title: 'Geschätzte Wege', info: 'Reisen ohne GPS (z. B. alte Autoferien) bekommen eine geschätzte Linie von zuhause zum Ziel. Über Meer wird daraus eine Fähre.', fields: [
    ['est.show', 'b', 'Geschätzte Wege zeigen'],
    ['est.dash', 's', 'Linientyp', DASH_OPTS],
    ['est.opacity', 'r', 'Deckkraft', [0.2, 1, 0.05, '%']],
    ['est.curve', 'r', 'Bogen', [0, 2.5, 0.1, '×']],
    ['est.ferry', 'b', 'Fähren übers Meer zeigen'],
  ]},
  {id: 'areas', tabs: ['reisen'], icon: '🫧', title: 'Flächen', info: 'Wo du dich oft auf kleinem Raum bewegst (Ferienort, Stadt), zeigt die Karte statt vieler Striche eine weiche Fläche. „Verbunden“ lässt nahe Flächen zu einer Form verschmelzen.', fields: [
    ['areas.show', 'b', 'Flächen zeigen'],
    ['areas.shape', 's', 'Form', [['organic', 'verbunden'], ['circles', 'Kreise']]],
    ['areas.size', 'r', 'Grösse', [0.5, 3, 0.1, '×']],
    ['areas.connect', 'r', 'Verschmelzen', [0, 3, 0.1, '×']],
    ['areas.smooth', 'r', 'Weicher Rand', [0.3, 2.5, 0.1, '×']],
    ['areas.opacity', 'r', 'Deckkraft', [0.1, 1, 0.05, '%']],
    ['areas.outline_width', 'r', 'Randdicke', [0, 6, 0.2, 'px']],
    ['areas.outline_color', 's', 'Randfarbe', [['fill', 'wie Fläche'], ['darker', 'dunkler'], ['white', 'weiss'], ['none', 'kein Rand']]],
  ]},
  {id: 'tracks', tabs: ['spuren'], icon: '〰️', title: 'Spuren-Karte', fields: [
    ['tracks.width', 'r', 'Linienbreite', [0.4, 3, 0.1, '×']],
    ['tracks.opacity', 'r', 'Deckkraft', [0.2, 1, 0.05, '%']],
    ['tracks.everyday_opacity', 'r', 'Deckkraft Alltag', [0.1, 1, 0.05, '%']],
    ['tracks.glow', 'b', 'Leuchtende Linien'],
    ['tracks.airports', 'b', 'Flughafen-Schilder (IATA)'],
    ['map.gaps', 's', 'Lücken ohne bekannte Strecke', [['dotted', 'gepunktet'], ['straight', 'gerade'], ['open', 'offen']]],
  ]},
  {id: 'places', tabs: ['orte'], icon: '📍', title: 'Orte & Tage', fields: [
    ['places.size_by', 's', 'Kreisgrösse nach', [['days', 'Tagen'], ['visits', 'Besuchen'], ['same', 'alle gleich']]],
    ['places.size_min', 'r', 'Kleinster Kreis', [1, 12, 0.5, 'px']],
    ['places.size_max', 'r', 'Grösster Kreis', [4, 40, 1, 'px']],
    ['places.style', 's', 'Kreis-Stil', [['filled', 'gefüllt'], ['ring', 'Ring'], ['glow', 'leuchtend']]],
    ['places.color_by', 's', 'Farbe nach', [['person', 'Person'], ['year', 'Jahr'], ['days', 'Tagen']]],
    ['places.opacity', 'r', 'Deckkraft', [0.2, 1, 0.05, '%']],
    ['places.names', 's', 'Ortsnamen', [['none', 'keine'], ['big', 'wichtige'], ['all', 'alle']]],
    ['places.name_min_days', 'r', 'Name ab so vielen Tagen', [0, 60, 1, ' Tage']],
    ['places.name_size', 'r', 'Schriftgrösse', [0.6, 2, 0.05, '×']],
    ['places.collide', 'b', 'Überlappende Namen ausblenden'],
  ]},
  {id: 'regions', tabs: ['regionen'], icon: '🗾', title: 'Regionen', fields: [
    ['regions.fill_by', 's', 'Farbe nach', [['first', 'erstes Jahr'], ['days', 'Tagen'], ['stay', 'übernachtet']]],
    ['regions.fill_opacity', 'r', 'Deckkraft der Farbe', [0.1, 1, 0.05, '%']],
    ['regions.borders', 's', 'Regionsgrenzen', [['visited', 'nur besuchte Länder'], ['all', 'alle'], ['none', 'keine']]],
    ['regions.border_color', 'c', 'Farbe der Regionsgrenzen'],
    ['regions.border_width', 'r', 'Dicke der Regionsgrenzen', [0, 4, 0.1, 'px']],
    ['regions.border_opacity', 'r', 'Deckkraft der Regionsgrenzen', [0, 1, 0.05, '%']],
    ['regions.country_width', 'r', 'Dicke der Landesgrenzen', [0, 5, 0.1, 'px']],
    ['regions.names', 'b', 'Regionsnamen'],
  ]},
  {id: 'anim', tabs: ['reisen', 'spuren'], icon: '✈️', title: 'Animation', info: 'Flugzeuge, Züge, Autos und Fähren auf den Karten Reisen und Spuren. Flugzeuge fliegen auf kurzen und langen Strecken gleich schnell.', fields: [
    ['anim.on', 'b', 'Animation einschalten (Standard)'],
    ['anim.planes', 'b', '✈️ Flugzeuge'], ['anim.trains', 'b', '🚆 Züge'], ['anim.cars', 'b', '🚗 Autos'], ['anim.ferries', 'b', '⛴️ Fähren'],
    ['anim.min_km_plane', 'r', 'Flugzeuge ab', [0, 5000, 50, ' km']],
    ['anim.min_km_train', 'r', 'Züge ab', [0, 2000, 10, ' km']],
    ['anim.min_km_car', 'r', 'Autos ab', [0, 2000, 10, ' km']],
    ['anim.min_km_ferry', 'r', 'Fähren ab', [0, 2000, 10, ' km']],
    ['anim.max_count', 'r', 'Höchstens gleichzeitig', [5, 300, 5, '']],
    ['anim.plane_speed', 'r', 'Tempo Flugzeuge', [0.25, 4, 0.05, '×']],
    ['anim.speed', 'r', 'Tempo Züge, Autos, Fähren', [0.25, 4, 0.05, '×']],
    ['anim.size', 'r', 'Grösse', [0.5, 2, 0.1, '×']],
    ['anim.hide_line', 'b', 'Linie unter dem Fahrzeug ausblenden'],
  ]},
  {id: 'timelapse', tabs: ['zeit'], icon: '🎬', title: 'Reisefilm', info: 'Die Kamera fliegt von Reise zu Reise, die Route zeichnet sich mit dem Fahrzeug, jedes Jahr ist ein Kapitel.', fields: [
    ['timelapse.speed', 'r', 'Tempo', [0.25, 4, 0.05, '×']],
    ['timelapse.pause', 'r', 'Verweilen am Ziel', [0, 3, 0.1, '×']],
    ['timelapse.min_km', 'r', 'Nur Reisen ab', [0, 3000, 25, ' km']],
    ['timelapse.cinema', 'b', 'Kino-Look (dunkle Karte)'],
    ['timelapse.glow', 'b', 'Leuchtende Spuren'],
    ['timelapse.cards', 'b', 'Titelkarte pro Reise'],
    ['timelapse.chapters', 'b', 'Jahres-Kapitel'],
    ['timelapse.counters', 'b', 'Zähler (km, Länder, Reisen)'],
  ]},
  {id: 'map', tabs: ['reisen', 'spuren', 'orte', 'regionen', 'zeit'], icon: '🗺️', title: 'Grundkarte', fields: [
    ['map.theme', 's', 'Erscheinungsbild', [['auto', 'wie Gerät'], ['light', '☀ hell'], ['dark', '☾ dunkel']]],
    ['map.basemap', 's', 'Kartenfarben (hell)', [['standard', 'Standard'], ['paper', 'Papier'], ['mono', 'Grau']]],
    ['map.palette', 's', 'Farben für Personen', [['neon', 'Neon'], ['classic', 'Klassisch'], ['pastel', 'Pastell'], ['earth', 'Erde'], ['contrast', 'Kontrast'], ['mono', 'Ton in Ton']]],
    ['map.labels', 's', 'Ortsnamen der Karte', [['many', 'viele'], ['normal', 'normal'], ['few', 'wenige'], ['off', 'keine']]],
    ['map.rivers', 'b', 'Flüsse'],
    ['map.provinces', 'b', 'Grenzen von Kantonen und Regionen'],
  ]},
];
const WM_MODES = [['road', '🚗', 'Auto'], ['rail', '🚆', 'Zug & ÖV'], ['fly', '✈️', 'Flug'], ['ferry', '⛴️', 'Schiff'], ['foot', '🚶', 'Zu Fuss']];

const wmGet = (o, k) => k.split('.').reduce((a, x) => (a == null ? a : a[x]), o);
function wmSet(o, k, v) { const ks = k.split('.'); let a = o; for (let i = 0; i < ks.length - 1; i++) a = a[ks[i]]; a[ks[ks.length - 1]] = v; }
const wmEsc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
function wmFmt(v, x) { const u = x[3]; return u === '%' ? Math.round(v * 100) + ' %' : u === '×' ? String(+(+v).toFixed(2)).replace('.', ',') + '×' : (Math.round(v * 10) / 10) + u; }

/* HTML for one section; inputs carry data-k, the caller listens for 'input' and 'click' on the container */
function wmSection(sec, st) {
  const f = sec.fields.map(([k, t, label, x]) => {
    const v = wmGet(st, k);
    if (t === 'b') return `<label class="wsw"><input type="checkbox" data-k="${k}" ${v ? 'checked' : ''}><span></span>${wmEsc(label)}</label>`;
    if (t === 'r') return `<label class="wrg"><span>${wmEsc(label)}</span><input type="range" data-k="${k}" min="${x[0]}" max="${x[1]}" step="${x[2]}" value="${v}"><b>${wmFmt(v, x)}</b></label>`;
    if (t === 'c') return `<div class="wcl"><span>${wmEsc(label)}</span><label class="wsw sm"><input type="checkbox" data-auto="${k}" ${v ? '' : 'checked'}><span></span>automatisch</label><input type="color" data-k="${k}" value="${v || '#8A84A8'}" ${v ? '' : 'disabled'} aria-label="${wmEsc(label)}"></div>`;
    return `<div class="wsg"><span>${wmEsc(label)}</span><div class="wseg" role="radiogroup" data-k="${k}">${x.map(([o, l]) => `<button type="button" role="radio" aria-checked="${o === v}" class="${o === v ? 'on' : ''}" data-v="${o}">${wmEsc(l)}</button>`).join('')}</div></div>`;
  }).join('');
  return `<div class="wsec" data-sec="${sec.id}"><h4>${sec.icon} ${wmEsc(sec.title)}</h4>${sec.info ? `<p class="winfo">${wmEsc(sec.info)}</p>` : ''}${f}</div>`;
}
function wmModes(st) {
  return `<div class="wsec" data-sec="modes"><h4>🎨 Linien &amp; Farben</h4>${WM_MODES.map(([m, ico, n]) => `<div class="wmode"><span>${ico} ${n}</span><input type="color" data-k="modes.${m}.color" value="${st.modes[m].color}" aria-label="Farbe ${n}"><select data-k="modes.${m}.dash" aria-label="Linientyp ${n}">${DASH_OPTS.map(([o, l]) => `<option value="${o}" ${o === st.modes[m].dash ? 'selected' : ''}>${l}</option>`).join('')}</select><input type="range" data-k="modes.${m}.width" min="0.5" max="3" step="0.1" value="${st.modes[m].width}" aria-label="Dicke ${n}"></div>`).join('')}</div>`;
}
/* wires a container: every change updates st and calls onChange(key) */
function wmBind(box, st, onChange) {
  const byK = {}; for (const s of WM_SPEC) for (const f of s.fields) byK[f[0]] = f;
  box.addEventListener('input', (e) => { const t = e.target, k = t.dataset.k; if (!k) return;
    const v = t.type === 'checkbox' ? t.checked : t.type === 'range' ? +t.value : t.value; wmSet(st, k, v);
    if (t.type === 'range' && byK[k]) { const b = t.parentElement.querySelector('b'); if (b) b.textContent = wmFmt(v, byK[k][3]); }
    onChange(k); });
  box.addEventListener('change', (e) => { const t = e.target;
    if (t.dataset.auto) { const c = box.querySelector(`input[type=color][data-k="${t.dataset.auto}"]`); c.disabled = t.checked; wmSet(st, t.dataset.auto, t.checked ? '' : c.value); onChange(t.dataset.auto); } });
  box.addEventListener('click', (e) => { const b = e.target.closest('.wseg button'); if (!b) return; const g = b.parentElement;
    g.querySelectorAll('button').forEach((x) => { x.classList.toggle('on', x === b); x.setAttribute('aria-checked', String(x === b)); });
    wmSet(st, g.dataset.k, b.dataset.v); onChange(g.dataset.k); });
}
