import os
import logging

from flask import Flask, render_template, request, redirect, url_for
from flask_mail import Mail, Message
from dotenv import load_dotenv

# Load variables from .env file (local development only)
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')

# ========================
# SMTP Configuration
# ========================
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get(
    'MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME']
)

# Prefer TLS on port 587, fall back to SSL on port 465
mail_port = os.environ.get('MAIL_PORT')
if mail_port:
    app.config['MAIL_PORT'] = int(mail_port)
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
    app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'False') == 'True'
else:
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False

# Optional debugging for Render logs
app.config['MAIL_DEBUG'] = True

mail = Mail(app)

# ========================
# Survey Data
# ========================

# (keeping your QUESTIONS, LEVELS, RECOMMENDATIONS dictionaries unchanged)
# --- shortened for readability ---
QUESTIONS = {
    # ... your full QUESTIONS dict here ...
}

LEVELS = {
    "Minimal": {"en": "Minimal", "ar": "أساسي"},
    "Emerging": {"en": "Emerging", "ar": "ناشئ"},
    "Basic": {"en": "Basic", "ar": "مبتدئ"},
    "Intermediate": {"en": "Intermediate", "ar": "متوسط"},
    "Advanced": {"en": "Advanced", "ar": "متقدم"},
}

RECOMMENDATIONS = {
    # ... your full RECOMMENDATIONS dict here ...
}

# ========================
# Helper Function
# ========================
def calculate_maturity(answers_str):
    total_score = 0
    answers = {}
    if answers_str:
        try:
            answers = dict(item.split("=") for item in answers_str.split("&"))
        except ValueError:
            answers = {}

    level_scores_breakdown = {"Minimal": 0, "Emerging": 0, "Basic": 0, "Intermediate": 0, "Advanced": 0}

    for level, data in QUESTIONS.items():
        for i in range(len(data["questions"])):
            answer_key = f"q_{level}_{i}"
            user_answer = answers.get(answer_key)
            if user_answer:
                if user_answer.startswith('B'):
                    total_score += 1
                    level_scores_breakdown[level] += 1
                elif user_answer.startswith('C'):
                    total_score += 2
                    level_scores_breakdown[level] += 2

    if total_score <= 6:
        final_level = "Minimal"
    elif 7 <= total_score <= 12:
        final_level = "Emerging"
    elif 13 <= total_score <= 19:
        final_level = "Basic"
    elif 20 <= total_score <= 26:
        final_level = "Intermediate"
    else:
        final_level = "Advanced"

    return final_level, level_scores_breakdown

# ========================
# Routes
# ========================
@app.route('/')
def index():
    lang = request.args.get('lang', 'en')
    return render_template('index.html', lang=lang,
                           logo_url=url_for('static', filename='img/rasheed_logo.png'))

@app.route('/set_language/<lang>')
def set_language(lang):
    from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
    referrer = request.referrer
    if referrer and lang in ['en', 'ar']:
        url_parts = list(urlparse(referrer))
        query = dict(parse_qsl(url_parts[4]))
        query['lang'] = lang
        url_parts[4] = urlencode(query)
        return redirect(urlunparse(url_parts))
    return redirect(url_for('index', lang=lang))

@app.route('/survey/<level>', methods=['GET', 'POST'])
def survey(level):
    levels = list(QUESTIONS.keys())
    try:
        level_index = levels.index(level)
    except ValueError:
        return "Invalid survey level", 404

    lang = request.args.get('lang', 'en')
    previous_answers = request.args.get('answers', '')
    level_data = QUESTIONS[level]

    if request.method == 'POST':
        all_answers_dict = {}
        if request.form.get('previous_answers'):
            all_answers_dict = dict(item.split("=") for item in request.form.get('previous_answers').split("&"))

        for i in range(len(level_data["questions"])):
            answer_key = f"q_{level}_{i}"
            all_answers_dict[answer_key] = request.form.get(f"q_{level}_{i}")

        new_answers = "&".join([f"{key}={value}" for key, value in all_answers_dict.items() if value])

        if level_index + 1 < len(levels):
            next_level = levels[level_index + 1]
            return redirect(url_for('survey', level=next_level, answers=new_answers, lang=lang))
        else:
            return redirect(url_for('final', answers=new_answers, lang=lang))

    return render_template('survey.html',
                           level_data=level_data,
                           current_level=level,
                           level_index=level_index,
                           total_levels=len(levels),
                           logo_url=url_for('static', filename='img/rasheed_logo.png'),
                           lang=lang,
                           previous_answers=previous_answers,
                           levels=levels)

@app.route('/final', methods=['GET', 'POST'])
def final():
    lang = request.args.get('lang', 'en')
    answers_str = request.args.get('answers', '')

    final_level, level_scores = calculate_maturity(answers_str)

    if request.method == 'POST':
        user_email = request.form.get('email')
        app.logger.info(f"POST /final received email={user_email}")

        try:
            msg = Message(
                subject="Your Agentic AI Maturity Assessment Result",
                recipients=[user_email] if user_email else [],
                bcc=[os.environ.get('BCC_EMAIL')] if os.environ.get('BCC_EMAIL') else [],
                html=render_template('email_template.html',
                                     final_level_en=LEVELS[final_level]["en"],
                                     final_level_ar=LEVELS[final_level]["ar"],
                                     level_scores=level_scores,
                                     recommendation_en=RECOMMENDATIONS[final_level]["en"],
                                     recommendation_ar=RECOMMENDATIONS[final_level]["ar"],
                                     logo_url=url_for('static', filename='img/rasheed_logo.png'))
            )
            mail.send(msg)
            return render_template('thanks.html',
                                   message="Your results have been sent to your email. Thank you!",
                                   lang=lang)
        except Exception as e:
            app.logger.error(f"Error sending email: {e}")
            return f"An error occurred: {e}", 500

    return render_template('final.html',
                           logo_url=url_for('static', filename='img/rasheed_logo.png'),
                           lang=lang)

@app.route('/thanks')
def thanks():
    lang = request.args.get('lang', 'en')
    return render_template('thanks.html', message="Your results have been sent to your email. Thank you!",
                           lang=lang)

if __name__ == '__main__':
    app.run(debug=True)
