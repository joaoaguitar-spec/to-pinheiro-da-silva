"""
Discogs Discography Scraper — Tó Pinheiro da Silva (CRIATURA Memory Archive)

Fetches every release credited to António Pinheiro da Silva (Discogs artist
ID 435863), downloads the cover art, and writes structured outputs plus a
self-contained HTML gallery.

Run with:  python fetch_discography.py

Outputs (all local, kept out of git):
  to_pinheiro_discography.json
  to_pinheiro_discography.csv
  to_pinheiro_discography_summary.txt
  to_pinheiro_discography.html
  discography_covers/            (cover images, named by release id)
  failed_covers.log              (any covers that failed to download)
"""

# ─────────────────────────────────────────────
# BEFORE RUNNING: insert your Discogs token below
# Get one free at: https://www.discogs.com/settings/developers
DISCOGS_TOKEN = "YOUR_TOKEN_HERE"
# ─────────────────────────────────────────────

import csv
import json
import os
import time
from datetime import datetime

import requests

# ---------- configuration ----------
ARTIST_ID = "435863"
BASE_URL = "https://api.discogs.com"
USER_AGENT = "ToArquivo/1.0 +https://github.com/joaoaguitar-spec/to-pinheiro-da-silva"

COVERS_DIR = "discography_covers"
JSON_OUT = "to_pinheiro_discography.json"
CSV_OUT = "to_pinheiro_discography.csv"
SUMMARY_OUT = "to_pinheiro_discography_summary.txt"
HTML_OUT = "to_pinheiro_discography.html"
FAILED_LOG = "failed_covers.log"

PER_PAGE = 100
API_PAUSE = 1.0      # between paginated / detail API calls (60 req/min limit)
IMAGE_PAUSE = 0.5    # between image downloads

# Content-Type → file extension. Covers are saved with their REAL extension
# detected from the HTTP response, not forced to .jpg.
EXT_BY_CONTENT_TYPE = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
KNOWN_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".gif")

CSV_COLUMNS = [
    "unique_id", "id", "title", "artist", "role", "year",
    "format", "label", "cover_local", "cover_url", "discogs_url",
]

# Roles listed explicitly in the summary (in this order); any others are
# bucketed under their own name after these.
SUMMARY_ROLES = [
    "Mastered By", "Engineer", "Mixed By", "Recorded By",
    "Technician", "Remastered By", "Edited By",
]

