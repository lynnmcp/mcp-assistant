# -*- coding: utf-8 -*-
"""
MC Prime 内容雷达 - GitHub Actions 版主控

三种运行模式:
  python main.py briefing      # 每天 UTC 00:00 (北京 08:00) 跑
  python main.py poll_once     # 每 10 分钟跑一次，处理 Telegram 指令
  python main.py test          # 连通性测试
"""
import sys
import json
import logging
import traceback
from datetime import datetime

from config import OUTPUT_DIR, LOG_DIR
from fetcher import fetch_all
from analyzer import analyze_news
from telegram_bot import (
    send_message, send_document,
    format_daily_briefing, poll_commands
)
from content_generator import generate_content, format_content_markdown
from video_generator import generate_video

LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOG_DIR / f"radar_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("main")

OFFSET_FILE = OUTPUT_DIR / "last_update_id.txt"


def run_briefing():
    logger.info("=" * 50)
    logger.info("开始每日晨报流程")
    try:
        news = fetch_all()
        if not news:
            send_message("⚠️ 今日无新闻抓取到，请检查数据源")
            return

        analysis = analyze_news(news)
        if not analysis.get("topics"):
            send_message("⚠️ 分析结果为空")
            return

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime("%Y%m%d")
        topic_file = OUTPUT_DIR / f"topics_{date_str}.json"
        topic_file.write_text(
            json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (OUTPUT_DIR / "topics_latest.json").write_text(
            json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        send_message(format_daily_briefing(analysis))
        logger.info(f"晨报推送完成，{len(analysis['topics'])} 个选题")
    except Exception as e:
        logger.error(f"晨报出错: {e}\n{traceback.format_exc()}")
        send_message(f"❌ 晨报出错: {str(e)[:200]}")


def run_poll_once():
    logger.info("轮询 Telegram 指令...")
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        commands = poll_commands(offset_file=str(OFFSET_FILE))
        if not commands:
            logger.info("无新指令")
            return
        logger.info(f"收到 {len(commands)} 条指令")
        for cmd_name, args in commands:
            if cmd_name == "gen":
                handle_gen_command(args)
    except Exception as e:
        logger.error(f"轮询出错: {e}\n{traceback.format_exc()}")
        send_message(f"❌ 轮询出错: {str(e)[:200]}")


def handle_gen_command(args):
    ids = args["ids"]
    opts = args["opts"]
    make_video = "video" in opts
    lang = "ko" if "ko" in opts else "zh-CN"

    date_str = datetime.now().strftime("%Y%m%d")
    topic_file = OUTPUT_DIR / f"topics_{date_str}.json"
    if not topic_file.exists():
        latest = OUTPUT_DIR / "topics_latest.json"
        if latest.exists():
            topic_file = latest
        else:
            candidates = sorted(OUTPUT_DIR.glob("topics_*.json"), reverse=True)
            if not candidates:
                send_message("❌ 找不到选题文件，请先运行 briefing")
                return
            topic_file = candidates[0]

    analysis = json.loads(topic_file.read_text(encoding="utf-8"))
    topics_by_id = {t["id"]: t for t in analysis["topics"]}

    send_message(f"⏳ 开始生成选题 {ids} 的内容包，1-3 分钟...")

    for tid in ids:
        topic = topics_by_id.get(tid)
        if not topic:
            send_message(f"⚠️ 未找到选题 #{tid}")
            continue

        angle = topic["angles"][0]
        content = generate_content(topic, angle, language=lang)
        if not content:
            send_message(f"❌ 选题 #{tid} 生成失败")
            continue

        md = format_content_markdown(content)
        md_path = OUTPUT_DIR / f"content_{date_str}_topic{tid}_{lang}.md"
        md_path.write_text(md, encoding="utf-8")

        json_path = OUTPUT_DIR / f"content_{date_str}_topic{tid}_{lang}.json"
        json_path.write_text(
            json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        send_document(str(md_path), caption=f"📄 选题 #{tid} 内容包（{lang}）")

        video_result = generate_video(
            content,
            level="both" if make_video else "level1",
            language="ko" if lang == "ko" else "zh",
        )
        level1_path = OUTPUT_DIR / f"video_level1_{date_str}_topic{tid}.json"
        level1_path.write_text(
            json.dumps(video_result.get("level1", {}), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        send_document(str(level1_path), caption=f"🎬 选题 #{tid} 视频素材包")

        if make_video:
            video_url = video_result.get("level2_video_url")
            if video_url:
                send_message(f"🎥 选题 #{tid} 数字人视频: {video_url}")
            else:
                send_message(f"⚠️ 选题 #{tid} 数字人视频失败")

    send_message("✅ 全部生成完成")


def run_test():
    send_message("✅ MC Prime 内容雷达 · GitHub Actions 版连接测试成功")
    print("Telegram 已发送测试消息")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "briefing"
    if mode == "briefing":
        run_briefing()
    elif mode == "poll_once":
        run_poll_once()
    elif mode == "test":
        run_test()
    else:
        print("用法: python main.py [briefing|poll_once|test]")
