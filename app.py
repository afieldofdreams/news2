import os
import secrets
import sqlite3
from contextlib import closing
from functools import wraps

from flask import (
    Flask,
    Response,
    abort,
    redirect,
    render_template_string,
    request,
    session,
    url_for,
)
from flask_session import Session

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
app.config["SESSION_TYPE"] = "filesystem"
app.config["ANALYTICS_DB_PATH"] = os.environ.get("ANALYTICS_DB_PATH", "analytics.db")
Session(app)


CONTACT_URL = "https://crox.io"
LINKEDIN_URL = "https://www.linkedin.com/in/afieldio"

EVENT_VISIT = "visit"
EVENT_SUBMIT = "submit"
EVENT_RESULT = "result"
EVENT_CLICK_LINKEDIN = "click_linkedin"
EVENT_CLICK_CONTACT = "click_contact"
FUNNEL_STEPS = [
    (EVENT_VISIT, "Visited"),
    (EVENT_SUBMIT, "Entered data"),
    (EVENT_RESULT, "Saw result"),
    (EVENT_CLICK_LINKEDIN, "Clicked LinkedIn"),
    (EVENT_CLICK_CONTACT, "Clicked contact"),
]


def _db_connect():
    conn = sqlite3.connect(app.config["ANALYTICS_DB_PATH"])
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_analytics_db():
    with closing(_db_connect()) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visitor_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_visitor ON events(visitor_id)")
        conn.commit()


def _ensure_visitor_id():
    visitor_id = session.get("visitor_id")
    if not visitor_id:
        visitor_id = secrets.token_urlsafe(16)
        session["visitor_id"] = visitor_id
    return visitor_id


def track_event(event_type):
    visitor_id = _ensure_visitor_id()
    try:
        with closing(_db_connect()) as conn:
            conn.execute(
                "INSERT INTO events (visitor_id, event_type) VALUES (?, ?)",
                (visitor_id, event_type),
            )
            conn.commit()
    except sqlite3.Error:
        # Analytics failures must never break the user flow.
        pass


