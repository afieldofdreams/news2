"""
Tests for the NEWS2 scoring functions and HTTP flow.

Reference: Royal College of Physicians, NEWS2 chart (2017, updated 2020).
https://www.rcplondon.ac.uk/projects/outputs/national-early-warning-score-news-2

Each parametrised case lists (input, expected_score) at the band edges
so a regression in the thresholds will fail loudly.
"""
import pytest

from app import (
    app,
    score_respiratory_rate,
    score_oxygen_saturation_scale_1,
    score_oxygen_saturation_scale_2,
    score_supplemental_oxygen,
    score_systolic_bp,
    score_pulse_rate,
    score_temperature,
    score_consciousness,
    determine_band,
)


# ---------- unit tests: scoring per parameter ----------

@pytest.mark.parametrize("rr,expected", [
    (0, 3), (8, 3),                 # <=8 -> 3
    (9, 1), (10, 1), (11, 1),       # 9-11 -> 1
    (12, 0), (16, 0), (20, 0),      # 12-20 -> 0
    (21, 2), (24, 2),               # 21-24 -> 2
    (25, 3), (40, 3),               # >=25 -> 3
])
def test_respiratory_rate(rr, expected):
    assert score_respiratory_rate(rr) == expected


@pytest.mark.parametrize("spo2,expected", [
    (70, 3), (91, 3),               # <=91 -> 3
    (92, 2), (93, 2),               # 92-93 -> 2
    (94, 1), (95, 1),               # 94-95 -> 1
    (96, 0), (98, 0), (100, 0),     # >=96 -> 0
])
def test_oxygen_saturation_scale_1(spo2, expected):
    assert score_oxygen_saturation_scale_1(spo2) == expected


@pytest.mark.parametrize("spo2,on_oxygen,expected", [
    # On oxygen, the high-saturation bands fire
    (97, True, 3), (100, True, 3),
    (95, True, 2), (96, True, 2),
    (93, True, 1), (94, True, 1),
    # Target range 88-92, regardless of oxygen
    (88, True, 0), (92, True, 0),
    (88, False, 0), (92, False, 0),
    # On air, anything >=93 sits in the target/above-target zone -> 0
    (93, False, 0), (100, False, 0),
    # Below target band (applies to both)
    (86, False, 1), (87, False, 1),
    (84, False, 2), (85, False, 2),
    (83, False, 3), (70, False, 3),
    (86, True, 1), (84, True, 2), (83, True, 3),
])
def test_oxygen_saturation_scale_2(spo2, on_oxygen, expected):
    assert score_oxygen_saturation_scale_2(spo2, on_oxygen) == expected


@pytest.mark.parametrize("on_oxygen,expected", [(True, 2), (False, 0)])
def test_supplemental_oxygen(on_oxygen, expected):
    assert score_supplemental_oxygen(on_oxygen) == expected


@pytest.mark.parametrize("bp,expected", [
    (60, 3), (90, 3),               # <=90 -> 3
    (91, 2), (100, 2),              # 91-100 -> 2
    (101, 1), (110, 1),             # 101-110 -> 1
    (111, 0), (180, 0), (219, 0),   # 111-219 -> 0
    (220, 3), (260, 3),             # >=220 -> 3
])
def test_systolic_bp(bp, expected):
    assert score_systolic_bp(bp) == expected


@pytest.mark.parametrize("pr,expected", [
    (30, 3), (40, 3),               # <=40 -> 3
    (41, 1), (50, 1),               # 41-50 -> 1
    (51, 0), (70, 0), (90, 0),      # 51-90 -> 0
    (91, 1), (110, 1),              # 91-110 -> 1
    (111, 2), (130, 2),             # 111-130 -> 2
    (131, 3), (200, 3),             # >=131 -> 3
])
def test_pulse_rate(pr, expected):
    assert score_pulse_rate(pr) == expected


@pytest.mark.parametrize("temp,expected", [
    (33.0, 3), (35.0, 3),                       # <=35.0 -> 3
    (35.1, 1), (35.5, 1), (36.0, 1),            # 35.1-36.0 -> 1
    (36.1, 0), (37.0, 0), (38.0, 0),            # 36.1-38.0 -> 0
    (38.1, 1), (39.0, 1),                       # 38.1-39.0 -> 1
    (39.1, 2), (40.0, 2),                       # >=39.1 -> 2
])
def test_temperature(temp, expected):
    assert score_temperature(temp) == expected


