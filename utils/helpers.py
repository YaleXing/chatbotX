"""
辅助函数模块
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from utils.logger import logger


def get_current_time() -> str:
    """获取当前时间字符串"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def extract_code_blocks(text: str) -> list[dict]:
    """
    从文本中提取代码块

    Args:
        text: 包含代码块的文本

    Returns:
        代码块列表，每个元素包含 language 和 code
    """
    # 匹配 ```language\ncode\n``` 格式
    pattern = r'```(\w*)\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)

    code_blocks = []
    for lang, code in matches:
        code_blocks.append({
            "language": lang if lang else "text",
            "code": code.strip()
        })

    return code_blocks


def is_image_message(message: str) -> bool:
    """
    判断是否是图片消息

    Args:
        message: 消息内容

    Returns:
        是否是图片消息
    """
    # 检查 CQ 码中的图片格式
    is_image = "[CQ:image," in message
    if is_image:
        logger.info(f"检测到图片消息: {message[:100]}...")
    return is_image


def extract_image_url(message: str) -> Optional[str]:
    """
    从图片消息中提取图片 URL

    Args:
        message: 图片消息

    Returns:
        图片 URL，如果没有则返回 None
    """
    # 匹配 CQ 码中的 URL（优先）
    pattern = r'\[CQ:image,[^\]]*url=([^\],]+)'
    match = re.search(pattern, message)

    if match:
        url = match.group(1)
        # 确保是 HTTP URL
        if url.startswith("http"):
            return url

    # 尝试匹配 file 字段
    pattern = r'\[CQ:image,[^\]]*file=([^\],]+)'
    match = re.search(pattern, message)

    if match:
        file = match.group(1)
        # 如果是 HTTP URL，直接返回
        if file.startswith("http"):
            return file
        # 如果是 base64 数据，需要转换
        if file.startswith("base64://"):
            # 需要下载 base64 数据并转换为 URL
            # 这里暂时返回 None，后续可以添加支持
            logger.warning("收到 base64 图片，暂不支持识别")
            return None
        # 如果是本地文件路径，需要下载
        if file.startswith("file:///") or not file.startswith("http"):
            logger.warning(f"收到本地图片文件: {file}")
            # 需要从 NapCat 下载图片
            return None

    return None


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除非法字符

    Args:
        filename: 原始文件名

    Returns:
        清理后的文件名
    """
    # 移除或替换非法字符
    illegal_chars = '<>:"/\\|?*'
    for char in illegal_chars:
        filename = filename.replace(char, '_')

    # 限制长度
    if len(filename) > 200:
        filename = filename[:200]

    return filename


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小

    Args:
        size_bytes: 文件大小（字节）

    Returns:
        格式化后的文件大小字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0

    return f"{size_bytes:.2f} TB"


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    截断文本

    Args:
        text: 原始文本
        max_length: 最大长度

    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - 3] + "..."


def is_command(message: str) -> bool:
    """
    判断是否是命令

    Args:
        message: 消息内容

    Returns:
        是否是命令
    """
    # 以 / 或 # 开头的视为命令
    return message.startswith('/') or message.startswith('#')


def parse_command(message: str) -> tuple[str, list[str]]:
    """
    解析命令

    Args:
        message: 命令消息

    Returns:
        (命令名, 参数列表)
    """
    # 移除前缀
    if message.startswith('/') or message.startswith('#'):
        message = message[1:]

    # 分割命令和参数
    parts = message.split()
    command = parts[0] if parts else ""
    args = parts[1:] if len(parts) > 1 else []

    return command, args
