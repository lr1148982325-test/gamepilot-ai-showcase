#!/usr/bin/env python3
"""
自动生成 Pages 落地页 public/index.html。

扫描 docs/ 目录下所有 .html 文件（排除 index.html 自身），
读取每个文件的 <title> 作为卡片标题，读取 hero 的 subtitle / 描述作为卡片简介，
自动生成带卡片网格的落地页。

用法：python3 scripts/generate_index.py
输出：public/index.html
"""
import html
import re
import sys
from pathlib import Path
from urllib.parse import quote

DOCS_DIR = Path("docs")
OUTPUT = Path("public/index.html")

MAX_DESC = 200

# 针对个别没有 subtitle 的文档，提供人工精炼的描述（比直接取正文第一段更准确）
DESCRIPTION_OVERRIDES = {
    "p4-merge-workflow-standalone_V1.html": (
        "Turns a million-file Perforce merge into a repeatable GamePilot skill — "
        "detecting stream topology, syncing by content digest, and splitting resolves "
        "into path-disjoint, human-owned waves."
    ),
    "rd-knowledge-base-deepwiki-standalone_V1.html": (
        "DeepWiki converts a game codebase into a navigable technical wiki; the "
        "Knowledge Base then combines it with project documents into a permission-aware, "
        "reusable context supply for onboarding, coding, review, and QA workflows."
    ),
}

# 落地页模板：__CARDS__ 为自动生成的卡片列表，__COUNT__ 为 showcase 数量
TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RDEC AI Showcases</title>
<style>
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background: #f6f8fb;
  color: #1f2937;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
    "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
  line-height: 1.6;
}
.page { max-width: 1080px; margin: 0 auto; padding: 48px 24px 80px; }
header.hero {
  background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 55%, #3b82f6 100%);
  color: #fff;
  border-radius: 16px;
  padding: 40px 40px 36px;
  margin-bottom: 32px;
  box-shadow: 0 12px 30px rgba(37, 99, 235, 0.25);
}
header.hero h1 { margin: 0 0 10px; font-size: 30px; font-weight: 700; }
header.hero p { margin: 0; color: rgba(255,255,255,0.85); font-size: 15px; }
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}
.card {
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px 22px;
  text-decoration: none;
  color: inherit;
  transition: transform .12s ease, box-shadow .12s ease, border-color .12s ease;
}
.card:hover {
  transform: translateY(-2px);
  border-color: #2563eb;
  box-shadow: 0 8px 20px rgba(37, 99, 235, 0.12);
}
.card h2 {
  margin: 0 0 8px;
  font-size: 17px;
  font-weight: 650;
  color: #111827;
  line-height: 1.35;
}
.card .desc {
  margin: 0 0 4px;
  font-size: 14px;
  color: #6b7280;
  line-height: 1.55;
}
.card .arrow {
  margin-top: auto;
  padding-top: 12px;
  font-size: 14px;
  color: #2563eb;
}
footer {
  margin-top: 40px;
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
}
</style>
</head>
<body>
<div class="page">
  <header class="hero">
    <h1>RDEC AI Showcases</h1>
    <p>AI 通用能力项展示 · 点击任意卡片在线浏览渲染后的页面</p>
  </header>

  <div class="grid">
__CARDS__
  </div>

  <footer>RDEC AI Showcases · 由工蜂 Pages 自动部署 · 共 __COUNT__ 项</footer>
</div>
</body>
</html>
"""


def strip_tags(text: str) -> str:
    """去掉 HTML 标签与实体，压缩空白。"""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def truncate(text: str, limit: int = MAX_DESC) -> str:
    if len(text) <= limit:
        return text
    cut = text[:limit].rstrip()
    return cut.rstrip(".,;:·-") + "…"


def extract_title(text: str, fallback: str) -> str:
    """读取 <title>，去掉 em dash 后的后缀（如 ' — Showcase'）。"""
    m = re.search(r"<title[^>]*>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
    if not m:
        return fallback
    title = html.unescape(m.group(1)).strip()
    if " — " in title:
        title = title.split(" — ", 1)[0].strip()
    return title or fallback


def extract_description(text: str) -> str:
    """优先读 hero 的 subtitle / sub / note，否则回退到正文第一段。"""
    for pattern in (
        r'<p class="subtitle"[^>]*>(.*?)</p>',
        r'<div class="sub"[^>]*>(.*?)</div>',
        r'<p class="note"[^>]*>(.*?)</p>',
    ):
        m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if m:
            desc = strip_tags(m.group(1))
            if desc:
                return truncate(desc)
    # 回退：正文第一个非空 <p>
    m = re.search(r"<main[^>]*>(.*?)</main>", text, re.IGNORECASE | re.DOTALL)
    if m:
        for pm in re.finditer(r"<p[^>]*>(.*?)</p>", m.group(1), re.IGNORECASE | re.DOTALL):
            desc = strip_tags(pm.group(1))
            if desc:
                return truncate(desc)
    return ""


# 匹配文件名中的版本号后缀，如 "-standalone_V1.html" / "-standalone_V2.html"
VERSION_RE = re.compile(r"-standalone_V(\d+)\.html$", re.IGNORECASE)


def pick_latest(files):
    """同名能力项若存在多个版本（V1/V2/...），只保留最高版本。"""
    groups = {}
    for name in files:
        m = VERSION_RE.search(name)
        base = VERSION_RE.sub("", name)  # 去掉版本号后的基础名
        version = int(m.group(1)) if m else 0
        if base not in groups or version > groups[base][1]:
            groups[base] = (name, version)
    return sorted(groups[base][0] for base in sorted(groups))


def build_cards(items):
    cards = []
    for filename, title, desc in items:
        href = quote(filename)  # 文件名空格等字符自动 URL 编码
        desc_html = html.escape(desc) if desc else ""
        cards.append(
            f'    <a class="card" href="{href}">\n'
            f'      <h2>{html.escape(title)}</h2>\n'
            + (f'      <p class="desc">{desc_html}</p>\n' if desc_html else "")
            + f'      <span class="arrow">Open &rarr;</span>\n'
            f'    </a>'
        )
    return "\n".join(cards)


def main():
    if not DOCS_DIR.is_dir():
        print(f"错误：找不到 {DOCS_DIR} 目录", file=sys.stderr)
        sys.exit(1)

    files = sorted(
        p.name for p in DOCS_DIR.glob("*.html")
        if p.name.lower() != "index.html"
    )
    if not files:
        print("警告：docs/ 下没有找到任何 .html 文件", file=sys.stderr)

    files = pick_latest(files)

    items = []
    for name in files:
        path = DOCS_DIR / name
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        title = extract_title(text, path.stem)
        desc = DESCRIPTION_OVERRIDES.get(name) or extract_description(text)
        items.append((name, title, desc))

    cards = build_cards(items)
    page = TEMPLATE.replace("__CARDS__", cards).replace("__COUNT__", str(len(items)))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(page, encoding="utf-8")
    print(f"已生成 {OUTPUT}：共 {len(items)} 个 showcase")


if __name__ == "__main__":
    main()
