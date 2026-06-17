"""
代码处理模块
处理代码识别、格式化和打包
"""

import zipfile
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional

from utils.logger import logger
from utils.helpers import sanitize_filename


class CodeProcessor:
    """代码处理器"""

    def __init__(self, temp_dir: str = "data/temp"):
        """
        初始化代码处理器

        Args:
            temp_dir: 临时文件目录
        """
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # 代码文件扩展名映射
        self.extension_map = {
            "python": ".py",
            "py": ".py",
            "javascript": ".js",
            "js": ".js",
            "typescript": ".ts",
            "ts": ".ts",
            "java": ".java",
            "c": ".c",
            "cpp": ".cpp",
            "c++": ".cpp",
            "csharp": ".cs",
            "c#": ".cs",
            "go": ".go",
            "rust": ".rs",
            "ruby": ".rb",
            "php": ".php",
            "swift": ".swift",
            "kotlin": ".kt",
            "html": ".html",
            "css": ".css",
            "sql": ".sql",
            "shell": ".sh",
            "bash": ".sh",
            "powershell": ".ps1",
            "json": ".json",
            "xml": ".xml",
            "yaml": ".yaml",
            "yml": ".yaml",
            "markdown": ".md",
            "md": ".md",
            "text": ".txt",
            "txt": ".txt",
        }

        logger.info("代码处理器初始化完成")

    async def package_code(
        self,
        code_blocks: list[dict],
        filename_prefix: str = "code"
    ) -> Optional[str]:
        """
        将代码块打包成 zip 文件

        Args:
            code_blocks: 代码块列表，每个包含 language 和 code
            filename_prefix: 文件名前缀

        Returns:
            zip 文件路径，如果失败则返回 None
        """
        if not code_blocks:
            return None

        try:
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"{filename_prefix}_{timestamp}.zip"
            zip_path = self.temp_dir / zip_filename

            # 创建 zip 文件
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for i, block in enumerate(code_blocks):
                    language = block.get("language", "text")
                    code = block.get("code", "")

                    # 确定文件扩展名
                    ext = self.extension_map.get(language.lower(), ".txt")

                    # 生成文件名
                    if len(code_blocks) == 1:
                        file_name = f"{filename_prefix}{ext}"
                    else:
                        file_name = f"{filename_prefix}_{i + 1}{ext}"

                    # 写入 zip
                    zf.writestr(file_name, code)

            logger.info(f"代码打包完成: {zip_path}")
            return str(zip_path)

        except Exception as e:
            logger.error(f"代码打包失败: {e}")
            return None

    async def format_code(self, code: str, language: str) -> str:
        """
        格式化代码（简单处理）

        Args:
            code: 代码内容
            language: 编程语言

        Returns:
            格式化后的代码
        """
        # 移除首尾空白
        code = code.strip()

        # 添加语言标识
        return f"```{language}\n{code}\n```"

    def cleanup_temp(self, max_age_hours: int = 24):
        """
        清理临时文件

        Args:
            max_age_hours: 最大保留时间（小时）
        """
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600

            for file_path in self.temp_dir.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        logger.debug(f"清理临时文件: {file_path}")

        except Exception as e:
            logger.error(f"清理临时文件失败: {e}")

    async def close(self):
        """关闭资源"""
        # 清理超过 1 小时的临时文件
        self.cleanup_temp(max_age_hours=1)
