import os
from flask import Flask, render_template, request, redirect, url_for
from flask_mail import Mail, Message
from dotenv import load_dotenv

#  Load variables from .env file (local development only)
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')

# SMTP Configuration: Now reading securely from environment variables
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 465))
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')
mail = Mail(app)

# The survey questions and choices
QUESTIONS = {
    "Minimal": {
        "level_en": "Minimal",
        "level_ar": "أساسي",
        "questions": [
            {"q": "What is the primary function of your AI-driven customer-facing tool?",
             "q_ar": "ما هي الوظيفة الأساسية لأداة الذكاء الاصطناعي التي تستخدمها للتواصل مع العملاء؟",
             "options": ["A. It provides pre-programmed answers to a limited set of FAQs.",
                         "B. It handles basic queries and can escalate to a human agent.",
                         "C. It can understand and respond to natural language queries."],
             "options_ar": ["أ. تقدم إجابات مبرمجة مسبقًا لمجموعة محدودة من الأسئلة الشائعة.",
                            "ب. تتعامل مع الاستفسارات الأساسية ويمكنها تصعيدها إلى وكيل بشري.",
                            "ج. يمكنها فهم لغة البشر الطبيعية والاستجابة لها."]},
            {"q": "How is your AI tool's knowledge base updated?",
             "q_ar": "كيف يتم تحديث قاعدة بيانات أداة الذكاء الاصطناعي لديك؟",
             "options": ["A. Manually by a human team adding new rules and responses.",
                         "B. It uses a simple keyword or phrase-matching system.",
                         "C. It is integrated with a broader knowledge base or LLM."],
             "options_ar": ["أ. يتم يدويا عبر فريق بشري يضيف قواعد واستجابات جديدة.",
                            "ب. تستخدم نظاما بسيطا لمطابقة الكلمات المفتاحية أو العبارات.",
                            "ج. يتم دمجها مع قاعدة بيانات أوسع أو نماذج لغوية كبيرة."]},
            {"q": "How does your AI tool handle user input that it doesn't recognize?",
             "q_ar": "كيف تتعامل أداة الذكاء الاصطناعي مع إدخال المستخدم الذي لا تتعرف عليه؟",
             "options": ["A. It provides a generic, canned response like 'I don't understand.'",
                         "B. It searches for the closest keyword match and provides a pre-defined answer.",
                         "C. It can interpret the intent and redirect the user to a relevant topic."],
             "options_ar": ["أ. تقدم استجابة عامة ومحفوظة مثل 'لا أفهم'.",
                            "ب. تبحث عن أقرب تطابق للكلمات المفتاحية وتقدم إجابة محددة مسبقا.",
                            "ج. يمكنها تفسير القصد وإعادة توجيه المستخدم إلى موضوع ذي صلة."]}
        ]
    },
    "Emerging": {
        "level_en": "Emerging",
        "level_ar": "ناشئ",
        "questions": [
            {"q": "What is the AI assistant's ability to maintain context within a conversation?",
             "q_ar": "ما هي قدرة مساعد الذكاء الاصطناعي على الحفاظ على السياق داخل المحادثة؟",
             "options": ["A. It treats each message as a new query without remembering past interactions.",
                         "B. It can remember a few key details from the current conversation.",
                         "C. It retains context across a single conversation session."],
             "options_ar": ["أ. تتعامل مع كل رسالة كاستفسار جديد دون تذكر التفاعلات السابقة.",
                            "ب. يمكنها تذكر بعض التفاصيل الرئيسية من المحادثة الحالية.",
                            "ج. تحتفظ بالسياق عبر جلسة محادثة واحدة."]},
            {"q": "How does the AI assistant respond to questions it hasn't been trained on?",
             "q_ar": "كيف يستجيب مساعد الذكاء الاصطناعي للأسئلة التي لم يتم تدريبه عليها؟",
             "options": ["A. It fails or provides an irrelevant, non-contextual response.",
                         "B. It escalates the conversation to a human without attempting to answer.",
                         "C. It can provide a helpful, but potentially unspecific, response using generative AI."],
             "options_ar": ["أ. تفشل أو تقدم استجابة غير ذات صلة وخارج السياق.",
                            "ب. تصعّد المحادثة إلى إنسان دون محاولة الإجابة.",
                            "ج. يمكنها تقديم استجابة مفيدة، ولكنها قد تكون غير محددة، باستخدام الذكاء الاصطناعي التوليدي."]},
            {"q": "Does the AI assistant have a distinct personality or tone?",
             "q_ar": "هل لدى مساعد الذكاء الاصطناعي شخصية أو نبرة مميزة؟",
             "options": ["A. No, responses are generic and robotic.",
                         "B. Yes, it has been programmed with a consistent brand voice.",
                         "C. Yes, it can adjust its tone based on the user's sentiment."],
             "options_ar": ["أ. لا، الإجابات عامة وآلية.", "ب. نعم، لقد تمت برمجتها بنبرة متناسقة مع العلامة التجارية.",
                            "ج. نعم، يمكنها تعديل نبرتها بناءً على مشاعر المستخدم."]}
        ]
    },
    "Basic": {
        "level_en": "Basic",
        "level_ar": "مبتدئ",
        "questions": [
            {"q": "Can your AI agent integrate with other systems (e.g., CRM, calendar)?",
             "q_ar": "هل يمكن لوكيل الذكاء الاصطناعي الخاص بك أن يتكامل مع أنظمة أخرى (مثل CRM أو التقويم)؟",
             "options": ["A. No, it's a standalone system.",
                         "B. Yes, through pre-programmed APIs for a limited set of functions.",
                         "C. Yes, it can use a variety of tools to complete tasks."],
             "options_ar": ["أ. لا، إنه نظام مستقل.",
                            "ب. نعم، من خلال واجهات برمجة تطبيقات مبرمجة مسبقًا لمجموعة محدودة من الوظائف.",
                            "ج. نعم، يمكنه استخدام مجموعة متنوعة من الأدوات لإنجاز المهام."]},
            {"q": "How does your AI agent handle user-requested actions (e.g., 'book a meeting')?",
             "q_ar": "كيف يتعامل وكيل الذكاء الاصطناعي مع الإجراءات التي يطلبها المستخدم (مثل 'حجز اجتماع')؟",
             "options": ["A. It can't perform actions; it only provides information.",
                         "B. It can perform simple actions after explicit user confirmation.",
                         "C. It can perform multi-step actions based on user intent."],
             "options_ar": ["أ. لا يمكنه أداء الإجراءات؛ إنه يوفر المعلومات فقط.",
                            "ب. يمكنه أداء إجراءات بسيطة بعد تأكيد صريح من المستخدم.",
                            "ج. يمكنه أداء إجراءات متعددة الخطوات بناءً على نية المستخدم."]},
            {"q": "What is the AI agent's ability to 'reason' and follow instructions?",
             "q_ar": "ما هي قدرة وكيل الذكاء الاصطناعي على 'التفكير' واتباع التعليمات؟",
             "options": ["A. It follows a rigid, linear script.",
                         "B. It can handle a basic set of 'if-then' logic scenarios.",
                         "C. It uses a chain of thought to break down and execute complex tasks."],
             "options_ar": ["أ. يتبع نصًا صارمًا وخطيًا.",
                            "ب. يمكنه التعامل مع مجموعة أساسية من سيناريوهات المنطق 'إذا-ثم'.",
                            "ج. يستخدم سلسلة من الأفكار لتقسيم المهام المعقدة وتنفيذها."]}
        ]
    },
    "Intermediate": {
        "level_en": "Intermediate",
        "level_ar": "متوسط",
        "questions": [
            {"q": "How does the AI agent handle errors or failures during a task?",
             "q_ar": "كيف يتعامل وكيل الذكاء الاصطناعي مع الأخطاء أو الفشل أثناء مهمة ما؟",
             "options": ["A. It fails and stops the process, requiring a human to intervene.",
                         "B. It tries a single, pre-defined fallback option.",
                         "C. It can identify the cause of the failure and attempt an alternative solution."],
             "options_ar": ["أ. يفشل ويوقف العملية، مما يتطلب تدخلًا بشريًا.",
                            "ب. يحاول خيارًا احتياطيًا واحدًا محددًا مسبقًا.",
                            "ج. يمكنه تحديد سبب الفشل ومحاولة إيجاد حل بديل."]},
            {"q": "How is the AI agent's performance evaluated?", "q_ar": "كيف يتم تقييم أداء وكيل الذكاء الاصطناعي؟",
             "options": ["A. Manually, through limited human review of conversation logs.",
                         "B. Using basic metrics like user satisfaction scores.",
                         "C. Through a continuous feedback loop where performance metrics are monitored and used to refine the agent's behavior."],
             "options_ar": ["أ. يدويًا، من خلال مراجعة بشرية محدودة لسجلات المحادثات.",
                            "ب. باستخدام مقاييس أساسية مثل درجات رضا المستخدم.",
                            "ج. من خلال حلقة تغذية راجعة مستمرة حيث يتم مراقبة مقاييس الأداء واستخدامها لتحسين سلوك الوكيل."]},
            {"q": "Can the AI agent manage its own goals?",
             "q_ar": "هل يمكن لوكيل الذكاء الاصطناعي أن يدير أهدافه الخاصة؟",
             "options": ["A. No, it only executes tasks given by a human.",
                         "B. It can be assigned a simple, singular goal.",
                         "C. It can manage a multi-step project with a clear end goal."],
             "options_ar": ["أ. لا، إنه ينفذ المهام الموكلة إليه من قبل إنسان فقط.", "ب. يمكن تعيين هدف بسيط وفردي له.",
                            "ج. يمكنه إدارة مشروع متعدد الخطوات بهدف نهائي واضح."]}
        ]
    },
    "Advanced": {
        "level_en": "Advanced",
        "level_ar": "متقدم",
        "questions": [
            {"q": "How much human supervision does the AI agent need?",
             "q_ar": "ما مقدار الإشراف البشري الذي يحتاجه وكيل الذكاء الاصطناعي؟",
             "options": ["A. It requires constant human oversight and approval for all actions.",
                         "B. It operates with limited supervision on simple, low-risk tasks.",
                         "C. It can act as a fully autonomous workforce, initiating and completing tasks without human intervention."],
             "options_ar": ["أ. يتطلب إشرافًا بشريًا مستمرًا وموافقة على جميع الإجراءات.",
                            "ب. يعمل بإشراف محدود على المهام البسيطة ومنخفضة المخاطر.",
                            "ج. يمكنه العمل كقوة عاملة مستقلة تمامًا، بدء وإكمال المهام دون تدخل بشري."]},
            {"q": "How does the AI agent handle ethical and safety considerations?",
             "q_ar": "كيف يتعامل وكيل الذكاء الاصطناعي مع الاعتبارات الأخلاقية والسلامة؟",
             "options": ["A. It has no built-in safety or ethical guidelines.",
                         "B. It has a basic set of rules to avoid harmful content.",
                         "C. It can reason about ethical dilemmas and make decisions that align with a pre-defined set of values."],
             "options_ar": ["أ. ليس لديه إرشادات أمان أو أخلاقية مدمجة.",
                            "ب. لديه مجموعة أساسية من القواعد لتجنب المحتوى الضار.",
                            "ج. يمكنه التفكير في المعضلات الأخلاقية واتخاذ قرارات تتماشى مع مجموعة محددة مسبقًا من القيم."]},
            {"q": "What is the AI agent's capability for collaboration?",
             "q_ar": "ما هي قدرة وكيل الذكاء الاصطناعي على التعاون؟",
             "options": ["A. It works in isolation and cannot interact with other agents or systems.",
                         "B. It can exchange basic information with other agents in a predefined manner.",
                         "C. It can orchestrate a 'swarm' of other agents to achieve a complex, overarching objective."],
             "options_ar": ["أ. يعمل بمعزل عن الآخرين ولا يمكنه التفاعل مع الوكلاء أو الأنظمة الأخرى.",
                            "ب. يمكنه تبادل المعلومات الأساسية مع وكلاء آخرين بطريقة محددة مسبقًا.",
                            "ج. يمكنه تنسيق 'سرب' من الوكلاء الآخرين لتحقيق هدف معقد وشامل."]},
            {"q": "How does the agent's work scale within the organization?",
             "q_ar": "كيف يتوسع عمل الوكيل داخل المنظمة؟",
             "options": ["A. It only performs a single, specific function.",
                         "B. It can be deployed in multiple departments for a limited set of tasks.",
                         "C. It is a core part of the organization's operational infrastructure, deployed at scale."],
             "options_ar": ["أ. إنه يؤدي وظيفة واحدة ومحددة فقط.",
                            "ب. يمكن نشره في أقسام متعددة لمجموعة محدودة من المهام.",
                            "ج. إنه جزء أساسي من البنية التحتية التشغيلية للمنظمة، ويتم نشره على نطاق واسع."]},
            {"q": "How does the agent handle unpredictable or novel situations?",
             "q_ar": "كيف يتعامل الوكيل مع المواقف غير المتوقعة أو المستجدة؟",
             "options": ["A. It fails or provides a generic response.",
                         "B. It follows a limited set of pre-programmed rules for unexpected events.",
                         "C. It can dynamically create a new plan and course of action to address the situation without human intervention."],
             "options_ar": ["أ. يفشل أو يقدم استجابة عامة.",
                            "ب. يتبع مجموعة محدودة من القواعد المبرمجة مسبقًا للأحداث غير المتوقعة.",
                            "ج. يمكنه إنشاء خطة جديدة ومسار عمل ديناميكي لمعالجة الموقف دون تدخل بشري."]},
            {"q": "How does the agent's decision-making process work?",
             "q_ar": "كيف تعمل عملية اتخاذ القرار لدى الوكيل؟",
             "options": ["A. It's a simple, rule-based process.", "B. It uses a single decision-making model.",
                         "C. It has a meta-cognition layer, allowing it to reflect on its own thought process and improve how it makes decisions."],
             "options_ar": ["أ. إنها عملية بسيطة قائمة على القواعد.", "ب. يستخدم نموذجًا واحدًا لاتخاذ القرار.",
                            "ج. لديه طبقة من الإدراك الذاتي، مما يسمح له بالتفكير في عملية تفكيره وتحسين طريقة اتخاذ القرارات."]}
        ]
    }
}

