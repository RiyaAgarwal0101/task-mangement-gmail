import base64
from email.message import EmailMessage

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from config import (
    GMAIL_SENDER,
    GMAIL_REFRESH_TOKEN,
    GMAIL_CLIENT_ID,
    GMAIL_CLIENT_SECRET,
    GMAIL_ACCESS_TOKEN,
)

GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.send"


def get_gmail_service():
    if not GMAIL_REFRESH_TOKEN:
        raise RuntimeError("GMAIL_REFRESH_TOKEN is not configured")

    credentials = Credentials(
        token=GMAIL_ACCESS_TOKEN or None,
        refresh_token=GMAIL_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GMAIL_CLIENT_ID,
        client_secret=GMAIL_CLIENT_SECRET,
        scopes=[GMAIL_SCOPE],
    )

    return build("gmail", "v1", credentials=credentials, cache_discovery=False)


def send_email(to_email: str, subject: str, body: str):
    if not GMAIL_SENDER:
        raise RuntimeError("GMAIL_SENDER is not configured")

    message = EmailMessage()
    message["To"] = to_email
    message["From"] = GMAIL_SENDER
    message["Subject"] = subject
    message.set_content(body)

    encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()

    service = get_gmail_service()
    return (
        service.users()
        .messages()
        .send(userId="me", body={"raw": encoded})
        .execute()
    )


def send_task_created_email(task, assignee):
    return send_email(
        assignee["email"],
        f"New task assigned: {task['title']}",
        (
            f"Hello {assignee['full_name']},\n\n"
            f"You have been assigned a new task.\n\n"
            f"Task: {task['title']}\n"
            f"Description: {task.get('description', '') or 'No description'}\n\n"
            f"Please log in to the Task Management app to view it."
        ),
    )


def send_task_completed_email(task, creator):
    return send_email(
        creator["email"],
        f"Task completed: {task['title']}",
        (
            f"Hello {creator['full_name']},\n\n"
            f"Your task has been marked as completed.\n\n"
            f"Task: {task['title']}\n"
            f"Description: {task.get('description', '') or 'No description'}\n\n"
            f"Please log in to the Task Management app to view the update."
        ),
    )
