import os, sys, json, argparse, pickle, re
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = "youtube_token.pickle"

def get_authenticated_service(client_id=None, client_secret=None, refresh_token=None):
    creds = None
    if refresh_token and client_id and client_secret:
        creds = Credentials(
            None,
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=SCOPES
        )
        creds.refresh(Request())
        return build("youtube", "v3", credentials=creds)
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)
    return build("youtube", "v3", credentials=creds)

def upload_video(youtube, video_path, title, description, tags, privacy="public", category="17"):
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category,
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  Uploaded {int(status.progress() * 100)}%")
    print(f"  Uploaded! Video ID: https://youtu.be/{response['id']}")
    return response["id"]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--auth-only", action="store_true", help="Run OAuth locally to get refresh token")
    parser.add_argument("--video", help="Path to video file")
    parser.add_argument("--metadata", help="Path to metadata JSON file")
    parser.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"])
    args = parser.parse_args()

    client_id = os.environ.get("YT_CLIENT_ID")
    client_secret = os.environ.get("YT_CLIENT_SECRET")
    refresh_token = os.environ.get("YT_REFRESH_TOKEN")

    if args.auth_only:
        print("Starting OAuth flow to get refresh token...")
        youtube = get_authenticated_service()
        print(f"\nRefresh Token: {youtube._http.credentials.refresh_token}")
        print("\nSave this as YT_REFRESH_TOKEN in GitHub Secrets!")
        return

    if args.video and args.metadata:
        with open(args.metadata, encoding="utf-8") as f:
            meta = json.load(f)
        title = meta["title_options"][0]
        description = meta["description"]
        tags = meta["tags"]

        youtube = get_authenticated_service(client_id, client_secret, refresh_token)
        print(f"Uploading: {title}")
        upload_video(youtube, args.video, title, description, tags, args.privacy)
        return

    print("Usage:")
    print("  First-time setup:  python scripts/upload_youtube.py --auth-only")
    print("  Upload:            python scripts/upload_youtube.py --video <file> --metadata <json>")
    print("  GitHub Actions:    Set YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN env vars")

if __name__ == "__main__":
    main()