NHS_BASE_STYLES = '''
    :root {
        /* Deliberately not NHS blue. This is an independent reference tool. */
        --nhsuk-blue: #0f5a64;
        --nhsuk-dark-blue: #073f47;
        --nhsuk-bright-blue: #157684;
        --nhsuk-black: #212b32;
        --nhsuk-grey-1: #4c6272;
        --nhsuk-grey-3: #aeb7bd;
        --nhsuk-grey-4: #d8dde0;
        --nhsuk-grey-5: #f0f4f5;
        --nhsuk-white: #ffffff;
        --nhsuk-yellow: #ffeb3b;
        --nhsuk-warm-yellow: #ffb81c;
        --nhsuk-warm-red: #d5281b;
        --nhsuk-green: #007f3b;
        --nhsuk-focus: #ffeb3b;
    }

    * { box-sizing: border-box; }

    html, body {
        margin: 0;
        padding: 0;
        font-family: "Frutiger W01", Arial, sans-serif;
        font-size: 16px;
        line-height: 1.5;
        color: var(--nhsuk-black);
        background: var(--nhsuk-white);
    }

    a {
        color: var(--nhsuk-blue);
        text-decoration: underline;
    }
    a:hover { color: var(--nhsuk-dark-blue); }
    a:focus {
        outline: 4px solid var(--nhsuk-focus);
        outline-offset: 0;
        background: var(--nhsuk-focus);
        color: var(--nhsuk-black);
        text-decoration: none;
        box-shadow: 0 -2px var(--nhsuk-focus), 0 4px var(--nhsuk-black);
    }

    .nhsuk-width-container {
        max-width: 720px;
        margin: 0 auto;
        padding: 24px 16px 48px;
    }
    @media (max-width: 480px) {
        h1.nhsuk-heading-xl { font-size: 26px; }
        h2.nhsuk-heading-l { font-size: 20px; }
    }

    h1.nhsuk-heading-xl {
        font-size: 32px;
        line-height: 1.2;
        font-weight: 700;
        margin: 0 0 24px;
        color: var(--nhsuk-black);
    }
    h2.nhsuk-heading-l {
        font-size: 24px;
        line-height: 1.3;
        font-weight: 700;
        margin: 32px 0 16px;
    }

    .nhsuk-hint {
        color: var(--nhsuk-grey-1);
        font-size: 16px;
        margin-bottom: 8px;
    }

    .nhsuk-form-group {
        margin-bottom: 24px;
        padding-left: 0;
    }
    .nhsuk-form-group--error {
        padding-left: 16px;
        border-left: 4px solid var(--nhsuk-warm-red);
    }
    .nhsuk-label {
        display: block;
        font-weight: 600;
        font-size: 19px;
        margin-bottom: 8px;
        color: var(--nhsuk-black);
    }
    .nhsuk-input,
    .nhsuk-select {
        font-family: inherit;
        font-size: 19px;
        line-height: 1.4;
        padding: 12px;
        border: 2px solid var(--nhsuk-black);
        border-radius: 0;
        background: var(--nhsuk-white);
        width: 100%;
        max-width: 100%;
        min-height: 48px;
    }
    @media (min-width: 481px) {
        .nhsuk-input--width-5 { max-width: 9em; }
        .nhsuk-select { max-width: 20em; }
    }
    .nhsuk-input:focus,
    .nhsuk-select:focus,
    .nhsuk-checkboxes__input:focus + .nhsuk-checkboxes__label::before {
        outline: 4px solid var(--nhsuk-focus);
        outline-offset: 0;
        box-shadow: inset 0 0 0 2px var(--nhsuk-black);
    }
    .nhsuk-input--width-5 { max-width: 7em; }

    .nhsuk-checkboxes__item {
        position: relative;
        min-height: 40px;
        padding: 0 0 0 40px;
        margin-bottom: 8px;
    }
    .nhsuk-checkboxes__input {
        position: absolute;
        left: 0;
        top: 0;
        width: 40px;
        height: 40px;
        cursor: pointer;
        opacity: 0;
        margin: 0;
        z-index: 1;
    }
    .nhsuk-checkboxes__label {
        display: inline-block;
        padding: 7px 12px 5px 12px;
        cursor: pointer;
        font-size: 19px;
        line-height: 1.4;
    }
    .nhsuk-checkboxes__label::before {
        content: "";
        position: absolute;
        left: 0;
        top: 0;
        width: 40px;
        height: 40px;
        border: 2px solid var(--nhsuk-black);
        background: var(--nhsuk-white);
    }
    .nhsuk-checkboxes__label::after {
        content: "";
        position: absolute;
        left: 9px;
        top: 11px;
        width: 18px;
        height: 7px;
        border: solid var(--nhsuk-black);
        border-width: 0 0 4px 4px;
        transform: rotate(-45deg);
        opacity: 0;
    }
    .nhsuk-checkboxes__input:checked + .nhsuk-checkboxes__label::after { opacity: 1; }

    .nhsuk-button {
        font-family: inherit;
        font-size: 19px;
        font-weight: 600;
        line-height: 1.4;
        padding: 14px 20px 12px;
        background: var(--nhsuk-bright-blue);
        color: var(--nhsuk-white);
        border: 2px solid transparent;
        border-bottom: 4px solid var(--nhsuk-dark-blue);
        border-radius: 0;
        cursor: pointer;
        text-align: center;
        margin-top: 8px;
        min-height: 48px;
        width: 100%;
        max-width: 360px;
        text-decoration: none;
        display: inline-block;
    }
    .nhsuk-button:hover { background: var(--nhsuk-blue); }
    .nhsuk-button:focus {
        outline: 4px solid var(--nhsuk-focus);
        outline-offset: 0;
        background: var(--nhsuk-focus);
        color: var(--nhsuk-black);
        box-shadow: 0 4px 0 var(--nhsuk-black);
    }
    .nhsuk-button--secondary {
        background: var(--nhsuk-grey-5);
        color: var(--nhsuk-black);
        border-bottom-color: var(--nhsuk-grey-3);
    }
    .nhsuk-button--secondary:hover { background: var(--nhsuk-grey-4); }

    /* Author card */
    .author-card {
        background: var(--nhsuk-grey-5);
        border-left: 4px solid var(--nhsuk-blue);
        padding: 16px 20px 20px;
        margin: 32px 0 8px;
        font-size: 15px;
        line-height: 1.5;
    }
    .author-card h3 {
        font-size: 18px;
        margin: 0 0 8px;
    }
    .author-card p { margin: 0 0 8px; }
    .author-card__support {
        margin-top: 16px;
    }
    /* Result actions row */
    .result-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin: 24px 0 8px;
    }
    .result-actions .nhsuk-button { margin: 0; }
    .share-toast {
        display: inline-block;
        margin-left: 4px;
        padding: 6px 10px;
        font-size: 14px;
        color: var(--nhsuk-black);
        background: #d9f4e3;
        border: 1px solid #007f3b;
        opacity: 0;
        transition: opacity 0.15s ease-in;
    }
    .share-toast.is-visible { opacity: 1; }

    /* Dismissible disclaimer — compact yellow caution */
    .disclaimer {
        position: relative;
        background: #fff8e0;
        border: 2px solid var(--nhsuk-warm-yellow);
        border-left-width: 8px;
        padding: 12px 44px 12px 16px;
        margin: 0 0 24px;
        font-size: 15px;
        line-height: 1.4;
    }
    .disclaimer__title {
        font-size: 16px;
        font-weight: 700;
        margin: 0 0 4px;
        color: var(--nhsuk-black);
    }
    .disclaimer p { margin: 0; }
    .disclaimer__close {
        position: absolute;
        top: 4px;
        right: 4px;
        width: 36px;
        height: 36px;
        background: transparent;
        border: 2px solid transparent;
        color: var(--nhsuk-black);
        font-size: 24px;
        line-height: 1;
        cursor: pointer;
        padding: 0;
    }
    .disclaimer__close:hover { background: var(--nhsuk-warm-yellow); }
    .disclaimer__close:focus {
        outline: 4px solid var(--nhsuk-focus);
        outline-offset: 0;
        background: var(--nhsuk-focus);
    }
    .disclaimer-dismissed .disclaimer { display: none; }

    .nhsuk-error-summary {
        border: 4px solid var(--nhsuk-warm-red);
        padding: 16px;
        margin-bottom: 24px;
    }
    .nhsuk-error-summary__title {
        font-size: 22px;
        font-weight: 700;
        margin: 0 0 8px;
        color: var(--nhsuk-warm-red);
    }
    .nhsuk-error-summary__list { margin: 0; padding-left: 20px; }
    .nhsuk-error-summary__list a {
        color: var(--nhsuk-warm-red);
        font-weight: 600;
    }
    .nhsuk-error-message {
        color: var(--nhsuk-warm-red);
        font-weight: 600;
        margin-bottom: 8px;
    }
    .nhsuk-error-message::before { content: "Error: "; }

    .nhsuk-footer {
        background: var(--nhsuk-grey-5);
        border-top: 1px solid var(--nhsuk-grey-4);
        padding: 24px 16px;
        margin-top: 48px;
        font-size: 16px;
        color: var(--nhsuk-grey-1);
    }
    .nhsuk-footer__inner { max-width: 960px; margin: 0 auto; }
'''


