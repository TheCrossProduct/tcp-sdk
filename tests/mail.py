import os.path
import base64
import json
import re
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import logging
import requests
from datetime import datetime, timedelta
import pathlib
import os

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]


def check_out_mail(
    mfrom: str = "contact@thecrossproduct.com",
    mto: str = "api.tester@thecrossproduct.com",
    subject: str = "test@helloworld is over.",
    delay="1h",
):
    creds = None

    credentials_dir = None
    if 'GAPIS_CREDENTIALS_DIR' in os.environ:
        credentials_dir = os.environ['GAPIS_CREDENTIALS_DIR']
    else:
        credentials_dir = pathlib.Path(__file__).parent.resolve()

    token_path = os.path.join(credentials_dir, "token.json")
    credentials_path = os.path.join(credentials_dir, "credentials.json")

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    out = []

    try:
        # Call the Gmail API
        service = build("gmail", "v1", credentials=creds)
        results = (
            service.users()
            .messages()
            .list(
                userId="me",
                labelIds=["INBOX"],
                q=f"is:unread from:{mfrom} newer_than:{delay} subject:{subject} to:{mto}",
            )
            .execute()
        )
        messages = results.get("messages", [])
        if not messages:
            print("No new messages.")
        else:
            message_count = 0
            for message in messages:
                msg = (
                    service.users()
                    .messages()
                    .get(userId="me", id=message["id"])
                    .execute()
                )
                try:
                    email_data = msg["payload"]["headers"]
                    data = msg["payload"]["parts"][-1]["body"]["data"]
                    byte_code = base64.urlsafe_b64decode(data)
                    text = byte_code.decode("utf-8")
                    out.append(text)
                    # mark the message as read (optional)
                    msg = (
                        service.users()
                        .messages()
                        .modify(
                            userId="me",
                            id=message["id"],
                            body={"removeLabelIds": ["UNREAD"]},
                        )
                        .execute()
                    )
                except BaseException as error:
                    print(f"An error occurred: {error}")
                    pass
    except Exception as error:
        print(f"An error occurred: {error}")
    return out