# English and Arabic translations for the results
LEVELS = {
    "Minimal": {"en": "Minimal", "ar": "أساسي"},
    "Emerging": {"en": "Emerging", "ar": "ناشئ"},
    "Basic": {"en": "Basic", "ar": "مبتدئ"},
    "Intermediate": {"en": "Intermediate", "ar": "متوسط"},
    "Advanced": {"en": "Advanced", "ar": "متقدم"},
}

RECOMMENDATIONS = {
    "Minimal": {
        "en": "Your organization is at the foundational stage of AI agent adoption. To advance, focus on expanding your AI assistant's capabilities beyond simple Q&A and integrating it with more business functions.",
        "ar": "منظمتك في المرحلة التأسيسية لاعتماد وكلاء الذكاء الاصطناعي. للتقدم، ركز على توسيع قدرات مساعد الذكاء الاصطناعي الخاص بك لتتجاوز الأسئلة والأجوبة البسيطة ودمجها مع المزيد من وظائف الأعمال."
    },
    "Emerging": {
        "en": "Your organization is effectively using conversational AI. The next step is to transition from an assistant to a true agent by leveraging Large Language Models to perform multi-step tasks.",
        "ar": "تستخدم منظمتك الذكاء الاصطناعي للمحادثة بفعالية. الخطوة التالية هي الانتقال من المساعد إلى الوكيل الحقيقي من خلال الاستفادة من نماذج اللغة الكبيرة لأداء مهام متعددة الخطوات."
    },
    "Basic": {
        "en": "You are on the right path with an LLM-based agent. To reach the next level, you need to build in learning loops and error-handling capabilities so your agents can adapt and improve over time.",
        "ar": "أنت على الطريق الصحيح مع وكيل قائم على LLM. للوصول إلى المستوى التالي، تحتاج إلى بناء حلقات تعلم وقدرات على التعامل مع الأخطاء حتى يتمكن وكلاؤك من التكيف والتحسن بمرور الوقت."
    },
    "Intermediate": {
        "en": "Your agents are already learning and adapting. To achieve autonomy, focus on a framework for your agents to operate with minimal human supervision and handle complex, unpredictable situations on their own.",
        "ar": "وكلاؤك يتعلمون ويتكيفون بالفعل. لتحقيق الاستقلالية، ركز على إطار عمل لوكلائك للعمل بأقل قدر من الإشراف البشري والتعامل مع المواقف المعقدة وغير المتوقعة بمفردهم."
    },
    "Advanced": {
        "en": "Congratulations! Your organization is a leader in AI agent maturity. Your focus should be on scaling your autonomous agents to new domains and exploring how they can orchestrate and manage entire business processes.",
        "ar": "تهانينا! منظمتك هي رائدة في نضج وكيل الذكاء الاصطناعي. يجب أن يكون تركيزك على توسيع نطاق وكلاء الذكاء الاصطناعي المستقلين إلى مجالات جديدة واستكشاف كيف يمكنهم تنظيم وإدارة عمليات الأعمال بأكملها."
    }
}