@pytest.mark.parametrize("level,expected", [
    ("alert", 0),
    ("confusion", 3),
    ("voice", 3),
    ("pain", 3),
    ("unresponsive", 3),
])
def test_consciousness(level, expected):
    assert score_consciousness(level) == expected


# ---------- unit tests: clinical risk banding ----------

@pytest.mark.parametrize("total,has_3,expected_label", [
    (0, False, "Low risk"),
    (4, False, "Low risk"),
    (5, False, "Medium risk"),
    (6, False, "Medium risk"),
    (7, False, "High risk"),
    (15, False, "High risk"),
    # Single parameter scoring 3 at low aggregate escalates to medium-equivalent
    (3, True, "Low to medium risk (single parameter 3)"),
    (4, True, "Low to medium risk (single parameter 3)"),
    # ...but at total >= 5, the higher band already covers it
    (5, True, "Medium risk"),
    (7, True, "High risk"),
])
def test_determine_band(total, has_3, expected_label):
    assert determine_band(total, has_3)["band_label"] == expected_label


# ---------- integration: full-form scenarios via the HTTP layer ----------

@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def _form(**overrides):
    base = {
        "respiratoryRate": "16",
        "oxygenSaturation": "98",
        "systolicBP": "120",
        "pulseRate": "70",
        "temperature": "37.0",
        "consciousness": "alert",
    }
    base.update(overrides)
    return base


def test_get_form_loads(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"NEWS2 score calculator" in r.data
    assert b'method="POST"' in r.data
    # Numeric keypad on mobile
    assert b'inputmode="numeric"' in r.data
    assert b'inputmode="decimal"' in r.data


def test_empty_post_shows_error_summary(client):
    r = client.post("/calculate", data={})
    assert r.status_code == 400
    assert b"There is a problem" in r.data
    assert b"Enter a respiratory rate" in r.data


def test_non_numeric_input_rejected(client):
    r = client.post("/calculate", data=_form(respiratoryRate="abc"))
    assert r.status_code == 400
    assert b"Respiratory rate must be a number" in r.data


def test_out_of_range_rejected(client):
    r = client.post("/calculate", data=_form(systolicBP="500"))
    assert r.status_code == 400
    assert b"Systolic blood pressure must be between" in r.data


def test_healthy_patient_total_zero(client):
    r = client.post("/calculate", data=_form(), follow_redirects=True)
    assert r.status_code == 200
    assert b"NEWS2 result" in r.data
    assert b"Low risk" in r.data
    # The score display shows 0
    assert b">0<" in r.data


def test_high_risk_total_matches_chart(client):
    # RR 28 (3) + SpO2 90 scale1 (3) + Suppl O2 (2) + BP 85 (3)
    # + PR 135 (3) + Temp 39.5 (2) + Unresponsive (3) = 19
    r = client.post("/calculate", data=_form(
        respiratoryRate="28",
        oxygenSaturation="90",
        supplementalOxygen="yes",
        systolicBP="85",
        pulseRate="135",
        temperature="39.5",
        consciousness="unresponsive",
    ), follow_redirects=True)
    assert r.status_code == 200
    assert b"High risk" in r.data
    assert b">19<" in r.data


def test_single_parameter_three_escalates(client):
    # Temp 34.0 scores 3, everything else 0 -> total 3, but single-3 escalation
    r = client.post("/calculate", data=_form(temperature="34.0"), follow_redirects=True)
    assert r.status_code == 200
    assert b"single parameter 3" in r.data


def test_hypercapnic_on_oxygen_at_98_scores_high(client):
    # SpO2 98% on O2 with Scale 2 -> 3, plus supplemental O2 -> 2. Total 5 -> Medium.
    r = client.post("/calculate", data=_form(
        oxygenSaturation="98",
        supplementalOxygen="yes",
        hypercapnic="yes",
    ), follow_redirects=True)
    assert r.status_code == 200
    assert b"Medium risk" in r.data
    assert b">5<" in r.data


def test_results_redirects_when_no_session(client):
    r = client.get("/results")
    assert r.status_code == 302
    assert "/" in r.headers["Location"]
