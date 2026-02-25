import os
import base64
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete token.json
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

class EmailInformation:
    def __init__(self, senderEmail, toEmails):
        self.senderEmail = senderEmail
        self.toEmails = toEmails

def authenticate_gmail():
    creds = None

    # Load token if it exists
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If no valid credentials, run OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials for next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)


def create_message(sender, to_list, subject, body_text):
    message = MIMEText(body_text)
    message['to'] = ', '.join(to_list)
    message['from'] = sender
    message['subject'] = subject

    raw_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    return {'raw': raw_message}


def send_email(sender, recipients, subject, body):
    service = authenticate_gmail()

    message = create_message(sender, recipients, subject, body)

    sent = service.users().messages().send(
        userId="me",
        body=message
    ).execute()

    print(f"Message sent. ID: {sent['id']}")


if __name__ == "__main__":
    sender_email = "your_email@gmail.com"

    recipients = [
        "recipient1@example.com",
        "recipient2@example.com"
    ]

    subject = "Test Email from Python Gmail API"
    body = "This is a test email sent using the Gmail API and OAuth2."

    send_email(sender_email, recipients, subject, body)