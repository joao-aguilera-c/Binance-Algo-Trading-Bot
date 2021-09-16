import smtplib
import ssl


def send_email(subject, matter):
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = "bot.notifications.jaguilera@gmail.com"  # Enter your address
    receiver_email = "bot.notifications.jaguilera@gmail.com"  # Enter receiver address
    password = "********"
    message = 'Subject: {}\n\n{}'.format(subject, matter)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)

