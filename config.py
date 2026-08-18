# -*- coding: utf-8 -*-
"""
MC Prime 内容雷达 - Gemini 免费版配置
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"

# ========== API 密钥 ==========
# Google Gemini API - 免费申请: https://aistudio.google.com/apikey
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# HeyGen（可选）
HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY", "")
HEYGEN_AVATAR_ID = os.getenv("HEYGEN_AVATAR_ID", "")
HEYGEN_VOICE_ID_ZH = os.getenv("HEYGEN_VOICE_ID_ZH", "")
HEYGEN_VOICE_ID_KO = os.getenv("HEYGEN_VOICE_ID_KO", "")

if not GEMINI_API_KEY:
    raise RuntimeError("缺少 GEMINI_API_KEY，请在 GitHub Secrets 或 .env 配置")
if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    raise RuntimeError("缺少 Telegram 配置")

# ========== Gemini 模型 ==========
# gemini-2.5-flash: 免费额度大，速度快，效果好
# gemini-1.5-pro: 更强但免费额度更小
GEMINI_MODEL = "gemini-2.5-flash"

# ========== 分析参数 ==========
DAILY_TOPIC_COUNT = 12
IMPORTANCE_THRESHOLD = 6

TARGET_MARKETS = ["中国", "韩国", "全球宏观"]

PLATFORMS = {
    "zhihu": {"name": "知乎", "lang": "zh-CN", "length": "long"},
    "youtube": {"name": "YouTube", "lang": "zh-CN", "length": "medium"},
    "instagram": {"name": "Instagram", "lang": "en/ko", "length": "short"},
    "douyin": {"name": "抖音", "lang": "zh-CN", "length": "short"},
}

MCP_BRAND = {
    "name": "MC Prime",
    "slogan": "赢势无形 · 交易无界",
    "leverage": "灵活杠杆（最高 1:500）",
    "spread": "点差低至 0.0 pips",
    "min_deposit": "$50",
    "platforms": "MT4 / MT5",
    "licenses": "CySEC 299/16, FSA SD184, FSC GB23201764",
    "website": "www.mc-prime.com",
    "contact": "service@mc-prime.com",
}

COMPLIANCE_REPLACEMENTS = {
    "开户": "注册体验账户",
    "入金": "存入资金",
    "高杠杆": "灵活杠杆",
    "包赚": "",
    "稳赚": "",
    "保本": "",
    "无风险": "",
}
