"""
NapCat 文件下载帮助模块
"""

import aiohttp
from pathlib import Path
from typing import Optional

from utils.logger import logger


class NapCatFileHelper:
    """NapCat 文件下载帮助类"""

    def __init__(self, api_url: str, access_token: str = ""):
        """
        初始化文件帮助类

        Args:
            api_url: NapCat API 地址
            access_token: Access Token
        """
        self.api_url = api_url
        self.access_token = access_token

        # 临时文件目录
        self.temp_dir = Path("data/temp")
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def download_image(self, file_id: str) -> Optional[str]:
        """
        下载图片文件

        Args:
            file_id: 文件 ID（CQ 码中的 file 字段）

        Returns:
            本地文件路径，失败返回 None
        """
        try:
            # 构建请求头
            headers = {"Content-Type": "application/json"}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"

            # 调用 /get_file 接口
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/get_file",
                    params={"file_id": file_id},
                    headers=headers
                ) as resp:
                    if resp.status != 200:
                        logger.error(f"获取文件信息失败: {resp.status}")
                        return None

                    result = await resp.json()
                    if result.get("status") != "ok":
                        logger.error(f"获取文件信息失败: {result}")
                        return None

                    data = result.get("data", {})
                    file_path = data.get("file", "")

                    if file_path and Path(file_path).exists():
                        logger.info(f"图片文件路径: {file_path}")
                        return file_path

                    logger.warning(f"图片文件不存在: {file_path}")
                    return None

        except Exception as e:
            logger.error(f"下载图片失败: {e}")
            return None

    async def download_record(self, file_id: str) -> Optional[str]:
        """
        下载语音文件

        Args:
            file_id: 文件 ID（CQ 码中的 file 字段）

        Returns:
            本地文件路径，失败返回 None
        """
        try:
            # 构建请求头
            headers = {"Content-Type": "application/json"}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"

            # 调用 /get_record 接口
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/get_record",
                    params={"file_id": file_id, "out_format": "wav"},
                    headers=headers
                ) as resp:
                    if resp.status != 200:
                        logger.error(f"获取语音信息失败: {resp.status}")
                        return None

                    result = await resp.json()
                    if result.get("status") != "ok":
                        logger.error(f"获取语音信息失败: {result}")
                        return None

                    data = result.get("data", {})
                    file_path = data.get("file", "")

                    if file_path and Path(file_path).exists():
                        logger.info(f"语音文件路径: {file_path}")
                        return file_path

                    logger.warning(f"语音文件不存在: {file_path}")
                    return None

        except Exception as e:
            logger.error(f"下载语音失败: {e}")
            return None

    def extract_file_id(self, cq_message: str) -> Optional[str]:
        """
        从 CQ 码中提取文件 ID

        Args:
            cq_message: CQ 码消息

        Returns:
            文件 ID
        """
        import re

        # 匹配 file=xxx 格式
        pattern = r'\[CQ:(?:image|record),[^\]]*file=([^\],]+)'
        match = re.search(pattern, cq_message)

        if match:
            return match.group(1)

        return None
