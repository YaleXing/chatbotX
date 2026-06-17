"""
权限控制模块
管理用户权限和命令访问控制
"""

from typing import Optional
from dataclasses import dataclass

from utils.logger import logger


@dataclass
class UserPermission:
    """用户权限"""
    user_id: str
    level: str  # "owner", "admin", "user"
    name: str = ""


class PermissionManager:
    """权限管理器"""

    def __init__(self, config: dict):
        """
        初始化权限管理器

        Args:
            config: 配置字典，包含：
                - owner_qq: 主人 QQ 号
                - owner_only_commands: 主人专属命令列表
        """
        self.owner_qq = config.get("owner_qq", "")
        self.owner_only_commands = config.get("owner_only_commands", [])

        # 用户权限缓存
        self._permissions: dict[str, UserPermission] = {}

        # 初始化主人权限
        if self.owner_qq:
            self._permissions[self.owner_qq] = UserPermission(
                user_id=self.owner_qq,
                level="owner",
                name="主人"
            )

        logger.info(f"权限管理器初始化完成，主人 QQ: {self.owner_qq}")

    def get_permission(self, user_id: str) -> UserPermission:
        """
        获取用户权限

        Args:
            user_id: 用户 ID

        Returns:
            用户权限
        """
        if user_id in self._permissions:
            return self._permissions[user_id]

        # 默认为普通用户
        return UserPermission(
            user_id=user_id,
            level="user"
        )

    def is_owner(self, user_id: str) -> bool:
        """
        判断是否是主人

        Args:
            user_id: 用户 ID

        Returns:
            是否是主人
        """
        return user_id == self.owner_qq

    def is_admin(self, user_id: str) -> bool:
        """
        判断是否是管理员

        Args:
            user_id: 用户 ID

        Returns:
            是否是管理员
        """
        perm = self.get_permission(user_id)
        return perm.level in ["owner", "admin"]

    def can_execute_command(self, user_id: str, command: str) -> bool:
        """
        判断用户是否可以执行命令

        Args:
            user_id: 用户 ID
            command: 命令名称

        Returns:
            是否可以执行
        """
        # 检查是否是主人专属命令
        if command in self.owner_only_commands:
            if not self.is_owner(user_id):
                logger.warning(f"用户 {user_id} 尝试执行主人专属命令: {command}")
                return False

        return True

    def add_admin(self, user_id: str, name: str = ""):
        """
        添加管理员

        Args:
            user_id: 用户 ID
            name: 用户名称
        """
        if user_id == self.owner_qq:
            logger.warning("不能将主人添加为管理员")
            return

        self._permissions[user_id] = UserPermission(
            user_id=user_id,
            level="admin",
            name=name
        )

        logger.info(f"添加管理员: {user_id} ({name})")

    def remove_admin(self, user_id: str):
        """
        移除管理员

        Args:
            user_id: 用户 ID
        """
        if user_id == self.owner_qq:
            logger.warning("不能移除主人的权限")
            return

        if user_id in self._permissions:
            del self._permissions[user_id]
            logger.info(f"移除管理员: {user_id}")

    def get_permission_denied_message(self, command: str) -> str:
        """
        获取权限不足的提示消息

        Args:
            command: 命令名称

        Returns:
            提示消息
        """
        return f"抱歉，这个指令只有主人才能使用哦~ (｡•́︿•̀｡)"

    def get_help_text(self) -> str:
        """获取权限帮助文本"""
        return """🔐 权限说明

👑 主人权限：
- 所有功能都可以使用
- 可以执行管理命令
- 可以切换机器人设置

👤 普通用户：
- 基本聊天功能
- 发送图片和表情
- 使用帮助命令

💡 提示：
- 管理命令需要主人授权
- 请勿滥用机器人功能"""
