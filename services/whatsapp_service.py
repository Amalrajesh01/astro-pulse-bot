from twilio.rest import Client
import time
import os
import requests
import threading
from utils.helpers import get_current_phase

from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from textwrap import wrap

FONT_NAME = "NotoSansMalayalam"
FONT_PATH = "fonts/NotoSansMalayalam-Regular.ttf"

if not os.path.exists(FONT_PATH):
    raise FileNotFoundError(f"Font file not found: {FONT_PATH}")

pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))


account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_NUMBER")

client = Client(account_sid, auth_token)

def send_whatsapp_message(to, body):
    client.messages.create(
        from_=twilio_number,
        body=body,
        to=to
    )

def send_whatsapp_media(to, body, media_url):
    client.messages.create(
        from_=twilio_number,
        body=body,
        media_url=[media_url],
        to=to
    )


def create_malayalam_pdf(prediction_text, category, year):
    buffer = io.BytesIO()
    width, height = A4
    c = canvas.Canvas(buffer, pagesize=A4)
    
    # Set font to Malayalam font
    c.setFont(FONT_NAME, 14)
    
    # Title
    c.drawCentredString(width / 2, height - 50, f"{year} ലെ {category} പ്രവചനം")
    
    # Start text below title
    text_object = c.beginText(40, height - 80)
    text_object.setFont(FONT_NAME, 12)
    
    # Wrap text reasonably (ReportLab doesn't support Malayalam width measurement perfectly,
    # but wrapping manually helps readability)
    for line in wrap(prediction_text, 85):
        text_object.textLine(line)
    
    c.drawText(text_object)
    c.save()
    buffer.seek(0)
    
    # Save to static file
    os.makedirs("static", exist_ok=True)
    file_path = os.path.join("static", "your_personalised_report.pdf")
    with open(file_path, "wb") as f:
        f.write(buffer.getbuffer())
    
    return file_path


