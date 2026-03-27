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

    gfg_user = GFG_USERNAME if GFG_USERNAME else "krishhnnna"

    svg = f"""<svg width="600" height="300" viewBox="0 0 600 300" fill="none" xmlns="http://www.w3.org/2000/svg">
    <style>
        .title {{ font: 600 18px 'Segoe UI', Ubuntu, Sans-Serif; fill: #7aa2f7; }}
        .label {{ font: 400 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: #c0caf5; }}
        .value {{ font: 600 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: #9ece6a; }}
        .header {{ font: 600 13px 'Segoe UI', Ubuntu, Sans-Serif; fill: #bb9af7; }}
        a {{ cursor: pointer; }}
        a:hover .label {{ text-decoration: underline; }}
    </style>
    
    <rect x="0.5" y="0.5" width="599" height="299" rx="8" fill="#1a1b27" stroke="#383e59" stroke-width="1"/>
    
    <text x="25" y="35" class="title">🏆 Combined Competitive Programming</text>

    <text x="30" y="70" class="header">Platform</text>
    <text x="150" y="70" class="header">Profiles</text>
    <text x="360" y="70" class="header">Rating (Max)</text>
    <text x="490" y="70" class="header">Solved</text>
    <line x1="25" y1="80" x2="575" y2="80" stroke="#383e59" stroke-width="1"/>

    <!-- LeetCode -->
    <text x="30" y="110" class="label">🟡 LeetCode</text>
    <a href="https://leetcode.com/wtffff__" target="_blank"><text x="150" y="110" class="label">wtffff__, Hackker_69</text></a>
    <text x="360" y="110" class="label">1919 (Knight)</text>
    <text x="490" y="110" class="value">{lc_total}</text>

    <!-- Codeforces -->
    <text x="30" y="140" class="label">🔵 Codeforces</text>
    <a href="https://codeforces.com/profile/krishnnna" target="_blank"><text x="150" y="140" class="label">Hackker_69, krishnnna</text></a>
    <text x="360" y="140" class="label">{best_cf} ({cf_rank_label(best_cf).split()[-1]})</text>
    <text x="490" y="140" class="value">{cf_total}</text>

    <!-- CodeChef -->
    <text x="30" y="170" class="label">🟠 CodeChef</text>
    <a href="https://www.codechef.com/users/hackker_69" target="_blank"><text x="150" y="170" class="label">hackker_69</text></a>
    <text x="360" y="170" class="label">{cc_stats["rating"]} ({cc_stats["stars"]})</text>
    <text x="490" y="170" class="value">{cc_total}</text>

    <!-- AtCoder -->
    <text x="30" y="200" class="label">🔴 AtCoder</text>
    <a href="https://atcoder.jp/users/krishnnna" target="_blank"><text x="150" y="200" class="label">krishnnna</text></a>
    <text x="360" y="200" class="label">{at_stats["rating"]} ({atcoder_rank_label(at_stats["max_rating"]).split()[-1]})</text>
    <text x="490" y="200" class="value">{at_total}</text>

    <!-- CSES & Others -->
    <text x="30" y="230" class="label">🌐 CSES &amp; GFG</text>
    <a href="https://cses.fi/problemset/user/338950/" target="_blank"><text x="150" y="230" class="label">338950, {gfg_user}</text></a>
    <text x="360" y="230" class="label">—</text>
    <text x="490" y="230" class="value">{cses_total + gfg_total}</text>

    <line x1="25" y1="245" x2="575" y2="245" stroke="#383e59" stroke-width="1"/>

    <!-- Grand Total -->
    <text x="30" y="275" class="title" fill="#f7768e">⚡ Grand Total</text>
    <text x="490" y="275" class="value" style="font-size: 16px;">{grand_total}</text>

</svg>"""

    import os
    svg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cp_stats.svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"✅ Generated {svg_path}")

    # Use a cache-busting timestamp param to ensure GitHub updates the SVG image when refreshed
    timestamp = datetime.datetime.utcnow().strftime('%s')
    
    md = f"""<!-- COMBINED_STATS_START -->
<div align="center">
  <img src="cp_stats.svg?t={timestamp}" alt="Combined Competitive Programming Stats" />
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
