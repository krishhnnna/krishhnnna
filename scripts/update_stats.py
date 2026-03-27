import requests
import datetime
import re
import os
from bs4 import BeautifulSoup

# ─────────────── CONFIG ───────────────
LEETCODE_ACCOUNTS   = ["wtffff__", "Hackker_69"]
CODEFORCES_ACCOUNTS = ["Hackker_69", "krishnnna"]
CODECHEF_ACCOUNT    = "hackker_69"
ATCODER_ACCOUNT     = "krishnnna"
# CSES requires login to scrape — update manually when solved count changes
CSES_SOLVED         = 57
# GFG — update manually when solved count changes
GFG_SOLVED          = 45
GFG_USERNAME        = ""   # optional: your GeeksForGeeks username (for profile link)
# ─────────────────────────────────────

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}


# ──────────── LEETCODE ────────────────
def get_leetcode_stats(username):
    query = """
    query getUserProfile($username: String!) {
        matchedUser(username: $username) {
            profile { ranking }
            submitStats {
                acSubmissionNum { difficulty count }
            }
        }
    }"""
    try:
        resp = requests.post(
            "https://leetcode.com/graphql",
            json={"query": query, "variables": {"username": username}},
            headers={**HEADERS, "Content-Type": "application/json",
                     "Referer": "https://leetcode.com"},
            timeout=15
        )
        data = resp.json()["data"]["matchedUser"]
        ac = data["submitStats"]["acSubmissionNum"]
        total  = next(x["count"] for x in ac if x["difficulty"] == "All")
        easy   = next(x["count"] for x in ac if x["difficulty"] == "Easy")
        medium = next(x["count"] for x in ac if x["difficulty"] == "Medium")
        hard   = next(x["count"] for x in ac if x["difficulty"] == "Hard")
        return {"username": username, "total": total,
                "easy": easy, "medium": medium, "hard": hard}
    except Exception as e:
        print(f"[LeetCode] Error for {username}: {e}")
        return {"username": username, "total": 0, "easy": 0, "medium": 0, "hard": 0}


# ──────────── CODEFORCES ─────────────
def get_codeforces_stats(handle):
    try:
        info = requests.get(
            f"https://codeforces.com/api/user.info?handles={handle}",
            timeout=10
        ).json()
        user       = info["result"][0]
        rating     = user.get("rating", 0)
        max_rating = user.get("maxRating", 0)
        rank       = user.get("rank", "unrated").title()

        subs = requests.get(
            f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=10000",
            timeout=20
        ).json()
        solved = set()
        for sub in subs["result"]:
            if sub["verdict"] == "OK":
                p = sub["problem"]
                solved.add(f"{p.get('contestId', '')}{p['index']}")
        return {"handle": handle, "rating": rating,
                "max_rating": max_rating, "rank": rank, "solved": len(solved)}
    except Exception as e:
        print(f"[Codeforces] Error for {handle}: {e}")
        return {"handle": handle, "rating": 0, "max_rating": 0,
                "rank": "Unrated", "solved": 0}


