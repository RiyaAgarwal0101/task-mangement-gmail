from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send"
]

flow = InstalledAppFlow.from_client_secrets_file(
    "client_secret.json",
    SCOPES
)

credentials = flow.run_local_server(
    port=8080,
    open_browser=True,
    access_type="offline",
    prompt="consent"
)

print("\nREFRESH TOKEN:")
print(credentials.refresh_token)