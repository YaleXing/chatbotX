"""
本地 llama.cpp 模型接口
支持 OpenAI 兼容的 API 格式
"""

import httpx
from typing import Optional
from pathlib import Path

from .base import BaseAI, Message, ImageContent
from utils.logger import logger


class LocalLlamaAI(BaseAI):
    """本地 llama.cpp 模型接口"""

    def __init__(self, config: dict):
        """
        初始化本地模型接口

        Args:
            config: 配置字典，包含：
                - local_api_url: llama-server 地址
                - local_model: 模型名称（可选）
                - max_context: 最大上下文轮数
                - temperature: 温度参数
                - max_tokens: 最大 token 数
        """
        super().__init__(config)

        self.api_url = config.get("local_api_url", "http://localhost:8080")
        self.model = config.get("local_model", "local")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 2048)

        # 加载默认人格
        self.personality = self.load_personality("config/prompts/default.txt")

        # HTTP 客户端
        self.client = httpx.AsyncClient(
            base_url=self.api_url,
            headers={"Content-Type": "application/json"},
            timeout=120.0  # 本地模型可能较慢
        )

        logger.info(f"本地 llama 模型初始化完成，API: {self.api_url}")

    async def chat(
        self,
        user_id: str,
        message: str,
        images: Optional[list[ImageContent]] = None
    ) -> str:
        """
        与本地模型对话

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
            logger.error(f"本地模型对话失败: {e}")
            return f"抱歉，我暂时无法回复~ (╥﹏╥)\n错误: {str(e)}"

    async def chat_with_image(
        self,
        user_id: str,
        message: str,
        image_url: str
    ) -> str:
        """
        与本地模型对话（带图片）

        Args:
            user_id: 用户 ID
            message: 用户消息
            image_url: 图片 URL（data:image/xxx;base64,... 格式）

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
        调用本地 API

        Args:
            messages: 消息列表

        Returns:
            AI 回复
        """
        logger.info(f"调用本地 llama API")

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

        # llama.cpp 使用 OpenAI 兼容的 /v1/chat/completions 接口
        response = await self.client.post(
            "/v1/chat/completions",
            json=payload
        )

        logger.info(f"本地 API 响应状态码: {response.status_code}")

        if response.status_code != 200:
            logger.error(f"本地 API 错误: {response.text}")
            response.raise_for_status()

        data = response.json()

        content = data["choices"][0]["message"]["content"]
        logger.info(f"本地 API 返回内容长度: {len(content)}")

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
