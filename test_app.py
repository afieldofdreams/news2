"""
Tests for the NEWS2 scoring functions and HTTP flow.

Reference: Royal College of Physicians, NEWS2 chart (2017, updated 2020).
https://www.rcplondon.ac.uk/projects/outputs/national-early-warning-score-news-2

Each parametrised case lists (input, expected_score) at the band edges
so a regression in the thresholds will fail loudly.
"""
import os
import sqlite3
from contextlib import closing

import pytest

from app import (
    app,
    init_analytics_db,
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
def client(tmp_path):
    app.config["TESTING"] = True
    # Isolate analytics DB per test so events don't leak between tests.
    app.config["ANALYTICS_DB_PATH"] = str(tmp_path / "analytics.db")
    with app.app_context():
        init_analytics_db()
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
    assert b"NEWS2 Reference Calculator" in r.data
    assert b'method="POST"' in r.data
    # Numeric keypad on mobile
    assert b'inputmode="numeric"' in r.data
    assert b'inputmode="decimal"' in r.data


def test_form_has_dismissible_disclaimer(client):
    r = client.get("/")
    assert b'class="disclaimer__close"' in r.data
    assert b"news2DisclaimerDismissed" in r.data


def test_form_has_linkedin_cta_and_contact(client):
    r = client.get("/")
    # Follow-on-LinkedIn CTA pointing at the tracking redirect, not the raw URL.
    assert b"Follow on LinkedIn" in r.data
    assert b"/go/linkedin" in r.data
    # Contact link goes through tracking redirect too.
    assert b"/go/contact" in r.data
    # Raw LinkedIn URL must not appear directly — tracking would be bypassed.
    assert b"linkedin.com/in/" not in r.data


def test_single_parameter_three_response_text_matches_rcp(client):
    # The single-parameter-3 escalation row in RCP NEWS2 Chart 4 reads
    # "urgent review by a ward-based clinician"; making sure the page reflects
    # that and doesn't downgrade to "registered nurse".
    r = client.post("/calculate", data=_form(temperature="34.0"), follow_redirects=True)
    assert r.status_code == 200
    assert b"ward-based clinician" in r.data


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


def test_results_redirects_when_no_query_string(client):
    r = client.get("/results")
    assert r.status_code == 302
    assert "/" in r.headers["Location"]


def test_results_renders_from_query_string(client):
    # Shareable result URLs: a direct GET with full inputs renders the result page
    # without needing a prior POST in the same session.
    r = client.get(
        "/results",
        query_string=_form(
            oxygenSaturation="98",
            supplementalOxygen="yes",
            hypercapnic="yes",
        ),
    )
    assert r.status_code == 200
    assert b"NEWS2 result" in r.data
    assert b"Medium risk" in r.data
    assert b">5<" in r.data


def test_results_redirects_when_query_string_invalid(client):
    # Tampered or malformed share URL — bounce back to home rather than 400.
    r = client.get("/results", query_string={"respiratoryRate": "abc"})
    assert r.status_code == 302


# ---------- analytics & admin ----------

def _event_counts(client):
    with closing(sqlite3.connect(app.config["ANALYTICS_DB_PATH"])) as conn:
        rows = conn.execute(
            "SELECT event_type, COUNT(*) FROM events GROUP BY event_type"
        ).fetchall()
    return dict(rows)


def test_home_visit_is_tracked(client):
    client.get("/")
    counts = _event_counts(client)
    assert counts.get("visit") == 1


def test_full_funnel_tracked_for_single_visitor(client):
    client.get("/")
    # follow_redirects=True chases /calculate -> /results?... so EVENT_RESULT fires.
    client.post("/calculate", data=_form(), follow_redirects=True)
    client.get("/go/linkedin")
    client.get("/go/contact")
    counts = _event_counts(client)
    assert counts.get("visit") == 1
    assert counts.get("submit") == 1
    assert counts.get("result") == 1
    assert counts.get("click_linkedin") == 1
    assert counts.get("click_contact") == 1


def test_linkedin_redirect_goes_to_linkedin(client):
    r = client.get("/go/linkedin")
    assert r.status_code == 302
    assert "linkedin.com/in/" in r.headers["Location"]


def test_contact_redirect_goes_to_crox(client):
    r = client.get("/go/contact")
    assert r.status_code == 302
    assert "crox.io" in r.headers["Location"]


def test_admin_requires_auth(client, monkeypatch):
    monkeypatch.setenv("ADMIN_USER", "adam")
    monkeypatch.setenv("ADMIN_PASS", "hunter2")
    r = client.get("/admin")
    assert r.status_code == 401
    assert "WWW-Authenticate" in r.headers
    assert "Basic" in r.headers["WWW-Authenticate"]


def test_admin_rejects_bad_credentials(client, monkeypatch):
    import base64
    monkeypatch.setenv("ADMIN_USER", "adam")
    monkeypatch.setenv("ADMIN_PASS", "hunter2")
    bad = base64.b64encode(b"adam:nope").decode()
    r = client.get("/admin", headers={"Authorization": f"Basic {bad}"})
    assert r.status_code == 401


def test_admin_disabled_when_env_not_set(client, monkeypatch):
    # Without ADMIN_USER/ADMIN_PASS, /admin must not be reachable even with creds.
    monkeypatch.delenv("ADMIN_USER", raising=False)
    monkeypatch.delenv("ADMIN_PASS", raising=False)
    import base64
    creds = base64.b64encode(b"anyone:anything").decode()
    r = client.get("/admin", headers={"Authorization": f"Basic {creds}"})
    assert r.status_code == 401


def test_admin_shows_funnel(client, monkeypatch):
    import base64
    monkeypatch.setenv("ADMIN_USER", "adam")
    monkeypatch.setenv("ADMIN_PASS", "hunter2")
    # Generate a full funnel for one visitor.
    client.get("/")
    client.post("/calculate", data=_form(), follow_redirects=True)
    client.get("/go/linkedin")

    creds = base64.b64encode(b"adam:hunter2").decode()
    r = client.get("/admin", headers={"Authorization": f"Basic {creds}"})
    assert r.status_code == 200
    assert b"Visited" in r.data
    assert b"Entered data" in r.data
    assert b"Saw result" in r.data
    assert b"Clicked LinkedIn" in r.data
    assert b"Funnel" in r.data
