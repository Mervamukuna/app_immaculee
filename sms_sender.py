# sms_sender.py
from twilio.rest import Client
import os
# Ces valeurs seront à remplacer après inscription chez Twilio
ACCOUNT_SID = "AC5adeddc830995a859b9cb8d909b77164"
AUTH_TOKEN = "773167a0824e44ca845cfc3528356d22"
TWILIO_PHONE_NUMBER = "+12674891003"  # Numéro Twilio

def envoyer_sms(numero_destinataire, message):
    try:
        client = Client(ACCOUNT_SID, AUTH_TOKEN)
        message = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=numero_destinataire
        )
        print("✅ SMS envoyé avec succès :", message.sid)
        return True
    except Exception as e:
        print("❌ Erreur lors de l'envoi du SMS :", e)
        return False