HTML_FORM = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NEWS2 Reference Calculator</title>
    <script>
        // Apply dismissed state before paint to avoid a flash of the warning.
        try {
            if (sessionStorage.getItem('news2DisclaimerDismissed') === '1') {
                document.documentElement.className += ' disclaimer-dismissed';
            }
        } catch (e) {}
    </script>
    <style>{{ base_styles|safe }}</style>
</head>
<body>
    <main class="nhsuk-width-container" id="main-content">
        <div class="disclaimer" role="note" aria-labelledby="disclaimer-title">
            <button type="button" class="disclaimer__close" aria-label="Dismiss disclaimer">&times;</button>
            <p class="disclaimer__title" id="disclaimer-title">Not an NHS service. Not a medical device.</p>
            <p>Independent educational reference only &mdash; not for clinical use.</p>
        </div>

        <h1 class="nhsuk-heading-xl">NEWS2 Reference Calculator</h1>
        <p>Enter observations below to compute the NEWS2 aggregate score using the algorithm
        published in the
        <a href="https://www.rcplondon.ac.uk/projects/outputs/national-early-warning-score-news-2"
           rel="noopener noreferrer" target="_blank">Royal College of Physicians NEWS2 chart</a>
        (RCP, 2017). All fields are required.</p>

        {% if errors %}
        <div class="nhsuk-error-summary" aria-labelledby="error-summary-title" role="alert" tabindex="-1">
            <h2 class="nhsuk-error-summary__title" id="error-summary-title">There is a problem</h2>
            <ul class="nhsuk-error-summary__list">
                {% for field, msg in errors.items() %}
                <li><a href="#{{ field }}">{{ msg }}</a></li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}

        <form method="POST" action="{{ url_for('calculate_news2') }}" novalidate>
            <div class="nhsuk-form-group {% if errors.respiratoryRate %}nhsuk-form-group--error{% endif %}">
                <label class="nhsuk-label" for="respiratoryRate">Respiratory rate (breaths per minute)</label>
                <div class="nhsuk-hint">Typical range 12 to 20 breaths per minute.</div>
                {% if errors.respiratoryRate %}<p class="nhsuk-error-message">{{ errors.respiratoryRate }}</p>{% endif %}
                <input class="nhsuk-input nhsuk-input--width-5" id="respiratoryRate" name="respiratoryRate"
                       type="number" min="0" max="60" inputmode="numeric" pattern="[0-9]*"
                       autocomplete="off"
                       value="{{ values.respiratoryRate or '' }}">
            </div>

            <div class="nhsuk-form-group {% if errors.oxygenSaturation %}nhsuk-form-group--error{% endif %}">
                <label class="nhsuk-label" for="oxygenSaturation">Oxygen saturation (SpO<sub>2</sub>, %)</label>
                <div class="nhsuk-hint">Whole number, 0 to 100.</div>
                {% if errors.oxygenSaturation %}<p class="nhsuk-error-message">{{ errors.oxygenSaturation }}</p>{% endif %}
                <input class="nhsuk-input nhsuk-input--width-5" id="oxygenSaturation" name="oxygenSaturation"
                       type="number" min="0" max="100" inputmode="numeric" pattern="[0-9]*"
                       autocomplete="off"
                       value="{{ values.oxygenSaturation or '' }}">
            </div>

            <div class="nhsuk-form-group">
                <div class="nhsuk-checkboxes__item">
                    <input class="nhsuk-checkboxes__input" id="supplementalOxygen" name="supplementalOxygen"
                           type="checkbox" value="yes" {% if values.supplementalOxygen %}checked{% endif %}>
                    <label class="nhsuk-checkboxes__label" for="supplementalOxygen">
                        Patient is receiving supplemental oxygen
                    </label>
                </div>
                <div class="nhsuk-checkboxes__item">
                    <input class="nhsuk-checkboxes__input" id="hypercapnic" name="hypercapnic"
                           type="checkbox" value="yes" {% if values.hypercapnic %}checked{% endif %}>
                    <label class="nhsuk-checkboxes__label" for="hypercapnic">
                        Use SpO<sub>2</sub> Scale 2 (hypercapnic respiratory failure, target 88&ndash;92%)
                    </label>
                </div>
            </div>

            <div class="nhsuk-form-group {% if errors.systolicBP %}nhsuk-form-group--error{% endif %}">
                <label class="nhsuk-label" for="systolicBP">Systolic blood pressure (mmHg)</label>
                <div class="nhsuk-hint">Whole number, 40 to 260.</div>
                {% if errors.systolicBP %}<p class="nhsuk-error-message">{{ errors.systolicBP }}</p>{% endif %}
                <input class="nhsuk-input nhsuk-input--width-5" id="systolicBP" name="systolicBP"
                       type="number" min="40" max="260" inputmode="numeric" pattern="[0-9]*"
                       autocomplete="off"
                       value="{{ values.systolicBP or '' }}">
            </div>

            <div class="nhsuk-form-group {% if errors.pulseRate %}nhsuk-form-group--error{% endif %}">
                <label class="nhsuk-label" for="pulseRate">Pulse rate (beats per minute)</label>
                <div class="nhsuk-hint">Whole number, 20 to 220.</div>
                {% if errors.pulseRate %}<p class="nhsuk-error-message">{{ errors.pulseRate }}</p>{% endif %}
                <input class="nhsuk-input nhsuk-input--width-5" id="pulseRate" name="pulseRate"
                       type="number" min="20" max="220" inputmode="numeric" pattern="[0-9]*"
                       autocomplete="off"
                       value="{{ values.pulseRate or '' }}">
            </div>

            <div class="nhsuk-form-group {% if errors.temperature %}nhsuk-form-group--error{% endif %}">
                <label class="nhsuk-label" for="temperature">Temperature (&deg;C)</label>
                <div class="nhsuk-hint">Decimal, 25.0 to 45.0.</div>
                {% if errors.temperature %}<p class="nhsuk-error-message">{{ errors.temperature }}</p>{% endif %}
                <input class="nhsuk-input nhsuk-input--width-5" id="temperature" name="temperature"
                       type="number" min="25" max="45" step="0.1" inputmode="decimal"
                       autocomplete="off"
                       value="{{ values.temperature or '' }}">
            </div>

            <div class="nhsuk-form-group">
                <label class="nhsuk-label" for="consciousness">Level of consciousness (ACVPU)</label>
                <div class="nhsuk-hint">Select the patient's current state.</div>
                <select class="nhsuk-select" id="consciousness" name="consciousness">
                    <option value="alert" {% if values.consciousness == 'alert' %}selected{% endif %}>Alert</option>
                    <option value="confusion" {% if values.consciousness == 'confusion' %}selected{% endif %}>New confusion</option>
                    <option value="voice" {% if values.consciousness == 'voice' %}selected{% endif %}>Responds to voice</option>
                    <option value="pain" {% if values.consciousness == 'pain' %}selected{% endif %}>Responds to pain</option>
                    <option value="unresponsive" {% if values.consciousness == 'unresponsive' %}selected{% endif %}>Unresponsive</option>
                </select>
            </div>

            <button class="nhsuk-button" type="submit">Calculate score</button>
        </form>

        <script>
            // Dismissible disclaimer — closed for the rest of the tab session.
            (function() {
                var close = document.querySelector('.disclaimer__close');
                if (!close) return;
                close.addEventListener('click', function() {
                    try { sessionStorage.setItem('news2DisclaimerDismissed', '1'); } catch (e) {}
                    document.documentElement.classList.add('disclaimer-dismissed');
                });
            })();
        </script>

        <aside class="author-card" aria-label="About the author">
            <h3>About the author</h3>
            <p>Built by Adam Field &mdash; product builder shipping small useful tools.
            More of my work at <a href="{{ url_for('redirect_contact') }}" rel="noopener">crox.io</a>.</p>
            <p>Want to support me? Follow me on LinkedIn.</p>
            <p class="author-card__support">
                <a class="nhsuk-button nhsuk-button--secondary"
                   href="{{ url_for('redirect_linkedin') }}"
                   rel="noopener noreferrer" target="_blank">Follow on LinkedIn</a>
            </p>
        </aside>
    </main>

    <footer class="nhsuk-footer">
        <div class="nhsuk-footer__inner">
            Independent educational reference, not affiliated with the NHS or any healthcare
            organisation. Not a medical device. Not for clinical decision support.
        </div>
    </footer>
