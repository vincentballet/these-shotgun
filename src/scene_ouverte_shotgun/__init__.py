import logging
import os
import smtplib
import sys
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from bs4 import BeautifulSoup

FROM = os.getenv("FROM")
RECIPIENTS = os.getenv("RECIPIENTS").split(",")
ICLOUD_APP_PASSWORD = os.getenv("ICLOUD_APP_PASSWORD")

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def main() -> int:
    res = requests.get("https://facmedecine.umontpellier.fr/theses/")
    if not res.ok:
        logging.info("Could not fetch HTML page")
        return 1
    soup = BeautifulSoup(res.text, "html.parser")

    # 1. Find the <h4> tag that contains "MAJ :"
    maj_h4 = soup.find("h4", string=re.compile(r"\d{2}/\d{2}/\d{4}"))
    maj_date = "Not found"
    if maj_h4:
        match = re.search(r'\d{2}/\d{2}/\d{4}', maj_h4.text)
        if match:
            maj_date = match.group(0)

    # 2. Find the first <ul> that appears after the MAJ heading
    first_ul_after_maj = maj_h4.find_next("ul") if maj_h4 else None

    # 3. Get the first <li> in that <ul>
    first_li_text = None
    if first_ul_after_maj:
        first_li = first_ul_after_maj.find("li")
        if first_li:
            first_li_text = first_li.get_text(strip=True)

    send_email(
        subject="Last update {}".format(maj_date),
        body="Latest news : '{}'".format(first_li_text),
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
