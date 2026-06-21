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

            # 确定 MIME 类型
            mime_map = {
                "wav": "audio/wav",
                "mp3": "audio/mpeg",
                "amr": "audio/wav"  # amr 转换后通常是 wav
            }
            mime_type = mime_map.get(audio_format, "audio/wav")

            logger.info(f"使用 ASR 模型: {self.asr_model}，音频格式: {audio_format}，MIME: {mime_type}")

            # 构建请求 - 使用官方文档格式
            # 音频数据需要是 data:{MIME_TYPE};base64,$BASE64_AUDIO 格式
            data_url = f"data:{mime_type};base64,{audio_base64}"

            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": data_url
                            }
                        }
                    ]
                }
            ]

            # 调用 API（带 asr_options）
            response = await self._call_api_with_options(messages, {"language": "zh"})

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
            logger.info(f"开始语音合成，文本长度: {len(text)}")

            # 优先使用 edge-tts（免费、稳定）
            result = await self._synthesize_with_edge_tts(text)
            if result:
                return result

            # 如果 edge-tts 失败，尝试小米 MiMo API
            result = await self._synthesize_with_mimo_tts(text)
            if result:
                return result

            logger.error("所有 TTS 方式都失败")
            return None

        except Exception as e:
            logger.error(f"语音合成失败: {e}")
            return None

    async def _synthesize_with_edge_tts(self, text: str) -> Optional[str]:
        """
        使用 edge-tts 合成语音（免费、稳定）

        Args:
            text: 要合成的文本

        Returns:
            语音文件路径，失败返回 None
        """
        try:
            import edge_tts
            import hashlib

            logger.info("使用 edge-tts 合成语音")

            # 中文语音选项
            # zh-CN-XiaoxiaoNeural - 女声（活泼）
            # zh-CN-YunxiNeural - 男声（沉稳）
            # zh-CN-XiaoyiNeural - 女声（温柔）
            voice = "zh-CN-XiaoxiaoNeural"

            # 生成输出文件路径
            text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            output_path = self.temp_dir / f"tts_{text_hash}.mp3"

            # 合成语音
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(output_path))

            abs_path = output_path.resolve()
            logger.info(f"edge-tts 合成成功: {abs_path}")
            return str(abs_path)

        except Exception as e:
            logger.warning(f"edge-tts 合成失败: {e}")
            return None

    async def _synthesize_with_mimo_tts(self, text: str) -> Optional[str]:
        """
        使用小米 MiMo TTS 合成语音

        Args:
            text: 要合成的文本

        Returns:
            语音文件路径，失败返回 None
        """
        try:
            logger.info("尝试小米 MiMo TTS")

            # 构建请求
            payload = {
                "model": self.tts_model,
                "input": text,
                "voice": "alloy",
                "response_format": "mp3"
            }

            # 尝试多个可能的端点
            endpoints = [
                "/audio/speech",
                "/v1/audio/speech",
                "/tts",
                "/v1/tts"
            ]

            for endpoint in endpoints:
                logger.info(f"尝试 TTS 端点: {endpoint}")

                try:
                    response = await self.client.post(
                        endpoint,
                        json=payload,
                        timeout=30.0
                    )

                    if response.status_code == 200:
                        import hashlib
                        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
                        output_path = self.temp_dir / f"tts_{text_hash}.mp3"

                        with open(output_path, "wb") as f:
                            f.write(response.content)

                        abs_path = output_path.resolve()
                        logger.info(f"MiMo TTS 合成成功: {abs_path}")
                        return str(abs_path)
                    else:
                        logger.debug(f"端点 {endpoint} 返回: {response.status_code}")

                except Exception as e:
                    logger.debug(f"端点 {endpoint} 失败: {e}")
                    continue

            return None

        except Exception as e:
            logger.warning(f"MiMo TTS 合成失败: {e}")
            return None

    async def _call_api_with_options(self, messages: list[dict], options: dict = None) -> Optional[str]:
        """
        调用 API（带额外选项）

        Args:
            messages: 消息列表
            options: 额外选项（如 asr_options）

        Returns:
            AI 回复
        """
        try:
            payload = {
                "model": self.asr_model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2048
            }

            # 添加额外选项
            if options:
                payload.update(options)

            logger.info(f"调用语音识别 API，模型: {self.asr_model}，选项: {options}")

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
