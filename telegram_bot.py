# -*- coding: utf-8 -*-
"""
Telegram Bot 模块
功能:
  1. 推送每日选题清单
  2. 接收 /generate 1,3,5 这样的指令来生成内容
  3. 把生成好的内容包发回给你
"""
import json
import logging
import requests
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def send_message(text, chat_id=None, parse_mode="HTML"):
    """发送文本消息"""
    chat_id = chat_id or TELEGRAM_CHAT_ID
    # Telegram 单条消息 4096 字符上限，超长自动分段
    max_len = 3800
    if len(text) <= max_len:
        chunks = [text]
    else:
        chunks = []
        while text:
            chunks.append(text[:max_len])
            text = text[max_len:]

    for chunk in chunks:
        try:
            resp = requests.post(
                f"{BASE_URL}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": True,
                },
                timeout=15,
            )
            if resp.status_code != 200:
                logger.error(f"Telegram send failed: {resp.text}")
        except Exception as e:
            logger.error(f"Telegram error: {e}")


def send_document(filepath, caption="", chat_id=None):
    """发送文件（生成好的内容包）"""
    chat_id = chat_id or TELEGRAM_CHAT_ID
    try:
        with open(filepath, "rb") as f:
            resp = requests.post(
                f"{BASE_URL}/sendDocument",
                data={"chat_id": chat_id, "caption": caption},
                files={"document": f},
                timeout=60,
            )
            if resp.status_code != 200:
                logger.error(f"Telegram doc send failed: {resp.text}")
    except Exception as e:
        logger.error(f"Telegram doc error: {e}")


def format_daily_briefing(analysis_result):
    """把分析结果格式化成 Telegram 消息"""
    date = analysis_result.get("date", datetime.now().strftime("%Y-%m-%d"))
    summary = analysis_result.get("market_summary", {})
    topics = analysis_result.get("topics", [])

    lines = [
        f"📊 <b>MC Prime 每日内容雷达</b>",
        f"🗓 {date}",
        "",
        f"<b>🇨🇳 中国市场</b>: {summary.get('cn', 'N/A')}",
        f"<b>🇰🇷 韩国市场</b>: {summary.get('kr', 'N/A')}",
        f"<b>🌏 全球宏观</b>: {summary.get('global', 'N/A')}",
        "",
        f"<b>今日候选选题（共 {len(topics)} 个）</b>",
        "━━━━━━━━━━━━━━",
    ]

    for topic in topics:
        tid = topic.get("id")
        imp = topic.get("importance")
        market = topic.get("market")
        event = topic.get("event")
        stars = "⭐" * min(imp // 2, 5)

        lines.append(f"\n<b>【{tid}】{stars} 热度 {imp}/10</b>")
        lines.append(f"📍 {market}｜{event}")

        for i, angle in enumerate(topic.get("angles", []), 1):
            platforms = "/".join([
                {"zhihu": "知乎", "youtube": "YT", "instagram": "IG", "douyin": "抖音"}.get(p, p)
                for p in angle.get("best_platforms", [])
            ])
            lines.append(f"  · {angle.get('angle')}")
            lines.append(f"    钩子: {angle.get('hook')}")
            lines.append(f"    平台: {platforms}｜{angle.get('content_type', '')}")
            if angle.get("compliance_notes"):
                lines.append(f"    ⚠️ {angle['compliance_notes']}")

    lines.extend([
        "",
        "━━━━━━━━━━━━━━",
        "<b>如何生成内容：</b>",
        "回复我以下指令，我就自动生成对应选题的全平台内容包：",
        "",
        "<code>/gen 1,3,5</code>  → 生成选题 1、3、5 的四平台文案 + 视频脚本",
        "<code>/gen 2 video</code>  → 加做 HeyGen 数字人成品视频（Level 2）",
        "<code>/gen 4 ko</code>  → 生成韩语版本",
    ])

    return "\n".join(lines)


def poll_commands(offset_file="last_update_id.txt"):
    """
    轮询 Telegram 获取你发的指令
    返回: (command, args) 或 None
    """
    try:
        try:
            with open(offset_file) as f:
                last_id = int(f.read().strip())
        except (FileNotFoundError, ValueError):
            last_id = 0

        resp = requests.get(
            f"{BASE_URL}/getUpdates",
            params={"offset": last_id + 1, "timeout": 30},
            timeout=40,
        )
        updates = resp.json().get("result", [])
        commands = []
        for update in updates:
            update_id = update["update_id"]
            with open(offset_file, "w") as f:
                f.write(str(update_id))
            msg = update.get("message", {})
            if str(msg.get("chat", {}).get("id")) != str(TELEGRAM_CHAT_ID):
                continue
            text = msg.get("text", "").strip()
            if text.startswith("/gen"):
                parts = text[4:].strip().split()
                if not parts:
                    continue
                # 解析 id 列表
                ids = [int(x) for x in parts[0].split(",") if x.isdigit()]
                opts = parts[1:] if len(parts) > 1 else []
                commands.append(("gen", {"ids": ids, "opts": opts}))
        return commands
    except Exception as e:
        logger.error(f"Poll commands error: {e}")
        return []


if __name__ == "__main__":
    send_message("✅ MC Prime 内容雷达连接测试成功")
