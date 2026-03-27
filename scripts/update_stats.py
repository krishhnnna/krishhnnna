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
CSES_ACCOUNT        = "krishnannnna"   # set to "" to disable
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


# ──────────── CSES ───────────────────
def get_cses_stats(username):
    if not username:
        return {"username": "", "solved": 0}
    try:
        resp = requests.get(
            f"https://cses.fi/user/{username}",
            headers=HEADERS, timeout=10
        )
        if resp.status_code == 404:
            print(f"[CSES] Profile not found for '{username}'. Make sure the username is correct.")
            return {"username": username, "solved": 0, "not_found": True}

        soup = BeautifulSoup(resp.text, "html.parser")
        solved = 0
        text = soup.get_text()
        # Matches patterns like "200 / 300 tasks"
        matches = re.findall(r"(\d+)\s*/\s*\d+\s*tasks?", text, re.IGNORECASE)
        if matches:
            solved = sum(int(x) for x in matches)
        return {"username": username, "solved": solved, "not_found": False}
    except Exception as e:
        print(f"[CSES] Error for {username}: {e}")
        return {"username": username, "solved": 0, "not_found": False}


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


# ──────────── MARKDOWN GENERATOR ─────
def generate_markdown(lc_stats, cf_stats, cc_stats, at_stats, cses_stats):
    now = datetime.datetime.utcnow().strftime("%b %d, %Y · %H:%M UTC")

    lc_total    = sum(s["total"]  for s in lc_stats)
    lc_easy     = sum(s["easy"]   for s in lc_stats)
    lc_medium   = sum(s["medium"] for s in lc_stats)
    lc_hard     = sum(s["hard"]   for s in lc_stats)
    cf_total    = sum(s["solved"] for s in cf_stats)
    cc_total    = cc_stats["solved"]
    at_total    = at_stats["solved"]
    cses_total  = cses_stats["solved"]
    grand_total = lc_total + cf_total + cc_total + at_total + cses_total

    best_cf     = max(s["max_rating"] for s in cf_stats)
    best_cf_h   = max(cf_stats, key=lambda s: s["max_rating"])

    cses_note = ""
    if cses_stats.get("not_found"):
        cses_note = " ⚠️"

    md = f"""<!-- COMBINED_STATS_START -->
<div align="center">

## 🏆 Competitive Programming

*Auto-updated daily &nbsp;·&nbsp; {now}*

</div>

---

### ⚡ Total: `{grand_total}` problems solved across 5 platforms

<div align="center">

| | 🟡 LeetCode | 🔵 Codeforces | 🟠 CodeChef | 🔴 AtCoder | 🟢 CSES |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Solved** | **{lc_total}** | **{cf_total}** | **{cc_total}** | **{at_total}** | **{cses_total}{cses_note}** |
| **Best Rating** | 1919 | {best_cf} | {cc_stats["rating"]} | {at_stats["max_rating"]} | — |
| **Rank/Title** | ⚔️ Knight | {cf_rank_label(best_cf)} | {cc_stats["stars"]} | {atcoder_rank_label(at_stats["max_rating"])} | — |

</div>

---

### 🟡 LeetCode

<div align="center">

| Account | Total | 🟢 Easy | 🟡 Medium | 🔴 Hard |
|:---:|:---:|:---:|:---:|:---:|"""

    for s in lc_stats:
        md += f"\n| [`{s['username']}`](https://leetcode.com/{s['username']}) | **{s['total']}** | {s['easy']} | {s['medium']} | {s['hard']} |"

    md += f"\n| **Combined** | **{lc_total}** | {lc_easy} | {lc_medium} | {lc_hard} |"

    md += f"""

</div>

---

### 🔵 Codeforces

<div align="center">

| Handle | ✅ Solved | Current | Max | Rank |
|:---:|:---:|:---:|:---:|:---:|"""

    for s in cf_stats:
        md += f"\n| [`{s['handle']}`](https://codeforces.com/profile/{s['handle']}) | **{s['solved']}** | {s['rating']} | {s['max_rating']} | {s['rank']} |"

    md += f"\n| **Combined** | **{cf_total}** | — | **{best_cf}** | {cf_rank_label(best_cf)} |"

    md += f"""

</div>

---

### 🟠 CodeChef &nbsp;·&nbsp; 🔴 AtCoder &nbsp;·&nbsp; 🟢 CSES

<div align="center">

| Platform | Handle | ✅ Solved | 📈 Rating | 🏅 Rank |
|:---:|:---:|:---:|:---:|:---:|
| 🟠 [CodeChef](https://www.codechef.com/users/hackker_69) | `hackker_69` | **{cc_total}** | {cc_stats["rating"]} | {cc_stats["stars"]} |
| 🔴 [AtCoder](https://atcoder.jp/users/krishnnna) | `krishnnna` | **{at_total}** | {at_stats["rating"]} (Max: {at_stats["max_rating"]}) | {atcoder_rank_label(at_stats["max_rating"])} |
| 🟢 [CSES](https://cses.fi/user/{CSES_ACCOUNT}) | `{CSES_ACCOUNT}` | **{cses_total}{cses_note}** | — | — |

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

    print("🔄 Fetching CSES stats...")
    cses_stats = get_cses_stats(CSES_ACCOUNT)

    print("\n📊 Summary:")
    for s in lc_stats:
        print(f"  LC  [{s['username']}]: {s['total']} solved")
    for s in cf_stats:
        print(f"  CF  [{s['handle']}]:  {s['solved']} solved, rating {s['rating']}")
    print(f"  CC  [{cc_stats['username']}]:   {cc_stats['solved']} solved, {cc_stats['rating']}")
    print(f"  AT  [{at_stats['username']}]:  {at_stats['solved']} solved, {at_stats['rating']}")
    print(f"  CSES[{cses_stats['username']}]: {cses_stats['solved']} solved")

    markdown = generate_markdown(lc_stats, cf_stats, cc_stats, at_stats, cses_stats)
    update_readme(markdown)
