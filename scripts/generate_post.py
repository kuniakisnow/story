#!/usr/bin/env python3
"""
Generate a blog post from collected articles.
Creates a Markdown file in _posts/ directory.
"""

import json
import sys
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
POSTS_DIR = Path(__file__).resolve().parent.parent / "_posts"
KNOWLEDGE_FILE = DATA_DIR / "knowledge.json"
TZ_JST = timezone(timedelta(hours=9))


def load_knowledge() -> dict:
    if not KNOWLEDGE_FILE.exists():
        print("No knowledge data found. Run collect.py first.", file=sys.stderr)
        sys.exit(1)
    with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text[:60]


def build_post_from_articles(top_articles: list) -> str:
    """Build a markdown post from the top scored articles."""
    now = datetime.now(TZ_JST)
    date_str = now.strftime("%Y-%m-%d")
    title = f"週次ストレージ・光伝送ダイジェスト ({date_str})"
    slug = f"weekly-digest-{now.strftime('%Y%m%d')}"

    lines = [
        "---",
        f"layout: post",
        f'title: "{title}"',
        f"date: {now.strftime('%Y-%m-%d %H:%M:%S %z')}",
        f"tags: [digest, storage, optical]",
        f'description: "今週のストレージ技術・光伝送技術の注目記事をまとめました。"',
        "---",
        "",
        f"## 今週のトピック ({date_str})",
        "",
    ]

    # Group by category
    storage_arts = [a for a in top_articles if a.get("category") == "storage"]
    optical_arts = [a for a in top_articles if a.get("category") == "optical"]
    vendor_arts = [a for a in top_articles if a.get("category") == "vendor"]

    if storage_arts:
        lines.append("### ストレージ技術")
        lines.append("")
        for a in storage_arts[:5]:
            lines.append(f"- **[{a['source']}]** {a['title']}")
            if a.get("url"):
                lines.append(f"  - URL: {a['url']}")
            lines.append("")

    if optical_arts:
        lines.append("### 光伝送技術")
        lines.append("")
        for a in optical_arts[:5]:
            lines.append(f"- **[{a['source']}]** {a['title']}")
            if a.get("url"):
                lines.append(f"  - URL: {a['url']}")
            lines.append("")

    if vendor_arts:
        lines.append("### ベンダー情報")
        lines.append("")
        for a in vendor_arts[:3]:
            lines.append(f"- **[{a['source']}]** {a['title']}")
            if a.get("url"):
                lines.append(f"  - URL: {a['url']}")
            lines.append("")

    lines.extend([
        "---",
        "",
        "### 今週の注目ポイント",
        "",
        "来週も最新情報をお届けします。",
        "",
    ])

    return "\n".join(lines), slug


def main():
    knowledge = load_knowledge()
    articles = knowledge.get("articles", [])

    if not articles:
        print("No articles found.", file=sys.stderr)
        sys.exit(1)

    # Filter for recent, high-scored articles
    high_score = [a for a in articles if a.get("score", 0) >= 50]
    high_score.sort(key=lambda x: x.get("score", 0), reverse=True)

    if not high_score:
        print("No high-scored articles found. Running with all articles.")
        high_score = articles[:10]

    content, slug = build_post_from_articles(high_score)

    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(TZ_JST)
    filename = f"{now.strftime('%Y-%m-%d')}-{slug}.md"
    filepath = POSTS_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Generated: {filepath}")
    return filepath


if __name__ == "__main__":
    print("=== Blog Post Generator ===")
    main()
