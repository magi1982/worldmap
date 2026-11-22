import io
import json

import pytest

from worldmap.importers import UserImportError, detect_and_parse


def j(obj):
    return json.dumps(obj).encode()


def test_google_records():
    data = j({"locations": [
        {"latitudeE7": 470000000, "longitudeE7": 80000000, "timestamp": "2025-07-01T08:00:00Z", "accuracy": 10},
        {"latitudeE7": 461000000, "longitudeE7": 72000000, "timestampMs": "1751364000000"},
    ]})
    r = detect_and_parse(data, "Records.json", "Alex")
    assert r.format == "google-records"
    assert len(r.points) == 2
    assert r.points[0][1:5] == (47.0, 8.0, "Alex", "google")


def test_google_semantic():
    data = j({"timelineObjects": [
        {"placeVisit": {"location": {"latitudeE7": 461000000, "longitudeE7": 72000000, "name": "Sample Hotel"},
                        "duration": {"startTimestamp": "2025-07-01T10:00:00Z", "endTimestamp": "2025-07-01T18:00:00Z"}}},
        {"activitySegment": {"startLocation": {"latitudeE7": 470000000, "longitudeE7": 80000000},
                             "endLocation": {"latitudeE7": 461000000, "longitudeE7": 72000000},
                             "duration": {"startTimestamp": "2025-07-01T08:00:00Z", "endTimestamp": "2025-07-01T10:00:00Z"},
                             "activityType": "IN_PASSENGER_VEHICLE",
                             "simplifiedRawPath": {"points": [{"latE7": 465000000, "lngE7": 76000000, "timestamp": "2025-07-01T09:00:00Z"}]}}},
    ]})
    r = detect_and_parse(data)
    assert r.format == "google-semantic"
    assert len(r.points) == 5
    assert any(p[6] == "Sample Hotel" for p in r.points)


def test_google_device_android():
    data = j({"semanticSegments": [
        {"startTime": "2025-07-01T08:00:00.000+02:00", "endTime": "2025-07-01T10:00:00.000+02:00",
         "timelinePath": [{"point": "47.0°, 8.0°", "time": "2025-07-01T08:00:00.000+02:00"},
                          {"point": "46.5°, 7.6°", "time": "2025-07-01T09:00:00.000+02:00"}]},
        {"startTime": "2025-07-01T10:00:00.000+02:00", "endTime": "2025-07-01T18:00:00.000+02:00",
         "visit": {"topCandidate": {"placeLocation": {"latLng": "46.1°, 7.2°"}}}},
    ], "rawSignals": [{"position": {"LatLng": "46.2°, 7.3°", "timestamp": "2025-07-01T12:00:00.000+02:00", "accuracyMeters": 5}}]})
    r = detect_and_parse(data)
    assert r.format == "google-device"
    assert len(r.points) == 5


def test_google_device_ios():
    data = j([
        {"startTime": "2025-07-01T08:00:00.000+02:00", "endTime": "2025-07-01T10:00:00.000+02:00",
         "activity": {"start": "geo:47.0,8.0", "end": "geo:46.1,7.2", "topCandidate": {"type": "in passenger vehicle"}}},
        {"startTime": "2025-07-01T08:00:00.000+02:00", "endTime": "2025-07-01T10:00:00.000+02:00",
         "timelinePath": [{"point": "geo:46.5,7.6", "durationMinutesOffsetFromStartTime": "60"}]},
    ])
    r = detect_and_parse(data)
    assert r.format == "google-device-ios"
    assert len(r.points) == 3
    assert r.points[2][0] - r.points[0][0] == 3600


def test_gpx_and_kml():
    gpx = b"""<?xml version="1.0"?><gpx xmlns="http://www.topografix.com/GPX/1/1"><trk><trkseg>
      <trkpt lat="46.1" lon="7.2"><time>2025-07-01T08:00:00Z</time></trkpt>
      <trkpt lat="46.2" lon="7.3"><time>2025-07-01T09:00:00Z</time></trkpt></trkseg></trk></gpx>"""
    assert len(detect_and_parse(gpx, "a.gpx").points) == 2
    kml = b"""<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2"><Document>
      <Placemark><gx:Track><when>2025-07-01T08:00:00Z</when><gx:coord>7.2 46.1 0</gx:coord>
      <when>2025-07-01T09:00:00Z</when><gx:coord>7.3 46.2 0</gx:coord></gx:Track></Placemark></Document></kml>"""
    r = detect_and_parse(kml, "a.kml")
    assert r.format == "kml" and r.points[0][1] == 46.1


def test_xml_entities_rejected():
    evil = b"""<?xml version="1.0"?><!DOCTYPE gpx [<!ENTITY x SYSTEM "file:///etc/passwd">]><gpx>&x;</gpx>"""
    with pytest.raises(ValueError):
        detect_and_parse(evil, "evil.gpx")


def test_exiftool_csv_with_dms_and_folder_hint():
    csv = (
        b"SourceFile,Directory,FileName,DateTimeOriginal,GPSLatitude,GPSLongitude,Make,Model\n"
        b"/p/2019_Sample Trip/a.jpg,/p/2019_Sample Trip,a.jpg,2019:08:01 10:00:00,"
        b"\"46 deg 6' 0.00\"\" N\",\"7 deg 12' 0.00\"\" E\",Brand,Phone A\n"
        b"/p/x/b.jpg,/p/x,b.jpg,2019:08:01 11:00:00,,,Brand,Phone A\n"
    )
    r = detect_and_parse(csv, "export.csv")
    assert r.format == "csv"
    assert len(r.points) == 1 and r.skipped == 1
    ts, lat, lon, person, src, acc, hint = r.points[0]
    assert lat == pytest.approx(46.1) and lon == pytest.approx(7.2)
    assert "2019_Sample Trip" in hint and "Phone A" in hint


def test_german_semicolon_csv_with_separate_date_and_time():
    csv = "Datum;Zeit;Breitengrad;Längengrad;Ort\n01.08.2019;10:00;46,1;7,2;Beispielort\n".encode("cp1252")
    r = detect_and_parse(csv, "liste.csv")
    assert len(r.points) == 1
    assert r.columns["lat"] == "Breitengrad"


def test_pair_column_and_ref_columns():
    csv = b"time,location\n2019-08-01T10:00:00Z,\"46.1, 7.2\"\n"
    assert detect_and_parse(csv).points[0][1:3] == (46.1, 7.2)
    csv = b"DateTimeOriginal,GPSLatitude,GPSLatitudeRef,GPSLongitude,GPSLongitudeRef\n2019:08:01 10:00:00,33.9,S,18.4,E\n"
    assert detect_and_parse(csv).points[0][1] == -33.9


def test_xlsx():
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.append(["Notes"])
    ws.append(["Timestamp", "Latitude", "Longitude"])
    ws.append(["2019-08-01 10:00:00", 46.1, 7.2])
    buf = io.BytesIO()
    wb.save(buf)
    r = detect_and_parse(buf.getvalue(), "list.xlsx")
    assert r.format == "xlsx" and len(r.points) == 1


@pytest.mark.parametrize("data", [b"just,some,text\n1,2,3\n", b'{"foo": 1}', b"{broken"])
def test_unusable_input_gives_user_error(data):
    with pytest.raises(UserImportError):
        detect_and_parse(data, "x")
