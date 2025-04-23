import logging
import os
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from bs4 import BeautifulSoup

FROM = os.getenv("FROM")
RECIPIENTS = os.getenv("RECIPIENTS").split(",")
ICLOUD_APP_PASSWORD = os.getenv("ICLOUD_APP_PASSWORD")

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def main() -> int:
    res = requests.get("https://www.whatdayisit.co.uk/")
    if not res.ok:
        logging.info("Could not fetch HTML page")
        return 1
    soup = BeautifulSoup(res.text, "html.parser")

    # Thanks ChatGPT
    big_p = soup.find('p', style=lambda value: value and 'font-size:130px' in value)
    day = big_p.get_text(separator=' ', strip=True) if big_p else "I don't know man"
    print(day)
    
    send_email(
        subject="What day is it ?",
        body=day,
        recipient_emails=RECIPIENTS,
    )   
    return 0


def send_email(subject, body, recipient_emails):
    # iCloud SMTP server settings
    smtp_server = "smtp.mail.me.com"
    smtp_port = 587
    from_email = FROM
    app_password = ICLOUD_APP_PASSWORD

    # Create the email headers and content
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = ", ".join(recipient_emails)
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    try:
        # Set up the SMTP server and start TLS
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()

        # Log in to the iCloud account
        server.login(from_email, app_password)

        # Send the email
        server.sendmail(from_email, recipient_emails, msg.as_string())

        # Close the server connection
        server.quit()

        logging.info("Email sent successfully!")
    except Exception as e:
        logging.error(f"Failed to send email. Error: {e}")
