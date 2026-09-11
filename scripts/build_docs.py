#!/usr/bin/env python3
"""把 docs/*.md 渲染成 standalone 展示页，并在 Markdown 变更时自动重建 HTML。

约定：docs/ 下的 Markdown 是唯一数据源，HTML 是渲染产物。
每个生成的页面都带指纹：

    <meta name="rdec-source-md" content="psd2umg_V1.md">
    <meta name="rdec-source-hash" content="sha256:xxxxxxxxxxxxxxxx">

每次运行会比较 Markdown 的哈希与页面里的指纹，不一致就重新生成该页面。

用法：
    python3 scripts/build_docs.py             # 增量：只生成缺失或已变更的页面
    python3 scripts/build_docs.py --check     # 只检查不写文件；有缺失/过期时退出码 1
    python3 scripts/build_docs.py --force     # 全部按 Markdown 重新生成（接管人工维护页面）
    python3 scripts/build_docs.py --adopt     # 给人工维护页面补上指纹，之后即可增量检测

说明：没有指纹的 HTML 被视为人工维护页面，默认不会覆盖；
      需要让它跟随 Markdown 自动更新时，用 --force 重新生成一次即可。
"""
from __future__ import annotations

import argparse
import hashlib
import html
import re
import sys
from pathlib import Path

DOCS_DIR = Path("docs")

# psd2umg_V1.md / psd2umg_V1_cn.md
MD_FILE_RE = re.compile(r"^(?P<base>.+?)_V(?P<ver>\d+)(?P<lang>_cn)?\.md$", re.IGNORECASE)
# psd2umg-standalone_V1.html / psd2umg-standalone_V1_cn.html
HTML_FILE_RE = re.compile(
    r"^(?P<base>.+?)-standalone_V(?P<ver>\d+)(?P<lang>_cn)?\.html$", re.IGNORECASE
)

SOURCE_MD_RE = re.compile(r'<meta name="rdec-source-md" content="([^"]*)"')
SOURCE_HASH_RE = re.compile(r'<meta name="rdec-source-hash" content="([^"]*)"')
HEAD_END_RE = re.compile(r"</head>", re.IGNORECASE)

TITLE_SPLIT_RE = re.compile(r"\s*(?::\s|：|\s—\s|\s–\s|\s-\s)\s*")
VIDEO_LINK_RE = re.compile(r"^\s*(?:\*\*)?\[(?P<label>[^\]]*)\]\((?P<url>[^)\s]+\.(?:mp4|webm|mov))\)(?:\*\*)?\s*$")

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="__LANG__">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ — Showcase</title>
<meta name="rdec-source-md" content="__SOURCE_MD__">
<meta name="rdec-source-hash" content="__SOURCE_HASH__">
<meta name="rdec-generated-by" content="scripts/build_docs.py">
<style>

:root {
  --bg: #f6f8fb;
  --card: #ffffff;
  --text: #1f2937;
  --muted: #6b7280;
  --accent: #2563eb;
  --accent-soft: #eff6ff;
  --border: #e5e7eb;
  --code-bg: #f1f5f9;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
    "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
  line-height: 1.7;
  font-size: 16px;
}
.page {
  max-width: 1080px;
  margin: 0 auto;
  padding: 48px 24px 80px;
}
header.hero {
  background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 55%, #3b82f6 100%);
  color: #fff;
  border-radius: 16px;
  padding: 40px 40px 36px;
  margin-bottom: 40px;
  box-shadow: 0 12px 30px rgba(37, 99, 235, 0.25);
}
header.hero h1 {
  margin: 0 0 14px;
  font-size: 32px;
  line-height: 1.3;
  font-weight: 700;
  letter-spacing: -0.01em;
}
header.hero .subtitle {
  margin: 0;
  color: rgba(255, 255, 255, 0.85);
  font-size: 15px;
}
main.content {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 40px 44px;
  box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
}
main.content h1, main.content h2, main.content h3, main.content h4 {
  color: #111827;
  line-height: 1.35;
  scroll-margin-top: 24px;
}
main.content h1 { font-size: 26px; margin: 0 0 20px; }
main.content h2 {
  font-size: 24px;
  margin: 40px 0 16px;
  padding-bottom: 10px;
  border-bottom: 2px solid var(--border);
}
main.content h3 { font-size: 19px; margin: 28px 0 12px; }
main.content h4 { font-size: 16px; margin: 22px 0 10px; }
main.content p { margin: 0 0 16px; }
main.content strong { color: #111827; }
main.content a { color: var(--accent); text-decoration: none; }
main.content a:hover { text-decoration: underline; }
main.content ul, main.content ol { margin: 0 0 16px; padding-left: 24px; }
main.content li { margin: 6px 0; }
main.content blockquote {
  margin: 16px 0;
  padding: 12px 18px;
  background: var(--accent-soft);
  border-left: 4px solid var(--accent);
  border-radius: 0 8px 8px 0;
  color: #374151;
}
main.content code {
  font-family: "SF Mono", SFMono-Regular, ui-monospace, Menlo, Consolas, monospace;
  background: var(--code-bg);
  padding: 2px 6px;
  border-radius: 5px;
  font-size: 0.9em;
  color: #b91c1c;
}
main.content pre {
  background: #0f172a;
  color: #e2e8f0;
  padding: 16px 18px;
  border-radius: 10px;
  overflow-x: auto;
  margin: 0 0 18px;
  font-size: 13.5px;
  line-height: 1.6;
}
main.content pre code {
  background: transparent;
  color: inherit;
  padding: 0;
  font-size: inherit;
}
main.content img {
  max-width: 100%;
  height: auto;
  border-radius: 10px;
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.12);
  display: block;
}
main.content p[align="center"] { text-align: center; }
main.content p[align="center"] img { display: inline-block; }
main.content em { color: var(--muted); }
main.content hr { border: none; border-top: 1px solid var(--border); margin: 32px 0; }

