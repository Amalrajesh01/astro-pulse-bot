from flask import Flask, request, send_from_directory
import requests
from twilio.rest import Client
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.units import inch
import os
import time
import threading

app = Flask(__name__)

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_NUMBER")

client = Client(account_sid, auth_token)
user_sessions = {}

# Prediction categories
CATEGORIES = [
    'health', 'physique', 'relationship', 'career', 'travel',
    'family', 'friends', 'finances', 'status'
]

# Create PDF with dynamic text
def create_thank_you_pdf(text, category, year):
    folder = 'static'
    if not os.path.exists(folder):
        os.makedirs(folder)
    file_path = os.path.join(folder, 'your_personalised_report.pdf')

    doc = SimpleDocTemplate(file_path, pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    story = []

    header = Paragraph("<b>🌟 Astro Pulse: Thank You!</b>", styles['Title'])
    subheader = Paragraph(f"<b>Your {category.capitalize()} Prediction for {year}:</b>", styles['Heading2'])
    body = Paragraph(text.replace("\n", "<br/>"), styles['BodyText'])

    story.append(header)
    story.append(subheader)
    story.append(body)

    doc.build(story)

# Send WhatsApp text message
def send_whatsapp_message(to, body):
    client.messages.create(
        from_=twilio_number,
        body=body,
        to=to
    )

# Send WhatsApp media (PDF)
def send_whatsapp_media(to, body, media_url):
    client.messages.create(
        from_=twilio_number,
        body=body,
        media_url=[media_url],
        to=to
    )

# Delayed message function
def send_delayed_message(to, delay_seconds=30):
    time.sleep(delay_seconds)
    send_whatsapp_message(
        to,
        "🌟 Your chat has ended. Send 'hi' or 'hello' to restart the conversation."
    )

# Determine current phase based on month
def get_current_phase():
    current_month = datetime.now().month
    if 1 <= current_month <= 3:
        return 'phase_1'
    elif 4 <= current_month <= 6:
        return 'phase_2'
    elif 7 <= current_month <= 9:
        return 'phase_3'
    else:
        return 'phase_4'

@app.route('/bot', methods=['POST'])
def whatsapp_reply():
    try:
        sender = request.form.get('From')
        body = request.form.get('Body', '').lower().strip()
        session = user_sessions.get(sender, {"step": 0})

        # Step 0: Welcome message and prediction menu
        if body in ['hi', 'hello'] and session["step"] == 0:
            welcome_message = (
                "🌟 Welcome to Astro Pulse! 🌟\n\n"
                "Unlock the secrets of the stars with our cosmic insights!\n"
                "What would you like to know?\n"
                "1. Yearly Horoscope\n"
                "2. Weekly Horoscope (Coming Soon!)\n\n"
                "Enter the number of your choice:"
            )
            send_whatsapp_message(sender, welcome_message)
            session["step"] = 1

        # Step 1: Handle prediction type selection
        elif session["step"] == 1:
            if body == '1':
                zodiac_list = (
                    "Choose your Zodiac sign number:\n"
                    "1: Aries\n2: Taurus\n3: Gemini\n4: Cancer\n"
                    "5: Leo\n6: Virgo\n7: Libra\n8: Scorpio\n"
                    "9: Sagittarius\n10: Capricorn\n11: Aquarius\n12: Pisces\n\n"
                    "Enter the number:"
                )
                send_whatsapp_message(sender, zodiac_list)
                session["step"] = 2
            elif body == '2':
                send_whatsapp_message(sender, "❌ Weekly Horoscope is coming soon! Please choose 1 for Yearly Horoscope.")
            else:
                send_whatsapp_message(sender, "❌ Invalid choice. Please enter 1 for Yearly Horoscope or 2 for Weekly (Coming Soon).")

        # Step 2: Handle Zodiac selection
        elif session["step"] == 2:
            if body.isdigit() and 1 <= int(body) <= 12:
                session["zodiac"] = body
                session["step"] = 3
                send_whatsapp_message(sender, "✅ Got it! Now enter the year (e.g., 2025):")
            else:
                send_whatsapp_message(sender, "❌ Invalid choice. Please enter a number between 1 and 12.")

        # Step 3: Handle year input
        elif session["step"] == 3:
            if body.isdigit():
                session["year"] = body
                category_list = (
                    "Choose the category for your prediction:\n"
                    "1. Health\n2. Physique\n3. Relationship\n4. Career\n"
                    "5. Travel\n6. Family\n7. Friends\n8. Finances\n9. Status\n\n"
                    "Enter the number:"
                )
                send_whatsapp_message(sender, category_list)
                session["step"] = 4
            else:
                send_whatsapp_message(sender, "❌ Please enter a valid year.")

        # Step 4: Handle category selection and generate prediction
        elif session["step"] == 4:
            if body.isdigit() and 1 <= int(body) <= 9:
                category_index = int(body) - 1
                selected_category = CATEGORIES[category_index]
                zodiac = session['zodiac']
                year = session['year']
                url = f"https://api.vedicastroapi.com/v3-json/prediction/yearly?year={year}&zodiac={zodiac}&api_key=7fc2e77b-b33b-51e1-9abb-1cf20de8dc04&lang=en"
                api_response = requests.get(url).json()
                current_phase = get_current_phase()
                prediction = api_response['response'][current_phase][selected_category]['prediction']

                # Create and send PDF
                create_thank_you_pdf(prediction, selected_category, year)
                pdf_url = "https://8b535fdf336d.ngrok-free.app/static/your_personalised_report.pdf"
                send_whatsapp_media(
                    sender,
                    f"✅ Your {selected_category.capitalize()} Prediction for {year} is ready. Please download the PDF below.",
                    pdf_url
                )

                # Start a thread for the delayed message
                threading.Thread(target=send_delayed_message, args=(sender, 30)).start()

                session["step"] = 0
            else:
                send_whatsapp_message(sender, "❌ Invalid choice. Please enter a number between 1 and 9.")

        user_sessions[sender] = session
        return "success"

    except requests.RequestException as e:
        print(f"API Error: {e}")
        send_whatsapp_message(sender, "⚠️ API error occurred. Try again later.")
        return "error"
    except Exception as e:
        print(f"Error: {e}")
        send_whatsapp_message(sender, "⚠️ Something went wrong. Try again later.")
        return "error"

# Serve PDF files (for development only)
@app.route('/static/<path:filename>')
def serve_pdf(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)