</body>
</html>
'''


HTML_RESULTS = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NEWS2 Reference Calculator — result</title>
    <script>
        try {
            if (sessionStorage.getItem('news2DisclaimerDismissed') === '1') {
                document.documentElement.className += ' disclaimer-dismissed';
            }
        } catch (e) {}
    </script>
    <style>
        {{ base_styles|safe }}
        .nhsuk-care-card {
            border-left: 8px solid {{ band_color }};
            background: var(--nhsuk-grey-5);
            padding: 16px 20px;
            margin: 24px 0;
        }
        .nhsuk-care-card__heading {
            background: {{ band_color }};
            color: {{ band_text_color }};
            display: inline-block;
            padding: 8px 12px;
            margin: 0 0 12px;
            font-size: 22px;
            font-weight: 700;
        }
        .nhsuk-score-display {
            font-size: 48px;
            font-weight: 700;
            line-height: 1;
            color: var(--nhsuk-black);
            margin: 8px 0 16px;
        }
        @media (max-width: 480px) {
            .nhsuk-score-display { font-size: 40px; }
            .nhsuk-care-card { padding: 12px 16px; }
        }
        .nhsuk-summary-list {
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0 24px;
        }
        .nhsuk-summary-list th,
        .nhsuk-summary-list td {
            text-align: left;
            padding: 12px 8px;
            border-bottom: 1px solid var(--nhsuk-grey-4);
            font-size: 16px;
        }
        .nhsuk-summary-list th { font-weight: 600; }
        .nhsuk-summary-list td:last-child { text-align: right; font-weight: 600; }
    </style>
</head>
<body>
    <main class="nhsuk-width-container" id="main-content">
        <div class="disclaimer" role="note" aria-labelledby="disclaimer-title">
            <button type="button" class="disclaimer__close" aria-label="Dismiss disclaimer">&times;</button>
            <p class="disclaimer__title" id="disclaimer-title">Not an NHS service. Not a medical device.</p>
            <p>Independent educational reference only &mdash; not for clinical use.</p>
        </div>

        <h1 class="nhsuk-heading-xl">NEWS2 result</h1>

        <div class="nhsuk-care-card" role="region" aria-label="Reference output">
            <p class="nhsuk-care-card__heading">{{ band_label }}</p>
            <p class="nhsuk-score-display">{{ score }}</p>
            <p><strong>Clinical response:</strong> {{ response }}</p>
            <p><strong>Monitoring:</strong> {{ monitoring_time }}</p>
            {% if has_level_3 %}
            <p><strong>Note:</strong> At least one individual parameter scored 3. Per the published
            NEWS2 algorithm, this flag exists in the chart even when the aggregate score is low.</p>
            {% endif %}
        </div>

        <h2 class="nhsuk-heading-l">Score breakdown</h2>
        <table class="nhsuk-summary-list">
            <thead>
                <tr><th scope="col">Parameter</th><th scope="col">Score</th></tr>
            </thead>
            <tbody>
                {% for param, value in sorted_scores %}
                <tr><th scope="row">{{ param }}</th><td>{{ value }}</td></tr>
                {% endfor %}
                <tr><th scope="row">Total</th><td>{{ score }}</td></tr>
            </tbody>
        </table>

        <div class="result-actions">
            <a class="nhsuk-button" href="{{ url_for('home') }}">Calculate another score</a>
            <button class="nhsuk-button nhsuk-button--secondary"
                    type="button" id="share-button" hidden>Share result</button>
            <span class="share-toast" id="share-toast" role="status" aria-live="polite"></span>
        </div>

        <aside class="author-card" aria-label="About the author">
            <h3>About the author</h3>
            <p>Built by Adam Field &mdash; product builder shipping small useful tools.
            More of my work at <a href="{{ url_for('redirect_contact') }}" rel="noopener">crox.io</a>.</p>
            <p>Want to support me? Follow me on LinkedIn.</p>
            <p class="author-card__support">
                <a class="nhsuk-button nhsuk-button--secondary"
                   href="{{ url_for('redirect_linkedin') }}"
                   rel="noopener noreferrer" target="_blank">Follow on LinkedIn</a>
            </p>
        </aside>

        <script>
            (function() {
                var close = document.querySelector('.disclaimer__close');
                if (close) {
                    close.addEventListener('click', function() {
                        try { sessionStorage.setItem('news2DisclaimerDismissed', '1'); } catch (e) {}
                        document.documentElement.classList.add('disclaimer-dismissed');
                    });
                }

                var btn = document.getElementById('share-button');
                var toast = document.getElementById('share-toast');
                if (!btn) return;
                btn.hidden = false;

                var url = window.location.href;
                var shareText = {{ share_text|tojson }};

                function showToast(msg) {
                    if (!toast) return;
                    toast.textContent = msg;
                    toast.classList.add('is-visible');
                    setTimeout(function() { toast.classList.remove('is-visible'); }, 2500);
                }

                btn.addEventListener('click', function() {
                    if (navigator.share) {
                        navigator.share({
                            title: 'NEWS2 reference result',
                            text: shareText,
                            url: url
                        }).catch(function() { /* user cancelled */ });
                        return;
                    }
                    if (navigator.clipboard && navigator.clipboard.writeText) {
                        navigator.clipboard.writeText(url).then(function() {
                            showToast('Link copied');
                        }).catch(function() {
                            showToast('Copy failed — long-press the URL bar');
                        });
                    } else {
                        showToast('Copy the URL from your browser bar');
                    }
                });
            })();
        </script>
    </main>

    <footer class="nhsuk-footer">
        <div class="nhsuk-footer__inner">
            Independent educational reference, not affiliated with the NHS or any healthcare
            organisation. Not a medical device. Not for clinical decision support.
        </div>
    </footer>
</body>
</html>
'''


