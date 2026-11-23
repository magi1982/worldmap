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
