from twilio.rest import Client

# Tes informations Twilio
account_sid = 'AC5adeddc830995a859b9cb8d909b77164'
auth_token = '773167a0824e44ca845cfc3528356d22'
twilio_number = '+12674891003'  # ex: '+1415XXXXXXX'

# Numéro vers lequel tu veux envoyer le SMS (doit être vérifié si c’est un compte trial)
receiver_number = '+243811329047'  # ex: '+2438XXXXXXXX'

# Créer un client Twilio
client = Client(account_sid, auth_token)

# Envoi du SMS
message = client.messages.create(
    body='Salut ! Ceci est un test depuis mon app Flask 🚀',
    from_=twilio_number,
    to=receiver_number
)

print(f"Message envoyé avec SID : {message.sid}")