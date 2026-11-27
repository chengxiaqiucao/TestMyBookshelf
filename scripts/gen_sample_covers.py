"""生成示例图书封面 SVG（无第三方依赖，浏览器原生渲染）。

输出目录：app/static/covers/
书本封面按书名匹配回填到示例数据（见 database.py 的 SAMPLE_COVERS）。
重复执行会覆盖同名文件，幂等。
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "app" / "static" / "covers"
OUT.mkdir(parents=True, exist_ok=True)

# file, title, author, theme(c1,c2,accent), motif
BOOKS = [
    ("santi.svg",    "三体",       "刘慈欣",        "#0b1d3a", "#1b4f8c", "#7ec8ff", "stars"),
    ("huozhe.svg",   "活着",       "余华",          "#7a2e1d", "#c85a2b", "#ffd9a0", "sun"),
    ("bainian.svg",  "百年孤独",   "加西亚·马尔克斯", "#1d4d3a", "#2f8f63", "#ffe08a", "leaves"),
    ("weicheng.svg", "围城",       "钱钟书",        "#5a1a1a", "#9e3b3b", "#f2c9a0", "wall"),
    ("pingfan.svg",  "平凡的世界", "路遥",          "#3b2c1a", "#8a6d3b", "#f5e0b0", "hills"),
]


def motif_svg(kind, accent):
    if kind == "stars":
        dots = "\n".join(
            f'<circle cx="{60+(i*47)%130}" cy="{40+(i*71)%150}" r="{1.5+(i%3)}" fill="{accent}" opacity="{0.4+(i%4)*0.15:.2f}"/>'
            for i in range(22)
        )
        return (f'<g>{dots}</g>'
                f'<circle cx="150" cy="120" r="46" fill="none" stroke="{accent}" stroke-width="1.5" opacity="0.6"/>'
                f'<circle cx="150" cy="120" r="30" fill="{accent}" opacity="0.12"/>')
    if kind == "sun":
        return (f'<circle cx="150" cy="112" r="52" fill="{accent}" opacity="0.18"/>'
                f'<circle cx="150" cy="112" r="34" fill="{accent}" opacity="0.35"/>'
                f'<path d="M0 250 Q100 200 200 250 V300 H0 Z" fill="{accent}" opacity="0.15"/>')
    if kind == "leaves":
        return (f'<path d="M40 250 Q100 120 175 60" fill="none" stroke="{accent}" stroke-width="2" opacity="0.5"/>'
                f'<path d="M70 210 Q40 170 90 150 Q110 190 70 210" fill="{accent}" opacity="0.18"/>'
                f'<path d="M130 140 Q100 95 155 78 Q170 120 130 140" fill="{accent}" opacity="0.18"/>')
    if kind == "wall":
        rows = "".join(
            f'<rect x="{20+((i%2)*22)}" y="{70+i*26}" width="160" height="22" fill="none" '
            f'stroke="{accent}" stroke-width="1" opacity="0.3"/>'
            for i in range(7)
        )
        return f'<g>{rows}</g>'
    if kind == "hills":
        return (f'<path d="M0 230 Q60 170 120 220 Q170 260 200 200 V300 H0 Z" fill="{accent}" opacity="0.16"/>'
                f'<path d="M0 260 Q70 210 140 250 Q175 270 200 240 V300 H0 Z" fill="{accent}" opacity="0.26"/>')
    return ""


def make_svg(title, author, c1, c2, accent, kind):
    motif = motif_svg(kind, accent)
    title_size = 34 if len(title) <= 4 else 28
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="200" height="300" viewBox="0 0 200 300">
<defs>
 <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/>
 </linearGradient>
</defs>
<rect width="200" height="300" rx="8" fill="url(#bg)"/>
{motif}
<rect x="10" y="10" width="180" height="280" rx="4" fill="none" stroke="{accent}" stroke-width="1" opacity="0.45"/>
<text x="100" y="46" text-anchor="middle" font-family="'Microsoft YaHei','PingFang SC',sans-serif"
      font-size="11" letter-spacing="3" fill="{accent}" opacity="0.85">经典藏书</text>
<line x1="55" y1="58" x2="145" y2="58" stroke="{accent}" stroke-width="1" opacity="0.5"/>
<text x="100" y="205" text-anchor="middle" font-family="'Microsoft YaHei','PingFang SC',sans-serif"
      font-size="{title_size}" font-weight="bold" fill="#ffffff">{title}</text>
<text x="100" y="238" text-anchor="middle" font-family="'Microsoft YaHei','PingFang SC',sans-serif"
      font-size="12" fill="{accent}">{author}</text>
</svg>
'''


if __name__ == "__main__":
    for fname, title, author, c1, c2, accent, kind in BOOKS:
        (OUT / fname).write_text(make_svg(title, author, c1, c2, accent, kind), encoding="utf-8")
        print("generated", fname)
    print("covers dir:", OUT)
