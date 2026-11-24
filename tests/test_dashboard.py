"""Dashboard tiles: run the real code from atlas.js in Node with invented trips."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

STATIC = Path(__file__).resolve().parents[1] / "worldmap" / "app" / "worldmap" / "static"

STUBS = r"""
const MODES=['fly','rail','road','ferry','foot'];
const MCOL={fly:'#f0f',rail:'#0f0',road:'#00f',ferry:'#0ff',foot:'#fa0'};
const MNAME={fly:'Flug',rail:'Zug',road:'Auto',ferry:'Schiff',foot:'Zu Fuss'};
const ICO={fly:'✈️',rail:'🚆',road:'🚗',ferry:'⛴️',foot:'🚶'};
const WCOL={Alex:'#111111',Sam:'#222222',Paar:'#333333'};
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=n=>Math.round(n).toLocaleString('de-CH').replace(/[, \s]/g,'’');
const dateOf=s=>{const [y,m,d]=s.split('-').map(Number);return new Date(Date.UTC(y,m-1,d))};
let SEL=null,TAB='dash';const HOME=[47,8];const RG={list:null};const tripById={};
const GROUPS={Paar:['Alex','Sam']};
const members=n=>n?(GROUPS[n]||[n]):['Alex','Sam'];
const tripSel=t=>!SEL||t.w==SEL||(members(t.w).includes(SEL)&&!!GROUPS[t.w]);
const placeSel=()=>true;const need=()=>Promise.resolve();
const localStorage={getItem:()=>null,setItem:()=>{}};
const D=__DATA__;
"""

TRIPS = [
    {"id": 0, "name": "Testinsel <b>x</b>", "a": "2021-07-03", "b": "2021-07-10", "y": 2021, "n": 7, "w": "Paar",
     "c": "Spanien", "m": ["fly", "ferry"], "km": 4000, "k": {"fly": 3800, "ferry": 200}, "p": [28.1, -16.6],
     "st": [[28.1, -16.6, "Testinsel"], [28.1, -17.2, "Nachbarinsel"]]},
    {"id": 1, "name": "Bergdorf", "a": "2021-02-13", "b": "2021-02-20", "y": 2021, "n": 7, "w": "Alex",
     "c": "Schweiz", "m": ["road"], "km": 300, "k": {"road": 300}, "p": [46.6, 9.6]},
    {"id": 2, "name": "Rundreise", "a": "2023-09-02", "b": "2023-09-16", "y": 2023, "n": 14, "w": "Sam",
     "c": "Italien", "m": ["road", "rail"], "km": 2500, "k": {"road": 2100, "rail": 400}, "p": [43.8, 11.3]},
]


def run(js: str) -> dict:
    src = (STATIC / "atlas.js").read_text(encoding="utf-8")
    a = src.index("/* Dashboard: the trips")
    b = src.index("window.__T={};", a)
    data = {"trips": TRIPS, "persons": ["Alex", "Sam"], "places": [], "groups_cfg": []}
    code = STUBS.replace("__DATA__", json.dumps(data)) + src[a:b] + "\n" + js
    out = subprocess.run(["node", "-e", code], capture_output=True, text=True, timeout=30, check=True)
    return json.loads(out.stdout)


pytestmark = pytest.mark.skipif(not shutil.which("node"), reason="node not installed")


def test_tiles_render_and_count():
    r = run("""const T=dTrips();console.log(JSON.stringify({kpi:tKpi(T),earth:tEarth(T),rec:tRecords(T),
      pass:tPassport(T),pc:tPostcard(T),cal:tCalendar(T),lanes:tLanes(T),wheel:tWheel(T),co2:tCo2(T),favs:tFavs()}))""")
    assert "<b>3</b><span>Reisen</span>" in r["kpi"]
    assert "<b>3</b><span>Länder</span>" in r["kpi"]
    assert "<b>28</b><span>Nächte unterwegs</span>" in r["kpi"]
    assert re.search(r"<b>6.800 km</b> auf Reisen", r["earth"])
    assert "Rundreise" in r["rec"] and "Längste Autofahrt" in r["rec"]
    assert r["pass"].count("dstamp") == 3
    assert "Nachbarinsel" in r["pc"] or "Rundreise" in r["pc"]
    assert "15 von 365 Tagen" in r["cal"]  # 2023 is the newest year with trips: 15 days
    assert r["lanes"].count('data-trip="0"') == 2  # a shared trip shows on both lanes
    assert "Juli" in r["wheel"] or "September" in r["wheel"]
    assert "CO₂" in r["co2"]
    assert "empty" in r["favs"]


def test_names_are_escaped():
    r = run("DASH.pc=0;console.log(JSON.stringify({pc:tPostcard(dTrips()),rec:tRecords(dTrips())}))")
    for html in r.values():
        assert "<b>x</b>" not in html
    assert "&lt;b&gt;x&lt;/b&gt;" in r["pc"]


def test_selection_and_year_preset():
    r = run("""SEL='Sam';const a=dTrips().length;SEL=null;DASH.preset='year';
      console.log(JSON.stringify({sam:a,order:dOrder(),year:dOpts().year}))""")
    assert r["sam"] == 2  # her own trip and the couple's trip
    assert r["order"][0] == "kpi" and r["year"] == 1


def test_postcard_front_and_back():
    """0.15.0: the postcard has a canvas front, a back with greetings, km per transport and the stations,
    and buttons to turn it over, browse, pick a random trip and save it as a picture."""
    r = run("""const T=dTrips();DASH.pc=0;const html=tPostcard(T);
      const vague={...T.find(t=>t.id==2),dp:'month',a:'2023-09-02',b:'2023-09-16'};
      console.log(JSON.stringify({html,back:pcBack(T.find(t=>t.id==0)),vague:pcBack(vague),st:pcStations(T.find(t=>t.id==0)),one:pcStations(T.find(t=>t.id==1)),
        short:dfmtShort('2021-07-03'),order:DTILES.map(t=>t[0]).slice(0,2),kiosk:DPRESETS.find(p=>p[0]=='kiosk')[3][0]}))""")
    h = r["html"]
    assert '<canvas id="pccv"' in h and 'class="pcb"' in h
    for act in ("prev", "next", "rnd", "flip", "png"):
        assert f'data-pc="{act}"' in h
    assert 'data-pc="prev" aria-label="Vorherige Reise" disabled' not in h  # trip 0 is not the first by date
    b = r["back"]
    assert "Grüsse aus Testinsel &lt;b&gt;x&lt;/b&gt;!" in b
    assert "Flug 3’800 km" in b or "Flug 3'800 km" in b or "Flug 3800 km" in b.replace("’", "")
    assert "Testinsel → Nachbarinsel" in b and "Dabei: Paar" in b
    assert "~ September 2023" in r["vague"]                     # a trip known only by month says so
    assert [x["n"] for x in r["st"]] == ["Testinsel", "Nachbarinsel"] and r["one"][0]["n"] == "Bergdorf"
    assert r["short"] == "3 JUL 2021"
    assert r["order"] == ["kpi", "postcard"] and r["kiosk"] == "postcard"


def test_dashboard_is_the_first_tab_but_the_map_opens():
    html = (STATIC / "atlas.html").read_text(encoding="utf-8")
    tabs = re.findall(r'<button data-t="(\w+)"( class="on")?', html)
    assert tabs[0][0] == "dash" and dict(tabs)["reisen"] == ' class="on"'
    js = (STATIC / "atlas.js").read_text(encoding="utf-8")
    assert "setTab(NEEDS[h]?h:'reisen')" in js  # without a link to a tab the map is shown first