def score_respiratory_rate(rr):
    if rr <= 8:
        return 3
    if 9 <= rr <= 11:
        return 1
    if 12 <= rr <= 20:
        return 0
    if 21 <= rr <= 24:
        return 2
    return 3  # >= 25


def score_oxygen_saturation_scale_1(spo2):
    if spo2 <= 91:
        return 3
    if 92 <= spo2 <= 93:
        return 2
    if 94 <= spo2 <= 95:
        return 1
    return 0  # >= 96


def score_oxygen_saturation_scale_2(spo2, on_oxygen):
    if on_oxygen:
        if spo2 >= 97:
            return 3
        if 95 <= spo2 <= 96:
            return 2
        if 93 <= spo2 <= 94:
            return 1
    if 88 <= spo2 <= 92:
        return 0
    if not on_oxygen and spo2 >= 93:
        return 0
    if 86 <= spo2 <= 87:
        return 1
    if 84 <= spo2 <= 85:
        return 2
    return 3  # <= 83


def score_supplemental_oxygen(on_oxygen):
    return 2 if on_oxygen else 0


def score_systolic_bp(bp):
    if bp <= 90:
        return 3
    if 91 <= bp <= 100:
        return 2
    if 101 <= bp <= 110:
        return 1
    if 111 <= bp <= 219:
        return 0
    return 3  # >= 220


