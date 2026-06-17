"""
表情包管理模块
管理本地表情包库
"""

import random
from pathlib import Path
from typing import Optional

from utils.logger import logger


class EmojiManager:
    """表情包管理器"""

    def __init__(self, config: dict):
        """
        初始化表情包管理器

        Args:
            config: 配置字典，包含：
                - enabled: 是否启用
                - directory: 表情包目录
                - max_per_message: 每条消息最大表情数
        """
        self.enabled = config.get("enabled", True)
        self.emoji_dir = Path(config.get("directory", "resources/emojis"))
        self.max_per_message = config.get("max_per_message", 1)

        # 情绪分类
        self.emotions = ["happy", "sad", "funny", "angry", "surprised", "love"]

        # 确保目录存在
        self._ensure_directories()

        # 缓存表情包列表
        self._emoji_cache: dict[str, list[Path]] = {}
        self._load_emoji_cache()

        logger.info(f"表情包管理器初始化完成，共加载 {sum(len(v) for v in self._emoji_cache.values())} 个表情")

    def _ensure_directories(self):
        """确保表情包目录存在"""
        self.emoji_dir.mkdir(parents=True, exist_ok=True)

        for emotion in self.emotions:
            (self.emoji_dir / emotion).mkdir(exist_ok=True)

    def _load_emoji_cache(self):
        """加载表情包缓存"""
        for emotion in self.emotions:
            emotion_dir = self.emoji_dir / emotion
            emojis = list(emotion_dir.glob("*.jpg")) + \
                     list(emotion_dir.glob("*.png")) + \
                     list(emotion_dir.glob("*.gif"))
            self._emoji_cache[emotion] = emojis

    def get_random_emoji(self, emotion: Optional[str] = None) -> Optional[str]:
        """
        获取随机表情包

        Args:
            emotion: 情绪类型，如果不指定则随机选择

        Returns:
            表情包文件路径，如果没有则返回 None
        """
        if not self.enabled:
            return None

        # 确定从哪个情绪分类中选择
        if emotion and emotion in self._emoji_cache:
            emojis = self._emoji_cache[emotion]
        else:
            # 随机选择一个情绪分类
            all_emojis = []
            for emoji_list in self._emoji_cache.values():
                all_emojis.extend(emoji_list)
            emojis = all_emojis

        if not emojis:
            logger.warning("没有可用的表情包")
            return None

        # 随机选择一个
        selected = random.choice(emojis)
        return str(selected)

    def get_emoji_by_text(self, text: str) -> Optional[str]:
        """
        根据文本内容选择合适的表情包

        Args:
            text: 文本内容

        Returns:
            表情包文件路径
        """
        # 简单的情绪判断
        emotion = self._detect_emotion(text)
        return self.get_random_emoji(emotion)

    def _detect_emotion(self, text: str) -> str:
        """
        检测文本情绪

        Args:
            text: 文本内容

        Returns:
            情绪类型
        """
        text = text.lower()

        # 开心相关
        happy_words = ["哈哈", "开心", "高兴", "嘻嘻", "太棒了", "好的", "可以", "没问题"]
        if any(word in text for word in happy_words):
            return "happy"

        # 难过相关
        sad_words = ["难过", "伤心", "哭", "不开心", "郁闷", "唉"]
        if any(word in text for word in sad_words):
            return "sad"

        # 搞笑相关
        funny_words = ["哈哈", "笑死", "搞笑", "逗", "段子"]
        if any(word in text for word in funny_words):
            return "funny"

        # 生气相关
        angry_words = ["生气", "愤怒", "讨厌", "烦", "滚"]
        if any(word in text for word in angry_words):
            return "angry"

        # 惊讶相关
        surprised_words = ["哇", "天哪", "不会吧", "真的吗", "惊"]
        if any(word in text for word in surprised_words):
            return "surprised"

        # 爱心相关
        love_words = ["爱", "喜欢", "么么", "亲", "心"]
        if any(word in text for word in love_words):
            return "love"

        # 默认随机
        return random.choice(self.emotions)

    def add_emoji(self, emotion: str, file_path: str) -> bool:
        """
        添加表情包

        Args:
            emotion: 情绪类型
            file_path: 表情包文件路径

        Returns:
            是否成功
        """
        if emotion not in self.emotions:
            logger.warning(f"不支持的情绪类型: {emotion}")
            return False

        source = Path(file_path)
        if not source.exists():
            logger.warning(f"表情包文件不存在: {file_path}")
            return False

        # 复制到对应目录
        target = self.emoji_dir / emotion / source.name

        try:
            import shutil
            shutil.copy2(source, target)

            # 更新缓存
            self._emoji_cache[emotion].append(target)

            logger.info(f"添加表情包: {target}")
            return True

        except Exception as e:
            logger.error(f"添加表情包失败: {e}")
            return False

    def get_emoji_count(self) -> dict[str, int]:
        """
        获取各情绪的表情包数量

        Returns:
            各情绪的表情包数量字典
        """
        return {emotion: len(emojis) for emotion, emojis in self._emoji_cache.items()}
