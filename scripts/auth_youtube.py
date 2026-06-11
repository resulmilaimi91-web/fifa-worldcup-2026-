import json, requests, urllib.parse, os, sys

SCOPE = "https://www.googleapis.com/auth/youtube.upload"
REDIRECT_URI = "http://localhost"

def get_creds():
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "client_secret.json")
    if not os.path.exists(path):
        print(f"ERROR: {path} not found")
        print("Shkarko client_secret.json nga Google Cloud Console")
        sys.exit(1)
    with open(path) as f:
        d = json.load(f)["installed"]
    return d["client_id"], d["client_secret"]

CLIENT_ID, CLIENT_SECRET = get_creds()

auth_url = (
    "https://accounts.google.com/o/oauth2/auth"
    "?response_type=code"
    f"&client_id={CLIENT_ID}"
    f"&redirect_uri={urllib.parse.quote(REDIRECT_URI, safe='')}"
    f"&scope={urllib.parse.quote(SCOPE, safe='')}"
    "&access_type=offline"
    "&prompt=consent"
)

print("=" * 60)
print("YOUTUBE OAUTH - HAPI 1")
print("=" * 60)
print()
print("Hape kete link ne browser:")
print(auth_url)
print()
print("1. Logohu me YouTube")
print("2. Kliko Allow")
print("3. Do te qellohet ne nje faqe bosh (localhost)")
print("4. Kopjo URL-ne nga address bar")
print("   (fillon me: http://localhost/?code=...)")
print()

redirect_url = input("Ngjit URL-ne ketu: ").strip()
parsed = urllib.parse.urlparse(redirect_url)
params = urllib.parse.parse_qs(parsed.query)
code = params.get("code", [None])[0]

if not code:
    print("ERROR: Nuk gjeta kodin ne URL.")
    print("Sigurohu qe kopjove URL-ne e plote.")
    sys.exit(1)

print("Duke kerkuar refresh token...")

r = requests.post("https://oauth2.googleapis.com/token", data={
    "code": code,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri": REDIRECT_URI,
    "grant_type": "authorization_code",
})

if r.status_code != 200:
    print(f"ERROR: {r.status_code} - {r.text}")
    sys.exit(1)

data = r.json()
refresh_token = data.get("refresh_token")

print()
print("=" * 60)
print("REFRESH TOKEN:")
print(refresh_token)
print()
print("CLIENT ID:")
print(CLIENT_ID)
print()
print("CLIENT SECRET:")
print(CLIENT_SECRET)
print("=" * 60)
print()
print("Shto keto 3 ne GitHub Secrets:")
print(f"YT_CLIENT_ID = {CLIENT_ID}")
print(f"YT_CLIENT_SECRET = {CLIENT_SECRET}")
print(f"YT_REFRESH_TOKEN = {refresh_token}")
print()

with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "youtube_token.json"), "w") as f:
    json.dump(data, f, indent=2)
print("Token u ruajt ne youtube_token.json")