DECADES = ["1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]


# ---------- HTTP helpers ----------
def api_headers():
    return {
        "Authorization": f"Discogs token={DISCOGS_TOKEN}",
        "User-Agent": USER_AGENT,
    }


def api_get(url, params=None, max_retries=4):
    """GET against the Discogs API with basic 429 back-off handling."""
    for attempt in range(max_retries):
        resp = requests.get(url, headers=api_headers(), params=params, timeout=30)
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", "5")) or 5
            print(f"  rate limited — waiting {wait}s ...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError(f"Gave up after {max_retries} retries: {url}")


# ---------- step 1: fetch all releases ----------
def fetch_all_releases():
    print("Fetching release list ...")
    releases = []
    page = 1
    url = f"{BASE_URL}/artists/{ARTIST_ID}/releases"
    while True:
        params = {
            "per_page": PER_PAGE,
            "page": page,
            "sort": "year",
            "sort_order": "asc",
        }
        data = api_get(url, params=params)
        batch = data.get("releases", [])
        releases.extend(batch)
        pages = data.get("pagination", {}).get("pages", 1)
        print(f"  page {page}/{pages} — {len(batch)} releases (total {len(releases)})")
        if page >= pages:
            break
        page += 1
        time.sleep(API_PAUSE)
    return releases


# ---------- step 2: cover art ----------
def fetch_primary_image_url(release):
    """Return the best cover URL for a release.

    Prefers the primary image from the full release/master detail; falls back
    to the thumbnail. Returns "" if nothing is available.
    """
    resource_url = release.get("resource_url", "")
    thumb = (release.get("thumb") or "").strip()
    if not resource_url:
        return thumb
    try:
        detail = api_get(resource_url)
    except Exception as exc:  # noqa: BLE001 — detail is best-effort
        print(f"  detail fetch failed ({release.get('id')}): {exc}")
        return thumb
    finally:
        time.sleep(API_PAUSE)

    images = detail.get("images") or []
    primary = next((img for img in images if img.get("type") == "primary"), None)
    chosen = primary or (images[0] if images else None)
    if chosen:
        return chosen.get("uri") or chosen.get("uri150") or thumb
    return thumb


def existing_cover_path(release_id):
    for ext in KNOWN_EXTS:
        path = os.path.join(COVERS_DIR, f"{release_id}{ext}")
        if os.path.exists(path):
            return path
    return None


def ext_from_url(url):
    lower = url.lower().split("?")[0]
    for ext in KNOWN_EXTS:
        if lower.endswith(ext):
            return ".jpg" if ext == ".jpeg" else ext
    return None


def download_cover(release_id, image_url):
    """Download a cover, saving it with the extension implied by Content-Type.

    Returns the local path (posix-style, relative) or None on failure.
    """
    existing = existing_cover_path(release_id)
    if existing:
        return existing.replace(os.sep, "/")
    if not image_url:
        return None

    resp = requests.get(image_url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    content_type = resp.headers.get("Content-Type", "").split(";")[0].strip().lower()
    ext = EXT_BY_CONTENT_TYPE.get(content_type) or ext_from_url(image_url) or ".jpg"

    path = os.path.join(COVERS_DIR, f"{release_id}{ext}")
    with open(path, "wb") as f:
        f.write(resp.content)
    return path.replace(os.sep, "/")


# ---------- normalisation ----------
def to_int_year(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def discogs_url_for(release):
    rid = release.get("id")
    kind = "master" if release.get("type") == "master" else "release"
    return f"https://www.discogs.com/{kind}/{rid}"


def normalise(release):
    return {
        "id": str(release.get("id", "")),
        "title": release.get("title", "") or "",
        "artist": release.get("artist", "") or "",
        "role": release.get("role", "") or "",
        "year": to_int_year(release.get("year")),
        "format": release.get("format", "") or "",
        "label": release.get("label", "") or "",
        "cover_local": "",
        "cover_url": "",
        "discogs_url": discogs_url_for(release),
        "type": release.get("type", "") or "",
    }


# ---------- output writers ----------
def write_json(records, path=JSON_OUT):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def write_csv(records, path=CSV_OUT):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for rec in records:
            writer.writerow(rec)


def decade_of(year):
    if not year:
        return None
    base = (year // 10) * 10
    return f"{base}s"


def write_summary(records, downloaded, failed, path=SUMMARY_OUT):
    role_counts = {}
    for rec in records:
        role = rec["role"] or "(no role)"
        role_counts[role] = role_counts.get(role, 0) + 1

    decade_counts = {d: 0 for d in DECADES}
    other_decades = {}
    for rec in records:
        d = decade_of(rec["year"])
        if d is None:
            continue
        if d in decade_counts:
            decade_counts[d] += 1
        else:
            other_decades[d] = other_decades.get(d, 0) + 1

    lines = [f"Total releases: {len(records)}", "By role:"]
    for role in SUMMARY_ROLES:
        lines.append(f"  {role}: {role_counts.get(role, 0)}")
    for role in sorted(role_counts):
        if role not in SUMMARY_ROLES:
            lines.append(f"  {role}: {role_counts[role]}")

    lines.append("By decade:")
    for d in DECADES:
        lines.append(f"  {d}: {decade_counts[d]}")
    for d in sorted(other_decades):
        lines.append(f"  {d}: {other_decades[d]}")

    lines.append(f"Covers downloaded: {downloaded}")
    lines.append(f"Covers failed: {failed}")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return "\n".join(lines)


# ---------- HTML gallery ----------
def build_html(records, path=HTML_OUT):
    years = [r["year"] for r in records if r["year"]]
    year_min = min(years) if years else 1977
    year_max = max(years) if years else 2025
    generated = datetime.now().strftime("%Y-%m-%d")

    # Embed data as a JS array; neutralise any "</script>" sequences.
    data_json = json.dumps(records, ensure_ascii=False).replace("</", "<\\/")

    roles_present = sorted({r["role"] for r in records if r["role"]})
    role_options = "".join(f'<option value="{r}">{r}</option>' for r in roles_present)

    html = HTML_TEMPLATE.format(
        credits=len(records),
        year_min=year_min,
        year_max=year_max,
        role_options=role_options,
        data_json=data_json,
        generated=generated,
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>António Pinheiro da Silva — Discografia</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;800&family=Space+Grotesk:wght@400;500;700&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg:#0a0a0a; --surface:#111111; --accent:#8B0000; --accent-bright:#a00000;
    --text:#f0ede8; --muted:#888880; --border:#222220;
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; background:var(--bg); color:var(--text);
    font-family:'Space Grotesk',sans-serif; line-height:1.4;
  }}
  .wrap {{ max-width:1400px; margin:0 auto; padding:40px 24px 80px; }}
  header h1 {{
    font-family:'Playfair Display',serif; font-weight:800;
    font-size:clamp(2rem,5vw,3.4rem); margin:0 0 8px;
  }}
  .subtitle {{
    font-family:'Space Mono',monospace; font-size:.8rem; letter-spacing:.08em;
    color:var(--accent-bright); text-transform:uppercase;
  }}
  .filters {{
    display:flex; flex-wrap:wrap; gap:12px; align-items:center;
    margin:32px 0 20px; padding:16px; background:var(--surface);
    border:1px solid var(--border); border-radius:8px;
  }}
  .filters select, .filters input {{
    background:var(--bg); color:var(--text); border:1px solid var(--border);
    border-radius:6px; padding:8px 10px; font-family:'Space Grotesk',sans-serif;
    font-size:.9rem;
  }}
  .filters input {{ flex:1; min-width:160px; }}
  .filters label {{
    font-family:'Space Mono',monospace; font-size:.7rem; color:var(--muted);
    text-transform:uppercase; letter-spacing:.06em; margin-right:4px;
  }}
  #count {{
    font-family:'Space Mono',monospace; font-size:.75rem; color:var(--muted);
    margin-left:auto;
  }}
  .grid {{
    display:grid; grid-template-columns:repeat(auto-fill,minmax(160px,1fr));
    gap:16px;
  }}
  .card {{
    background:var(--surface); border:1px solid var(--border); border-radius:8px;
    overflow:hidden; cursor:pointer; text-decoration:none; color:inherit;
    display:flex; flex-direction:column; transition:border-color .15s,transform .15s;
  }}
  .card:hover {{ border-color:var(--accent); transform:translateY(-2px); }}
  .cover {{ position:relative; aspect-ratio:1/1; background:#000; }}
  .cover img {{ width:100%; height:100%; object-fit:cover; display:block; }}
  .overlay {{
    position:absolute; inset:0; background:rgba(139,0,0,.78);
    opacity:0; transition:opacity .15s; display:flex; align-items:flex-end;
    padding:10px;
  }}
  .card:hover .overlay {{ opacity:1; }}
  .badge {{
    font-family:'Space Mono',monospace; font-size:.62rem; font-weight:700;
    text-transform:uppercase; letter-spacing:.05em; color:#fff;
    padding:4px 8px; border-radius:4px; background:#333;
  }}
  .meta {{ padding:10px 12px 14px; display:flex; flex-direction:column; gap:2px; }}
  .meta .t {{
    font-weight:700; font-size:.86rem; line-height:1.25;
    display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical;
    overflow:hidden;
  }}
  .meta .a {{ font-size:.78rem; color:var(--muted);
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .meta .y {{ font-family:'Space Mono',monospace; font-size:.7rem; color:var(--accent-bright); }}
  footer {{
    margin-top:60px; padding-top:24px; border-top:1px solid var(--border);
    font-family:'Space Mono',monospace; font-size:.68rem; color:var(--muted);
    line-height:1.8;
  }}
  .empty {{ color:var(--muted); padding:40px 0; font-family:'Space Mono',monospace; }}
  @media (max-width:480px) {{
    .grid {{ grid-template-columns:repeat(auto-fill,minmax(120px,1fr)); gap:10px; }}
    .wrap {{ padding:24px 14px 60px; }}
    #count {{ margin-left:0; width:100%; }}
  }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>António Pinheiro da Silva</h1>
    <div class="subtitle">Discografia Completa · {credits} créditos · {year_min}–{year_max}</div>
  </header>

  <div class="filters">
    <label>Função</label>
    <select id="roleFilter">
      <option value="">Todas</option>
      {role_options}
    </select>
    <label>Década</label>
    <select id="decadeFilter">
      <option value="">Todas</option>
      <option value="1970">1970s</option>
      <option value="1980">1980s</option>
      <option value="1990">1990s</option>
      <option value="2000">2000s</option>
      <option value="2010">2010s</option>
      <option value="2020">2020s</option>
    </select>
    <input id="search" type="text" placeholder="Procurar título ou artista...">
    <span id="count"></span>
  </div>

  <div id="grid" class="grid"></div>
  <footer>
    Fonte: Discogs API · Artist ID 435863 · Gerado em {generated}<br>
    Arquivo privado — Tó Pinheiro da Silva
  </footer>
</div>

<script>
const DATA = {data_json};
const ROLE_COLORS = {{
  "Mastered By":"#8B0000", "Mixed By":"#5a3000",
  "Engineer":"#003050", "Recorded By":"#004030"
}};
const grid = document.getElementById('grid');
const roleFilter = document.getElementById('roleFilter');
const decadeFilter = document.getElementById('decadeFilter');
const search = document.getElementById('search');
const count = document.getElementById('count');

function esc(s) {{
  return String(s == null ? '' : s).replace(/[&<>"']/g, c => (
    {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]
  ));
}}

function badgeColor(role) {{ return ROLE_COLORS[role] || "#333"; }}

function cardHTML(r) {{
  const cover = r.cover_local || r.cover_url || '';
  const fallback = r.cover_url || '';
  const onerr = fallback && fallback !== cover
    ? `this.onerror=null;this.src='${{esc(fallback)}}'` : `this.style.display='none'`;
  const img = cover
    ? `<img loading="lazy" src="${{esc(cover)}}" alt="${{esc(r.title)}}" onerror="${{onerr}}">`
    : '';
  return `<a class="card" href="${{esc(r.discogs_url)}}" target="_blank" rel="noopener">
    <div class="cover">${{img}}
      <div class="overlay"><span class="badge" style="background:${{badgeColor(r.role)}}">${{esc(r.role || '—')}}</span></div>
    </div>
    <div class="meta">
      <span class="t">${{esc(r.title)}}</span>
      <span class="a">${{esc(r.artist)}}</span>
      <span class="y">${{r.year || '—'}}</span>
    </div>
  </a>`;
}}

function render() {{
  const role = roleFilter.value;
  const decade = decadeFilter.value;
  const q = search.value.trim().toLowerCase();
  const filtered = DATA.filter(r => {{
    if (role && r.role !== role) return false;
    if (decade) {{
      const d = Math.floor((r.year || 0) / 10) * 10;
      if (String(d) !== decade) return false;
    }}
    if (q) {{
      const hay = ((r.title || '') + ' ' + (r.artist || '')).toLowerCase();
      if (!hay.includes(q)) return false;
    }}
    return true;
  }});
  grid.innerHTML = filtered.length
    ? filtered.map(cardHTML).join('')
    : '<div class="empty">Nenhum resultado.</div>';
  count.textContent = `Showing ${{filtered.length}} of ${{DATA.length}}`;
}}

roleFilter.addEventListener('change', render);
decadeFilter.addEventListener('change', render);
search.addEventListener('input', render);
render();
</script>
</body>
</html>
"""


# ---------- orchestration ----------
def main():
    if DISCOGS_TOKEN == "YOUR_TOKEN_HERE" or not DISCOGS_TOKEN.strip():
        raise SystemExit(
            "Set DISCOGS_TOKEN at the top of this script first.\n"
            "Get a free token at https://www.discogs.com/settings/developers"
        )

    os.makedirs(COVERS_DIR, exist_ok=True)

    raw_releases = fetch_all_releases()
    records = [normalise(r) for r in raw_releases]

    # Sort by year ascending (year 0 / unknown sinks to the end), then assign IDs.
    records.sort(key=lambda r: (r["year"] == 0, r["year"], r["title"].lower()))
    for idx, rec in enumerate(records, start=1):
        rec["unique_id"] = f"TPS-{idx:05d}"

    print(f"\nDownloading covers for {len(records)} releases ...")
    downloaded = 0
    failed = 0
    if os.path.exists(FAILED_LOG):
        os.remove(FAILED_LOG)

    for i, (rec, raw) in enumerate(zip(records, raw_releases), start=1):
        image_url = fetch_primary_image_url(raw)
        rec["cover_url"] = image_url or ""
        try:
            local = download_cover(rec["id"], image_url)
        except Exception as exc:  # noqa: BLE001
            local = None
            print(f"  [{i}/{len(records)}] cover failed ({rec['id']}): {exc}")
        if local:
            rec["cover_local"] = local
            downloaded += 1
        else:
            failed += 1
            with open(FAILED_LOG, "a", encoding="utf-8") as f:
                f.write(f"{rec['id']}\t{rec['title']}\t{image_url}\n")
        time.sleep(IMAGE_PAUSE)

    write_json(records)
    write_csv(records)
    summary = write_summary(records, downloaded, failed)
    build_html(records)

    print("\n" + summary)
    print(f"\nWrote: {JSON_OUT}, {CSV_OUT}, {SUMMARY_OUT}, {HTML_OUT}")
    print(f"Covers in ./{COVERS_DIR}/  (downloaded {downloaded}, failed {failed})")


if __name__ == "__main__":
    main()
