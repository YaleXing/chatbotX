"""
AI 接口基类
定义统一的 AI 对话接口
"""

from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Message:
    """消息数据类"""
    role: str  # "system", "user", "assistant"
    content: str | list  # 文本或多模态内容


@dataclass
class ImageContent:
    """图片内容"""
    url: str  # 图片 URL 或 base64
    detail: str = "auto"  # "low", "high", "auto"


class BaseAI(ABC):
    """AI 接口基类"""

    def __init__(self, config: dict):
        """
        初始化 AI 接口

        Args:
            config: 配置字典
        """
        self.config = config
        self.model = config.get("model", "")
        self.max_context = config.get("max_context", 100)
        self.conversations: dict[str, list[Message]] = {}

    @abstractmethod
    async def chat(
        self,
        user_id: str,
        message: str,
        images: Optional[list[ImageContent]] = None
    ) -> str:
        """
        与 AI 对话

        Args:
            user_id: 用户 ID
            message: 用户消息
            images: 图片列表（可选）

        Returns:
            AI 回复
        """
        pass

    @abstractmethod
    async def chat_with_image(
        self,
        user_id: str,
        message: str,
        image_url: str
    ) -> str:
        """
        与 AI 对话（带图片）

        Args:
            user_id: 用户 ID
            message: 用户消息
            image_url: 图片 URL

        Returns:
            AI 回复
        """
        pass

    def get_conversation(self, user_id: str) -> list[Message]:
        """
        获取用户对话历史

        Args:
            user_id: 用户 ID

        Returns:
            对话历史列表
        """
        if user_id not in self.conversations:
            self.conversations[user_id] = []

        return self.conversations[user_id]

    def add_message(self, user_id: str, message: Message):
        """
        添加消息到对话历史

        Args:
            user_id: 用户 ID
            message: 消息对象
        """
        if user_id not in self.conversations:
            self.conversations[user_id] = []

        self.conversations[user_id].append(message)

        # 限制上下文长度
        if len(self.conversations[user_id]) > self.max_context * 2:
            # 保留最近的消息
            self.conversations[user_id] = self.conversations[user_id][-self.max_context * 2:]

    def clear_conversation(self, user_id: str):
        """
        清空用户对话历史

        Args:
            user_id: 用户 ID
        """
        if user_id in self.conversations:
            del self.conversations[user_id]

    def load_personality(self, personality_file: str) -> str:
        """
        加载人格文件

        Args:
            personality_file: 人格文件路径

        Returns:
            人格提示词
        """
        try:
            path = Path(personality_file)
            if path.exists():
                return path.read_text(encoding="utf-8").strip()
        except Exception as e:
            print(f"加载人格文件失败: {e}")

        return ""
