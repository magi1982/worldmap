import json

from worldmap import style as S  # noqa: N812


def test_validate_clamps_and_drops():
    s = S.validate({"modes": {"road": {"color": "#abcdef", "dash": "dotted", "width": 99}, "fly": {"color": "red", "dash": "x"}},
                    "areas": {"show": "yes", "opacity": -3, "size": "nan"}, "map": {"labels": "few", "theme": "dark"},
                    "evil": "<script>"})
    assert s["modes"]["road"] == {"color": "#ABCDEF", "dash": "dotted", "width": 3.0}
    assert s["modes"]["fly"] == S.DEFAULT["modes"]["fly"]
    assert s["areas"]["show"] is True and s["areas"]["opacity"] == 0.1 and s["areas"]["size"] == 1.0
    assert s["map"]["labels"] == "few" and s["map"]["theme"] == "dark" and "evil" not in s
    assert S.validate(None) == S.DEFAULT and S.validate([1, 2]) == S.DEFAULT


def test_versions_save_and_restore(tmp_path):
    st = S.StyleStore(str(tmp_path))
    assert st.get()["style"] == S.DEFAULT and st.get()["versions"] == []
    a = st.save({"modes": {"rail": {"color": "#000000"}}}, "black trains")
    assert a["style"]["modes"]["rail"]["color"] == "#000000" and a["versions"][0]["note"] == "black trains"
    st.save({"modes": {"rail": {"color": "#000000"}}}, "same again")  # unchanged: no new version
    b = st.save({"areas": {"show": False}}, "no areas\x00\nnewline")
    assert len(b["versions"]) == 2 and "\x00" not in b["versions"][0]["note"]
    first = b["versions"][-1]["id"]
    c = st.restore(first)
    assert c["style"]["modes"]["rail"]["color"] == "#000000" and c["style"]["areas"]["show"] is True
    assert c["versions"][0]["note"].startswith("Zurück zu")
    for i in range(30):
        st.save({"areas": {"opacity": 0.1 + i / 100}}, str(i))
    assert len(st.get()["versions"]) == S.MAX_VERSIONS
    raw = json.loads((tmp_path / "style.json").read_text())
    assert raw["current"]["areas"]["opacity"] == 0.39


def test_corrupt_file_falls_back(tmp_path):
    (tmp_path / "style.json").write_text("{not json")
    assert S.StyleStore(str(tmp_path)).get()["style"] == S.DEFAULT


def test_new_style_options():
    s = S.validate({"map": {"palette": "pastel", "basemap": "paper"}, "modes": {"road": {"dash": "dashdot"}},
                    "anim": {"on": False, "speed": 99, "size": "x"}, "timelapse": {"cinema": False, "glow": "no"}})
    assert s["map"]["palette"] == "pastel" and s["map"]["basemap"] == "paper" and s["modes"]["road"]["dash"] == "dashdot"
    assert s["anim"]["on"] is False and s["anim"]["speed"] == 4.0 and s["anim"]["size"] == 1.0
    assert s["timelapse"] == {"cinema": False, "skip_everyday": True, "glow": True}
    assert S.validate({"map": {"palette": "<x>"}})["map"]["palette"] == "neon"