table {
  width: 100%;
  border-collapse: collapse;
  margin: 18px 0 20px;
  font-size: 15px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
}
th, td {
  border: 1px solid var(--border);
  padding: 10px 14px;
  text-align: left;
  vertical-align: top;
}
th {
  background: #f1f5f9;
  color: #111827;
  font-weight: 600;
  white-space: nowrap;
}
tbody tr:nth-child(even) { background: #fafbfd; }
td img { margin: 0 auto; }

.video-wrap {
  margin: 20px 0 24px;
}
.video-wrap video {
  width: 100%;
  border-radius: 10px;
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.12);
  background: #000;
}
.video-wrap p {
  margin: 8px 0 0;
  color: var(--muted);
  font-size: 14px;
  text-align: center;
}

@media (max-width: 720px) {
  .page { padding: 20px 12px 60px; }
  header.hero { padding: 28px 22px; }
  header.hero h1 { font-size: 24px; }
  main.content { padding: 24px 18px; }
  th, td { padding: 8px 10px; }
}

</style>
</head>
<body>
<div class="page">
  <header class="hero">
    <h1>__H1__</h1>
    <p class="subtitle">__SUBTITLE__</p>
  </header>
  <main class="content">
__BODY__
  </main>
</div>
</body>
</html>
"""


# ---------------------------------------------------------------- 渲染：正文


def escape(text: str) -> str:
    return html.escape(text, quote=False)


def render_table(header, rows) -> str:
    head = "".join(f"<th>{inline(cell)}</th>" for cell in header)
    body = "".join(
        "<tr>" + "".join(f"<td>{inline(cell)}</td>" for cell in row) + "</tr>" for row in rows
    )
    return f"<table>\n<thead>\n<tr>{head}</tr>\n</thead>\n<tbody>\n{body}\n</tbody>\n</table>"


def inline(text: str) -> str:
    """行内 Markdown：代码、图片、链接、粗体、斜体。"""
    text = escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(
        r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)",
        r'<img src="\2" alt="\1">',
        text,
    )
    text = re.sub(r"\[([^\]]*)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    return text


BLOCK_START_RE = re.compile(
    r"^\s*(#{1,6}\s|>|```|[-*+]\s|\d+\.\s|\||<[a-zA-Z/!])"
)


def render_builtin(text: str) -> str:
    """无第三方依赖时的 Markdown 渲染（覆盖本仓库用到的语法）。"""
    lines = text.splitlines()
    out: list[str] = []
    i, n = 0, len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped.startswith("```"):
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>" + escape("\n".join(buf)) + "</code></pre>")
            continue

        if re.match(r"^\s*<[a-zA-Z/!]", line):  # 原始 HTML 块原样保留
            buf = []
            while i < n and lines[i].strip():
                buf.append(lines[i])
                i += 1
            out.append("\n".join(buf))
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading:
            level = min(len(heading.group(1)), 4)
            out.append(f"<h{level}>{inline(heading.group(2))}</h{level}>")
            i += 1
            continue

        if stripped.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append("<blockquote>" + inline(" ".join(buf)) + "</blockquote>")
            continue

        bullet = re.match(r"^\s*([-*+]|\d+\.)\s+", line)
        if bullet:
            ordered = bool(re.match(r"^\s*\d+\.", line))
            items = []
            while i < n and re.match(r"^\s*([-*+]|\d+\.)\s+", lines[i]):
                items.append(inline(re.sub(r"^\s*([-*+]|\d+\.)\s+", "", lines[i]).strip()))
                i += 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{it}</li>" for it in items) + f"</{tag}>")
            continue

        if stripped.startswith("|") and i + 1 < n and re.match(
            r"^\|?[\s:\-|]+\|[\s:\-|]*$", lines[i + 1].strip()
        ):
            header_cells = [c.strip() for c in stripped.strip("|").split("|")]
            i += 2
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            out.append(render_table(header_cells, rows))
            continue

        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", stripped):
            out.append("<hr>")
            i += 1
            continue

        buf = []
        while i < n and lines[i].strip() and not BLOCK_START_RE.match(lines[i]):
            buf.append(lines[i].strip())
            i += 1
        if buf:
            out.append("<p>" + inline(" ".join(buf)) + "</p>")
        else:
            i += 1

    return "\n".join(out)


def convert_videos(text: str) -> str:
    """把独占一行的视频链接转成 <video> 播放器。"""
    lines = text.splitlines()
    out = []
    for line in lines:
        m = VIDEO_LINK_RE.match(line)
        if m:
            label = m.group("label").strip()
            url = m.group("url")
            caption = f"<p>{escape(label)}</p>" if label else ""
            out.append(
                f'<div class="video-wrap"><video controls playsinline preload="metadata" '
                f'src="{escape(url)}"></video>{caption}</div>'
            )
        else:
            out.append(line)
    return "\n".join(out)


def render_markdown(text: str) -> str:
    text = convert_videos(text)
    try:
        import markdown  # type: ignore

        return markdown.markdown(
            text,
            extensions=["tables", "fenced_code", "sane_lists", "attr_list", "md_in_html"],
        )
    except ImportError:
        return render_builtin(text)


# ------------------------------------------------------------ 渲染：页面元数据


def extract_hero(text: str):
    """返回 (h1, subtitle, 去掉首个 H1 后的正文)。"""
    lines = text.splitlines()
    title = ""
    title_idx = -1
    for idx, raw in enumerate(lines):
        stripped = raw.strip().lstrip("\ufeff")
        if not title:
            m = re.match(r"^#{1,3}\s+(.*)$", stripped)
            if m:
                title = re.sub(r"[*`_]", "", m.group(1)).strip()
                title_idx = idx
            continue
        break

    body_lines = list(lines)
    if title_idx >= 0:
        del body_lines[title_idx]

    h1, subtitle = title, ""
    parts = TITLE_SPLIT_RE.split(title, maxsplit=1)
    if len(parts) == 2 and 1 <= len(parts[0]) <= 60 and parts[1].strip():
        h1, subtitle = parts[0].strip(), parts[1].strip()

    if not subtitle:
        for raw in body_lines:
            line = raw.strip()
            if not line or line.startswith(("#", "|", "!", ">", "<", "```", "---", "***")):
                continue
            subtitle = re.sub(r"[*`_]", "", line)
            break

    subtitle = re.sub(r"\s+", " ", subtitle).strip()
    if len(subtitle) > 180:
        subtitle = subtitle[:180].rstrip() + "…"

    return (h1 or "Showcase"), subtitle, "\n".join(body_lines).strip()


def sha256_short(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()[:16]


def build_page(md_name: str, lang: str, h1: str, subtitle: str, body_html: str, digest: str) -> str:
    return (
        PAGE_TEMPLATE.replace("__LANG__", "zh-CN" if lang == "cn" else "en")
        .replace("__TITLE__", escape(h1))
        .replace("__H1__", escape(h1))
        .replace("__SUBTITLE__", escape(subtitle))
        .replace("__BODY__", body_html)
        .replace("__SOURCE_MD__", escape(md_name))
        .replace("__SOURCE_HASH__", digest)
    )


# ------------------------------------------------------------------ 主流程


def existing_html_index() -> dict:
    """{能力项名小写: {版本+语言: 实际文件名}}，用于复用已有的大小写写法。"""
    index: dict = {}
    for path in DOCS_DIR.glob("*.html"):
        m = HTML_FILE_RE.match(path.name)
        if not m:
            continue
        lang = "cn" if m.group("lang") else "en"
        index.setdefault(m.group("base").lower(), {})[(m.group("ver"), lang)] = path.name
    return index


def resolve_target(base: str, version: str, lang: str, index: dict) -> Path:
    suffix = "_cn" if lang == "cn" else ""
    default = f"{base}-standalone_V{version}{suffix}.html"
    for ver in (version, None):
        found = index.get(base.lower(), {}).get((ver, lang)) if ver else None
        if found:
            return DOCS_DIR / found
    return DOCS_DIR / default


def read_fingerprint(path: Path):
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None, None
    md_match = SOURCE_MD_RE.search(text)
    hash_match = SOURCE_HASH_RE.search(text)
    return text, (hash_match.group(1) if hash_match and md_match else None)


def adopt_fingerprint(path: Path, md_name: str, digest: str) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"警告：读取 {path} 失败：{exc}", file=sys.stderr)
        return False
    block = (
        f'<meta name="rdec-source-md" content="{escape(md_name)}">\n'
        f'<meta name="rdec-source-hash" content="{digest}">\n'
    )
    if HEAD_END_RE.search(text):
        text = HEAD_END_RE.sub(block + "</head>", text, count=1)
    else:
        text = text.replace("<body", block + "<body", 1)
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        print(f"警告：写入 {path} 失败：{exc}", file=sys.stderr)
        return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="由 docs/*.md 生成 standalone HTML（增量）")
    parser.add_argument("--check", action="store_true", help="只检查不写文件，有缺失/过期时退出码 1")
    parser.add_argument("--force", action="store_true", help="按 Markdown 重新生成所有页面（含人工维护页面）")
    parser.add_argument("--adopt", action="store_true", help="给无指纹的页面补指纹，不改动正文")
    parser.add_argument("--quiet", action="store_true", help="只输出结果统计")
    args = parser.parse_args()

    if not DOCS_DIR.is_dir():
        print(f"错误：找不到 {DOCS_DIR} 目录", file=sys.stderr)
        sys.exit(1)

    index = existing_html_index()
    created, updated, fresh, manual, pending = [], [], [], [], []

    for md_path in sorted(DOCS_DIR.glob("*.md")):
        m = MD_FILE_RE.match(md_path.name)
        if not m:
            continue
        base, version, lang = m.group("base"), m.group("ver"), ("cn" if m.group("lang") else "en")
        raw = md_path.read_bytes()
        digest = sha256_short(raw)
        target = resolve_target(base, version, lang, index)

        h1, subtitle, body_text = extract_hero(raw.decode("utf-8", errors="replace"))
        text, current_hash = read_fingerprint(target)

        if text is None:  # 还没有 HTML：直接生成
            if args.check:
                pending.append(f"{md_path.name} → {target.name}（缺失）")
                continue
            page = build_page(md_path.name, lang, h1, subtitle, render_markdown(body_text), digest)
            target.write_text(page, encoding="utf-8")
            created.append(target.name)
            continue

        if current_hash is None:  # 人工维护页面
            md_newer = md_path.stat().st_mtime > target.stat().st_mtime
            label = f"{target.name}（人工维护，源 {md_path.name}"
            if md_newer:
                label += "，md 比 html 新"
            label += "）"
            if args.force:
                page = build_page(md_path.name, lang, h1, subtitle, render_markdown(body_text), digest)
                target.write_text(page, encoding="utf-8")
                updated.append(f"{target.name}（已接管重建）")
            elif args.adopt:
                if adopt_fingerprint(target, md_path.name, digest):
                    fresh.append(f"{target.name}（已补指纹）")
            else:
                manual.append(label)
                if md_newer or args.check:
                    pending.append(label + " 需 --force 或 --adopt")
            continue

        if current_hash == digest and not args.force:
            fresh.append(target.name)
            continue

        if args.check:
            pending.append(f"{target.name}（源 {md_path.name} 已更新）")
            continue

        page = build_page(md_path.name, lang, h1, subtitle, render_markdown(body_text), digest)
        target.write_text(page, encoding="utf-8")
        updated.append(target.name)

    if args.quiet:
        if pending:
            print("\n".join(pending))
    else:
        for name in created:
            print(f"新建  {name}")
        for name in updated:
            print(f"更新  {name}")
        for name in manual:
            print(f"跳过  {name}")
        print(
            f"完成：新建 {len(created)}，更新 {len(updated)}，"
            f"最新 {len(fresh)}，人工维护跳过 {len(manual)}"
        )
        if pending:
            print("待处理：")
            for item in pending:
                print(f"  - {item}")

    sys.exit(1 if (args.check and pending) else 0)


if __name__ == "__main__":
    main()