def score_pulse_rate(pr):
    if pr <= 40:
        return 3
    if 41 <= pr <= 50:
        return 1
    if 51 <= pr <= 90:
        return 0
    if 91 <= pr <= 110:
        return 1
    if 111 <= pr <= 130:
        return 2
    return 3  # >= 131


def score_temperature(temp):
    if temp <= 35.0:
        return 3
    if 35.1 <= temp <= 36.0:
        return 1
    if 36.1 <= temp <= 38.0:
        return 0
    if 38.1 <= temp <= 39.0:
        return 1
    return 2  # >= 39.1


def score_consciousness(level):
    return 0 if level == 'alert' else 3


FIELD_SPECS = {
    'respiratoryRate': {'label': 'respiratory rate', 'type': int, 'min': 0, 'max': 60},
    'oxygenSaturation': {'label': 'oxygen saturation', 'type': int, 'min': 0, 'max': 100},
    'systolicBP': {'label': 'systolic blood pressure', 'type': int, 'min': 40, 'max': 260},
    'pulseRate': {'label': 'pulse rate', 'type': int, 'min': 20, 'max': 220},
    'temperature': {'label': 'temperature', 'type': float, 'min': 25.0, 'max': 45.0},
}


def parse_inputs(source):
    """Parse NEWS2 inputs from a form or query-string source (anything with .get)."""
    values = {}
    errors = {}
    for name, spec in FIELD_SPECS.items():
        raw = source.get(name, '').strip()
        if raw == '':
            errors[name] = f"Enter a {spec['label']}"
            values[name] = ''
            continue
        try:
            v = spec['type'](raw)
        except ValueError:
            errors[name] = f"{spec['label'].capitalize()} must be a number"
            values[name] = raw
            continue
        if v < spec['min'] or v > spec['max']:
            errors[name] = f"{spec['label'].capitalize()} must be between {spec['min']} and {spec['max']}"
            values[name] = raw
            continue
        values[name] = v

    values['supplementalOxygen'] = source.get('supplementalOxygen') == 'yes'
    values['hypercapnic'] = source.get('hypercapnic') == 'yes'
    consciousness = source.get('consciousness', 'alert')
    if consciousness not in {'alert', 'confusion', 'voice', 'pain', 'unresponsive'}:
        consciousness = 'alert'
    values['consciousness'] = consciousness
    return values, errors


def compute_result(values):
    """Run the NEWS2 scoring on validated inputs and return the template kwargs."""
    on_oxygen = values['supplementalOxygen']
    hypercapnic = values['hypercapnic']
    spo2 = values['oxygenSaturation']

    if hypercapnic:
        spo2_score = score_oxygen_saturation_scale_2(spo2, on_oxygen)
    else:
        spo2_score = score_oxygen_saturation_scale_1(spo2)

    scores = {
        'Respiratory rate': score_respiratory_rate(values['respiratoryRate']),
        'Oxygen saturation': spo2_score,
        'Supplemental oxygen': score_supplemental_oxygen(on_oxygen),
        'Systolic blood pressure': score_systolic_bp(values['systolicBP']),
        'Pulse rate': score_pulse_rate(values['pulseRate']),
        'Temperature': score_temperature(values['temperature']),
        'Consciousness (ACVPU)': score_consciousness(values['consciousness']),
    }

    total_score = sum(scores.values())
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    has_level_3 = any(v == 3 for v in scores.values())
    band = determine_band(total_score, has_level_3)
    return {
        'score': total_score,
        'sorted_scores': sorted_scores,
        'has_level_3': has_level_3,
        **band,
    }


def values_to_share_params(values):
    """Serialise validated inputs into query-string args for a shareable /results URL."""
    return {
        'respiratoryRate': values['respiratoryRate'],
        'oxygenSaturation': values['oxygenSaturation'],
        'systolicBP': values['systolicBP'],
        'pulseRate': values['pulseRate'],
        'temperature': values['temperature'],
        'supplementalOxygen': 'yes' if values['supplementalOxygen'] else 'no',
        'hypercapnic': 'yes' if values['hypercapnic'] else 'no',
        'consciousness': values['consciousness'],
    }


