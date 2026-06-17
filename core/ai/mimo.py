"""
MiMo-V2.5 AI 接口实现
使用硅基流动 (SiliconFlow) API
"""

import base64
import httpx
from typing import Optional
from pathlib import Path

from .base import BaseAI, Message, ImageContent
from utils.logger import logger


class MiMoAI(BaseAI):
    """MiMo-V2.5 AI 接口"""

    def __init__(self, config: dict):
        """
        初始化 MiMo AI 接口

        Args:
            config: 配置字典，包含：
                - api_key: API 密钥
                - base_url: API 基础 URL
                - model: 模型名称
                - max_context: 最大上下文轮数
                - temperature: 温度参数
                - max_tokens: 最大 token 数
        """
        super().__init__(config)

        self.api_key = config.get("api_key", "")
        self.base_url = config.get("base_url", "https://api.siliconflow.cn/v1")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 2048)

        # 加载默认人格
        self.personality = self.load_personality("config/prompts/default.txt")

        # HTTP 客户端
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=60.0
        )

        logger.info(f"MiMo AI 初始化完成，模型: {self.model}")

    async def chat(
        self,
        user_id: str,
        message: str,
        images: Optional[list[ImageContent]] = None
    ) -> str:
        """
        与 MiMo 对话

        Args:
            user_id: 用户 ID
            message: 用户消息
            images: 图片列表（可选）

        Returns:
            AI 回复
        """
        try:
            # 构建消息列表
            messages = self._build_messages(user_id, message, images)

            # 调用 API
            response = await self._call_api(messages)

            # 保存对话历史
            self.add_message(user_id, Message(role="user", content=message))
            self.add_message(user_id, Message(role="assistant", content=response))

            return response

        except Exception as e:
            logger.error(f"MiMo 对话失败: {e}")
            return f"抱歉，我暂时无法回复~ (╥﹏╥)\n错误: {str(e)}"

    async def chat_with_image(
        self,
        user_id: str,
        message: str,
        image_url: str
    ) -> str:
        """
        与 MiMo 对话（带图片）

        Args:
            user_id: 用户 ID
            message: 用户消息
            image_url: 图片 URL

        Returns:
            AI 回复
        """
        images = [ImageContent(url=image_url)]
        return await self.chat(user_id, message, images)

    def _build_messages(
        self,
        user_id: str,
        message: str,
        images: Optional[list[ImageContent]] = None
    ) -> list[dict]:
        """
        构建消息列表

        Args:
            user_id: 用户 ID
            message: 用户消息
            images: 图片列表

        Returns:
            消息列表
        """
        messages = []

        # 添加系统提示
        if self.personality:
            messages.append({
                "role": "system",
                "content": self.personality
            })

        # 添加历史对话
        history = self.get_conversation(user_id)
        for msg in history[-self.max_context:]:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # 添加当前消息
        if images:
            # 多模态消息
            content = []
            content.append({"type": "text", "text": message})

            for img in images:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": img.url}
                })

            messages.append({
                "role": "user",
                "content": content
            })
        else:
            # 纯文本消息
            messages.append({
                "role": "user",
                "content": message
            })

        return messages

    async def _call_api(self, messages: list[dict]) -> str:
        """
        调用 API

        Args:
            messages: 消息列表

        Returns:
            AI 回复
        """
        logger.info(f"调用 MiMo API，模型: {self.model}")

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

        logger.info(f"发送请求到: {self.base_url}/chat/completions")
        logger.debug(f"请求体: {str(payload)[:500]}...")

        response = await self.client.post(
            "/chat/completions",
            json=payload
        )

        logger.info(f"收到响应，状态码: {response.status_code}")

        if response.status_code != 200:
            logger.error(f"API 错误: {response.text}")
            response.raise_for_status()

        data = response.json()

        content = data["choices"][0]["message"]["content"]
        logger.info(f"API 返回内容长度: {len(content)}")

        return content

    async def set_personality(self, personality_name: str) -> bool:
        """
        切换人格

        Args:
            personality_name: 人格名称

        Returns:
            是否成功
        """
        personality_file = f"config/prompts/{personality_name}.txt"
        path = Path(personality_file)

        if path.exists():
            self.personality = self.load_personality(personality_file)
            logger.info(f"切换人格到: {personality_name}")
            return True

        logger.warning(f"人格文件不存在: {personality_file}")
        return False

    async def close(self):
        """关闭 HTTP 客户端"""
        await self.client.aclose()
