# -*- coding: utf-8 -*-
"""
视频生成模块
Level 1: 生成给剪辑师用的素材包（脚本 + B-roll 关键词 + 数据图表建议）
Level 2: 调用 HeyGen API 生成 AI 数字人成品视频
"""
import json
import time
import logging
import requests
from config import (
    HEYGEN_API_KEY, HEYGEN_AVATAR_ID,
    HEYGEN_VOICE_ID_ZH, HEYGEN_VOICE_ID_KO,
)

logger = logging.getLogger(__name__)

HEYGEN_API_BASE = "https://api.heygen.com/v2"


# ============ Level 1: 素材包 ============

def build_level1_package(content):
    """
    生成 Level 1 素材包：
    - 完整口播稿（用于配音）
    - 分镜表（可直接给剪辑师）
    - B-roll 素材搜索关键词汇总
    - 建议的图表数据
    """
    yt = content.get("youtube", {})
    dy = content.get("douyin", {})

    voiceover_full = "\n\n".join([s.get("voiceover", "") for s in yt.get("script", [])])
    all_broll = []
    for s in yt.get("script", []):
        all_broll.extend(s.get("broll_keywords", []))

    package = {
        "type": "level_1_editable",
        "topic_id": content.get("topic_id"),
        "youtube_voiceover": voiceover_full,
        "youtube_shot_list": yt.get("script", []),
        "youtube_broll_keywords": list(set(all_broll)),
        "douyin_shot_list": dy.get("script", []),
        "suggested_stock_footage": [
            "Pexels: " + kw for kw in list(set(all_broll))[:5]
        ],
        "suggested_charts": [
            "K线走势图 - 相关货币对最近 5 天走势",
            "对比条形图 - 数据前后对比",
            "文字动画卡片 - 关键数字放大展示",
        ],
        "tts_ready_script": voiceover_full,
    }
    return package


# ============ Level 2: HeyGen 数字人 ============

def create_heygen_video(script, language="zh"):
    """
    调用 HeyGen API 生成数字人视频
    返回视频 URL（需要几分钟渲染）
    """
    if not HEYGEN_API_KEY or not HEYGEN_AVATAR_ID:
        logger.warning("HeyGen not configured, skipping Level 2 video")
        return None

    voice_id = HEYGEN_VOICE_ID_KO if language == "ko" else HEYGEN_VOICE_ID_ZH

    headers = {
        "X-Api-Key": HEYGEN_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": HEYGEN_AVATAR_ID,
                    "avatar_style": "normal",
                },
                "voice": {
                    "type": "text",
                    "input_text": script,
                    "voice_id": voice_id,
                },
                "background": {
                    "type": "color",
                    "value": "#0A0E1A",  # MC Prime 品牌色
                },
            }
        ],
        "dimension": {"width": 1920, "height": 1080},
        "aspect_ratio": "16:9",
    }

    try:
        resp = requests.post(
            f"{HEYGEN_API_BASE}/video/generate",
            headers=headers,
            json=payload,
            timeout=30,
        )
        if resp.status_code != 200:
            logger.error(f"HeyGen create failed: {resp.text}")
            return None
        video_id = resp.json().get("data", {}).get("video_id")
        if not video_id:
            return None
        logger.info(f"HeyGen video created: {video_id}, polling...")
        return poll_heygen_video(video_id, headers)
    except Exception as e:
        logger.error(f"HeyGen API error: {e}")
        return None


def poll_heygen_video(video_id, headers, max_wait=600):
    """轮询直到视频渲染完成"""
    start = time.time()
    while time.time() - start < max_wait:
        try:
            resp = requests.get(
                f"{HEYGEN_API_BASE}/video_status.get?video_id={video_id}",
                headers=headers,
                timeout=15,
            )
            data = resp.json().get("data", {})
            status = data.get("status")
            if status == "completed":
                return data.get("video_url")
            if status == "failed":
                logger.error(f"HeyGen render failed: {data}")
                return None
            time.sleep(15)
        except Exception as e:
            logger.error(f"HeyGen poll error: {e}")
            time.sleep(15)
    logger.warning("HeyGen poll timeout")
    return None


def generate_video(content, level="both", language="zh"):
    """
    统一入口
    level: 'level1' | 'level2' | 'both'
    """
    result = {"topic_id": content.get("topic_id")}

    if level in ("level1", "both"):
        result["level1"] = build_level1_package(content)

    if level in ("level2", "both"):
        # 用 YouTube 完整口播稿做数字人视频
        yt = content.get("youtube", {})
        script = "\n\n".join([s.get("voiceover", "") for s in yt.get("script", [])])
        # HeyGen 单次口播不宜过长，超过 500 字建议截取核心段
        if len(script) > 500:
            script = script[:500]
        video_url = create_heygen_video(script, language=language)
        result["level2_video_url"] = video_url

    return result
