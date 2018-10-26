import smtplib

from .settings import SETTINGS


def send_email(to: list, subject: str, body_text: str):
    """
    Send an email
    """
    email_settings = SETTINGS['email']

    body = "\r\n".join((
        "From: %s" % email_settings['from'],
        "To: %s" % to,
        "Subject: %s" % subject,
        "",
        body_text
    ))

    server = smtplib.SMTP_SSL(email_settings['host'], email_settings['port'], timeout=1)

    if 'pass' in email_settings:
        server.login(email_settings['from'], email_settings['pass'])
        server.auth_plain()
    server.sendmail(email_settings['from'], to, body)
    server.quit()
    return
