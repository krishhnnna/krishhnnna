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

    svg = f"""<svg width="600" height="300" viewBox="0 0 600 300" fill="none" xmlns="http://www.w3.org/2000/svg">
    <style>
        .title {{ font: 600 18px 'Segoe UI', Ubuntu, Sans-Serif; fill: #7aa2f7; }}
        .label {{ font: 400 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: #c0caf5; }}
        .value {{ font: 600 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: #9ece6a; }}
        .header {{ font: 600 13px 'Segoe UI', Ubuntu, Sans-Serif; fill: #bb9af7; }}
        .total-label {{ font: 700 16px 'Segoe UI', Ubuntu, Sans-Serif; fill: #f7768e; }}
        .total-value {{ font: 800 18px 'Segoe UI', Ubuntu, Sans-Serif; fill: #9ece6a; }}
        .rank {{ font: 600 13px 'Segoe UI', Ubuntu, Sans-Serif; }}
    </style>
    
    <rect x="0.5" y="0.5" width="599" height="299" rx="8" fill="#1a1b27" stroke="#383e59" stroke-width="1"/>
    
    <!-- Title -->
    <text x="25" y="35" class="title">🏆 Competitive Programming Stats</text>

    <!-- Column Headers -->
    <text x="50" y="70" class="header">Platform</text>
    <text x="180" y="70" class="header">Profiles</text>
    <text x="370" y="70" class="header">Rating / Rank</text>
    <text x="540" y="70" class="header">Solved</text>
    <line x1="25" y1="80" x2="575" y2="80" stroke="#383e59" stroke-width="1"/>

    <!-- LeetCode icon -->
    <g transform="translate(25, 96) scale(0.65)">
      <path fill="#FFA116" d="M13.483 0a1.374 1.374 0 0 0-.961.438L7.116 6.226l-3.854 4.126a5.266 5.266 0 0 0-1.209 2.104 5.35 5.35 0 0 0-.125.513 5.527 5.527 0 0 0 .062 2.362 5.83 5.83 0 0 0 .349 1.017 5.938 5.938 0 0 0 1.271 1.818l4.277 4.193.039.038c2.248 2.165 5.852 2.133 8.063-.074l2.396-2.392c.54-.54.54-1.414.003-1.955a1.378 1.378 0 0 0-1.951-.003l-2.396 2.392a3.021 3.021 0 0 1-4.205.038l-.02-.019-4.276-4.193c-.652-.64-.972-1.469-.948-2.263a2.68 2.68 0 0 1 .066-.523 2.545 2.545 0 0 1 .619-1.164L9.13 8.114c1.058-1.134 3.204-1.27 4.43-.278l3.501 2.831c.593.48 1.461.387 1.94-.207a1.384 1.384 0 0 0-.207-1.943l-3.5-2.831c-.8-.647-1.766-1.045-2.774-1.202l2.015-2.158A1.384 1.384 0 0 0 13.483 0zm-2.866 12.815a1.38 1.38 0 0 0-1.38 1.382 1.38 1.38 0 0 0 1.38 1.382H20.79a1.38 1.38 0 0 0 1.38-1.382 1.38 1.38 0 0 0-1.38-1.382z"/>
    </g>
    <text x="50" y="110" class="label">LeetCode</text>
    <text x="180" y="110" class="label">{', '.join(s['username'] for s in lc_stats)}</text>
    <text x="370" y="110" class="label">1919</text>
    <text x="420" y="110" class="rank" fill="#e0af68">⚔️ Knight</text>
    <text x="540" y="110" class="value">{lc_total}</text>

    <!-- Codeforces icon -->
    <g transform="translate(25, 126) scale(0.65)">
      <path fill="#1F8ACB" d="M4.5 7.5C5.328 7.5 6 8.172 6 9v10.5c0 .828-.672 1.5-1.5 1.5h-3C.673 21 0 20.328 0 19.5V9c0-.828.673-1.5 1.5-1.5h3zm9-4.5c.828 0 1.5.672 1.5 1.5v15c0 .828-.672 1.5-1.5 1.5h-3c-.827 0-1.5-.672-1.5-1.5v-15c0-.828.673-1.5 1.5-1.5h3zm9 7.5c.828 0 1.5.672 1.5 1.5v7.5c0 .828-.672 1.5-1.5 1.5h-3c-.828 0-1.5-.672-1.5-1.5V12c0-.828.672-1.5 1.5-1.5h3z"/>
    </g>
    <text x="50" y="140" class="label">Codeforces</text>
    <text x="180" y="140" class="label">{', '.join(s['handle'] for s in cf_stats)}</text>
    <text x="370" y="140" class="label">{best_cf}</text>
    <text x="420" y="140" class="rank" fill="#7aa2f7">🔵 {cf_rank_label(best_cf).split()[-1]}</text>
    <text x="540" y="140" class="value">{cf_total}</text>

    <!-- CodeChef icon -->
    <g transform="translate(25, 156) scale(0.65)">
      <path fill="#5B4638" d="M11.2574.0039c-.37.0101-.7353.041-1.1003.095C9.6164.153 9.0766.4236 8.482.694c-.757.3244-1.5147.6486-2.2176.7027-1.1896.3785-1.568.919-1.8925 1.3516 0 .054-.054.1079-.054.1079-.4325.865-.4873 1.73-.325 2.5952.1621.5407.3786 1.0282.5408 1.5148.3785 1.0274.7578 2.0007.92 3.1362.1622.3244.3235.7571.4316 1.1897.2704.8651.542 1.8383 1.353 2.5952l.0057-.0028c.0175.0183.0301.0387.0482.0568.0072-.0036.0141-.0063.0213-.0099l-.0213-.5849c.6489-.9733 1.5673-1.6221 2.865-1.8925.5195-.1093 1.081-.1497 1.6625-.1278a8.7733 8.7733 0 0 1 1.7988.2357c1.4599.3785 2.595 1.1358 2.6492 1.7846.0273.3549.0398.6952.0326 1.0364-.001.064-.0046.1285-.007.193l.1362.0682c.075-.0375.1424-.107.2059-.1902.0008-.001.002-.002.0028-.0028.0018-.0023.0039-.0061.0057-.0085.0396-.0536.0747-.1236.1107-.1931.0188-.0377.0372-.0866.0554-.1292.2048-.4622.362-1.1536.538-1.9635.0541-.2703.1092-.4864.1633-.7027.4326-.9733 1.0266-1.8382 1.6213-2.6492.9733-1.3518 1.8928-2.5962 1.7846-4.0561-1.784-3.4608-4.2718-4.0017-5.5695-4.272-.2163-.0541-.3233-.0539-.4856-.108-1.3382-.2433-2.4945-.3953-3.6046-.3648z"/>
    </g>
    <text x="50" y="170" class="label">CodeChef</text>
    <text x="180" y="170" class="label">hackker_69</text>
    <text x="370" y="170" class="label">{cc_stats['rating']}</text>
    <text x="420" y="170" class="rank" fill="#e0af68">{cc_stats['stars']}</text>
    <text x="540" y="170" class="value">{cc_total}</text>

    <!-- AtCoder icon (simple "A" mark) -->
    <g transform="translate(25, 186) scale(0.65)">
      <circle cx="12" cy="12" r="11" fill="none" stroke="#dc143c" stroke-width="2"/>
      <text x="12" y="17" text-anchor="middle" fill="#dc143c" style="font: bold 14px 'Segoe UI', Sans-Serif;">A</text>
    </g>
    <text x="50" y="200" class="label">AtCoder</text>
    <text x="180" y="200" class="label">krishnnna</text>
    <text x="370" y="200" class="label">{at_stats['max_rating']}</text>
    <text x="420" y="200" class="rank" fill="#bb9af7">{atcoder_rank_label(at_stats['max_rating']).split()[-1]}</text>
    <text x="540" y="200" class="value">{at_total}</text>

    <!-- CSES & Others icon (globe) -->
    <g transform="translate(25, 216) scale(0.65)">
      <circle cx="12" cy="12" r="10" fill="none" stroke="#73daca" stroke-width="1.5"/>
      <ellipse cx="12" cy="12" rx="5" ry="10" fill="none" stroke="#73daca" stroke-width="1.2"/>
      <line x1="2" y1="12" x2="22" y2="12" stroke="#73daca" stroke-width="1.2"/>
      <line x1="12" y1="2" x2="12" y2="22" stroke="#73daca" stroke-width="1.2"/>
    </g>
    <text x="50" y="230" class="label">CSES &amp; Others</text>
    <text x="180" y="230" class="label">—</text>
    <text x="370" y="230" class="label">—</text>
    <text x="540" y="230" class="value">{cses_total + gfg_total}</text>

    <line x1="25" y1="245" x2="575" y2="245" stroke="#383e59" stroke-width="1"/>

    <!-- Grand Total -->
    <text x="30" y="275" class="total-label">⚡ Grand Total</text>
    <text x="520" y="275" class="total-value">{grand_total}</text>

</svg>"""

    svg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cp_stats.svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"✅ Generated {svg_path}")

    # Build clickable profile badges below the SVG (must use HTML inside <div>)
    lc_badges = "\n  ".join([f'<a href="https://leetcode.com/{s["username"]}"><img src="https://img.shields.io/badge/LC-{s["username"]}-FFA116?style=flat&logo=leetcode&logoColor=white" alt="{s["username"]}"/></a>' for s in lc_stats])
    cf_badges = "\n  ".join([f'<a href="https://codeforces.com/profile/{s["handle"]}"><img src="https://img.shields.io/badge/CF-{s["handle"]}-1F8ACB?style=flat&logo=codeforces&logoColor=white" alt="{s["handle"]}"/></a>' for s in cf_stats])

    md = f"""<!-- COMBINED_STATS_START -->
<div align="center">
  <img src="cp_stats.svg" alt="Competitive Programming Stats" />
  <br/><br/>
  {lc_badges}
  {cf_badges}
  <a href="https://www.codechef.com/users/hackker_69"><img src="https://img.shields.io/badge/CC-hackker__69-5B4638?style=flat&logo=codechef&logoColor=white" alt="CodeChef"/></a>
  <a href="https://atcoder.jp/users/krishnnna"><img src="https://img.shields.io/badge/AC-krishnnna-222222?style=flat&logo=atcoder&logoColor=white" alt="AtCoder"/></a>
  <a href="https://cses.fi/problemset/user/338950/"><img src="https://img.shields.io/badge/CSES-338950-1a1a2e?style=flat" alt="CSES"/></a>
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
