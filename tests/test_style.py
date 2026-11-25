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
    assert s["map"]["gaps"] == "dotted" and S.validate({"map": {"gaps": "open"}})["map"]["gaps"] == "open"
    assert s["anim"]["on"] is False and s["anim"]["speed"] == 4.0 and s["anim"]["size"] == 1.0
    assert {k: s["timelapse"][k] for k in ("cinema", "skip_everyday", "glow")} == {"cinema": False, "skip_everyday": True, "glow": True}
    assert S.validate({"map": {"palette": "<x>"}})["map"]["palette"] == "neon"


def test_every_map_setting_is_validated():
    s = S.validate({"anim": {"vehicles": False, "min_km_car": 99999, "max_count": "7"},
                    "places": {"size_max": -5, "names": "<script>", "color_by": "year"},
                    "regions": {"border_color": "#a0b0c0", "borders": "visited"},
                    "areas": {"shape": "circles", "outline_color": "red"}, "est": {"dash": "dotted"},
                    "evil": {"x": 1}})
    assert s["anim"]["trains"] is False and s["anim"]["cars"] is False and s["anim"]["planes"] is True  # old switch
    assert s["anim"]["min_km_car"] == 2000 and s["anim"]["max_count"] == 7
    assert s["places"]["size_max"] == 4 and s["places"]["names"] == "big" and s["places"]["color_by"] == "year"
    assert s["regions"]["border_color"] == "#A0B0C0" and s["regions"]["borders"] == "visited"
    assert S.validate({"regions": {"border_color": "url(x)"}})["regions"]["border_color"] == ""
    assert s["areas"]["shape"] == "circles" and s["areas"]["outline_color"] == "fill" and s["est"]["dash"] == "dotted"
    assert "evil" not in s and set(s) == set(S.DEFAULT)


def test_presets_save_rename_default_load(tmp_path):
    st = S.StyleStore(str(tmp_path))
    g = st.get()
    assert [p["name"] for p in g["presets"]] == ["Preset 1", "Preset 2", "Preset 3"] and g["preset_default"] == -1
    assert g["presets"][0]["style"] == S.DEFAULT  # preset 1 is today's map, untouched
    assert g["presets"][1]["style"]["map"]["basemap"] == "earth" and g["presets"][1]["style"]["map"]["look"] == "stars"
    r = st.preset(2, "save", "  Nacht\x00<b>look  " + "x" * 40, {"map": {"look": "medals", "theme": "dark"}, "evil": 1})
    p = r["presets"][2]
    assert p["name"] == ("Nachtblook  " + "x" * 40).strip()[:24] and p["style"]["map"]["look"] == "medals" and "evil" not in p["style"]
    assert st.preset(0, "rename", "")["presets"][0]["name"] == "Preset 1"  # empty name falls back
    assert st.preset(1, "default")["preset_default"] == 1
    assert st.preset(1, "default")["preset_default"] == -1  # second tap: no default
    st.preset(2, "default")
    loaded = st.preset(2, "load")
    assert loaded["style"]["map"]["look"] == "medals" and loaded["versions"][0]["note"].endswith("geladen")
    assert S.StyleStore(str(tmp_path)).get()["preset_default"] == 2  # survives a restart


def test_presets_reject_bad_input(tmp_path):
    import pytest
    st = S.StyleStore(str(tmp_path))
    for bad in (-1, 3, "1", True, None, 1.0):
        with pytest.raises(LookupError):
            st.preset(bad, "save", "x", {})
    with pytest.raises(ValueError):
        st.preset(0, "delete-everything")
    (tmp_path / "style.json").write_text(json.dumps({"current": {}, "versions": [], "presets": "nope", "preset_default": 99}))
    g = st.get()
    assert len(g["presets"]) == 3 and g["preset_default"] == -1
    assert S.validate({"map": {"look": "<script>", "basemap": "earth"}})["map"] == {**S.DEFAULT["map"], "basemap": "earth"}
