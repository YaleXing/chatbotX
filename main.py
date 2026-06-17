"""
QQ 聊天机器人入口
"""

import asyncio
import signal
import sys
from pathlib import Path

from core.bot import ChatBot
from utils.logger import logger


def main():
    """主函数"""
    # 确保工作目录正确
    script_dir = Path(__file__).parent
    import os
    os.chdir(script_dir)

    logger.info("=" * 50)
    logger.info("QQ 聊天机器人启动中...")
    logger.info("=" * 50)

    # 创建机器人
    try:
        bot = ChatBot()
    except Exception as e:
        logger.error(f"创建机器人失败: {e}")
        sys.exit(1)

    # 运行机器人
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