# ──────────── CODECHEF ───────────────
def get_codechef_stats(username):
    try:
        resp = requests.get(
            f"https://www.codechef.com/users/{username}",
            headers=HEADERS, timeout=15
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        full_text = soup.get_text()

        # Rating
        rating_el = soup.find("div", class_="rating-number")
        rating = rating_el.text.strip() if rating_el else "0"

        # Stars
        stars_el = soup.find("span", class_="rating")
        stars = stars_el.text.strip() if stars_el else ""

        # Total solved — "Total Problems Solved: N" appears in page text
        solved = 0
        m = re.search(r"Total Problems Solved:\s*(\d+)", full_text)
        if m:
            solved = int(m.group(1))
        else:
            # Fallback: section with "Fully Solved"
            m2 = re.search(r"Fully Solved[^\d]*(\d+)", full_text)
            if m2:
                solved = int(m2.group(1))

        return {"username": username, "rating": rating,
                "stars": stars, "solved": solved}
    except Exception as e:
        print(f"[CodeChef] Error for {username}: {e}")
        return {"username": username, "rating": "0", "stars": "", "solved": 0}


# ──────────── ATCODER ────────────────
def get_atcoder_stats(username):
    try:
        # Contest history (rating)
        hist = requests.get(
            f"https://atcoder.jp/users/{username}/history/json",
            headers=HEADERS, timeout=10
        ).json()
        current_rating = hist[-1]["NewRating"] if hist else 0
        max_rating     = max(h["NewRating"] for h in hist) if hist else 0
        contests       = len(hist)

        # Accepted problem count via AtCoder Problems API (v2)
        ac_resp = requests.get(
            f"https://kenkoooo.com/atcoder/atcoder-api/v2/user_info?user={username}",
            headers=HEADERS, timeout=10
        ).json()
        solved = ac_resp.get("accepted_count", 0)

        return {"username": username, "rating": current_rating,
                "max_rating": max_rating, "contests": contests, "solved": solved}
    except Exception as e:
        print(f"[AtCoder] Error for {username}: {e}")
        return {"username": username, "rating": 0,
                "max_rating": 0, "contests": 0, "solved": 0}


# ──────────── CSES & GFG ─────────────
# CSES requires login to view stats — values are read from config constants above.
# To update: change CSES_SOLVED / GFG_SOLVED at the top of this file, commit,
# and the GitHub Action will write them into the README automatically.


# ──────────── HELPERS ────────────────
def cf_rank_label(rating):
    if   rating >= 3000: return "👑 Legendary GM"
    elif rating >= 2600: return "🔴 Int. Grandmaster"
    elif rating >= 2400: return "🔴 Grandmaster"
    elif rating >= 2300: return "🔴 Int. Master"
    elif rating >= 2100: return "🟠 Master"
    elif rating >= 1900: return "🟣 Candidate Master"
    elif rating >= 1600: return "🔵 Expert"
    elif rating >= 1400: return "🩵 Specialist"
    elif rating >= 1200: return "🟢 Pupil"
    else:                return "⚫ Newbie"

def atcoder_rank_label(rating):
    if   rating >= 2800: return "🔴 Red"
    elif rating >= 2400: return "🟠 Orange"
    elif rating >= 2000: return "🟡 Yellow"
    elif rating >= 1600: return "🔵 Blue"
    elif rating >= 1200: return "🩵 Cyan"
    elif rating >= 800:  return "🟢 Green"
    elif rating >= 400:  return "🟤 Brown"
    else:                return "⚫ Gray"


# ──────────── SVG & MARKDOWN GENERATOR ─
def generate_svg_and_markdown(lc_stats, cf_stats, cc_stats, at_stats):
    now = datetime.datetime.utcnow().strftime("%b %d, %Y · %H:%M UTC")

    lc_total    = sum(s["total"]  for s in lc_stats)
    cf_total    = sum(s["solved"] for s in cf_stats)
    cc_total    = cc_stats["solved"]
    at_total    = at_stats["solved"]
    cses_total  = CSES_SOLVED
    gfg_total   = GFG_SOLVED
    grand_total = lc_total + cf_total + cc_total + at_total + cses_total + gfg_total

    best_cf     = max(s["max_rating"] for s in cf_stats)

    svg = f"""<svg width="495" height="290" viewBox="0 0 495 290" fill="none" xmlns="http://www.w3.org/2000/svg">
<style>
  .title {{ font: 600 18px 'Segoe UI', Ubuntu, Sans-Serif; fill: #70a5fd; }}
  .label {{ font: 400 13px 'Segoe UI', Ubuntu, Sans-Serif; fill: #adbac7; }}
  .value {{ font: 700 13px 'Segoe UI', Ubuntu, Sans-Serif; fill: #e3b341; }}
  .header {{ font: 600 12px 'Segoe UI', Ubuntu, Sans-Serif; fill: #8b949e; text-transform: uppercase; letter-spacing: 0.5px; }}
  .total-label {{ font: 700 15px 'Segoe UI', Ubuntu, Sans-Serif; fill: #f47067; }}
  .total-value {{ font: 800 18px 'Segoe UI', Ubuntu, Sans-Serif; fill: #57ab5a; }}
  .icon {{ font: 400 14px 'Segoe UI Emoji', 'Apple Color Emoji', Sans-Serif; }}
</style>

<rect x="0.5" y="0.5" width="494" height="289" rx="6" fill="#0d1117" stroke="#30363d" stroke-width="1"/>

<!-- Title -->
<text x="25" y="32" class="title">🏆 Competitive Programming Stats</text>
<text x="25" y="48" class="header">Auto-updated · {now}</text>

<!-- Column Headers -->
<text x="28" y="78" class="header">Platform</text>
<text x="158" y="78" class="header">Handle(s)</text>
<text x="310" y="78" class="header">Max Rating</text>
<text x="430" y="78" class="header">Solved</text>
<line x1="25" y1="86" x2="470" y2="86" stroke="#21262d" stroke-width="1"/>

<!-- LeetCode -->
<text x="28" y="112" class="icon">🟡</text>
<text x="48" y="112" class="label">LeetCode</text>
<text x="158" y="112" class="label">{', '.join(s['username'] for s in lc_stats)}</text>
<text x="310" y="112" class="label">1919 (Knight)</text>
<text x="430" y="112" class="value">{lc_total}</text>

<!-- Codeforces -->
<text x="28" y="140" class="icon">🔵</text>
<text x="48" y="140" class="label">Codeforces</text>
<text x="158" y="140" class="label">{', '.join(s['handle'] for s in cf_stats)}</text>
<text x="310" y="140" class="label">{best_cf} ({cf_rank_label(best_cf).split()[-1]})</text>
<text x="430" y="140" class="value">{cf_total}</text>

<!-- CodeChef -->
<text x="28" y="168" class="icon">🟠</text>
<text x="48" y="168" class="label">CodeChef</text>
<text x="158" y="168" class="label">hackker_69</text>
<text x="310" y="168" class="label">{cc_stats['rating']} ({cc_stats['stars']})</text>
<text x="430" y="168" class="value">{cc_total}</text>

<!-- AtCoder -->
<text x="28" y="196" class="icon">🔴</text>
<text x="48" y="196" class="label">AtCoder</text>
<text x="158" y="196" class="label">krishnnna</text>
<text x="310" y="196" class="label">{at_stats['max_rating']} ({atcoder_rank_label(at_stats['max_rating']).split()[-1]})</text>
<text x="430" y="196" class="value">{at_total}</text>

<!-- CSES & Others -->
<text x="28" y="224" class="icon">🌐</text>
<text x="48" y="224" class="label">CSES &amp; Others</text>
<text x="158" y="224" class="label">—</text>
<text x="310" y="224" class="label">—</text>
<text x="430" y="224" class="value">{cses_total + gfg_total}</text>

<line x1="25" y1="240" x2="470" y2="240" stroke="#21262d" stroke-width="1"/>

<!-- Grand Total -->
<text x="28" y="270" class="total-label">⚡ Grand Total</text>
<text x="420" y="270" class="total-value">{grand_total}</text>

</svg>"""

    svg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cp_stats.svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"✅ Generated {svg_path}")

    # Build clickable profile badges below the SVG
    lc_badges = " ".join([f'[![{s["username"]}](https://img.shields.io/badge/LC-{s["username"]}-FFA116?style=flat&logo=leetcode&logoColor=white)](https://leetcode.com/{s["username"]})' for s in lc_stats])
    cf_badges = " ".join([f'[![{s["handle"]}](https://img.shields.io/badge/CF-{s["handle"]}-1F8ACB?style=flat&logo=codeforces&logoColor=white)](https://codeforces.com/profile/{s["handle"]})' for s in cf_stats])

    md = f"""<!-- COMBINED_STATS_START -->
<div align="center">
  <img src="cp_stats.svg" alt="Competitive Programming Stats" />
  <br/><br/>
  {lc_badges}
  {cf_badges}
  [![CodeChef](https://img.shields.io/badge/CC-hackker__69-5B4638?style=flat&logo=codechef&logoColor=white)](https://www.codechef.com/users/hackker_69)
  [![AtCoder](https://img.shields.io/badge/AC-krishnnna-222222?style=flat&logo=atcoder&logoColor=white)](https://atcoder.jp/users/krishnnna)
  [![CSES](https://img.shields.io/badge/CSES-338950-1a1a2e?style=flat)](https://cses.fi/problemset/user/338950/)
</div>
<!-- COMBINED_STATS_END -->"""

    return md


