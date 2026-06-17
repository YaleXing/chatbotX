"""
NapCat QQ 平台接入
通过 WebSocket 与 NapCat 通信
"""

import asyncio
import json
from typing import Optional

import aiohttp

from platforms.base import BasePlatform, PlatformMessage
from utils.logger import logger


class NapCatPlatform(BasePlatform):
    """NapCat QQ 平台"""

    def __init__(self, config: dict):
        """
        初始化 NapCat 平台

        Args:
            config: 配置字典，包含：
                - api_url: NapCat API 地址
                - access_token: Access Token
                - owner_qq: 主人 QQ 号
        """
        super().__init__(config)

        self.api_url = config.get("api_url", "http://localhost:3000")
        self.access_token = config.get("access_token", "")
        self.owner_qq = config.get("owner_qq", "")

        # HTTP 会话（用于发送消息）
        self.session: Optional[aiohttp.ClientSession] = None

        # WebSocket 连接（用于接收消息）
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._ws_task: Optional[asyncio.Task] = None
        self._running = False

        # 将 HTTP URL 转换为 WebSocket URL
        self.ws_url = self.api_url.replace("http://", "ws://").replace("https://", "wss://")
        if not self.ws_url.endswith("/ws"):
            self.ws_url = f"{self.ws_url}/ws"

        logger.info(f"NapCat 平台初始化完成，API 地址: {self.api_url}")
        logger.info(f"WebSocket 地址: {self.ws_url}")

    async def start(self):
        """启动平台"""
        # 创建 HTTP 会话（用于发送消息）
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        self.session = aiohttp.ClientSession(
            base_url=self.api_url,
            headers=headers
        )

        # 测试 HTTP 连接
        try:
            await self._test_connection()
            logger.info("NapCat HTTP 连接成功")
        except Exception as e:
            logger.error(f"NapCat HTTP 连接失败: {e}")
            raise

        # 启动 WebSocket 连接
        self._running = True
        self._ws_task = asyncio.create_task(self._connect_websocket())

        logger.info("NapCat 平台启动完成")

    async def stop(self):
        """停止平台"""
        self._running = False

        # 取消 WebSocket 任务
        if self._ws_task:
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass

        # 关闭 WebSocket 连接
        if self.ws:
            await self.ws.close()

        # 关闭 HTTP 会话
        if self.session:
            await self.session.close()

        logger.info("NapCat 平台已停止")

    async def send_private_message(self, user_id: str, message: str) -> bool:
        """
        发送私聊消息

        Args:
            user_id: 用户 ID
            message: 消息内容

        Returns:
            是否成功
        """
        try:
            payload = {
                "user_id": int(user_id),
                "message": message
            }

            async with self.session.post("/send_private_msg", json=payload) as resp:
                result = await resp.json()

                if result.get("status") == "ok":
                    logger.debug(f"发送私聊消息成功: {user_id}")
                    return True
                else:
                    logger.error(f"发送私聊消息失败: {result}")
                    return False

        except Exception as e:
            logger.error(f"发送私聊消息异常: {e}")
            return False

    async def send_group_message(self, group_id: str, message: str) -> bool:
        """
        发送群消息

        Args:
            group_id: 群 ID
            message: 消息内容

        Returns:
            是否成功
        """
        try:
            payload = {
                "group_id": int(group_id),
                "message": message
            }

            async with self.session.post("/send_group_msg", json=payload) as resp:
                result = await resp.json()

                if result.get("status") == "ok":
                    logger.debug(f"发送群消息成功: {group_id}")
                    return True
                else:
                    logger.error(f"发送群消息失败: {result}")
                    return False

        except Exception as e:
            logger.error(f"发送群消息异常: {e}")
            return False

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
        # 使用 CQ 码发送图片
        message = f"[CQ:image,file=file:///{image_path}]"

        if message_type == "private":
            return await self.send_private_message(user_id, message)
        else:
            return await self.send_group_message(user_id, message)

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
        # 使用 CQ 码发送文件
        message = f"[CQ:file,file=file:///{file_path}]"

        if message_type == "private":
            return await self.send_private_message(user_id, message)
        else:
            return await self.send_group_message(user_id, message)

    async def _test_connection(self):
        """测试 HTTP 连接"""
        async with self.session.get("/get_login_info") as resp:
            result = await resp.json()

            if result.get("status") != "ok":
                raise Exception(f"连接失败: {result}")

            data = result.get("data", {})
            logger.info(f"登录成功: {data.get('nickname')} ({data.get('user_id')})")

    async def _connect_websocket(self):
        """连接 WebSocket"""
        logger.info(f"正在连接 WebSocket: {self.ws_url}")

        while self._running:
            try:
                # 构建 WebSocket 连接 headers
                ws_headers = {}
                if self.access_token:
                    ws_headers["Authorization"] = f"Bearer {self.access_token}"

                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(
                        self.ws_url,
                        headers=ws_headers,
                        heartbeat=30.0
                    ) as ws:
                        self.ws = ws
                        logger.info("WebSocket 连接成功")

                        # 接收消息
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                await self._handle_ws_message(msg.data)
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                logger.error(f"WebSocket 错误: {ws.exception()}")
                                break
                            elif msg.type == aiohttp.WSMsgType.CLOSED:
                                logger.info("WebSocket 连接关闭")
                                break

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"WebSocket 连接失败: {e}")
                if self._running:
                    logger.info("5 秒后重试...")
                    await asyncio.sleep(5)

    async def _handle_ws_message(self, data: str):
        """
        处理 WebSocket 消息

        Args:
            data: 消息数据（JSON 字符串）
        """
        try:
            event = json.loads(data)

            # 记录所有收到的事件（调试用）
            post_type = event.get("post_type")
            logger.debug(f"收到 WebSocket 事件: {post_type}")

            # 检查是否是消息事件
            if post_type == "message":
                logger.info(f"收到消息事件: {event.get('raw_message', '')[:50]}...")
                await self._process_message(event)

        except json.JSONDecodeError:
            logger.error(f"JSON 解析失败: {data}")
        except Exception as e:
            logger.error(f"处理 WebSocket 消息失败: {e}")

    async def _process_message(self, msg_data: dict):
        """
        处理单条消息

        Args:
            msg_data: 消息数据
        """
        try:
            # 提取消息信息
            message_id = msg_data.get("message_id", 0)
            user_id = str(msg_data.get("user_id", ""))
            message_type = msg_data.get("message_type", "private")
            raw_message = msg_data.get("raw_message", "")

            # 忽略自己的消息
            if user_id == self.owner_qq:
                return

            # 构建平台消息
            platform_msg = PlatformMessage(
                user_id=user_id,
                message_id=message_id,
                content=raw_message,
                message_type=message_type,
                group_id=msg_data.get("group_id"),
                sender_name=msg_data.get("sender", {}).get("nickname", "")
            )

            logger.info(f"收到消息: {raw_message[:50]}...")

            # 调用回调
            if self.message_callback:
                await self.message_callback(platform_msg)

        except Exception as e:
            logger.error(f"处理消息失败: {e}")