@app.route('/')
def home():
    track_event(EVENT_VISIT)
    return render_template_string(
        HTML_FORM,
        base_styles=NHS_BASE_STYLES,
        errors={},
        values={'consciousness': 'alert'},
    )


@app.route('/calculate', methods=['POST'])
def calculate_news2():
    track_event(EVENT_SUBMIT)
    values, errors = parse_inputs(request.form)
    if errors:
        return render_template_string(
            HTML_FORM,
            base_styles=NHS_BASE_STYLES,
            errors=errors,
            values=values,
        ), 400

    return redirect(url_for('results', **values_to_share_params(values)))


def determine_band(total_score, has_level_3):
    """Per NEWS2 chart: clinical response by aggregate score, with single-parameter-3 escalation."""
    if total_score == 0:
        band = {
            'band_label': 'Low risk',
            'band_color': '#007f3b',
            'band_text_color': '#ffffff',
            'response': 'Continue routine NEWS2 monitoring by a registered nurse.',
            'monitoring_time': 'Minimum 12-hourly observations.',
        }
    elif 1 <= total_score <= 4:
        band = {
            'band_label': 'Low risk',
            'band_color': '#007f3b',
            'band_text_color': '#ffffff',
            'response': 'Registered nurse to assess. Decide whether to increase frequency of monitoring or escalate clinical care.',
            'monitoring_time': 'Minimum 4 to 6-hourly observations.',
        }
    elif 5 <= total_score <= 6:
        band = {
            'band_label': 'Medium risk',
            'band_color': '#ed8b00',
            'band_text_color': '#212b32',
            'response': 'Urgent review by a clinician skilled in acute illness assessment. Patient to be in a clinical area with monitoring facilities.',
            'monitoring_time': 'Minimum 1-hourly observations.',
        }
    else:  # >= 7
        band = {
            'band_label': 'High risk',
            'band_color': '#d5281b',
            'band_text_color': '#ffffff',
            'response': 'Emergency assessment by a clinical team with critical-care competencies. Usually transfer to a higher level of care.',
            'monitoring_time': 'Continuous monitoring of vital signs.',
        }

    # Single-parameter score of 3 triggers urgent review even at low aggregate.
    # Wording mirrors RCP NEWS2 Chart 4 (clinical response) — the responder is a
    # ward-based clinician competent in acute-illness assessment, not a nurse alone.
    if has_level_3 and total_score < 5:
        band = {
            'band_label': 'Low to medium risk (single parameter 3)',
            'band_color': '#ed8b00',
            'band_text_color': '#212b32',
            'response': 'Urgent review by a ward-based clinician (competent in the assessment of acute illness) to decide whether escalation of care is necessary. A single parameter scoring 3 indicates a localised concern even when the total NEWS2 is low.',
            'monitoring_time': 'Minimum 1-hourly observations.',
        }
    return band


@app.route('/results')
def results():
    if not request.args:
        return redirect(url_for('home'))
    values, errors = parse_inputs(request.args)
    if errors:
        return redirect(url_for('home'))

    result = compute_result(values)
    track_event(EVENT_RESULT)
    share_text = (
        f"NEWS2 reference score {result['score']} ({result['band_label']}). "
        f"For information only, not a clinical assessment."
    )
    return render_template_string(
        HTML_RESULTS,
        base_styles=NHS_BASE_STYLES,
        share_text=share_text,
        **result,
    )


@app.route('/go/linkedin')
def redirect_linkedin():
    track_event(EVENT_CLICK_LINKEDIN)
    return redirect(LINKEDIN_URL, code=302)


@app.route('/go/contact')
def redirect_contact():
    track_event(EVENT_CLICK_CONTACT)
    return redirect(CONTACT_URL, code=302)


# ---------- admin / analytics ----------

def _check_admin_auth():
    expected_user = os.environ.get("ADMIN_USER", "")
    expected_pass = os.environ.get("ADMIN_PASS", "")
    if not expected_user or not expected_pass:
        return False
    auth = request.authorization
    if not auth or auth.username is None or auth.password is None:
        return False
    return (
        secrets.compare_digest(auth.username, expected_user)
        and secrets.compare_digest(auth.password, expected_pass)
    )


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not _check_admin_auth():
            return Response(
                "Authentication required.",
                401,
                {"WWW-Authenticate": 'Basic realm="NEWS2 admin"'},
            )
        return view(*args, **kwargs)

    return wrapper


def compute_funnel():
    counts = {step: 0 for step, _ in FUNNEL_STEPS}
    try:
        with closing(_db_connect()) as conn:
            rows = conn.execute(
                """
                SELECT event_type, COUNT(DISTINCT visitor_id)
                FROM events
                GROUP BY event_type
                """
            ).fetchall()
    except sqlite3.Error:
        rows = []
    for event_type, uniques in rows:
        if event_type in counts:
            counts[event_type] = uniques
    visits = counts[EVENT_VISIT] or 0
    funnel = []
    for step, label in FUNNEL_STEPS:
        uniques = counts.get(step, 0)
        pct = (uniques / visits * 100) if visits else 0.0
        funnel.append({"step": step, "label": label, "uniques": uniques, "pct": pct})
    return funnel


