"""
爬虫基类

提供所有爬虫的通用功能
"""

import os
import time
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..utils.logger import get_logger
from ..utils.config import get_config


class BaseScraper(ABC):
    """爬虫基类"""

    def __init__(self, market: str):
        """
        初始化爬虫

        Args:
            market: 市场类型（A, HK, US）
        """
        self.market = market
        self.logger = get_logger()
        self.config = get_config()

        # 创建 requests session（带重试）
        self.session = self._create_session()

        # 保存目录
        self.save_dir = self._get_save_dir()

    def _create_session(self) -> requests.Session:
        """
        创建带重试机制的 requests session

        Returns:
            配置好的 Session
        """
        session = requests.Session()

        # 重试策略
        retry_strategy = Retry(
            total=3,  # 最多重试 3 次
            backoff_factor=1,  # 重试间隔：1s, 2s, 4s
            status_forcelist=[429, 500, 502, 503, 504],  # 这些状态码会重试
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _get_save_dir(self) -> Path:
        """获取保存目录"""
        base_dir = Path(self.config.save_dir)
        market_dir = base_dir / f"{self.market}_stocks"
        market_dir.mkdir(parents=True, exist_ok=True)
        return market_dir

    def download_file(
        self,
        url: str,
        save_path: str,
        timeout: int = 30,
        skip_existing: bool = True
    ) -> bool:
        """
        下载文件

        Args:
            url: 文件 URL
            save_path: 保存路径
            timeout: 超时时间（秒）
            skip_existing: 是否跳过已存在的文件

        Returns:
            是否成功
        """
        # 检查文件是否已存在
        if skip_existing and os.path.exists(save_path):
            self.logger.info(f"文件已存在，跳过: {save_path}")
            return True

        self.logger.info(f"正在下载: {url}")

        try:
            response = self.session.get(url, stream=True, timeout=timeout)
            response.raise_for_status()

            # 下载文件
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            file_size = os.path.getsize(save_path)
            self.logger.info(f"下载完成: {save_path} ({file_size / 1024:.2f} KB)")
            return True

        except requests.exceptions.Timeout:
            self.logger.error(f"下载超时: {url}")
            return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"下载失败: {url}, 错误: {e}")
            return False
        except IOError as e:
            self.logger.error(f"文件写入失败: {save_path}, 错误: {e}")
            return False
        except Exception as e:
            self.logger.exception(f"下载出现未知错误: {url}")
            return False

    def sanitize_filename(self, filename: str, max_length: int = 200) -> str:
        """
        清理文件名

        Args:
            filename: 原始文件名
            max_length: 最大长度

        Returns:
            清理后的文件名
        """
        # 替换非法字符
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        # 限制长度
        if len(filename) > max_length:
            # 保留扩展名
            name, ext = os.path.splitext(filename)
            name = name[:max_length - len(ext)]
            filename = name + ext

        return filename

    def rate_limit(self, delay: float = 1.0):
        """
        速率限制（防止被封）

        Args:
            delay: 延迟秒数
        """
        time.sleep(delay)

    @abstractmethod
    def scrape(
        self,
        stock_code: str,
        lookback_days: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        爬取股票财报

        Args:
            stock_code: 股票代码
            lookback_days: 回溯天数

        Returns:
            财报列表
        """
        pass

    @abstractmethod
    def download_report(
        self,
        report_info: Dict[str, Any]
    ) -> Optional[str]:
        """
        下载财报文件

        Args:
            report_info: 财报信息

        Returns:
            下载的文件路径，失败返回 None
        """
        pass

    def __del__(self):
        """析构函数：关闭 session"""
        if hasattr(self, 'session'):
            self.session.close()
