import asyncio
import edge_tts

async def test():
    voices = await edge_tts.list_voices()
    found = False
    for v in voices:
        loc = v.get("Locale", "")
        name = v.get("Name", "")
        friendly = v.get("FriendlyName", "")
        if loc.startswith("sq"):
            print(f"Albanian: {name} - {loc} - {friendly}")
            found = True
    if not found:
        print("No Albanian voice found. Listing Balkan voices:")
        for v in voices:
            loc = v.get("Locale", "")
            if any(loc.startswith(x) for x in ["sq", "hr", "sr", "mk", "sl", "bg", "ro", "el", "it"]):
                print(f"  {v['Name']} - {v['Locale']} - {v['FriendlyName']}")

asyncio.run(test())
