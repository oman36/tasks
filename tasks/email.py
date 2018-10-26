import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

from .settings import SETTINGS


def send_email(to: list, subject: str, body_text: str, files=None):
    """
    Send an email
    """

    email_settings = SETTINGS['email']

    msg = MIMEMultipart()
    msg['From'] = email_settings['from']
    msg['To'] = ', '.join(to)
    msg['Subject'] = subject
    msg.attach(MIMEText(body_text))

    for file_data in files or []:
        with open(file_data['tmp_path'], "rb") as fil:
            part = MIMEApplication(fil.read(), Name=file_data['name'])
        part['Content-Disposition'] = 'attachment; filename="{}"'.format(file_data['name'])
        msg.attach(part)

    server = smtplib.SMTP_SSL(email_settings['host'], email_settings['port'], timeout=1)

    if 'pass' in email_settings:
        server.login(email_settings['from'], email_settings['pass'])
        server.auth_plain()

    server.sendmail(email_settings['from'], to, msg.as_string())
    server.quit()
    return