# ──────────── README UPDATER ─────────
def update_readme(markdown):
    readme_path = "README.md"
    if not os.path.exists(readme_path):
        print("⚠️  README.md not found in current directory!")
        return

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"<!-- COMBINED_STATS_START -->.*?<!-- COMBINED_STATS_END -->"
    if re.search(pattern, content, re.DOTALL):
        new_content = re.sub(pattern, markdown, content, flags=re.DOTALL)
    else:
        new_content = content + "\n\n" + markdown

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("✅ README.md updated!")


# ──────────── MAIN ───────────────────
if __name__ == "__main__":
    print("🔄 Fetching LeetCode stats...")
    lc_stats = [get_leetcode_stats(u) for u in LEETCODE_ACCOUNTS]

    print("🔄 Fetching Codeforces stats...")
    cf_stats = [get_codeforces_stats(h) for h in CODEFORCES_ACCOUNTS]

    print("🔄 Fetching CodeChef stats...")
    cc_stats = get_codechef_stats(CODECHEF_ACCOUNT)

    print("🔄 Fetching AtCoder stats...")
    at_stats = get_atcoder_stats(ATCODER_ACCOUNT)

    print("\n📊 Summary:")
    for s in lc_stats:
        print(f"  LC  [{s['username']}]: {s['total']} solved")
    for s in cf_stats:
        print(f"  CF  [{s['handle']}]:  {s['solved']} solved, rating {s['rating']}")
    print(f"  CC  [{cc_stats['username']}]:   {cc_stats['solved']} solved, {cc_stats['rating']}")
    print(f"  AT  [{at_stats['username']}]:  {at_stats['solved']} solved, {at_stats['rating']}")
    print(f"  CSES [338950]: {CSES_SOLVED} solved (hardcoded)")
    print(f"  GFG  [config]: {GFG_SOLVED} solved (hardcoded)")

    markdown = generate_svg_and_markdown(lc_stats, cf_stats, cc_stats, at_stats)
    # The README paths might be relative, ensure we act from the root
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    update_readme(markdown)
