# -*- coding: utf-8 -*-
"""
四平台内容生成模块 - Gemini 版
"""
import json
import logging
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL, MCP_BRAND, COMPLIANCE_REPLACEMENTS

logger = logging.getLogger(__name__)
genai.configure(api_key=GEMINI_API_KEY)


CONTENT_PROMPT = """你是 MC Prime（持牌离岸 CFD 券商）的多平台内容创作者。

## 选题信息
- 事件: {event}
- 内容角度: {angle}
- 钩子: {hook}
- 核心观点: {core_message}
- 交易机会点: {trading_opportunity}
- 目标市场: {market}
- 语言: {language}

## MC Prime 品牌
- 名称: {brand_name}
- 特点: {brand_leverage}, {brand_spread}, {brand_platforms}
- 官网: {brand_website}
- 牌照: {brand_licenses}

## 合规红线
- 禁用词: 稳赚、包赚、保本、无风险、必涨、必跌、100%盈利
- 替换: "开户"→"注册体验账户"、"入金"→"存入资金"、"高杠杆"→"灵活杠杆"
- 结尾引流克制: "欢迎交流""想了解更多可看主页"
- 不做具体买卖推荐

## 请一次性产出以下四个平台完整内容

### 【知乎】800-1500 字
- 场景/故事引入 → 拆解分析 → 框架 → 结尾自然引流

### 【YouTube】5-8 分钟
- 3 个标题 A/B/C
- 封面文字（≤12 字）
- 5 个分镜场景（镜头+口播+B-roll关键词）
- 视频描述含时间戳
- 5 个标签

### 【Instagram】
- Reels 60 秒脚本（钩子3秒+主体50秒+CTA7秒）
- 静态帖 caption（150-220 字含 emoji）
- 9 图轮播每张 ≤20 字
- 15 个 hashtag

### 【抖音】60 秒
- 3 个标题 A/B/C
- 封面文字（≤10 字够炸）
- 分镜每 5 秒一段
- 3 个话题标签
- BGM 类型建议

## 输出 JSON 格式（严格）

{{
  "topic_id": {topic_id},
  "angle": "选题角度",
  "language": "{language}",
  "zhihu": {{
    "title": "回答标题",
    "content": "完整正文用 \\n\\n 分段"
  }},
  "youtube": {{
    "titles": ["标题A", "标题B", "标题C"],
    "thumbnail_text": "封面文字",
    "script": [
      {{"scene": 1, "shot": "镜头", "voiceover": "口播", "broll_keywords": ["kw1"]}}
    ],
    "description": "视频描述",
    "tags": ["tag1"]
  }},
  "instagram": {{
    "reels_script": {{"hook": "3s", "body": "50s", "cta": "7s"}},
    "caption": "静态帖文案",
    "carousel": [{{"slide": 1, "text": "第1张文字"}}],
    "hashtags": ["#tag1"]
  }},
  "douyin": {{
    "titles": ["A", "B", "C"],
    "cover_text": "封面",
    "script": [{{"time": "0-5s", "visual": "画面", "voiceover": "台词"}}],
    "hashtags": ["#外汇"],
    "bgm_style": "BGM"
  }}
}}

只返回 JSON，不要 markdown 代码块。
"""


def sanitize_content(text):
    if not isinstance(text, str):
        return text
    for old, new in COMPLIANCE_REPLACEMENTS.items():
        text = text.replace(old, new)
    return text


def sanitize_recursive(obj):
    if isinstance(obj, str):
        return sanitize_content(obj)
    if isinstance(obj, list):
        return [sanitize_recursive(i) for i in obj]
    if isinstance(obj, dict):
        return {k: sanitize_recursive(v) for k, v in obj.items()}
    return obj


def generate_content(topic, angle, language="zh-CN"):
    prompt = CONTENT_PROMPT.format(
        topic_id=topic.get("id"),
        event=topic.get("event"),
        angle=angle.get("angle"),
        hook=angle.get("hook"),
        core_message=angle.get("core_message"),
        trading_opportunity=angle.get("trading_opportunity", "无"),
        market=topic.get("market"),
        language=language,
        brand_name=MCP_BRAND["name"],
        brand_leverage=MCP_BRAND["leverage"],
        brand_spread=MCP_BRAND["spread"],
        brand_platforms=MCP_BRAND["platforms"],
        brand_website=MCP_BRAND["website"],
        brand_licenses=MCP_BRAND["licenses"],
    )

    try:
        model = genai.GenerativeModel(
            GEMINI_MODEL,
            generation_config={
                "max_output_tokens": 8000,
                "temperature": 0.7,
                "response_mime_type": "application/json",
            },
        )
        response = model.generate_content(prompt)
        raw = response.text.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.rsplit("```", 1)[0]

        result = json.loads(raw.strip())
        return sanitize_recursive(result)
    except Exception as e:
        logger.error(f"内容生成失败: {e}")
        return None


def format_content_markdown(content):
    if not content:
        return "生成失败"
    lines = [
        f"# 选题 #{content.get('topic_id')} · {content.get('angle')}",
        f"语言: {content.get('language')}",
        "",
        "---",
        "",
        "## 📘 知乎回答",
        "",
        f"**建议标题**: {content['zhihu']['title']}",
        "",
        content['zhihu']['content'],
        "",
        "---",
        "",
        "## 🎥 YouTube 视频脚本",
        "",
        "**标题 A/B/C**:",
    ]
    for t in content['youtube']['titles']:
        lines.append(f"- {t}")
    lines.extend([
        "",
        f"**封面文字**: {content['youtube']['thumbnail_text']}",
        "",
        "**分镜脚本**:",
        "",
    ])
    for scene in content['youtube']['script']:
        lines.extend([
            f"### 场景 {scene['scene']}",
            f"- **镜头**: {scene['shot']}",
            f"- **口播**: {scene['voiceover']}",
            f"- **B-roll**: {', '.join(scene['broll_keywords'])}",
            "",
        ])
    lines.extend([
        f"**视频描述**:\n{content['youtube']['description']}",
        "",
        f"**标签**: {', '.join(content['youtube']['tags'])}",
        "",
        "---",
        "",
        "## 📷 Instagram",
        "",
        f"**Reels 钩子 (3s)**: {content['instagram']['reels_script']['hook']}",
        f"**Reels 主体 (50s)**: {content['instagram']['reels_script']['body']}",
        f"**Reels CTA (7s)**: {content['instagram']['reels_script']['cta']}",
        "",
        f"**Caption**: {content['instagram']['caption']}",
        "",
        "**9图轮播**:",
    ])
    for slide in content['instagram']['carousel']:
        lines.append(f"- 图{slide['slide']}: {slide['text']}")
    lines.extend([
        "",
        f"**Hashtags**: {' '.join(content['instagram']['hashtags'])}",
        "",
        "---",
        "",
        "## 📱 抖音 60 秒",
        "",
        "**标题 A/B/C**:",
    ])
    for t in content['douyin']['titles']:
        lines.append(f"- {t}")
    lines.extend([
        "",
        f"**封面文字**: {content['douyin']['cover_text']}",
        "",
        "**分镜脚本**:",
        "",
    ])
    for scene in content['douyin']['script']:
        lines.append(f"- **{scene['time']}** | 画面: {scene['visual']} | 台词: {scene['voiceover']}")
    lines.extend([
        "",
        f"**Hashtags**: {' '.join(content['douyin']['hashtags'])}",
        f"**BGM**: {content['douyin']['bgm_style']}",
    ])
    return "\n".join(lines)
