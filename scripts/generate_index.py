#!/usr/bin/env python3
"""
自动生成 Pages 落地页 public/index.html，并为文档页注入中英文切换入口。

1. 扫描 docs/ 目录下所有 .html 文件（排除 index.html 自身），
   读取每个文件的 <title> 作为卡片标题，读取 hero 的 subtitle / 描述作为卡片简介；
2. 同一能力项的中英文版本（xxx-standalone_V1.html / xxx-standalone_V1_cn.html）
   在落地页合并为一张卡片，卡片右上角可切换 EN / 中（点击即打开对应语言版本）；
3. 把 docs/*.html 同步到 public/，并为存在双语的文档在右上角注入语言切换条，
   打开文档后可直接切到另一种语言。

用法：python3 scripts/generate_index.py
输出：public/index.html 以及 public/ 下的各 showcase 页面副本
"""
import html
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import quote, unquote

DOCS_DIR = Path("docs")
PUBLIC_DIR = Path("public")
def find_readme() -> Path:
    """兼容不同平台的大小写：Readme.md / README.md / readme.md。"""
    for name in ("Readme.md", "README.md", "readme.md"):
        candidate = Path(name)
        if candidate.is_file():
            return candidate
    return Path("Readme.md")


README = find_readme()
OUTPUT = PUBLIC_DIR / "index.html"

# README 表格里未标注分类的能力项，归入该兜底分组（排在最后）
FALLBACK_CATEGORY = "其他"

# 分类展示顺序：列在这里的按此顺序排在前面，其余沿用 Readme.md 中的出现顺序
CATEGORY_PRIORITY = ("程序", "知识库", "美术")

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

# 文件名解析：能力项名 + 版本号 + 可选的语言后缀（_cn 为中文版）
FILE_RE = re.compile(
    r"^(?P<base>.+?)-standalone_V(?P<ver>\d+)(?P<lang>_cn)?\.html$",
    re.IGNORECASE,
)

LANG_LABELS = (("en", "EN"), ("cn", "中文"))

# README 表格的 Markdown 链接，用于从「HTML地址」列反查能力项分类
MD_LINK_RE = re.compile(r"\]\(([^)]+)\)")
HTML_NAME_RE = re.compile(r"-standalone_V\d+(_cn)?\.html$", re.IGNORECASE)

# Markdown 源文档（卡片文案优先取这里，HTML 视为渲染产物）
MD_FILE_RE = re.compile(r"^(?P<base>.+?)_V(?P<ver>\d+)(?P<lang>_cn)?\.md$", re.IGNORECASE)

# 缺少中文 Markdown 时使用的 AI 译文（人工可维护，key 为能力项名小写）
TRANSLATIONS_FILE = Path("scripts/translations.json")

# 注入到 showcase 页面的语言切换条（固定右上角）
SWITCH_START = "<!--RDEC_LANG_SWITCH_START-->"
SWITCH_END = "<!--RDEC_LANG_SWITCH_END-->"
SWITCH_BLOCK_RE = re.compile(
    re.escape(SWITCH_START) + r".*?" + re.escape(SWITCH_END), re.IGNORECASE | re.DOTALL
)
HEAD_END_RE = re.compile(r"</head>", re.IGNORECASE)
BODY_START_RE = re.compile(r"<body[^>]*>", re.IGNORECASE)

SWITCH_CSS = """<style>
.rdec-lang-switch {
  position: fixed;
  top: 18px;
  right: 24px;
  z-index: 9999;
  display: block;
  font-size: 0;
  padding: 4px;
  border-radius: 999px;
  background: #ffffff;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(15, 23, 42, 0.1);
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.14);
  font: 600 12px/1 -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
    "Hiragino Sans GB", "Microsoft YaHei", Arial, sans-serif;
  font-size: 0;
  backdrop-filter: saturate(180%) blur(8px);
}
.rdec-lang-switch a {
  display: inline-block;
  margin-left: 2px;
  font-size: 12px;
  padding: 6px 13px;
  border-radius: 999px;
  color: #4b5563;
  text-decoration: none;
  transition: background .15s ease, color .15s ease;
}
.rdec-lang-switch a:hover { background: #f1f5f9; color: #111827; text-decoration: none; }
.rdec-lang-switch a.is-active { background: #2563eb; color: #fff; }
@media (max-width: 640px) {
  .rdec-lang-switch { top: 10px; right: 12px; }
}
</style>"""


