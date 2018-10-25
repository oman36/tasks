import smtplib
import os
from .exceptions import FatalException

from_address = os.environ.get('SMTP_FROM')
host = os.environ.get('SMTP_HOST')
password = os.environ.get('SMTP_PASS')
port = os.environ.get('SMTP_PORT')

if not all((from_address, host, port)):
    raise FatalException('Env variables SMTP_FROM, SMTP_HOST, SMTP_PORT are required')


def send_email(to: list, subject: str, body_text: str):
    """
    Send an email
    """
    body = "\r\n".join((
        "From: %s" % from_address,
        "To: %s" % to,
        "Subject: %s" % subject,
        "",
        body_text
    ))

    server = smtplib.SMTP_SSL(host, port, timeout=1)
    if password:
        server.login(from_address, password)
        server.auth_plain()
    server.sendmail(from_address, to, body)
    server.quit()
    return
