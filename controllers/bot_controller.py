import traceback
from flask import Blueprint, request
from services.whatsapp_service import (
    send_english_flow,
    send_malayalam_flow,
    send_whatsapp_message
)

bot_blueprint = Blueprint('bot', __name__)

user_sessions = {}

@bot_blueprint.route('/bot', methods=['POST'])
def whatsapp_reply():
    try:
        sender = request.form.get('From')
        body = request.form.get('Body', '').strip().lower()
        session = user_sessions.get(sender, {"step": 0, "lang": None})

        # Step 0 → Language selection
        if session["step"] == 0 and body in ['hi', 'hello']:
            send_whatsapp_message(sender, "🌐 Choose your language:\n1. English\n2. മലയാളം")
            session["step"] = "lang"

        # Language selection step
        elif session["step"] == "lang":
            if body == '1':
                session["lang"] = "en"
                session = send_english_flow(0, sender, body, session)
            elif body == '2':
                session["lang"] = "ml"
                session = send_malayalam_flow(0, sender, body, session)
            else:
                send_whatsapp_message(sender, "❌ Invalid choice. Please enter 1 or 2.")

        # English flow
        elif session.get("lang") == "en":
            session = send_english_flow(session["step"], sender, body, session)

        # Malayalam flow
        elif session.get("lang") == "ml":
            session = send_malayalam_flow(session["step"], sender, body, session)

        # Save session back
        user_sessions[sender] = session
        return "success"

    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        if sender:
            send_whatsapp_message(sender, "⚠️ Something went wrong. Please try again later.")
        return "error"
