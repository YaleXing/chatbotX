"""
消息处理器模块
统一处理各种类型的消息
"""

from typing import Optional
from dataclasses import dataclass

from core.ai.base import BaseAI
from core.message.emoji import EmojiManager
from core.message.code import CodeProcessor
from core.message.voice import VoiceProcessor
from core.message.qq_face import get_random_face, get_face_cq
from platforms.qq.file_helper import NapCatFileHelper
from utils.logger import logger
from utils.helpers import (
    is_image_message,
    extract_code_blocks,
    is_command,
    parse_command
)


@dataclass
class IncomingMessage:
    """收到的消息"""
    user_id: str
    message_id: int
    content: str
    message_type: str  # "private" 或 "group"
    group_id: Optional[int] = None
    sender_name: str = ""


@dataclass
class OutgoingMessage:
    """发送的消息"""
    content: str
    images: list[str] = None  # 图片路径列表
    files: list[str] = None   # 文件路径列表

    def __post_init__(self):
        if self.images is None:
            self.images = []
        if self.files is None:
            self.files = []


class MessageHandler:
    """消息处理器"""

    def __init__(self, ai: BaseAI, config: dict):
        """
        初始化消息处理器

        Args:
            ai: AI 接口
            config: 配置字典
        """
        self.ai = ai
        self.config = config

        # 初始化表情管理器
        emoji_config = config.get("emoji", {})
        self.emoji_manager = EmojiManager(emoji_config)

        # 初始化代码处理器
        self.code_processor = CodeProcessor()

        # 初始化语音处理器
        voice_config = config.get("voice", {})
        self.voice_enabled = voice_config.get("enabled", False)
        if self.voice_enabled:
            self.voice_processor = VoiceProcessor(config.get("ai", {}))
        else:
            self.voice_processor = None

        # 初始化文件帮助类
        qq_config = config.get("qq", {})
        self.file_helper = NapCatFileHelper(
            api_url=qq_config.get("api_url", "http://localhost:3000"),
            access_token=qq_config.get("access_token", "")
        )

        # 表情发送概率
        self.emoji_probability = emoji_config.get("probability", 0.3)

        logger.info("消息处理器初始化完成")

    async def handle(self, message: IncomingMessage) -> OutgoingMessage:
        """
        处理消息

        Args:
            message: 收到的消息

        Returns:
            要发送的消息
        """
        try:
            logger.info(f"收到来自 {message.user_id} 的消息: {message.content[:50]}...")

            # 检查是否是命令
            if is_command(message.content):
                return await self._handle_command(message)

            # 检查是否是图片消息
            if is_image_message(message.content):
                return await self._handle_image_message(message)

            # 检查是否是语音消息
            if self._is_voice_message(message.content):
                return await self._handle_voice_message(message)

            # 普通文本消息
            return await self._handle_text_message(message)

        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            return OutgoingMessage(content="抱歉，处理消息时出错了~ (╥﹏╥)")

    async def _handle_command(self, message: IncomingMessage) -> OutgoingMessage:
        """
        处理命令

        Args:
            message: 消息

        Returns:
            回复消息
        """
        command, args = parse_command(message.content)

        logger.info(f"处理命令: {command}, 参数: {args}")

        # 这里先简单处理，后续在权限控制中扩展
        if command == "帮助":
            return OutgoingMessage(content=self._get_help_text())

        if command == "清空历史":
            self.ai.clear_conversation(message.user_id)
            return OutgoingMessage(content="对话历史已清空~ ✨")

        # 默认交给 AI 处理
        return await self._handle_text_message(message)

    async def _handle_image_message(self, message: IncomingMessage) -> OutgoingMessage:
        """
        处理图片消息

        Args:
            message: 图片消息

        Returns:
            回复消息
        """
        logger.info(f"开始处理图片消息: {message.content[:100]}...")

        # 提取文件 ID
        file_id = self.file_helper.extract_file_id(message.content)

        if not file_id:
            logger.warning("无法提取图片文件 ID")
            return OutgoingMessage(content="图片加载失败了~ (｡•́︿•̀｡)")

        logger.info(f"提取到图片文件 ID: {file_id}")

        # 下载图片文件
        image_path = await self.file_helper.download_image(file_id)

        if not image_path:
            logger.warning("下载图片失败")
            return OutgoingMessage(content="图片下载失败了~ (｡•́︿•̀｡)")

        logger.info(f"图片下载成功: {image_path}")

        # 读取图片并转换为 base64
        import base64
        from pathlib import Path

        try:
            image_data = Path(image_path).read_bytes()
            image_base64 = base64.b64encode(image_data).decode("utf-8")

            # 根据文件扩展名确定 MIME 类型
            ext = Path(image_path).suffix.lower()
            mime_map = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp"
            }
            mime_type = mime_map.get(ext, "image/jpeg")

            # 构建 data URL
            image_url = f"data:{mime_type};base64,{image_base64}"

            # 调用 AI 识别图片
            prompt = "请描述一下这张图片的内容，并做出有趣的回复~"
            response = await self.ai.chat_with_image(
                message.user_id,
                prompt,
                image_url
            )

        except Exception as e:
            logger.error(f"读取图片失败: {e}")
            return OutgoingMessage(content="图片处理失败了~ (｡•́︿•̀｡)")

        # 可能添加表情
        if self._should_add_emoji():
            emoji_path = self.emoji_manager.get_random_emoji()
            if emoji_path:
                return OutgoingMessage(content=response, images=[emoji_path])
            else:
                # 没有表情包时，使用 QQ 系统表情
                face_id = get_random_face()
                face_cq = get_face_cq(face_id)
                return OutgoingMessage(content=response + " " + face_cq)

        return OutgoingMessage(content=response)

    def _is_voice_message(self, content: str) -> bool:
        """
        判断是否是语音消息

        Args:
            content: 消息内容

        Returns:
            是否是语音消息
        """
        # NapCat 语音消息格式: [CQ:record,file=xxx]
        return "[CQ:record," in content

    async def _handle_voice_message(self, message: IncomingMessage) -> OutgoingMessage:
        """
        处理语音消息

        Args:
            message: 语音消息

        Returns:
            回复消息
        """
        if not self.voice_enabled or not self.voice_processor:
            return OutgoingMessage(content="语音功能未启用哦~ (｡•́︿•̀｡)")

        try:
            # 提取文件 ID
            file_id = self.file_helper.extract_file_id(message.content)

            if not file_id:
                logger.warning("无法提取语音文件 ID")
                return OutgoingMessage(content="语音文件加载失败了~ (｡•́︿•̀｡)")

            logger.info(f"提取到语音文件 ID: {file_id}")

            # 下载语音文件
            voice_path = await self.file_helper.download_record(file_id)

            if not voice_path:
                logger.warning("下载语音失败")
                return OutgoingMessage(content="语音下载失败了~ (｡•́︿•̀｡)")

            logger.info(f"语音下载成功: {voice_path}")

            # 识别语音内容
            text = await self.voice_processor.recognize_speech(voice_path)

            if not text:
                return OutgoingMessage(content="语音识别失败了，再说一遍好吗~ (｡•́︿•̀｡)")

            logger.info(f"语音识别结果: {text}")

            # 将识别结果发送给 AI
            response = await self.ai.chat(message.user_id, f"[语音消息] {text}")

            # 可能添加表情
            if self._should_add_emoji():
                emoji_path = self.emoji_manager.get_random_emoji()
                if emoji_path:
                    return OutgoingMessage(content=response, images=[emoji_path])

            return OutgoingMessage(content=response)

        except Exception as e:
            logger.error(f"处理语音消息失败: {e}")
            return OutgoingMessage(content="语音处理出错了~ (╥﹏╥)")

    async def _handle_text_message(self, message: IncomingMessage) -> OutgoingMessage:
        """
        处理文本消息

        Args:
            message: 文本消息

        Returns:
            回复消息
        """
        logger.info(f"开始调用 AI 处理文本消息...")

        # 调用 AI 生成回复
        response = await self.ai.chat(message.user_id, message.content)

        logger.info(f"AI 回复: {response[:50] if response else 'None'}...")

        # 检查回复中是否包含代码
        code_blocks = extract_code_blocks(response)

        if code_blocks:
            # 有代码块，打包成文件
            file_path = await self.code_processor.package_code(code_blocks)
            if file_path:
                return OutgoingMessage(
                    content=response,
                    files=[file_path]
                )

        # 可能添加表情
        if self._should_add_emoji():
            emoji_path = self.emoji_manager.get_random_emoji()
            if emoji_path:
                return OutgoingMessage(content=response, images=[emoji_path])
            else:
                # 没有表情包时，使用 QQ 系统表情
                face_id = get_random_face()
                face_cq = get_face_cq(face_id)
                return OutgoingMessage(content=response + " " + face_cq)

        return OutgoingMessage(content=response)

    def _should_add_emoji(self) -> bool:
        """
        判断是否应该添加表情

        Returns:
            是否添加表情
        """
        import random
        return random.random() < self.emoji_probability

    def _get_help_text(self) -> str:
        """获取帮助文本"""
        return """✨ 小助手功能说明 ✨

📝 基本功能：
- 直接发送文字和我聊天
- 发送图片我会识别内容
- 发送语音我会识别内容
- 发送代码我会帮你分析

🎮 指令：
/帮助 - 显示帮助信息
/清空历史 - 清空对话历史
/切换人格 [名称] - 切换性格

💡 小提示：
- 我会根据语境发表情包
- 支持 100 轮对话记忆
- 可以帮你打包代码哦~
- 支持语音消息识别~

快来和我聊天吧~ (◕‿◕)"""

    async def close(self):
        """关闭资源"""
        await self.code_processor.close()
        if self.voice_processor:
            await self.voice_processor.close()
