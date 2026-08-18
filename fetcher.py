# -*- coding: utf-8 -*-
"""
新闻抓取模块
从配置的所有新闻源抓取当天新闻
"""
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import urljoin
import time
import logging
from sources import NEWS_SOURCES

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9,ko;q=0.8,en;q=0.7",
}


def fetch_rss(source):
    """抓取 RSS 源"""
    news_items = []
    try:
        feed = feedparser.parse(source["url"])
        # 只取过去 24 小时的
        cutoff = datetime.now() - timedelta(hours=24)
        for entry in feed.entries[:30]:  # 单源最多 30 条
            try:
                # 解析发布时间
                pub_time = datetime.now()
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    pub_time = datetime(*entry.published_parsed[:6])
                if pub_time < cutoff:
                    continue

                summary = ""
                if hasattr(entry, "summary"):
                    summary = BeautifulSoup(entry.summary, "html.parser").get_text()[:500]

                news_items.append({
                    "source": source["name"],
                    "market": source["market"],
                    "title": entry.title.strip(),
                    "link": entry.link,
                    "summary": summary,
                    "pub_time": pub_time.isoformat(),
                })
            except Exception as e:
                logger.warning(f"Parse RSS entry failed: {e}")
                continue
    except Exception as e:
        logger.error(f"Fetch RSS {source['name']} failed: {e}")
    return news_items


def fetch_html(source):
    """抓取 HTML 页面"""
    news_items = []
    try:
        resp = requests.get(source["url"], headers=HEADERS, timeout=15)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select(source["selector"])[:20]

        for item in items:
            try:
                title_el = item.select_one(source["title_selector"])
                link_el = item.select_one(source["link_selector"])
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title or len(title) < 5:
                    continue

                link = ""
                if link_el and link_el.get("href"):
                    link = urljoin(source["url"], link_el["href"])

                news_items.append({
                    "source": source["name"],
                    "market": source["market"],
                    "title": title,
                    "link": link,
                    "summary": "",
                    "pub_time": datetime.now().isoformat(),
                })
            except Exception as e:
                logger.warning(f"Parse HTML item failed: {e}")
                continue
    except Exception as e:
        logger.error(f"Fetch HTML {source['name']} failed: {e}")
    return news_items


def fetch_all():
    """抓取所有配置的新闻源，返回合并去重后的列表"""
    all_news = []
    for source in NEWS_SOURCES:
        logger.info(f"Fetching: {source['name']} ({source['market']})")
        if source["type"] == "rss":
            items = fetch_rss(source)
        else:
            items = fetch_html(source)
        all_news.extend(items)
        time.sleep(1)  # 礼貌延迟

    # 基于标题去重
    seen_titles = set()
    unique = []
    for item in all_news:
        # 标题前 20 字用作去重键（避免同一事件不同标题）
        key = item["title"][:20]
        if key not in seen_titles:
            seen_titles.add(key)
            unique.append(item)

    logger.info(f"Total fetched: {len(all_news)}, after dedup: {len(unique)}")
    return unique


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    news = fetch_all()
    print(f"\n共抓取 {len(news)} 条新闻\n")
    for n in news[:5]:
        print(f"[{n['market']}] {n['title']}")
