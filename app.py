from flask import Flask, render_template_string, request, redirect, url_for, session
from flask_session import Session

app = Flask(__name__)
app.config["SECRET_KEY"] = "verysecretkey"  # Change this to a real secret key in production
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# HTML Form Template for Data Input
html_form = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NEWS2 Score Calculation Form</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    <style>
        body {
            font-family: Arial, sans-serif;
        }
        .form-container {
            width: 50%;
            margin: auto;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        .form-group input[type="text"],
        .form-group select {
            width: calc(100% - 24px);
            padding: 8px;
            margin-right: 24px;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
        .form-group input[type="checkbox"] {
            margin-right: 5px;
        }
        .form-group .checkbox-label {
            display: flex;
            align-items: center;
        }
        .form-group .info-icon {
            margin-left: 5px;
            color: #007bff;
            cursor: pointer;
        }
        .form-group .info-icon:hover {
            color: #0056b3;
        }
        .submit-btn {
            padding: 10px 20px;
            background-color: #28a745;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .submit-btn:hover {
            background-color: #218838;
        }
        .donation-message {
            margin-top: 20px;
            text-align: center;
            font-size: 14px;
            color: #555;
        }
        .donation-message a {
            color: #007bff;
            text-decoration: none;
        }
        .donation-message a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>

<div class="form-container">
    <h2>NEWS2 Score Calculation Form</h2>
    <form>
        <div class="form-group">
            <label for="rr">Respiratory Rate (RR):</label>
            <input type="text" id="rr" name="rr">
            <i class="fas fa-info-circle info-icon" title="Normal range: 12-20 breaths per minute"></i>
        </div>
        <div class="form-group checkbox-label">
            <input type="checkbox" id="hypercapnic_rf" name="hypercapnic_rf">
            <label for="hypercapnic_rf">Hypercapnic Respiratory Failure (check if yes)</label>
        </div>
        <div class="form-group">
            <label for="spo2">Oxygen Saturation (SpO2):</label>
            <input type="text" id="spo2" name="spo2">
            <i class="fas fa-info-circle info-icon" title="Normal range: 95-100%"></i>
        </div>
        <div class="form-group checkbox-label">
            <input type="checkbox" id="supplemental_oxygen" name="supplemental_oxygen">
            <label for="supplemental_oxygen">On supplemental oxygen (check if yes)</label>
        </div>
        <div class="form-group">
            <label for="bp">Systolic Blood Pressure (BP):</label>
            <input type="text" id="bp" name="bp">
            <i class="fas fa-info-circle info-icon" title="Normal range: 90-120 mmHg"></i>
        </div>
        <div class="form-group">
            <label for="pr">Pulse Rate (PR):</label>
            <input type="text" id="pr" name="pr">
            <i class="fas fa-info-circle info-icon" title="Normal range: 60-100 bpm"></i>
        </div>
        <div class="form-group">
            <label for="temperature">Temperature (°C):</label>
            <input type="text" id="temperature" name="temperature">
            <i class="fas fa-info-circle info-icon" title="Normal range: 36.1-37.2°C"></i>
        </div>
        <div class="form-group">
            <label for="consciousness">Level of Consciousness:</label>
            <select id="consciousness" name="consciousness">
                <option value="alert">Alert</option>
                <option value="voice">Voice</option>
                <option value="pain">Pain</option>
                <option value="unresponsive">Unresponsive</option>
            </select>
        </div>
        <button type="submit" class="submit-btn">Submit Form</button>
    </form>
    <div class="donation-message">
        Like what you see? I do this for free so all donations are welcome - <a href="https://checkout.revolut.com/pay/9a1c17c9-ce88-4fad-9ed9-174474c40582" target="_blank">Donate here</a>
    </div>
</div>

</body>
</html>

'''


@app.route('/')
def home():
    return render_template_string(html_form)


def score_respiratory_rate(rr):
    if rr < 9:
        return 3
    elif 9 <= rr <= 11:
        return 1
    elif 12 <= rr <= 20:
        return 0
    elif 21 <= rr <= 24:
        return 2
    elif rr > 24:
        return 3
    return 0


def score_oxygen_saturations(spO2, oxygen, hypercapnic):
    if hypercapnic:
        if spO2 >= 94:
            return 3
        elif 92 <= spO2 <= 93:
            return 2
        elif 88 <= spO2 <= 91:
            return 0
        elif 85 <= spO2 <= 87:
            return 2
        else:
            return 3
    else:
        if spO2 < 91:
            return 3
        elif 91 <= spO2 <= 93:
            return 2
        elif 94 <= spO2 <= 100 and not oxygen:
            return 0
        return 0


def score_systolic_bp(bp):
    if bp < 91:
        return 3
    elif 91 <= bp <= 100:
        return 2
    elif 101 <= bp <= 110:
        return 1
    elif 111 <= bp <= 219:
        return 0
    elif bp >= 220:
        return 3
    return 0


def score_pulse_rate(pr):
    if pr < 41:
        return 3
    elif 41 <= pr <= 50:
        return 1
    elif 51 <= pr <= 90:
        return 0
    elif 91 <= pr <= 110:
        return 1
    elif 111 <= pr <= 130:
        return 2
    elif pr > 130:
        return 3
    return 0


def score_temperature(temp):
    if temp < 35.0:
        return 3
    elif 35.1 <= temp <= 36.0:
        return 1
    elif 36.1 <= temp <= 38.0:
        return 0
    elif 38.1 <= temp <= 39.0:
        return 1
    elif temp > 39.0:
        return 2
    return 0


def score_consciousness(level):
    if level == 'alert':
        return 0
    return 3


@app.route('/calculate', methods=['POST'])
def calculate_news2():
    data = request.form
    respiratory_rate = int(data.get('respiratoryRate', 0))
    oxygen_saturation = int(data.get('oxygenSaturation', 0))
    supplemental_oxygen = 'supplementalOxygen' in data
    hypercapnic = 'hypercapnic' in data  # Capture hypercapnic status
    systolic_bp = int(data.get('systolicBP', 0))
    pulse_rate = int(data.get('pulseRate', 0))
    temperature = float(data.get('temperature', 0))
    consciousness = data.get('consciousness', 'alert')

    scores = {
        'Respiratory Rate': score_respiratory_rate(respiratory_rate),
        'Oxygen Saturation': score_oxygen_saturations(oxygen_saturation, supplemental_oxygen, hypercapnic),
        'Systolic Blood Pressure': score_systolic_bp(systolic_bp),
        'Pulse Rate': score_pulse_rate(pulse_rate),
        'Temperature': score_temperature(temperature),
        'Consciousness Level': score_consciousness(consciousness)
    }

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    total_score = sum(scores.values())

    response, monitoring_time, border_color = determine_response(total_score, scores)

    session['score'] = total_score
    session['sorted_scores'] = sorted_scores
    session['response'] = response
    session['monitoring_time'] = monitoring_time
    session['border_color'] = border_color

    return redirect(url_for('results'))


def determine_response(total_score, scores):
    """
    Determine the clinical response and monitoring time based on the NEWS2 score.
    """
    has_level_3 = any(score == 3 for score in scores.values())

    if total_score == 0:
        response = "Continue routine NEWS monitoring."
        monitoring_time = "Monitor at least every 12 hours."
        border_color = "#FFFFFF"  # White
    elif 1 <= total_score <= 4:
        response = "Inform a registered nurse for assessment. Increase monitoring frequency to every 4-6 hours or escalate care based on assessment."
        monitoring_time = "Monitor at least every 4-6 hours."
        border_color = "#FFFF00"  # Yellow
    elif total_score >= 5 and total_score < 7:
        response = "Urgent response needed. Inform medical team immediately for urgent assessment within 60 minutes. Monitor at least every hour. Consider moving the patient to an environment with monitoring facilities."
        monitoring_time = "Monitor at least every hour."
        border_color = "#FFA500"  # Orange
    elif total_score >= 7:
        response = "Emergency response threshold. Inform medical team immediately; continuous monitoring and emergency assessment required. Assess within 30 minutes, monitor every 30 minutes initially, senior clinician review expected within 60 minutes if no improvement. Consider transfer to a higher-dependency unit or ICU."
        monitoring_time = "Monitor continuously; assess every 30 minutes initially."
        border_color = "#FF0000"  # Red

    if has_level_3:
        response += " Note: At least one parameter has scored a value of 3."
        monitoring_time = "Monitor at least every hour."
        if total_score >= 7:
            monitoring_time = "Monitor continuously; assess every 30 minutes initially."

    print(border_color)
    return response, monitoring_time, border_color


@app.route('/results')
def results():
    score = session.get('score', 0)
    sorted_scores = session.get('sorted_scores', [])
    response = session.get('response', '')
    monitoring_time = session.get('monitoring_time', '')
    border_color = session.get('border_color', '')
    print(border_color)

    html_results = '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>NEWS2 Score Results</title>
            <style>
                body { font-family: Arial, sans-serif; background: #f4f4f9; }
                .container { width: 80%; max-width: 600px; margin: 20px auto; background: #fff; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
                h1 { color: #333; }
                .info { margin-top: 20px; padding: 10px; background-color: #e9ecef; border-left: 5px solid {{ session['border_color'] }};; }
                ul { list-style-type: none; padding: 0; }
                li { padding: 8px; border-bottom: 1px solid #ddd; }
                li:last-child { border-bottom: none; }
                .button { display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border: none; cursor: pointer; }
                .button:hover { background-color: #45a049; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>NEWS2 Score Results</h1>
                <div class="info"><strong>Score:</strong> {{ score }}</div>
                <div class="info"><strong>Monitoring Time:</strong> {{ monitoring_time }}</div>
                <div class="info"><strong>Response:</strong> {{ response }}</div>
                <div class="info">
                    <strong>Scores:</strong>
                    <ul>
                    {% for param, score in sorted_scores %}
                        <li>{{ param }}: {{ score }}</li>
                    {% endfor %}
                    </ul>
                </div>
                <a href="/" class="button">Calculate Again</a>
            </div>
        </body>
        </html>
    '''

    return render_template_string(html_results, score=score, monitoring_time=monitoring_time, response=response, sorted_scores=sorted_scores)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
