import os

from flask import Flask, render_template_string, request, redirect, url_for, session
from flask_session import Session

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


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

    .nhsuk-header {
        background: var(--nhsuk-blue);
        color: var(--nhsuk-white);
        padding: 16px 0;
        border-bottom: 4px solid var(--nhsuk-dark-blue);
    }
    .nhsuk-header__inner {
        max-width: 960px;
        margin: 0 auto;
        padding: 0 16px;
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
    }
    .nhsuk-header__logo {
        background: var(--nhsuk-white);
        color: var(--nhsuk-blue);
        font-weight: 700;
        padding: 6px 10px;
        font-size: 20px;
        letter-spacing: 0.5px;
    }
    .nhsuk-header__service {
        font-size: 18px;
        font-weight: 600;
    }

    .nhsuk-width-container {
        max-width: 720px;
        margin: 0 auto;
        padding: 24px 16px 48px;
    }
    @media (max-width: 480px) {
        h1.nhsuk-heading-xl { font-size: 26px; }
        h2.nhsuk-heading-l { font-size: 20px; }
        .nhsuk-header__service { font-size: 16px; }
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
    <style>{{ base_styles|safe }}</style>
</head>
<body>
    <header class="nhsuk-header" role="banner">
        <div class="nhsuk-header__inner">
            <span class="nhsuk-header__service">NEWS2 Reference Calculator</span>
        </div>
    </header>

    <main class="nhsuk-width-container" id="main-content">
        <div class="nhsuk-error-summary" role="alert" aria-labelledby="disclaimer-title">
            <h2 class="nhsuk-error-summary__title" id="disclaimer-title">Not an NHS service. Not a medical device.</h2>
            <p>This is an independent educational reference, not affiliated with, endorsed by,
            or connected to the NHS, the Royal College of Physicians, or any healthcare organisation.
            It is not a medical device, has not been validated for clinical use, and must not be used
            to inform patient care or clinical decision-making. Always use officially approved tools
            and clinical judgement when treating patients.</p>
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
                       type="number" min="0" max="60" inputmode="numeric"
                       value="{{ values.respiratoryRate or '' }}">
            </div>

            <div class="nhsuk-form-group {% if errors.oxygenSaturation %}nhsuk-form-group--error{% endif %}">
                <label class="nhsuk-label" for="oxygenSaturation">Oxygen saturation (SpO<sub>2</sub>, %)</label>
                <div class="nhsuk-hint">Whole number, 0 to 100.</div>
                {% if errors.oxygenSaturation %}<p class="nhsuk-error-message">{{ errors.oxygenSaturation }}</p>{% endif %}
                <input class="nhsuk-input nhsuk-input--width-5" id="oxygenSaturation" name="oxygenSaturation"
                       type="number" min="0" max="100" inputmode="numeric"
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
                       type="number" min="40" max="260" inputmode="numeric"
                       value="{{ values.systolicBP or '' }}">
            </div>

            <div class="nhsuk-form-group {% if errors.pulseRate %}nhsuk-form-group--error{% endif %}">
                <label class="nhsuk-label" for="pulseRate">Pulse rate (beats per minute)</label>
                <div class="nhsuk-hint">Whole number, 20 to 220.</div>
                {% if errors.pulseRate %}<p class="nhsuk-error-message">{{ errors.pulseRate }}</p>{% endif %}
                <input class="nhsuk-input nhsuk-input--width-5" id="pulseRate" name="pulseRate"
                       type="number" min="20" max="220" inputmode="numeric"
                       value="{{ values.pulseRate or '' }}">
            </div>

            <div class="nhsuk-form-group {% if errors.temperature %}nhsuk-form-group--error{% endif %}">
                <label class="nhsuk-label" for="temperature">Temperature (&deg;C)</label>
                <div class="nhsuk-hint">Decimal, 25.0 to 45.0.</div>
                {% if errors.temperature %}<p class="nhsuk-error-message">{{ errors.temperature }}</p>{% endif %}
                <input class="nhsuk-input nhsuk-input--width-5" id="temperature" name="temperature"
                       type="number" min="25" max="45" step="0.1" inputmode="decimal"
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

        <h2 class="nhsuk-heading-l">About this tool</h2>
        <p>NEWS2 is an aggregate score derived from six routine physiological measurements,
        described in the Royal College of Physicians' 2017 chart (linked above). This page
        implements the published algorithm as a reference and learning aid only. It is not a
        clinical tool and must not be used to inform care.</p>
        <p>If you find this useful as a reference, contributions toward hosting costs are welcome &mdash;
        <a href="https://checkout.revolut.com/pay/9a1c17c9-ce88-4fad-9ed9-174474c40582"
           rel="noopener noreferrer" target="_blank">contribute via Revolut</a>.</p>
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
    <header class="nhsuk-header" role="banner">
        <div class="nhsuk-header__inner">
            <span class="nhsuk-header__service">NEWS2 Reference Calculator</span>
        </div>
    </header>

    <main class="nhsuk-width-container" id="main-content">
        <div class="nhsuk-error-summary" role="alert" aria-labelledby="disclaimer-title">
            <h2 class="nhsuk-error-summary__title" id="disclaimer-title">Not an NHS service. Not a medical device.</h2>
            <p>This is an independent educational reference, not affiliated with, endorsed by,
            or connected to the NHS, the Royal College of Physicians, or any healthcare organisation.
            It is not a medical device, has not been validated for clinical use, and must not be used
            to inform patient care or clinical decision-making.</p>
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

        <a class="nhsuk-button" href="{{ url_for('home') }}">Calculate another score</a>
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


def parse_form(form):
    values = {}
    errors = {}
    for name, spec in FIELD_SPECS.items():
        raw = form.get(name, '').strip()
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

    values['supplementalOxygen'] = form.get('supplementalOxygen') == 'yes'
    values['hypercapnic'] = form.get('hypercapnic') == 'yes'
    consciousness = form.get('consciousness', 'alert')
    if consciousness not in {'alert', 'confusion', 'voice', 'pain', 'unresponsive'}:
        consciousness = 'alert'
    values['consciousness'] = consciousness
    return values, errors


@app.route('/')
def home():
    return render_template_string(
        HTML_FORM,
        base_styles=NHS_BASE_STYLES,
        errors={},
        values={'consciousness': 'alert'},
    )


@app.route('/calculate', methods=['POST'])
def calculate_news2():
    values, errors = parse_form(request.form)
    if errors:
        return render_template_string(
            HTML_FORM,
            base_styles=NHS_BASE_STYLES,
            errors=errors,
            values=values,
        ), 400

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

    session['result'] = {
        'score': total_score,
        'sorted_scores': sorted_scores,
        'has_level_3': has_level_3,
        **band,
    }
    return redirect(url_for('results'))


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
    if has_level_3 and total_score < 5:
        band = {
            'band_label': 'Low to medium risk (single parameter 3)',
            'band_color': '#ed8b00',
            'band_text_color': '#212b32',
            'response': 'Urgent review by a registered nurse to decide whether escalation is needed. A single parameter scoring 3 indicates a localised concern even when the total NEWS2 is low.',
            'monitoring_time': 'Minimum 1-hourly observations.',
        }
    return band


@app.route('/results')
def results():
    result = session.get('result')
    if not result:
        return redirect(url_for('home'))
    return render_template_string(
        HTML_RESULTS,
        base_styles=NHS_BASE_STYLES,
        **result,
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
