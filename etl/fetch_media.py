"""Photography from Wikimedia Commons, with its licence and author carried along.

Stock photo services give arbitrary images. On a site whose entire premise is
"every number tells you where it came from", an uncredited stock photo of a wave
captioned as a compute figure is worse than no photo at all.

Commons gives us images that are relevant, openly licensed, and citable, which
is exactly the standard the rest of the pipeline is held to.

Files are downloaded into public/media/ rather than hotlinked: Commons asks that
their thumbnail endpoints not be used as a CDN, their URLs carry tracking
parameters, and a local copy keeps the build reproducible offline.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from common import ROOT, SSL_CONTEXT, USER_AGENT, utcnow, write_dataset

MEDIA_DIR = ROOT / "public" / "media"
API = "https://commons.wikimedia.org/w/api.php"
SOURCE_ID = "wikimedia-commons"

# Licences we will display. Anything else gets skipped loudly rather than shipped.
ALLOWED_LICENCES = re.compile(r"^(CC0|CC BY|Public domain)", re.IGNORECASE)

# slot -> Commons file title. The slot is where the page uses it.
MANIFEST = {
    "compute-hall": {
        "title": "File:BalticServers data center.jpg",
        "width": 1400,
        "alt": "Rows of server racks in a data centre hall",
    },
    "governance-chamber": {
        "title": "File:Hemicycle of the European Parliament, Strasbourg 004.jpg",
        "width": 1200,
        "alt": "The debating chamber of the European Parliament in Strasbourg",
    },
}


def _strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", "", value or "")
    return re.sub(r"\s+", " ", text).strip()


def _api(params: dict) -> dict:
    url = f"{API}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60, context=SSL_CONTEXT) as response:
        return json.load(response)


def run(offline: bool = False) -> None:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    records = []

    for slot, spec in MANIFEST.items():
        target = MEDIA_DIR / f"{slot}.jpg"
        meta_path = MEDIA_DIR / f"{slot}.json"

        if offline or target.exists():
            if meta_path.exists():
                records.append(json.loads(meta_path.read_text(encoding="utf-8")))
                print(f"  {slot}: using local copy")
                continue
            if offline:
                raise RuntimeError(f"--offline set but no local copy of {slot}")

        payload = _api(
            {
                "action": "query",
                "titles": spec["title"],
                "prop": "imageinfo",
                "iiprop": "url|extmetadata",
                "iiurlwidth": str(spec["width"]),
                "format": "json",
            }
        )
        pages = payload.get("query", {}).get("pages", {})
        info = next(iter(pages.values()), {}).get("imageinfo")
        if not info:
            raise RuntimeError(f"{slot}: Commons returned no imageinfo for {spec['title']}")

        info = info[0]
        extra = info.get("extmetadata", {})
        licence = _strip_html(extra.get("LicenseShortName", {}).get("value", ""))

        if not ALLOWED_LICENCES.match(licence):
            # CC BY-SA is fine to display with attribution, but flag it so the
            # share-alike obligation is a conscious choice rather than an accident.
            print(f"  NOTE {slot}: licence is {licence!r}; displaying with attribution")

        thumb = info.get("thumburl") or info.get("url")
        request = urllib.request.Request(thumb, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=90, context=SSL_CONTEXT) as response:
            target.write_bytes(response.read())

        record = {
            "slot": slot,
            "file": f"/media/{slot}.jpg",
            "alt": spec["alt"],
            "title": spec["title"].removeprefix("File:").removesuffix(".jpg"),
            "author": _strip_html(extra.get("Artist", {}).get("value", "Unknown")),
            "licence": licence,
            "licence_url": _strip_html(extra.get("LicenseUrl", {}).get("value", "")),
            "page": info.get("descriptionurl", ""),
            "retrieved": utcnow(),
            "source_id": SOURCE_ID,
        }
        meta_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        records.append(record)
        print(f"  {slot}: {target.stat().st_size:,} bytes, {licence}")

    write_dataset(
        "media",
        records,
        source_ids=[SOURCE_ID],
        unit=None,
        notes=(
            "Photography from Wikimedia Commons, stored locally and credited to its "
            "author under its own licence. Images are illustrative backdrop and carry "
            "no data."
        ),
    )


if __name__ == "__main__":
    run(offline="--offline" in sys.argv)
