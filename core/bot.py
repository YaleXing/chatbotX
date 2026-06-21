"""
机器人主类
整合所有模块，提供统一的机器人接口
"""

import asyncio
import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

from core.ai.base import BaseAI
from core.ai.mimo import MiMoAI
from core.message.handler import MessageHandler, IncomingMessage, OutgoingMessage
from core.security.permission import PermissionManager
from platforms.base import BasePlatform, PlatformMessage
from platforms.qq.napcat import NapCatPlatform
from utils.logger import logger
from utils.helpers import is_command, parse_command


class ChatBot:
    """聊天机器人"""

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        初始化机器人

        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        self.config = self._load_config(config_path)

        # 初始化 AI
        self.ai: Optional[BaseAI] = None
        self._init_ai()

        # 初始化权限管理
        self.permission = PermissionManager(self.config.get("security", {}))

        # 初始化消息处理器
        self.handler = MessageHandler(self.ai, self.config)

        # 初始化平台
        self.platform: Optional[BasePlatform] = None
        self._init_platform()

        # 设置消息回调
        self.platform.on_message(self._on_message)

        logger.info("机器人初始化完成")

    def _load_config(self, config_path: str) -> dict:
        """
        加载配置文件

        Args:
            config_path: 配置文件路径

        Returns:
            配置字典
        """
        try:
            # 加载 .env 文件
            load_dotenv()

            path = Path(config_path)
            if not path.exists():
                # 如果配置文件不存在，使用示例配置
                example_path = Path("config/config.example.yaml")
                if example_path.exists():
                    logger.warning(f"配置文件不存在，使用示例配置: {example_path}")
                    path = example_path
                else:
                    raise FileNotFoundError(f"配置文件不存在: {config_path}")

            with open(path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # 从环境变量覆盖敏感配置
            if os.getenv("AI_API_KEY"):
                config.setdefault("ai", {})["api_key"] = os.getenv("AI_API_KEY")
            if os.getenv("AI_BASE_URL"):
                config.setdefault("ai", {})["base_url"] = os.getenv("AI_BASE_URL")
            if os.getenv("AI_MODEL"):
                config.setdefault("ai", {})["model"] = os.getenv("AI_MODEL")
            if os.getenv("QQ_API_URL"):
                config.setdefault("qq", {})["api_url"] = os.getenv("QQ_API_URL")
            if os.getenv("QQ_ACCESS_TOKEN"):
                config.setdefault("qq", {})["access_token"] = os.getenv("QQ_ACCESS_TOKEN")
            if os.getenv("QQ_OWNER_QQ"):
                config.setdefault("qq", {})["owner_qq"] = os.getenv("QQ_OWNER_QQ")

            logger.info(f"加载配置文件: {path}")
            return config

        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            raise

    def _init_ai(self):
        """初始化 AI"""
        ai_config = self.config.get("ai", {})
        provider = ai_config.get("provider", "mimo")

        if provider == "mimo":
            # 使用 MiMo 云端模型
            mimo_config = ai_config.get("mimo", {})
            mimo_config.update({
                "max_context": ai_config.get("max_context", 100),
                "temperature": ai_config.get("temperature", 0.7),
                "max_tokens": ai_config.get("max_tokens", 2048)
            })
            self.ai = MiMoAI(mimo_config)
            logger.info("使用 MiMo 云端模型")

        elif provider == "local":
            # 使用本地 llama.cpp 模型
            from core.ai.local import LocalLlamaAI
            local_config = ai_config.get("local", {})
            local_config.update({
                "max_context": ai_config.get("max_context", 100),
                "temperature": ai_config.get("temperature", 0.7),
                "max_tokens": ai_config.get("max_tokens", 2048)
            })
            self.ai = LocalLlamaAI(local_config)
            logger.info("使用本地 llama.cpp 模型")

        else:
            raise ValueError(f"不支持的 AI 提供商: {provider}")

    def _init_platform(self):
        """初始化平台"""
        qq_config = self.config.get("qq", {})
        platform = qq_config.get("platform", "napcat")

        if platform == "napcat":
            self.platform = NapCatPlatform(qq_config)
        else:
            raise ValueError(f"不支持的平台: {platform}")

    async def start(self):
        """启动机器人"""
        try:
            logger.info("启动机器人...")

            # 启动平台
            await self.platform.start()

            # 通知主人启动成功
            owner_qq = self.config.get("qq", {}).get("owner_qq", "")
            if owner_qq:
                await self.platform.send_private_message(
                    owner_qq,
                    "✨ 小助手已启动！快来和我聊天吧~ (◕‿◕)"
                )

            logger.info("机器人启动成功")

        except Exception as e:
            logger.error(f"启动机器人失败: {e}")
            raise

    async def stop(self):
        """停止机器人"""
        try:
            logger.info("停止机器人...")

            # 通知主人
            owner_qq = self.config.get("qq", {}).get("owner_qq", "")
            if owner_qq:
                await self.platform.send_private_message(
                    owner_qq,
                    "小助手要休息了~ 下次再见！(｡♥‿♥｡)"
                )

            # 停止平台
            await self.platform.stop()

            # 关闭 AI
            await self.ai.close()

            # 关闭消息处理器
            await self.handler.close()

            logger.info("机器人已停止")

        except Exception as e:
            logger.error(f"停止机器人失败: {e}")

    async def _on_message(self, platform_msg: PlatformMessage):
        """
        处理收到的消息

        Args:
            platform_msg: 平台消息
        """
        try:
            logger.info(f"开始处理消息: {platform_msg.content[:50]}...")

            # 检查是否是命令
            if is_command(platform_msg.content):
                command, args = parse_command(platform_msg.content)

                # 检查权限
                if not self.permission.can_execute_command(platform_msg.user_id, command):
                    await self._send_reply(
                        platform_msg,
                        self.permission.get_permission_denied_message(command)
                    )
                    return

                # 处理特殊命令
                if command == "关闭机器人":
                    if self.permission.is_owner(platform_msg.user_id):
                        await self._send_reply(platform_msg, "好的，我这就去休息~ (｡♥‿♥｡)")
                        await self.stop()
                        return

                elif command == "切换人格":
                    if len(args) > 0:
                        success = await self.ai.set_personality(args[0])
                        if success:
                            await self._send_reply(platform_msg, f"已切换到 {args[0]} 人格~ ✨")
                        else:
                            await self._send_reply(platform_msg, f"人格 {args[0]} 不存在哦~ (｡•́︿•̀｡)")
                    else:
                        await self._send_reply(platform_msg, "请指定人格名称，如：/切换人格 cool")
                    return

                elif command == "查看状态":
                    status = self._get_status()
                    await self._send_reply(platform_msg, status)
                    return

            # 转换为内部消息格式
            incoming_msg = IncomingMessage(
                user_id=platform_msg.user_id,
                message_id=platform_msg.message_id,
                content=platform_msg.content,
                message_type=platform_msg.message_type,
                group_id=platform_msg.group_id,
                sender_name=platform_msg.sender_name
            )

            logger.info(f"转换消息格式完成，开始调用 AI...")

            # 处理消息
            outgoing_msg = await self.handler.handle(incoming_msg)

            logger.info(f"AI 回复完成: {outgoing_msg.content[:50] if outgoing_msg.content else '无内容'}...")

            # 发送回复
            await self._send_reply(platform_msg, outgoing_msg)

            logger.info(f"回复发送完成")

        except Exception as e:
            logger.error(f"处理消息失败: {e}", exc_info=True)

    async def _send_reply(self, platform_msg: PlatformMessage, reply: OutgoingMessage | str):
        """
        发送回复

        Args:
            platform_msg: 原始消息
            reply: 回复内容
        """
        try:
            # 如果是字符串，转换为 OutgoingMessage
            if isinstance(reply, str):
                reply = OutgoingMessage(content=reply)

            # 发送文本
            if reply.content:
                if platform_msg.message_type == "private":
                    await self.platform.send_private_message(
                        platform_msg.user_id,
                        reply.content
                    )
                else:
                    await self.platform.send_group_message(
                        str(platform_msg.group_id),
                        reply.content
                    )

            # 发送图片
            for image_path in reply.images:
                await self.platform.send_image(
                    platform_msg.user_id,
                    image_path,
                    platform_msg.message_type
                )

            # 发送文件
            for file_path in reply.files:
                await self.platform.send_file(
                    platform_msg.user_id,
                    file_path,
                    platform_msg.message_type
                )

            # 发送语音条
            for voice_path in reply.voice_files:
                await self.platform.send_record(
                    platform_msg.user_id,
                    voice_path,
                    platform_msg.message_type
                )

        except Exception as e:
            logger.error(f"发送回复失败: {e}")

    def _get_status(self) -> str:
        """获取状态信息"""
        from utils.helpers import get_current_time

        return f"""✨ 小助手状态 ✨

⏰ 当前时间：{get_current_time()}
🤖 AI 模型：{self.ai.model}
💬 对话用户数：{len(self.ai.conversations)}
🔐 权限管理：已启用

运行正常~ (◕‿◕)"""

    async def run(self):
        """运行机器人（阻塞）"""
        try:
            await self.start()

            # 保持运行
            while True:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("收到停止信号")
        finally:
            await self.stop()