def build_switch_dom(current, targets):
    """targets: [(lang_code, label, href), ...]"""
    links = []
    for code, label, href in targets:
        active = " class=\"is-active\"" if code == current else ""
        links.append(f'<a href="{html.escape(href, quote=True)}"{active}>{label}</a>')
    return (
        f'{SWITCH_START}\n<div class="rdec-lang-switch">{ "".join(links) }</div>\n{SWITCH_END}'
    )


# 落地页模板：__SECTIONS__ 为按分类分块的卡片列表，__NAV__ 为分类锚点导航，
# __COUNT__ 为 showcase 数量
TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="referrer" content="no-referrer">
<meta name="format-detection" content="telephone=no,email=no,address=no">
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
.cat-nav {
  margin: 0 0 20px;
  font-size: 0;
}
.cat-nav a {
  display: inline-block;
  margin: 0 8px 8px 0;
  padding: 6px 14px;
  border-radius: 999px;
  background: #fff;
  border: 1px solid #e5e7eb;
  color: #4b5563;
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  transition: border-color .12s ease, color .12s ease;
}
.cat-nav a:hover { border-color: #2563eb; color: #2563eb; }
section.cat { margin-bottom: 40px; scroll-margin-top: 20px; }
.cat-head {
  margin: 0 0 14px;
  font-size: 0;
}
.cat-head h2 {
  display: inline-block;
  vertical-align: middle;
  margin: 0;
  font-size: 19px;
  font-weight: 700;
  color: #111827;
}
.cat-count {
  display: inline-block;
  vertical-align: middle;
  margin-left: 10px;
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  background: #eef2f7;
  border-radius: 999px;
  padding: 2px 10px;
}
.grid {
  display: -webkit-box;
  display: -webkit-flex;
  display: flex;
  -webkit-flex-wrap: wrap;
  flex-wrap: wrap;
  margin: 0 -8px;
}
.card {
  position: relative;
  display: -webkit-flex;
  display: flex;
  -webkit-flex-direction: column;
  flex-direction: column;
  width: 33.3333%;
  width: calc(33.3333% - 16px);
  margin: 0 8px 16px;
  font-size: 16px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  transition: transform .12s ease, box-shadow .12s ease, border-color .12s ease;
}
.card:hover {
  transform: translateY(-2px);
  border-color: #2563eb;
  box-shadow: 0 8px 20px rgba(37, 99, 235, 0.12);
}
.card-link {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 20px 22px;
  text-decoration: none;
  color: inherit;
}
.card h2 {
  margin: 0 0 8px;
  font-size: 17px;
  font-weight: 650;
  color: #111827;
  line-height: 1.35;
}
.card.has-lang h2 { padding-right: 96px; }
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
.lang-tabs {
  position: absolute;
  top: 12px;
  right: 14px;
  z-index: 2;
  display: block;
  font-size: 0;
  padding: 3px;
  border-radius: 999px;
  background: #f1f5f9;
  border: 1px solid #e5e7eb;
  font-weight: 700;
  line-height: 1;
}
.lang-tabs a {
  display: inline-block;
  margin-left: 2px;
  font-size: 11px;
  padding: 5px 10px;
  border-radius: 999px;
  color: #6b7280;
  text-decoration: none;
  cursor: pointer;
}
.lang-tabs a:hover { color: #111827; }
.lang-tabs a.is-active { background: #2563eb; color: #fff; }
footer {
  margin-top: 40px;
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
}
@media (max-width: 900px) {
  .card { width: 50%; width: calc(50% - 16px); }
}
@media (max-width: 620px) {
  .card { width: 100%; width: calc(100% - 16px); }
  .page { padding: 24px 14px 56px; }
  header.hero { padding: 28px 22px; }
}
</style>
</head>
<body>
<div class="page">
  <header class="hero">
    <h1>RDEC AI Showcases</h1>
    <p>AI 通用能力项展示 · 点击任意卡片在线浏览渲染后的页面 · 支持中英文切换</p>
  </header>

__NAV__
__SECTIONS__

  <footer>RDEC AI Showcases · 由工蜂 Pages 自动部署 · 共 __COUNT__ 项</footer>
</div>
<script>
(function () {
  var STORE_KEY = 'rdec-showcase-lang';
  function read() {
    try { return localStorage.getItem(STORE_KEY) === 'cn' ? 'cn' : 'en'; } catch (e) { return 'en'; }
  }
  function write(lang) {
    try { localStorage.setItem(STORE_KEY, lang); } catch (e) {}
  }
  function pick(card, lang) {
    var hasEn = !!card.getAttribute('data-en-href');
    var hasCn = !!card.getAttribute('data-cn-href');
    if (lang === 'cn' && hasCn) return 'cn';
    return hasEn ? 'en' : 'cn';
  }
  function apply(card, lang) {
    var use = pick(card, lang);
    var title = card.getAttribute('data-' + use + '-title') || '';
    var desc = card.getAttribute('data-' + use + '-desc') || '';
    card.querySelector('.card-link').setAttribute('href', card.getAttribute('data-' + use + '-href') || '#');
    card.querySelector('.card-title').textContent = title;
    var descEl = card.querySelector('.desc');
    descEl.textContent = desc;
    descEl.style.display = desc ? '' : 'none';
    var tabs = card.querySelectorAll('.lang-tabs a');
    for (var i = 0; i < tabs.length; i++) {
      var on = tabs[i].getAttribute('data-lang') === use;
      if (on) { tabs[i].classList.add('is-active'); } else { tabs[i].classList.remove('is-active'); }
    }
  }
  var cards = document.querySelectorAll('.card[data-en-href], .card[data-cn-href]');
  var pref = read();
  for (var i = 0; i < cards.length; i++) {
    (function (card) {
      var tabs = card.querySelectorAll('.lang-tabs a');
      for (var j = 0; j < tabs.length; j++) {
        tabs[j].addEventListener('click', function (e) {
          e.preventDefault();
          e.stopPropagation();
          var lang = this.getAttribute('data-lang');
          write(lang);
          for (var k = 0; k < cards.length; k++) { apply(cards[k], lang); }
        });
      }
      apply(card, pref);
    })(cards[i]);
  }
})();
</script>
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


def strip_md_inline(text: str) -> str:
    """去掉 Markdown 行内标记（图片、链接、强调、代码符号）。"""
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[*`_]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_md_meta(text: str):
    """从 Markdown 提取 (标题, 摘要)：首个 # 标题 + 其后第一个正文段落。"""
    title = ""
    desc = ""
    for raw in text.splitlines():
        line = raw.strip().lstrip("\ufeff")
        if not title:
            heading = re.match(r"^#{1,3}\s+(.*)$", line)
            if heading:
                title = strip_md_inline(heading.group(1))
            continue
        if not line or line.startswith(("#", "|", "!", ">", "<", "```", "---", "***")):
            continue
        desc = strip_md_inline(line)
        break
    return title, truncate(desc)


def load_markdown_meta():
    """扫描 docs/*.md，返回 {能力项名(小写): {lang: {title, desc, version}}}。"""
    meta = {}
    if not DOCS_DIR.is_dir():
        return meta
    for path in sorted(DOCS_DIR.glob("*.md")):
        m = MD_FILE_RE.match(path.name)
        if not m:
            continue
        key = m.group("base").lower()
        lang = "cn" if m.group("lang") else "en"
        version = int(m.group("ver"))
        bucket = meta.setdefault(key, {})
        if lang in bucket and bucket[lang]["version"] >= version:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        title, desc = extract_md_meta(text)
        bucket[lang] = {"title": title, "desc": desc, "version": version}
    return meta


def load_translations():
    """读取缺失中文文档时的 AI 译文缓存。"""
    if not TRANSLATIONS_FILE.is_file():
        print(f"提示：未找到 {TRANSLATIONS_FILE}，缺少中文 Markdown 的能力项将只有英文文案", file=sys.stderr)
        return {}
    try:
        raw = json.loads(TRANSLATIONS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"警告：读取 {TRANSLATIONS_FILE} 失败：{exc}", file=sys.stderr)
        return {}
    return {str(k).lower(): v for k, v in raw.items()}


def group_files(files):
    """按能力项分组：同名的中英文版本并为一组，且只保留最高版本（V1/V2/...）。"""
    groups = {}
    for name in files:
        m = FILE_RE.match(name)
        if m:
            base = m.group("base")
            version = int(m.group("ver"))
            lang = "cn" if m.group("lang") else "en"
        else:
            base = name[:-5] if name.lower().endswith(".html") else name
            version = 0
            lang = "en"
        group = groups.setdefault(base, {"base": base, "version": version, "files": {}})
        if version > group["version"]:  # 发现更高版本，丢弃低版本的语言副本
            group["version"] = version
            group["files"] = {}
        if version == group["version"]:
            group["files"][lang] = name
    return [groups[key] for key in sorted(groups)]


def load_categories():
    """从 Readme.md 的能力项表格读取「分类 → HTML 文件名」映射。

    返回 (category_by_base, category_order)，order 保持 README 中的出现顺序。
    """
    mapping = {}
    order = []
    if not README.is_file():
        print(f"警告：找不到 {README}，落地页将不按分类分块", file=sys.stderr)
        return mapping, order

    text = README.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        row = line.strip()
        if not row.startswith("|"):
            continue
        cells = [c.strip() for c in row.strip("|").split("|")]
        if len(cells) < 2:
            continue
        category = cells[0]
        if not category or category in ("分类",) or set(category) <= set("-: "):
            continue
        # HTML 地址在最后一列；个别行该列为空时向前兼容取剩余列
        link_scope = " ".join(cells[-1:] if len(cells) >= 7 else cells[5:])
        for url in MD_LINK_RE.findall(link_scope):
            name = unquote(url.rsplit("/", 1)[-1])
            if not name.lower().endswith(".html"):
                continue
            base = HTML_NAME_RE.sub("", name)
            if not base:
                continue
            mapping[base] = category
            if category not in order:
                order.append(category)
    return mapping, order


def build_card(item):
    versions = {lang: item[lang] for lang in ("en", "cn") if item[lang]}
    if not versions:
        return None
    default_lang = "en" if versions.get("en") else "cn"
    default = versions[default_lang]
    has_lang = len(versions) > 1

    attrs = []
    for lang in ("en", "cn"):
        meta = versions.get(lang)
        if not meta:
            continue
        attrs.append(f'data-{lang}-title="{html.escape(meta["title"], quote=True)}"')
        attrs.append(f'data-{lang}-desc="{html.escape(meta["desc"], quote=True)}"')
        attrs.append(f'data-{lang}-href="{html.escape(quote(meta["name"]), quote=True)}"')

    tabs = ""
    if has_lang:
        tab_links = "".join(
            f'<a href="#" data-lang="{lang}">{label}</a>'
            for lang, label in LANG_LABELS
            if versions.get(lang)
        )
        tabs = f'      <div class="lang-tabs">{tab_links}</div>\n'

    return (
        f'    <div class="card{" has-lang" if has_lang else ""}" {" ".join(attrs)}>\n'
        f"{tabs}"
        f'      <a class="card-link" href="{html.escape(quote(default["name"]), quote=True)}">\n'
        f'        <h2 class="card-title">{html.escape(default["title"])}</h2>\n'
        f'        <p class="desc">{html.escape(default["desc"])}</p>\n'
        f'        <span class="arrow">Open &rarr;</span>\n'
        f'      </a>\n'
        f'    </div>'
    )


def build_sections(items, category_map, category_order):
    """按 Readme 中的分类把卡片分块渲染，返回 (sections_html, nav_html)。"""
    buckets = {}
    for item in items:
        category = category_map.get(item["base"], FALLBACK_CATEGORY)
        buckets.setdefault(category, []).append(item)

    # 先按 CATEGORY_PRIORITY 排，其次沿用 README 出现顺序
    def sort_key(category):
        if category in CATEGORY_PRIORITY:
            return (0, CATEGORY_PRIORITY.index(category))
        rank = category_order.index(category) if category in category_order else len(category_order)
        return (1, rank)

    order = sorted((c for c in buckets if c != FALLBACK_CATEGORY), key=sort_key)
    # 兜底分组（含 README 未收录的项）固定在最后
    if FALLBACK_CATEGORY in buckets:
        order.append(FALLBACK_CATEGORY)

    sections = []
    nav = []
    for index, category in enumerate(order):
        group = buckets[category]
        cards = [build_card(item) for item in group]
        cards = [c for c in cards if c]
        if not cards:
            continue
        anchor = f"cat-{index}"
        nav.append(f'    <a href="#{anchor}">{html.escape(category)} · {len(cards)}</a>')
        sections.append(
            f'  <section class="cat" id="{anchor}">\n'
            f'    <div class="cat-head">\n'
            f'      <h2>{html.escape(category)}</h2>\n'
            f'      <span class="cat-count">{len(cards)} 项</span>\n'
            f'    </div>\n'
            f'    <div class="grid">\n'
            + "\n".join(cards)
            + "\n    </div>\n"
            f'  </section>'
        )
    nav_html = (
        '  <nav class="cat-nav">\n' + "\n".join(nav) + "\n  </nav>"
        if len(sections) > 1
        else ""
    )
    return "\n".join(sections), nav_html


def sync_to_public(name: str) -> bool:
    """把 docs 下的页面同步到 public（缺失或源文件更新时复制）。"""
    src = DOCS_DIR / name
    dst = PUBLIC_DIR / name
    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        return True
    try:
        shutil.copy2(src, dst)
    except OSError as exc:
        print(f"警告：复制 {src} 失败：{exc}", file=sys.stderr)
        return False
    return True


def inject_lang_switch(name: str, current: str, targets) -> None:
    """在 public 下的文档副本右上角注入中英文切换条（可重复执行）。"""
    path = PUBLIC_DIR / name
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"警告：读取 {path} 失败：{exc}", file=sys.stderr)
        return

    # 先清掉历史注入内容，保证重复执行不会叠加
    text = SWITCH_BLOCK_RE.sub("", text)
    dom = build_switch_dom(current, targets)

    if HEAD_END_RE.search(text):
        text = HEAD_END_RE.sub(
            f"{SWITCH_START}\n{SWITCH_CSS}\n{SWITCH_END}\n</head>", text, count=1
        )
    if BODY_START_RE.search(text):
        text = BODY_START_RE.sub(lambda m: f"{m.group(0)}\n{dom}", text, count=1)

    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        print(f"警告：写入 {path} 失败：{exc}", file=sys.stderr)


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

    groups = group_files(files)
    md_meta = load_markdown_meta()
    translations = load_translations()

    items = []
    for group in groups:
        key = group["base"].lower()
        md = md_meta.get(key, {})
        entry = {"base": group["base"], "en": None, "cn": None}
        for lang, name in group["files"].items():
            path = DOCS_DIR / name
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                text = ""
            # 文案优先级：Markdown 源文档 > HTML（渲染产物）
            source = md.get(lang)
            if source and source["title"]:
                title = source["title"]
                desc = source["desc"] or extract_description(text)
            else:
                title = extract_title(text, path.stem)
                desc = DESCRIPTION_OVERRIDES.get(name) or extract_description(text)
            entry[lang] = {"name": name, "title": title, "desc": desc}

        # 没有中文文档时，落地页展示 AI 翻译的中文文案（打开仍是英文文档）
        if entry["en"] and not entry["cn"]:
            translated = translations.get(key) or {}
            if translated.get("title"):
                entry["cn"] = {
                    "name": entry["en"]["name"],
                    "title": translated["title"],
                    "desc": translated.get("desc", ""),
                }
        items.append(entry)

    category_map, category_order = load_categories()
    sections, nav = build_sections(items, category_map, category_order)
    page = (
        TEMPLATE.replace("__SECTIONS__", sections)
        .replace("__NAV__", nav)
        .replace("__COUNT__", str(len(items)))
    )

    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(page, encoding="utf-8")
    unknown = sum(
        1 for item in items if item["base"] not in category_map
    )
    print(f"已生成 {OUTPUT}：共 {len(items)} 个 showcase")
    if unknown:
        print(f"提示：有 {unknown} 个能力项未在 Readme.md 表格中标注分类，已归入「{FALLBACK_CATEGORY}」")

    # 同步页面副本并注入语言切换条
    switched = 0
    missing_cn = []
    for item in items:
        langs = [lang for lang in ("en", "cn") if item[lang]]
        # 只有真的存在中英文两个页面文件时，才在页面右上角注入切换条
        bilingual_page = len({item[lang]["name"] for lang in langs}) > 1
        for lang in langs:
            if not sync_to_public(item[lang]["name"]):
                continue
            if bilingual_page:
                targets = [
                    (other, label, quote(item[other]["name"]))
                    for other, label in LANG_LABELS
                    if item[other]
                ]
                inject_lang_switch(item[lang]["name"], lang, targets)
        if bilingual_page:
            switched += 1
        elif not item["cn"]:
            missing_cn.append(item["base"])
    if switched:
        print(f"已为 {switched} 个中英双语文文档注入右上角语言切换条")
    if missing_cn:
        print(
            f"提示：{len(missing_cn)} 个能力项没有中文文档，落地页中文文案来自 "
            f"{TRANSLATIONS_FILE}：{', '.join(missing_cn)}"
        )


if __name__ == "__main__":
    main()
