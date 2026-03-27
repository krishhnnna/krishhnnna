import base64

def generate_custom_card():
    # Tokyonight colors
    bg = "#1a1b27"
    border = "#383e59"
    text_color = "#c0caf5"
    title_color = "#7aa2f7"
    accent_color = "#bb9af7"
    val_color = "#9ece6a"

    # SVG geometry
    width = 450
    height = 250
    
    # We will embed the logo base64 if needed, but for now we won't strictly need logos
    # Or we can just use simple emojis: 🟢 🟡 🔴 🔵 🟠
    
    svg = f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none" xmlns="http://www.w3.org/2000/svg">
    <style>
        .title {{ font: 600 18px 'Segoe UI', Ubuntu, Sans-Serif; fill: {title_color}; }}
        .label {{ font: 400 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: {text_color}; }}
        .value {{ font: 600 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: {val_color}; }}
        .header {{ font: 600 13px 'Segoe UI', Ubuntu, Sans-Serif; fill: {accent_color}; }}
        a {{ cursor: pointer; }}
        a:hover .label {{ text-decoration: underline; }}
    </style>
    
    <rect x="0.5" y="0.5" width="{width-1}" height="{height-1}" rx="8" fill="{bg}" stroke="{border}" stroke-width="1"/>
    
    <!-- Title -->
    <text x="25" y="35" class="title">🏆 Combined Competitive Programming</text>

    <!-- Column Headers -->
    <text x="30" y="70" class="header">Platform</text>
    <text x="130" y="70" class="header">ID</text>
    <text x="270" y="70" class="header">Rating/Max</text>
    <text x="380" y="70" class="header">Solved</text>
    <line x1="25" y1="80" x2="425" y2="80" stroke="{border}" stroke-width="1"/>

    <!-- LeetCode -->
    <text x="30" y="105" class="label">🟡 LeetCode</text>
    <a href="https://leetcode.com/wtffff__" target="_blank"><text x="130" y="105" class="label">wtffff__, Hackker_69</text></a>
    <text x="270" y="105" class="label">1919 (Knight)</text>
    <text x="380" y="105" class="value">417</text>

    <!-- Codeforces -->
    <text x="30" y="130" class="label">🔵 Codeforces</text>
    <a href="https://codeforces.com/profile/krishnnna" target="_blank"><text x="130" y="130" class="label">Hackker_69, krishnnna</text></a>
    <text x="270" y="130" class="label">1623 (Expert)</text>
    <text x="380" y="130" class="value">358</text>

    <!-- CodeChef -->
    <text x="30" y="155" class="label">🟠 CodeChef</text>
    <a href="https://www.codechef.com/users/hackker_69" target="_blank"><text x="130" y="155" class="label">hackker_69</text></a>
    <text x="270" y="155" class="label">1536 (2★)</text>
    <text x="380" y="155" class="value">45</text>

    <!-- AtCoder -->
    <text x="30" y="180" class="label">🔴 AtCoder</text>
    <a href="https://atcoder.jp/users/krishnnna" target="_blank"><text x="130" y="180" class="label">krishnnna</text></a>
    <text x="270" y="180" class="label">747 (Brown)</text>
    <text x="380" y="180" class="value">96</text>

    <!-- CSES & Others -->
    <text x="30" y="205" class="label">🌐 CSES &amp; GFG</text>
    <a href="https://cses.fi/problemset/user/338950/" target="_blank"><text x="130" y="205" class="label">338950, krishhnnna</text></a>
    <text x="270" y="205" class="label">—</text>
    <text x="380" y="205" class="value">102</text>

    <line x1="25" y1="220" x2="425" y2="220" stroke="{border}" stroke-width="1"/>

    <!-- Grand Total -->
    <text x="30" y="240" class="title" fill="#f7768e">⚡ Grand Total</text>
    <text x="380" y="240" class="value" style="font-size: 16px;">1018</text>

</svg>"""
    with open("cp_stats.svg", "w") as f:
        f.write(svg)
    print("Generated cp_stats.svg")

if __name__ == "__main__":
    generate_custom_card()