def create_thank_you_pdf(text, category, year):
    folder = 'static'
    if not os.path.exists(folder):
        os.makedirs(folder)

    file_path = os.path.join(folder, 'your_personalised_report.pdf')

    doc = SimpleDocTemplate(file_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    header = Paragraph("<b>🌟 Astro Pulse: Thank You!</b>", styles['Title'])
    subheader = Paragraph(f"<b>Your {category.capitalize()} Prediction for {year}:</b>", styles['Heading2'])
    body = Paragraph(text.replace("\n", "<br/>"), styles['BodyText'])

    story.append(header)
    story.append(subheader)
    story.append(body)

    doc.build(story)
    print(f"✅ PDF created: {file_path}")

def send_delayed_message(to, delay_seconds=30):
    time.sleep(delay_seconds)
    send_whatsapp_message(
        to,
        "🌟 Your chat has ended. Send 'hi' or 'hello' to restart the conversation."
    )
CATEGORIES = [
    'health', 'physique', 'relationship', 'career', 'travel',
    'family', 'friends', 'finances', 'status'
]



import threading
import os
import requests

def send_english_flow(step, sender, body, session):
    if session is None:
        session = {"step": 0}

    # Step 0: welcome message
    if step == 0:
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
        return session

    # Step 1: choose yearly/weekly
    if step == 1:
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
            send_whatsapp_message(sender, "❌ Invalid choice. Please enter 1 or 2.")
        return session

    # Step 2: get zodiac
    if step == 2:
        if body.isdigit() and 1 <= int(body) <= 12:
            session["zodiac"] = body
            send_whatsapp_message(sender, "✅ Got it! Now enter the year (e.g., 2025):")
            session["step"] = 3
        else:
            send_whatsapp_message(sender, "❌ Invalid choice. Please enter a number between 1 and 12.")
        return session

    # Step 3: get year
    if step == 3:
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
        return session

    # Step 4: get category and generate/send PDF
    if step == 4:
        if not (body.isdigit() and 1 <= int(body) <= 9):
            send_whatsapp_message(sender, "❌ Invalid choice. Please enter a number between 1 and 9.")
            return session

        category_map = {
            1: "health", 2: "physique", 3: "relationship", 4: "career",
            5: "travel", 6: "family", 7: "friends", 8: "finances", 9: "status"
        }
        category_index = int(body)
        selected_category = category_map[category_index]
        zodiac = session.get("zodiac")
        year = session.get("year")

        if not zodiac or not year:
            send_whatsapp_message(sender, "⚠️ Session error. Please start again by sending 'hi'.")
            session["step"] = 0
            return session

        # Call API with error handling
        api_url = "https://api.vedicastroapi.com/v3-json/prediction/yearly"
        params = {
            "year": year,
            "zodiac": zodiac,
            "api_key": os.getenv("VEDIC_API_KEY", "7fc2e77b-b33b-51e1-9abb-1cf20de8dc04"),
            "lang": "en"
        }

        try:
            res = requests.get(api_url, params=params, timeout=15)
            res.raise_for_status()
            api_response = res.json()

            response_data = api_response.get("response")
            if not response_data:
                raise ValueError("No 'response' in API data")

            current_phase = get_current_phase()
            phase_data = response_data.get(current_phase) or next(iter(response_data.values()))
            category_data = phase_data.get(selected_category)

            if not category_data or "prediction" not in category_data:
                raise ValueError(f"No prediction data for category '{selected_category}'")

            prediction_text = category_data["prediction"]

        except Exception as e:
            print(f"[API ERROR] {e}")
            send_whatsapp_message(sender, "❌ Sorry, could not retrieve your prediction. Please try again later.")
            session["step"] = 0
            return session

        # Create PDF (this should save the PDF to your static folder with a fixed name)
        try:
            create_thank_you_pdf(prediction_text, selected_category, year)
        except Exception as e:
            print(f"[PDF ERROR] {e}")
            send_whatsapp_message(sender, "❌ Error creating PDF. Please try again later.")
            session["step"] = 0
            return session

        # Construct public PDF URL from env
        pdf_base_url = os.getenv("PDF_BASE_URL", "https://8d16bfdc76c1.ngrok-free.app")
        pdf_url = pdf_base_url.rstrip("/") + "/static/your_personalised_report.pdf"

        # Send PDF via WhatsApp
        try:
            send_whatsapp_media(
                sender,
                f"✅ Your {selected_category.capitalize()} Prediction for {year} is ready. Please download the PDF below.",
                pdf_url
            )
        except Exception as e:
            print(f"[TWILIO SEND ERROR] {e}")
            send_whatsapp_message(sender, "❌ Error sending PDF. Please try again later.")
            session["step"] = 0
            return session

        # Send delayed follow-up message in background
        threading.Thread(target=send_delayed_message, args=(sender, 30), daemon=True).start()

        session["step"] = 0
        return session

    # Fallback for unknown steps
    send_whatsapp_message(sender, "❌ Invalid input. Please send 'hi' to start over.")
    session["step"] = 0
    return session


def send_malayalam_flow(step, sender, body, session):
    """Handles complete Malayalam conversation flow + API + PDF."""
    if step == 0:
        welcome_message = (
            "🌟 ആസ്ട്രോ പൾസിലേക്ക് സ്വാഗതം! 🌟\n\n"
            "നക്ഷത്രങ്ങളുടെ രഹസ്യങ്ങൾ തുറന്ന് കാണാം!\n"
            "താങ്കൾക്ക് എന്താണ് അറിയാൻ ആഗ്രഹിക്കുന്നത്?\n"
            "1. വാർഷിക ജാതകം\n"
            "2. ആഴ്ച്ചവാര ജാതകം (വേഗം വരുന്നു!)\n\n"
            "താങ്കളുടെ തിരഞ്ഞെടുപ്പ് നമ്പർ നൽകുക:"
        )
        send_whatsapp_message(sender, welcome_message)
        session["step"] = 1

    elif step == 1:
        if body == '1':
            zodiac_list = (
                "താങ്കളുടെ രാശി തിരഞ്ഞെടുക്കുക (നമ്പർ നൽകുക):\n"
                "1: മേടം (Aries)\n2: ഇടവം (Taurus)\n3: മിഥുനം (Gemini)\n4: കർക്കിടകം (Cancer)\n"
                "5: ചിങ്ങം (Leo)\n6: കന്നി (Virgo)\n7: തുലാം (Libra)\n8: വൃശ്ചികം (Scorpio)\n"
                "9: ധനു (Sagittarius)\n10: മകരം (Capricorn)\n11: കുംഭം (Aquarius)\n12: മീനം (Pisces)\n\n"
                "നമ്പർ നൽകുക:"
            )
            send_whatsapp_message(sender, zodiac_list)
            session["step"] = 2
        elif body == '2':
            send_whatsapp_message(sender, "❌ ആഴ്ച്ചവാര ജാതകം വേഗം വരുന്നു! ദയവായി 1 തിരഞ്ഞെടുക്കുക വാർഷിക ജാതകത്തിനായി.")
        else:
            send_whatsapp_message(sender, "❌ തെറ്റായ തിരഞ്ഞെടുപ്പ്. ദയവായി 1 അല്ലെങ്കിൽ 2 നൽകുക.")

    elif step == 2:
        if body.isdigit() and 1 <= int(body) <= 12:
            session["zodiac"] = body
            send_whatsapp_message(sender, "✅ ലഭിച്ചു! ഇപ്പോൾ വർഷം നൽകുക (ഉദാ: 2025):")
            session["step"] = 3
        else:
            send_whatsapp_message(sender, "❌ തെറ്റായ തിരഞ്ഞെടുപ്പ്. ദയവായി 1 മുതൽ 12 വരെയുള്ള നമ്പർ നൽകുക.")

    elif step == 3:
        if body.isdigit():
            session["year"] = body
            category_list = (
                "താങ്കളുടെ പ്രവചന വിഭാഗം തിരഞ്ഞെടുക്കുക:\n"
                "1. ആരോഗ്യം\n2. ശരീരഘടന\n3. ബന്ധം\n4. കരിയർ\n"
                "5. യാത്ര\n6. കുടുംബം\n7. സുഹൃത്തുക്കൾ\n8. സാമ്പത്തികം\n9. പ്രതിഷ്ഠ\n\n"
                "നമ്പർ നൽകുക:"
            )
            send_whatsapp_message(sender, category_list)
            session["step"] = 4
        else:
            send_whatsapp_message(sender, "❌ ശരിയായ വർഷം നൽകുക.")

    elif step == 4:
        if body.isdigit() and 1 <= int(body) <= 9:
            category_index = int(body) - 1
            selected_category = CATEGORIES[category_index]
            zodiac = session['zodiac']
            year = session['year']

            # Call API with Malayalam lang param
            url = f"https://api.vedicastroapi.com/v3-json/prediction/yearly?year={year}&zodiac={zodiac}&api_key=7fc2e77b-b33b-51e1-9abb-1cf20de8dc04&lang=ml"
            api_response = requests.get(url).json()
            current_phase = get_current_phase()
            prediction = api_response['response'][current_phase][selected_category]['prediction']

            # Create PDF locally with Malayalam text
            create_malayalam_pdf(prediction, selected_category, year)

            pdf_url = os.getenv("PDF_BASE_URL", "https://8d16bfdc76c1.ngrok-free.app") + "/static/your_personalised_report.pdf"

            # Send the PDF via WhatsApp
            send_whatsapp_media(
                sender,
                f"✅ താങ്കളുടെ {selected_category} പ്രവചനം {year} ലേക്ക് തയ്യാറായി. PDF താഴെ നിന്ന് ഡൗൺലോഡ് ചെയ്യുക.",
                pdf_url
            )

            # Send delayed message after 30 seconds
            threading.Thread(target=send_delayed_message, args=(sender, 30)).start()
            session["step"] = 0
        else:
            send_whatsapp_message(sender, "❌ തെറ്റായ തിരഞ്ഞെടുപ്പ്. ദയവായി 1 മുതൽ 9 വരെയുള്ള നമ്പർ നൽകുക.")

    else:
        # Handle unexpected steps
        send_whatsapp_message(sender, "❌ തെറ്റായ പ്രവേശനം. ദയവായി വീണ്ടും ആരംഭിക്കുക.")
        session["step"] = 0

    return session