def calculate_maturity(answers_str):
    total_score = 0
    answers = {}
    if answers_str:
        try:
            answers = dict(item.split("=") for item in answers_str.split("&"))
        except ValueError:
            # This handles cases where the string might be malformed
            answers = {}

    # Recalculate scores per level specifically for the email report
    level_scores_breakdown = {"Minimal": 0, "Emerging": 0, "Basic": 0, "Intermediate": 0, "Advanced": 0}

    # Sum points for each question and each level
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

    # Map the total score to a final level
    if total_score <= 6:
        final_level = "Minimal"
    elif 7 <= total_score <= 12:
        final_level = "Emerging"
    elif 13 <= total_score <= 19:
        final_level = "Basic"
    elif 20 <= total_score <= 26:
        final_level = "Intermediate"
    else:  # total_score > 26
        final_level = "Advanced"

    return final_level, level_scores_breakdown


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
        # Get answers from the submitted form and previous answers from the hidden field
        all_answers_dict = {}
        if request.form.get('previous_answers'):
            all_answers_dict = dict(item.split("=") for item in request.form.get('previous_answers').split("&"))

        # Add current answers to the dictionary with unique keys
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

        # This determines the final level and recommendations based on the user's answers.
        final_level_en = LEVELS[final_level]["en"]
        final_level_ar = LEVELS[final_level]["ar"]
        recommendation_en = RECOMMENDATIONS[final_level]["en"]
        recommendation_ar = RECOMMENDATIONS[final_level]["ar"]

        try:
            # THIS IS THE SOLID SOLUTION: Explicitly connect to the SMTP server.
            # The 'with' block ensures the connection is managed properly.
            with mail.connect() as conn:
                msg = Message(
                    subject="Your Agentic AI Maturity Assessment Result",
                    recipients=[user_email],
                    bcc=[os.environ.get('BCC_EMAIL')],
                    html=render_template('email_template.html',
                                         final_level_en=final_level_en,
                                         final_level_ar=final_level_ar,
                                         level_scores=level_scores,
                                         recommendation_en=recommendation_en,
                                         recommendation_ar=recommendation_ar,
                                         logo_url=url_for('static', filename='img/rasheed_logo.png'))
                )
                conn.send(msg)  # Use the connection object to send the message.

            return render_template('thanks.html', message="Your results have been sent to your email. Thank you!",
                                   lang=lang)

        except Exception as e:
            # This handles any remaining issues with the email sending process, like incorrect credentials.
            return f"An error occurred: {e}", 500

    # This handles the GET request, displaying the user's results before email submission.
    return render_template('final.html',
                           logo_url=url_for('static', filename='img/rasheed_logo.png'),
                           lang=lang,
                           final_level=final_level,
                           level_scores=level_scores,
                           recommendations=RECOMMENDATIONS,
                           levels=LEVELS,
                           answers_str=answers_str)

@app.route('/thanks')
def thanks():
    lang = request.args.get('lang', 'en')
    return render_template('thanks.html', message="Your results have been sent to your email. Thank you!",
                           lang=lang)


if __name__ == '__main__':
    app.run(debug=True)
