"""
平台基类
定义统一的消息平台接口
"""

from abc import ABC, abstractmethod
from typing import Optional, Callable
from dataclasses import dataclass


@dataclass
class PlatformMessage:
    """平台消息"""
    user_id: str
    message_id: int
    content: str
    message_type: str  # "private" 或 "group"
    group_id: Optional[int] = None
    sender_name: str = ""


class BasePlatform(ABC):
    """平台基类"""

    def __init__(self, config: dict):
        """
        初始化平台

        Args:
            config: 配置字典
        """
        self.config = config
        self.message_callback: Optional[Callable] = None

    @abstractmethod
    async def start(self):
        """启动平台"""
        pass

    @abstractmethod
    async def stop(self):
        """停止平台"""
        pass

    @abstractmethod
    async def send_private_message(self, user_id: str, message: str) -> bool:
        """
        发送私聊消息

        Args:
            user_id: 用户 ID
            message: 消息内容

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    async def send_group_message(self, group_id: str, message: str) -> bool:
        """
        发送群消息

        Args:
            group_id: 群 ID
            message: 消息内容

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    async def send_image(self, user_id: str, image_path: str, message_type: str = "private") -> bool:
        """
        发送图片

        Args:
            user_id: 用户 ID
            image_path: 图片路径
            message_type: 消息类型

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    async def send_file(self, user_id: str, file_path: str, message_type: str = "private") -> bool:
        """
        发送文件

        Args:
            user_id: 用户 ID
            file_path: 文件路径
            message_type: 消息类型

        Returns:
            是否成功
        """
        pass

    def on_message(self, callback: Callable):
        """
        设置消息回调

        Args:
            callback: 回调函数
        """
        self.message_callback = callback
