#!/usr/bin/env python3
"""
Article collection script for Storage & Optical Tech Blog.
Scrapes target websites for latest articles about storage and optical technologies.
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SITES_FILE = DATA_DIR / "sites.json"
KNOWLEDGE_FILE = DATA_DIR / "knowledge.json"


def load_sites() -> dict:
    with open(SITES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_knowledge() -> dict:
    if KNOWLEDGE_FILE.exists():
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_run": None, "articles": []}


def save_knowledge(data: dict):
    with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def fetch_page(url: str) -> Optional[str]:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"  [WARN] Failed to fetch {url}: {e}", file=sys.stderr)
        return None


def extract_articles_from_html(html: str, site_url: str) -> list:
    """Generic article extraction - override per-site for better results."""
    soup = BeautifulSoup(html, "html.parser")
    articles = []

    # Common article link patterns
    for tag in soup.find_all(["a", "h2", "h3", "article"]):
        links = tag.find_all("a") if tag.name in ["h2", "h3", "article"] else [tag]
        for a in links:
            href = a.get("href", "")
            text = a.get_text(strip=True)
            if not href or not text or len(text) < 15:
                continue
            if any(skip in href for skip in ["#", "javascript:", "login", "signup"]):
                continue
            full_url = urljoin(site_url, href)
            if full_url.startswith(("http://", "https://")):
                articles.append({"title": text, "url": full_url})

    return articles


def score_article(article: dict, keywords: list, site_name: str) -> dict:
    title = article.get("title", "")
    title_lower = title.lower()
    matched = [kw for kw in keywords if kw.lower() in title_lower]
    score = min(len(matched) * 15, 60)
    if score > 0:
        score += 15  # topic match bonus
    if site_name in ["ServeTheHome", "AnandTech", "IEEE"]:
        score += 10  # credibility bonus
    article["score"] = min(score, 100)
    article["matched_keywords"] = matched
    return article


def collect():
    sites = load_sites()
    knowledge = load_knowledge()
    all_keywords = []
    for cat in ["storage", "optical"]:
        all_keywords.extend(sites.get("keywords", {}).get(cat, []))

    new_articles = []

    for category, site_list in [
        ("storage", sites.get("storage_sites", [])),
        ("optical", sites.get("optical_sites", [])),
        ("vendor", sites.get("vendor_blogs", [])),
    ]:
        for site in site_list:
            print(f"  [{category}] {site['name']} ...", end=" ")
            html = fetch_page(site["url"])
            if not html:
                print("skip")
                continue
            found = extract_articles_from_html(html, site["url"])
            for art in found[:10]:
                art["source"] = site["name"]
                art["category"] = category
                art["fetched_at"] = datetime.now(timezone.utc).isoformat()
                art = score_article(art, all_keywords, site["name"])
                new_articles.append(art)
            print(f"{len(found)} articles")

    # Deduplicate by URL
    seen_urls = {a["url"] for a in knowledge["articles"]}
    unique_new = [a for a in new_articles if a["url"] not in seen_urls]
    unique_new.sort(key=lambda x: x.get("score", 0), reverse=True)

    knowledge["last_run"] = datetime.now(timezone.utc).isoformat()
    knowledge["articles"] = unique_new + knowledge["articles"]
    save_knowledge(knowledge)

    print(f"\nCollected {len(unique_new)} new articles (total: {len(knowledge['articles'])})")
    print(f"Top articles by score:")
    for a in unique_new[:10]:
        print(f"  [{a['score']:2d}] {a['source']}: {a['title'][:60]}")

    return unique_new


if __name__ == "__main__":
    print("=== Storage & Optical Tech Article Collector ===")
    collect()
