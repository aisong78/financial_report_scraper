"""
配置管理模块

支持从 YAML 文件和环境变量加载配置
优先级：环境变量 > 配置文件 > 默认值
"""

import os
from pathlib import Path
from typing import List, Optional, Any, Dict
import json

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from dotenv import load_dotenv


class Config:
    """配置类"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置

        Args:
            config_path: 配置文件路径，如果为 None 则使用默认路径
        """
        # 加载环境变量
        load_dotenv()

        # 确定配置文件路径
        if config_path is None:
            # 默认配置文件路径
            project_root = self._get_project_root()
            self.config_path = project_root / "config.json"

            # 如果存在 config.yaml，优先使用
            yaml_path = project_root / "config" / "config.yaml"
            if yaml_path.exists() and YAML_AVAILABLE:
                self.config_path = yaml_path
        else:
            self.config_path = Path(config_path)

        # 加载配置
        self._config_data = self._load_config()

    @staticmethod
    def _get_project_root() -> Path:
        """获取项目根目录"""
        current = Path(__file__).resolve()
        # 从 src/utils/config.py 回到项目根目录
        return current.parent.parent.parent

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_path.exists():
            print(f"警告：配置文件不存在: {self.config_path}")
            print("使用默认配置")
            return self._get_default_config()

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.config_path.suffix in ['.yaml', '.yml']:
                    if not YAML_AVAILABLE:
                        raise ImportError("需要安装 pyyaml: pip install pyyaml")
                    data = yaml.safe_load(f)
                elif self.config_path.suffix == '.json':
                    data = json.load(f)
                else:
                    raise ValueError(f"不支持的配置文件格式: {self.config_path.suffix}")

            print(f"配置文件加载成功: {self.config_path}")
            return data

        except Exception as e:
            print(f"加载配置文件失败: {e}")
            print("使用默认配置")
            return self._get_default_config()

    @staticmethod
    def _get_default_config() -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "stocks": [],
            "keywords": [
                "年度报告", "半年度报告", "季度报告",
                "年报", "半年报", "季报",
                "财务报告", "业绩公告"
            ],
            "save_dir": "data/reports",
            "lookback_days": 30,
            "user_email": "your_email@example.com"
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项

        优先级：环境变量 > 配置文件 > 默认值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        # 1. 尝试从环境变量获取（转换为大写）
        env_key = key.upper()
        env_value = os.getenv(env_key)
        if env_value is not None:
            return self._parse_env_value(env_value)

        # 2. 从配置文件获取
        if key in self._config_data:
            return self._config_data[key]

        # 3. 返回默认值
        return default

    @staticmethod
    def _parse_env_value(value: str) -> Any:
        """解析环境变量值"""
        # 尝试解析为 JSON（支持列表、字典等）
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass

        # 布尔值
        if value.lower() in ['true', 'yes', '1']:
            return True
        if value.lower() in ['false', 'no', '0']:
            return False

        # 数字
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        # 字符串
        return value

    # 便捷属性

    @property
    def stocks(self) -> List[str]:
        """自选股列表"""
        return self.get("stocks", [])

    @property
    def keywords(self) -> List[str]:
        """财报关键词"""
        return self.get("keywords", [])

    @property
    def save_dir(self) -> str:
        """保存目录"""
        save_dir = self.get("save_dir", "data/reports")
        # 转换为绝对路径
        if not os.path.isabs(save_dir):
            project_root = self._get_project_root()
            save_dir = str(project_root / save_dir)
        return save_dir

    @property
    def lookback_days(self) -> int:
        """回溯天数"""
        return self.get("lookback_days", 30)

    @property
    def user_email(self) -> str:
        """用户邮箱"""
        # 优先从环境变量获取
        return self.get("user_email", "your_email@example.com")

    @property
    def database_url(self) -> str:
        """数据库连接 URL"""
        db_url = self.get("database_url")
        if db_url:
            return db_url

        # 默认 SQLite
        project_root = self._get_project_root()
        db_path = project_root / "data" / "database.db"
        return f"sqlite:///{db_path}"

    @property
    def log_level(self) -> str:
        """日志级别"""
        return self.get("log_level", "INFO")

    @property
    def log_dir(self) -> str:
        """日志目录"""
        log_dir = self.get("log_dir", "logs")
        if not os.path.isabs(log_dir):
            project_root = self._get_project_root()
            log_dir = str(project_root / log_dir)
        return log_dir

    # API 密钥

    @property
    def anthropic_api_key(self) -> Optional[str]:
        """Anthropic API Key"""
        return self.get("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY")

    @property
    def openai_api_key(self) -> Optional[str]:
        """OpenAI API Key"""
        return self.get("openai_api_key") or os.getenv("OPENAI_API_KEY")

    def validate(self) -> bool:
        """
        验证配置完整性

        Returns:
            是否验证通过
        """
        issues = []

        # 检查邮箱
        if self.user_email == "your_email@example.com":
            issues.append("请在配置文件中设置有效的 user_email")

        # 检查自选股
        if not self.stocks:
            issues.append("警告：未配置自选股列表")

        # 打印问题
        if issues:
            print("配置验证发现以下问题：")
            for issue in issues:
                print(f"  - {issue}")
            return False

        print("配置验证通过")
        return True

    def __repr__(self) -> str:
        """字符串表示"""
        return f"<Config(path='{self.config_path}', stocks={len(self.stocks)})>"


# 全局配置实例（单例模式）
_config_instance: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """
    获取全局配置实例

    Args:
        config_path: 配置文件路径（仅首次调用时有效）

    Returns:
        Config 实例
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)
    return _config_instance


def reload_config(config_path: Optional[str] = None) -> Config:
    """
    重新加载配置

    Args:
        config_path: 配置文件路径

    Returns:
        新的 Config 实例
    """
    global _config_instance
    _config_instance = Config(config_path)
    return _config_instance


if __name__ == "__main__":
    # 测试配置加载
    config = get_config()
    print(f"配置实例: {config}")
    print(f"自选股: {config.stocks}")
    print(f"保存目录: {config.save_dir}")
    print(f"用户邮箱: {config.user_email}")
    print(f"数据库 URL: {config.database_url}")
    print(f"日志级别: {config.log_level}")

    # 验证配置
    config.validate()
