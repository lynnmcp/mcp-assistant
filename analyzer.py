# -*- coding: utf-8 -*-
"""
新闻分析模块 - Gemini 版
"""
import json
import logging
import google.generativeai as genai
from config import (
    GEMINI_API_KEY, GEMINI_MODEL,
    DAILY_TOPIC_COUNT, IMPORTANCE_THRESHOLD
)
from sources import PRIORITY_KEYWORDS

logger = logging.getLogger(__name__)

genai.configure(api_key=GEMINI_API_KEY)


ANALYSIS_PROMPT = """你是 MC Prime（一家持有 CySEC/FSA/FSC 牌照的离岸 CFD 券商）的内容策略分析师，服务对象是中国和韩国市场的散户交易者。

请分析今天抓取的以下 {news_count} 条外汇市场新闻，产出 {topic_count} 个最适合做社交媒体内容的选题。

## 抓取的新闻列表
{news_json}

## 你的任务

1. **聚类去重**：把讲同一件事的新闻合并
2. **重要性评估**：基于以下维度打分（1-10 分）
   - 对散户交易者的实操影响
   - 话题热度
   - 时效性
   - 交易机会
3. **选题提炼**：为每个入选事件设计 1-2 个内容角度
4. **平台适配**：判断适合哪些平台
5. **合规提示**：标注是否有敏感表述需要规避

## 选题优先级

- 优先：美联储/中国央行/韩国央行政策、非农 CPI GDP 等宏观数据、人民币/韩元汇率异动
- 中优先：技术分析教学、交易误区、平台功能科普
- 低优先：纯行情播报

## 品牌合规

- 禁用词: 稳赚、包赚、保本、无风险
- 替换: "开户"→"注册体验账户"、"入金"→"存入资金"、"高杠杆"→"灵活杠杆"
- 引流克制: 结尾轻度提示，不硬广

## 输出格式

严格按 JSON 格式输出，不要有任何前后缀说明:

{{
  "date": "2026-08-17",
  "market_summary": {{
    "cn": "一句话概括中国焦点",
    "kr": "一句话概括韩国焦点",
    "global": "一句话概括全球宏观"
  }},
  "topics": [
    {{
      "id": 1,
      "importance": 9,
      "market": "中国 / 韩国 / 全球",
      "event": "事件一句话描述",
      "source_titles": ["原始标题1"],
      "angles": [
        {{
          "angle": "内容角度",
          "hook": "开头钩子",
          "core_message": "核心观点",
          "trading_opportunity": "交易机会点",
          "best_platforms": ["zhihu", "youtube", "douyin", "instagram"],
          "content_type": "科普/深度/短视频/图文",
          "estimated_reach": "预期效果",
          "compliance_notes": "合规提示"
        }}
      ],
      "sensitive": false
    }}
  ]
}}

只返回 JSON，不要 markdown 代码块，不要解释。
"""


def score_by_keywords(title, summary):
    text = (title + " " + summary).lower()
    score = 0
    for kw in PRIORITY_KEYWORDS:
        if kw.lower() in text:
            score += 1
    return score


def prefilter_news(news_list, top_n=60):
    if len(news_list) <= top_n:
        return news_list
    scored = [(n, score_by_keywords(n["title"], n.get("summary", ""))) for n in news_list]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [n for n, _ in scored[:top_n]]


def call_gemini(prompt, max_tokens=8000):
    """调用 Gemini API"""
    model = genai.GenerativeModel(
        GEMINI_MODEL,
        generation_config={
            "max_output_tokens": max_tokens,
            "temperature": 0.7,
            "response_mime_type": "application/json",
        },
    )
    response = model.generate_content(prompt)
    return response.text


def analyze_news(news_list):
    filtered = prefilter_news(news_list, top_n=60)
    logger.info(f"Sending {len(filtered)} news items to Gemini")

    simplified = [
        {
            "id": i,
            "market": n["market"],
            "title": n["title"],
            "summary": n.get("summary", "")[:200],
            "source": n["source"],
        }
        for i, n in enumerate(filtered)
    ]

    prompt = ANALYSIS_PROMPT.format(
        news_count=len(simplified),
        topic_count=DAILY_TOPIC_COUNT,
        news_json=json.dumps(simplified, ensure_ascii=False, indent=2),
    )

    try:
        raw = call_gemini(prompt, max_tokens=8000).strip()

        # 清理可能的 markdown 代码块
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.rsplit("```", 1)[0]

        result = json.loads(raw.strip())

        result["topics"] = [
            t for t in result.get("topics", [])
            if t.get("importance", 0) >= IMPORTANCE_THRESHOLD
        ]

        title_to_link = {n["title"]: n.get("link", "") for n in news_list}
        for topic in result["topics"]:
            topic["source_links"] = [
                title_to_link.get(t, "") for t in topic.get("source_titles", [])
            ]

        logger.info(f"分析完成: {len(result['topics'])} 个选题")
        return result
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败: {e}\n原始输出:\n{raw[:1000]}")
        return {"date": "", "market_summary": {}, "topics": []}
    except Exception as e:
        logger.error(f"Gemini API 调用失败: {e}")
        return {"date": "", "market_summary": {}, "topics": []}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from fetcher import fetch_all
    news = fetch_all()
    result = analyze_news(news)
    print(json.dumps(result, ensure_ascii=False, indent=2))
