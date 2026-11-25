"""The 🎨 drawer on the map edits the live style through a proxy; the safe setter must still be able to write through it
(regression: since 0.15.1 every switch and button in the drawer did nothing)."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

STATIC = Path(__file__).resolve().parents[1] / "worldmap" / "app" / "worldmap" / "static"


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_drawer_proxy_can_be_written_but_not_polluted():
    atlas = (STATIC / "atlas.js").read_text(encoding="utf-8")
    line = next(x for x in atlas.splitlines() if "wmBind($('sd-b')" in x)
    proxy = line[line.index("new Proxy("):line.index("),k=>restyle")]
    script = (STATIC / "stylespec.js").read_text(encoding="utf-8") + f"""
let STYLE={{map:{{look:'classic'}},trips:{{line_width:1}}}};const P={proxy});
wmSet(P,'map.look','stars');wmSet(P,'trips.line_width',2);wmSet(P,'__proto__.x',1);wmSet(P,'map.__proto__',1);
console.log(JSON.stringify([STYLE.map.look,STYLE.trips.line_width,({{}}).x===undefined]));"""
    out = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=30, check=True)  # noqa: S603,S607
    assert json.loads(out.stdout.strip().splitlines()[-1]) == ["stars", 2, True]
