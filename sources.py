# -*- coding: utf-8 -*-
"""
新闻源清单
类型说明:
  rss  - 标准 RSS 订阅（最稳定）
  html - 网页抓取（需要 selector）
"""

NEWS_SOURCES = [
    # ========== 中国市场 ==========
    {
        "name": "金十数据-外汇",
        "market": "中国",
        "type": "html",
        "url": "https://www.jin10.com/example.html",
        "selector": "div.jin-list-item",
        "title_selector": "h3",
        "link_selector": "a",
    },
    {
        "name": "华尔街见闻-外汇",
        "market": "中国",
        "type": "rss",
        "url": "https://wallstreetcn.com/rss.xml",
    },
    {
        "name": "东方财富-外汇频道",
        "market": "中国",
        "type": "html",
        "url": "https://forex.eastmoney.com/news.html",
        "selector": "li.item",
        "title_selector": "a",
        "link_selector": "a",
    },
    {
        "name": "新浪财经-外汇",
        "market": "中国",
        "type": "rss",
        "url": "https://finance.sina.com.cn/roll/index.d.html?cid=56592&page=1",
    },
    {
        "name": "PBoC-中国人民银行公告",
        "market": "中国",
        "type": "html",
        "url": "http://www.pbc.gov.cn/goutongjiaoliu/113456/113469/index.html",
        "selector": "td.hei12jj",
        "title_selector": "a",
        "link_selector": "a",
    },

    # ========== 韩国市场 ==========
    {
        "name": "Yonhap Infomax FX",
        "market": "韩国",
        "type": "rss",
        "url": "https://news.einfomax.co.kr/rss/S1N9.xml",
    },
    {
        "name": "Hankyung 外汇",
        "market": "韩国",
        "type": "html",
        "url": "https://www.hankyung.com/finance/forex",
        "selector": "div.article-list",
        "title_selector": "h3.news-tit",
        "link_selector": "a",
    },
    {
        "name": "Maeil Business FX",
        "market": "韩国",
        "type": "html",
        "url": "https://www.mk.co.kr/news/economy/",
        "selector": "li.news_node",
        "title_selector": "h3",
        "link_selector": "a",
    },
    {
        "name": "Bank of Korea 公告",
        "market": "韩国",
        "type": "html",
        "url": "https://www.bok.or.kr/portal/bbs/B0000338/list.do?menuNo=200761",
        "selector": "td.title",
        "title_selector": "a",
        "link_selector": "a",
    },

    # ========== 全球宏观 ==========
    {
        "name": "Reuters FX",
        "market": "全球宏观",
        "type": "rss",
        "url": "https://feeds.reuters.com/reuters/USdollarReport",
    },
    {
        "name": "ForexLive",
        "market": "全球宏观",
        "type": "rss",
        "url": "https://www.forexlive.com/feed/news",
    },
    {
        "name": "Investing.com FX News",
        "market": "全球宏观",
        "type": "rss",
        "url": "https://www.investing.com/rss/news_1.rss",
    },
    {
        "name": "FXStreet",
        "market": "全球宏观",
        "type": "rss",
        "url": "https://www.fxstreet.com/rss/news",
    },
]

# 高优先级关键词（命中后自动提升重要性评分）
PRIORITY_KEYWORDS = [
    # 中英韩混合关键词
    "美联储", "Fed", "FOMC", "利率", "rate", "금리",
    "人民币", "CNY", "USD/CNY", "汇率",
    "韩元", "KRW", "USD/KRW", "원화",
    "日元", "JPY", "円",
    "央行", "PBoC", "BOK", "한국은행", "中国人民银行",
    "非农", "NFP", "CPI", "PMI", "GDP",
    "降息", "加息", "cut rate", "hike",
    "外汇储备", "reserves",
    "干预", "intervention", "개입",
]
