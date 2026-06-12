import os, sys, json, argparse, pickle, re, time, random, logging
from datetime import datetime, timezone, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = "youtube_token.pickle"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

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

def jitter_sleep(min_s=5, max_s=30):
    delay = random.uniform(min_s, max_s)
    log.info(f"Jitter delay: {delay:.1f}s")
    time.sleep(delay)

def rotate_title(title_options, used_titles=None):
    available = [t for t in title_options if not used_titles or t not in used_titles]
    if not available:
        return random.choice(title_options)
    return random.choice(available)

def rotate_tags(base_tags):
    shuffled = base_tags[:]
    random.shuffle(shuffled)
    if random.random() < 0.4:
        alt = ["viral", "trending", "fyp", "foryou", "mustwatch", "highlights", "sports", "football", "soccer"]
        extra = random.sample(alt, random.randint(1, 2))
        shuffled.extend(extra)
    return shuffled[:10]

def rotate_description(meta, video_filename=None):
    desc = meta.get("description", "")
    parts = [desc]
    if random.random() < 0.5:
        extra_lines = [
            "\n\nDon't forget to LIKE and SUBSCRIBE for more FIFA World Cup 2026 content!",
            "\n\nWhat do you think about this? Comment below!",
            "\n\nSubscribe for daily World Cup 2026 updates and highlights.",
            "\n\nWhich team are you supporting? Let me know in the comments!",
            "\n\nWorld Cup 2026 is the biggest tournament ever. Stay tuned for more!",
        ]
        parts.append(random.choice(extra_lines))
    hashtags = " #WorldCup2026 #FIFA2026 #Football"
    parts.append(hashtags)
    return "".join(parts)

def randomize_publish_at(base_publish_at=None):
    if base_publish_at:
        dt = datetime.fromisoformat(base_publish_at.replace("Z", "+00:00"))
    else:
        now = datetime.now(timezone.utc)
        dt = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    offset_hours = random.uniform(-3, 3)
    offset_minutes = random.randint(-30, 30)
    dt += timedelta(hours=offset_hours, minutes=offset_minutes)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def upload_video(youtube, video_path, title, description, tags, privacy="public", category="17", publish_at=None, max_retries=3):
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags,
            "categoryId": category,
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }
    if publish_at:
        body["status"]["publishAt"] = publish_at
        body["status"]["privacyStatus"] = "private"

    chunk = random.choice([-1, 5*1024*1024, 10*1024*1024, 20*1024*1024])
    media = MediaFileUpload(video_path, chunksize=chunk, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    for attempt in range(max_retries):
        try:
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    pct = int(status.progress() * 100)
                    log.info(f"Uploaded {pct}%")
            vid = response["id"]
            if publish_at:
                log.info(f"Scheduled! https://youtu.be/{vid} (goes public at {publish_at})")
            else:
                log.info(f"Uploaded! https://youtu.be/{vid}")
            return vid
        except HttpError as e:
            if e.resp.status in [403, 409] and attempt < max_retries - 1:
                wait = random.randint(60, 300)
                log.warning(f"HTTP {e.resp.status}, retry in {wait}s (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
                continue
            raise
    return None

def check_channel(youtube, expected_channel=None):
    try:
        res = youtube.channels().list(part="snippet", mine=True).execute()
        items = res.get("items", [])
        if items:
            name = items[0]["snippet"]["title"]
            log.info(f"Authenticated channel: {name}")
            if expected_channel and expected_channel.lower() not in name.lower():
                log.warning(f"Channel mismatch! Expected '{expected_channel}', got '{name}'")
                return False
            return True
        log.warning("No channel found")
        return False
    except Exception as e:
        log.error(f"Channel check failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--auth-only", action="store_true")
    parser.add_argument("--video")
    parser.add_argument("--metadata")
    parser.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"])
    parser.add_argument("--publish-at", help="ISO8601 datetime for scheduled publish")
    parser.add_argument("--jitter", type=int, default=0, help="Random delay in seconds before upload")
    parser.add_argument("--channel-name", help="Verify channel name before upload")
    args = parser.parse_args()

    client_id = os.environ.get("YT_CLIENT_ID")
    client_secret = os.environ.get("YT_CLIENT_SECRET")
    refresh_token = os.environ.get("YT_REFRESH_TOKEN")

    if args.auth_only:
        youtube = get_authenticated_service()
        if youtube:
            check_channel(youtube)
            creds = youtube._http.credentials
            log.info(f"Refresh Token: {creds.refresh_token}")
            log.info("Save as YT_REFRESH_TOKEN in GitHub Secrets!")
        return

    if args.video and args.metadata:
        with open(args.metadata, encoding="utf-8") as f:
            meta = json.load(f)

        video_size_mb = os.path.getsize(args.video) / (1024*1024)

        if args.jitter > 0:
            jitter_sleep(5, args.jitter)

        title_options = meta.get("title_options", [meta.get("title", "FIFA World Cup 2026")])
        title = rotate_title(title_options)
        description = rotate_description(meta, os.path.basename(args.video))
        tags = rotate_tags(meta.get("tags", ["worldcup2026"]))

        youtube = get_authenticated_service(client_id, client_secret, refresh_token)

        if args.channel_name:
            ok = check_channel(youtube, args.channel_name)
            if not ok:
                log.error("Channel verification failed. Aborting.")
                sys.exit(1)

        publish_at = args.publish_at
        if publish_at and publish_at.lower() != "none":
            publish_at = args.publish_at
        else:
            publish_at = None

        log.info(f"Uploading: {title} ({video_size_mb:.1f} MB)")
        log.info(f"Tags: {', '.join(tags[:5])}...")
        if publish_at:
            log.info(f"Publish scheduled: {publish_at}")

        upload_video(youtube, args.video, title, description, tags, args.privacy, publish_at=publish_at)

        return

    log.info("Usage:")
    log.info("  python scripts/upload_youtube.py --auth-only")
    log.info("  python scripts/upload_youtube.py --video <file> --metadata <json>")
    log.info("  python scripts/upload_youtube.py --video <file> --metadata <json> --publish-at 2026-06-12T00:00:00Z")

if __name__ == "__main__":
    main()