def compute_daily_stats(limit=30):
    try:
        with closing(_db_connect()) as conn:
            rows = conn.execute(
                """
                SELECT DATE(created_at) AS day, event_type,
                       COUNT(DISTINCT visitor_id) AS uniques
                FROM events
                GROUP BY day, event_type
                ORDER BY day DESC
                """
            ).fetchall()
    except sqlite3.Error:
        rows = []
    days = {}
    for day, event_type, uniques in rows:
        days.setdefault(day, {step: 0 for step, _ in FUNNEL_STEPS})
        if event_type in days[day]:
            days[day][event_type] = uniques
    ordered = sorted(days.items(), reverse=True)[:limit]
    return [{"day": day, **counts} for day, counts in ordered]


def compute_totals():
    try:
        with closing(_db_connect()) as conn:
            total_events = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            total_visitors = conn.execute(
                "SELECT COUNT(DISTINCT visitor_id) FROM events"
            ).fetchone()[0]
    except sqlite3.Error:
        return {"total_events": 0, "total_visitors": 0}
    return {"total_events": total_events, "total_visitors": total_visitors}


HTML_ADMIN = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NEWS2 admin</title>
    <style>
        {{ base_styles|safe }}
        .admin-funnel { margin: 24px 0 32px; }
        .admin-funnel__row {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 8px;
        }
        .admin-funnel__label {
            flex: 0 0 180px;
            font-weight: 600;
        }
        .admin-funnel__bar {
            flex: 1;
            background: var(--nhsuk-grey-4);
            height: 28px;
            position: relative;
            overflow: hidden;
            min-width: 80px;
        }
        .admin-funnel__bar-fill {
            background: var(--nhsuk-bright-blue);
            height: 100%;
        }
        .admin-funnel__value {
            flex: 0 0 160px;
            text-align: right;
            font-variant-numeric: tabular-nums;
        }
        .admin-totals {
            display: flex;
            gap: 24px;
            flex-wrap: wrap;
            margin: 16px 0 24px;
        }
        .admin-totals__card {
            flex: 1 1 200px;
            background: var(--nhsuk-grey-5);
            padding: 16px;
            border-left: 4px solid var(--nhsuk-blue);
        }
        .admin-totals__value {
            font-size: 28px;
            font-weight: 700;
            display: block;
        }
        table.admin-daily {
            border-collapse: collapse;
            width: 100%;
            font-size: 15px;
        }
        table.admin-daily th, table.admin-daily td {
            border-bottom: 1px solid var(--nhsuk-grey-4);
            padding: 8px;
            text-align: right;
        }
        table.admin-daily th:first-child,
        table.admin-daily td:first-child { text-align: left; }
        table.admin-daily th { background: var(--nhsuk-grey-5); }
    </style>
</head>
<body>
    <main class="nhsuk-width-container" id="main-content">
        <h1 class="nhsuk-heading-xl">Analytics</h1>

        <div class="admin-totals">
            <div class="admin-totals__card">
                <span class="admin-totals__value">{{ totals.total_visitors }}</span>
                Unique visitors (all-time)
            </div>
            <div class="admin-totals__card">
                <span class="admin-totals__value">{{ totals.total_events }}</span>
                Total events
            </div>
        </div>

        <h2 class="nhsuk-heading-l">Funnel (unique visitors)</h2>
        <div class="admin-funnel">
            {% set top = funnel[0].uniques if funnel and funnel[0].uniques else 1 %}
            {% for row in funnel %}
            <div class="admin-funnel__row">
                <div class="admin-funnel__label">{{ row.label }}</div>
                <div class="admin-funnel__bar">
                    <div class="admin-funnel__bar-fill"
                         style="width: {{ (row.uniques / top * 100)|round(1) }}%"></div>
                </div>
                <div class="admin-funnel__value">
                    {{ row.uniques }} ({{ '%.1f'|format(row.pct) }}%)
                </div>
            </div>
            {% endfor %}
        </div>

        <h2 class="nhsuk-heading-l">By day (last 30 days)</h2>
        {% if daily %}
        <table class="admin-daily">
            <thead>
                <tr>
                    <th>Date</th>
                    {% for step, label in funnel_steps %}<th>{{ label }}</th>{% endfor %}
                </tr>
            </thead>
            <tbody>
                {% for row in daily %}
                <tr>
                    <td>{{ row.day }}</td>
                    {% for step, _ in funnel_steps %}<td>{{ row[step] }}</td>{% endfor %}
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <p>No events recorded yet.</p>
        {% endif %}
    </main>
</body>
</html>
'''


@app.route('/admin')
@require_admin
def admin():
    return render_template_string(
        HTML_ADMIN,
        base_styles=NHS_BASE_STYLES,
        totals=compute_totals(),
        funnel=compute_funnel(),
        funnel_steps=FUNNEL_STEPS,
        daily=compute_daily_stats(),
    )


# Initialise the analytics DB at import time so the table exists for the
# first request (and for tests, which import this module).
with app.app_context():
    init_analytics_db()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
