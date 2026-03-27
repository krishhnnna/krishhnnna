import requests
import datetime
import re
import os
from bs4 import BeautifulSoup

# ─────────────── CONFIG ───────────────
LEETCODE_ACCOUNTS  = ["wtffff__", "Hackker_69"]
CODEFORCES_ACCOUNTS = ["Hackker_69", "krishnnna"]
CODECHEF_ACCOUNT   = "hackker_69"
ATCODER_ACCOUNT    = "krishnnna"
CSES_ACCOUNT       = "krishnannnna"
# ──────────────────────────────────────

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; readme-stats-bot/1.0)"}


# ──────────── LEETCODE ────────────────
def get_leetcode_stats(username):
    url = "https://leetcode.com/graphql"
    query = """
    query getUserProfile($username: String!) {
        matchedUser(username: $username) {
            profile { ranking }
            submitStats {
                acSubmissionNum {
                    difficulty
                    count
                }
            }
        }
    }
    """
    try:
        resp = requests.post(
            url,
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
        ranking = data["profile"]["ranking"]
        return {"username": username, "total": total,
                "easy": easy, "medium": medium, "hard": hard, "ranking": ranking}
    except Exception as e:
        print(f"[LeetCode] Error for {username}: {e}")
        return {"username": username, "total": 0, "easy": 0,
                "medium": 0, "hard": 0, "ranking": "N/A"}


# ──────────── CODEFORCES ──────────────
def get_codeforces_stats(handle):
    try:
        info = requests.get(
            f"https://codeforces.com/api/user.info?handles={handle}",
            timeout=10
        ).json()
        user = info["result"][0]
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
                solved.add(f"{p.get('contestId','')}{p['index']}")
        return {"handle": handle, "rating": rating,
                "max_rating": max_rating, "rank": rank, "solved": len(solved)}
    except Exception as e:
        print(f"[Codeforces] Error for {handle}: {e}")
        return {"handle": handle, "rating": 0, "max_rating": 0,
                "rank": "Unrated", "solved": 0}


# ──────────── CODECHEF ────────────────
def get_codechef_stats(username):
    try:
        resp = requests.get(
            f"https://www.codechef.com/users/{username}",
            headers=HEADERS, timeout=15
        )
        soup = BeautifulSoup(resp.text, "html.parser")

        rating_el = soup.find("div", class_="rating-number")
        rating = rating_el.text.strip() if rating_el else "0"

        stars_el = soup.find("span", class_="rating")
        stars = stars_el.text.strip() if stars_el else "?"

        # Fully solved count
        solved = 0
        section = soup.find("section", class_="rating-data-section problems-solved")
        if section:
            h3s = section.find_all("h3")
            for h3 in h3s:
                if "Fully Solved" in h3.text:
                    nums = re.findall(r"\d+", h3.text)
                    if nums:
                        solved = int(nums[0])
                    break

        return {"username": username, "rating": rating,
                "stars": stars, "solved": solved}
    except Exception as e:
        print(f"[CodeChef] Error for {username}: {e}")
        return {"username": username, "rating": "0", "stars": "?", "solved": 0}


# ──────────── ATCODER ─────────────────
def get_atcoder_stats(username):
    try:
        hist = requests.get(
            f"https://atcoder.jp/users/{username}/history/json",
            headers=HEADERS, timeout=10
        ).json()

        if hist:
            current_rating = hist[-1]["NewRating"]
            max_rating     = max(h["NewRating"] for h in hist)
            contests       = len(hist)
        else:
            current_rating = max_rating = contests = 0

        # AtCoder Problems API (kenkoooo.com) for accepted problem count
        try:
            ac_resp = requests.get(
                f"https://kenkoooo.com/atcoder/atcoder-api/v3/user/acceptance_count?user={username}",
                headers=HEADERS, timeout=10
            ).json()
            # Returns list of {problem_id, epoch_second}
            solved = len(ac_resp) if isinstance(ac_resp, list) else 0
        except Exception:
            solved = 0

        return {"username": username, "rating": current_rating,
                "max_rating": max_rating, "contests": contests, "solved": solved}
    except Exception as e:
        print(f"[AtCoder] Error for {username}: {e}")
        return {"username": username, "rating": 0,
                "max_rating": 0, "contests": 0, "solved": 0}


# ──────────── CSES ────────────────────
def get_cses_stats(username):
    try:
        resp = requests.get(
            f"https://cses.fi/user/{username}",
            headers=HEADERS, timeout=10
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        solved = 0
        # CSES profile page shows task counts in various sections
        for el in soup.find_all(["p", "span", "div", "td"]):
            text = el.get_text(strip=True)
            # Look for patterns like "X / Y tasks"
            m = re.search(r"(\d+)\s*/\s*\d+\s*tasks?", text, re.IGNORECASE)
            if m:
                solved = max(solved, int(m.group(1)))
        return {"username": username, "solved": solved}
    except Exception as e:
        print(f"[CSES] Error for {username}: {e}")
        return {"username": username, "solved": 0}


# ──────────── HELPERS ─────────────────
def cf_rank_label(rating):
    if   rating >= 3000: return "👑 Legendary GM"
    elif rating >= 2600: return "🔴 International GM"
    elif rating >= 2400: return "🔴 Grandmaster"
    elif rating >= 2300: return "🔴 International Master"
    elif rating >= 2100: return "🟠 Master"
    elif rating >= 1900: return "🟣 Candidate Master"
    elif rating >= 1600: return "🔵 Expert"
    elif rating >= 1400: return "🩵 Specialist"
    elif rating >= 1200: return "🟢 Pupil"
    else:                return "⚫ Newbie"


# ──────────── MARKDOWN GENERATOR ──────
def generate_markdown(lc_stats, cf_stats, cc_stats, at_stats, cses_stats):
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    lc_total   = sum(s["total"]  for s in lc_stats)
    lc_easy    = sum(s["easy"]   for s in lc_stats)
    lc_medium  = sum(s["medium"] for s in lc_stats)
    lc_hard    = sum(s["hard"]   for s in lc_stats)
    cf_total   = sum(s["solved"] for s in cf_stats)
    cc_total   = cc_stats["solved"]
    at_total   = at_stats["solved"]
    cses_total = cses_stats["solved"]
    grand_total = lc_total + cf_total + cc_total + at_total + cses_total

    best_cf_rating = max(s["max_rating"] for s in cf_stats)

    md = f"""<!-- COMBINED_STATS_START -->
## 🏆 Competitive Programming Stats

> 🤖 Auto-updated daily &nbsp;|&nbsp; Last sync: `{now}`

---

### 🌐 Grand Total — `{grand_total}` Problems Solved

<div align="center">

| Platform | Accounts | ✅ Solved | 📈 Best Rating |
|:---:|:---:|:---:|:---:|
| 🟡 **LeetCode** | `wtffff__` + `Hackker_69` | **{lc_total}** | 1919 ⚔️ Knight |
| 🔵 **Codeforces** | `Hackker_69` + `krishnnna` | **{cf_total}** | {best_cf_rating} · {cf_rank_label(best_cf_rating)} |
| 🟠 **CodeChef** | `hackker_69` | **{cc_total}** | {cc_stats["rating"]} {cc_stats["stars"]} |
| 🔴 **AtCoder** | `krishnnna` | **{at_total}** | {at_stats["max_rating"]} (Max) |
| 🟢 **CSES** | `krishnannnna` | **{cses_total}** | — |
| | 🏆 **Grand Total** | **{grand_total}** | |

</div>

---

### 🟡 LeetCode — Both Accounts Combined

<div align="center">

| Account | Total | 🟢 Easy | 🟡 Medium | 🔴 Hard |
|:---:|:---:|:---:|:---:|:---:|"""

    for s in lc_stats:
        md += f"\n| `{s['username']}` | **{s['total']}** | {s['easy']} | {s['medium']} | {s['hard']} |"

    md += f"\n| ✨ **Combined** | **{lc_total}** | {lc_easy} | {lc_medium} | {lc_hard} |"

    md += f"""

</div>

---

### 🔵 Codeforces — Both Accounts Combined

<div align="center">

| Handle | ✅ Solved | Rating | Max Rating | Rank |
|:---:|:---:|:---:|:---:|:---:|"""

    for s in cf_stats:
        md += f"\n| `{s['handle']}` | **{s['solved']}** | {s['rating']} | {s['max_rating']} | {s['rank']} |"

    md += f"\n| ✨ **Combined** | **{cf_total}** | — | {best_cf_rating} | {cf_rank_label(best_cf_rating)} |"

    md += f"""

</div>

---

### 🟠 CodeChef &nbsp;·&nbsp; 🔴 AtCoder &nbsp;·&nbsp; 🟢 CSES

<div align="center">

| Platform | Account | ✅ Solved | 📈 Rating |
|:---:|:---:|:---:|:---:|
| 🟠 CodeChef | `hackker_69` | **{cc_total}** | {cc_stats["rating"]} {cc_stats["stars"]} |
| 🔴 AtCoder | `krishnnna` | **{at_total}** | {at_stats["rating"]} (Max: {at_stats["max_rating"]}) |
| 🟢 CSES | `krishnannnna` | **{cses_total}** | — |

</div>

<!-- COMBINED_STATS_END -->"""

    return md


# ──────────── README UPDATER ──────────
def update_readme(markdown):
    readme_path = "README.md"
    if not os.path.exists(readme_path):
        print("README.md not found in current directory!")
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

    print("✅ README.md updated successfully!")


# ──────────── MAIN ────────────────────
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

    print("\n📊 Stats Summary:")
    for s in lc_stats:
        print(f"  LeetCode  [{s['username']}]: {s['total']} solved")
    for s in cf_stats:
        print(f"  Codeforces [{s['handle']}]: {s['solved']} solved, rating {s['rating']}")
    print(f"  CodeChef  [{cc_stats['username']}]: {cc_stats['solved']} solved, {cc_stats['rating']}")
    print(f"  AtCoder   [{at_stats['username']}]: {at_stats['solved']} solved, {at_stats['rating']}")
    print(f"  CSES      [{cses_stats['username']}]: {cses_stats['solved']} solved")

    markdown = generate_markdown(lc_stats, cf_stats, cc_stats, at_stats, cses_stats)
    update_readme(markdown)
