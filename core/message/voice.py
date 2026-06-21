"""
语音处理模块
处理语音识别和语音合成
"""

from pathlib import Path
from typing import Optional

import httpx

from utils.logger import logger


class VoiceProcessor:
    """语音处理器"""

    def __init__(self, config: dict):
        """
        初始化语音处理器

        Args:
            config: 配置字典，包含：
                - api_key: API 密钥
                - base_url: API 基础 URL
                - asr_model: 语音识别模型
                - tts_model: 语音合成模型
        """
        self.api_key = config.get("api_key", "")
        self.base_url = config.get("base_url", "https://api.xiaomimimo.com/v1")
        self.asr_model = config.get("asr_model", "mimo-v2.5-asr")  # 语音识别模型
        self.tts_model = config.get("tts_model", "mimo-v2.5-tts")  # 语音合成模型

        # 临时文件目录
        self.temp_dir = Path("data/temp/voice")
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # HTTP 客户端
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=60.0
        )

        logger.info(f"语音处理器初始化完成，ASR 模型: {self.asr_model}")

    async def recognize_speech(self, audio_path: str) -> Optional[str]:
        """
        识别语音内容

        Args:
            audio_path: 语音文件路径

        Returns:
            识别结果文本，失败返回 None
        """
        try:
            # 读取音频文件
            audio_path = Path(audio_path)
            if not audio_path.exists():
                logger.error(f"语音文件不存在: {audio_path}")
                return None

            # 转换为 base64
            import base64
            with open(audio_path, "rb") as f:
                audio_base64 = base64.b64encode(f.read()).decode("utf-8")

            # 获取音频格式
            audio_format = audio_path.suffix[1:]  # 移除点号
            if audio_format == "wav":
                audio_format = "wav"
            elif audio_format == "mp3":
                audio_format = "mp3"
            elif audio_format == "amr":
                audio_format = "amr"
            else:
                audio_format = "wav"  # 默认使用 wav

            logger.info(f"使用 ASR 模型: {self.asr_model}，音频格式: {audio_format}")

            # 构建请求 - 使用专门的 ASR 模型
            # MiMo ASR API 使用 input_audio 类型
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": audio_base64,
                                "format": audio_format
                            }
                        },
                        {
                            "type": "text",
                            "text": "请识别这段语音的内容，只输出识别到的文字，不要添加任何其他内容。"
                        }
                    ]
                }
            ]

            # 调用 API
            response = await self._call_api(messages)

            if response:
                logger.info(f"语音识别成功: {response[:50]}...")
                return response.strip()

            return None

        except Exception as e:
            logger.error(f"语音识别失败: {e}")
            return None

    async def synthesize_speech(self, text: str) -> Optional[str]:
        """
        合成语音

        Args:
            text: 要合成的文本

        Returns:
            语音文件路径，失败返回 None
        """
        try:
            # 构建请求
            messages = [
                {
                    "role": "user",
                    "content": f"请将以下文本转换为语音，只输出文本内容，不要添加任何其他内容：\n{text}"
                }
            ]

            # 调用 API 获取语音
            # 注意：这里需要根据 MiMo 的具体 API 调整
            # 如果 MiMo 支持直接输出语音文件，可以在这里调用
            # 如果不支持，可以使用其他 TTS 服务

            # 暂时返回 None，表示需要使用其他 TTS 服务
            logger.warning("语音合成功能需要根据 MiMo API 文档进一步实现")
            return None

        except Exception as e:
            logger.error(f"语音合成失败: {e}")
            return None

    async def _call_api(self, messages: list[dict]) -> Optional[str]:
        """
        调用 API

        Args:
            messages: 消息列表

        Returns:
            AI 回复
        """
        try:
            payload = {
                "model": self.asr_model,  # 使用 ASR 模型
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2048
            }

            logger.info(f"调用语音识别 API，模型: {self.asr_model}")

            response = await self.client.post(
                "/chat/completions",
                json=payload
            )

            logger.info(f"语音识别 API 响应状态码: {response.status_code}")

            if response.status_code != 200:
                logger.error(f"语音识别 API 错误: {response.text}")
                response.raise_for_status()

            data = response.json()

            return data["choices"][0]["message"]["content"]

        except Exception as e:
            logger.error(f"API 调用失败: {e}")
            return None

    async def close(self):
        """关闭资源"""
        await self.client.aclose()
