# 财报智能分析系统

> 💡 **适合投资小白的智能财报分析工具**

自动下载财报 → 智能解析数据 → 生成投资建议

[![Phase](https://img.shields.io/badge/Phase-1.0%20完成-success)]()
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.9+-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

---

## 🎯 这是什么？

一个帮你分析股票的工具，就像有个专业的财务分析师帮你看财报。

**你只需要：**
1. 输入股票代码（如：600519）
2. 等程序分析
3. 看结果：买入/持有/卖出

**程序会自动：**
- 下载最新财报
- 读懂三大报表（损益表、资产负债表、现金流量表）
- 提取46个关键指标（营收、利润、ROE等）
- 计算各种比率（毛利率、资产负债率、增长率等）
- 给出投资建议（Phase 2 开发中）

---

## ✨ 核心功能

- ✅ **多市场支持**：A股、港股、美股三大市场
- ✅ **自动下载**：智能下载财报，支持失败重试
- ✅ **智能解析**：自动识别三大报表，提取46个指标
- ✅ **数据验证**：一致性检查 + 置信度评分
- ✅ **历史数据**：支持5年历史查询
- ✅ **空间管理**：自动清理旧文件（只保留2期）
- 🚧 **分析框架**：价值投资、成长投资（Phase 2 开发中）
- 🚧 **投资建议**：买入/持有/卖出（Phase 2 开发中）
- 🚧 **一键分析**：CLI工具（Phase 2 开发中）
- 🚧 **自动追踪**：财报季提醒（Phase 3 计划中）

---

## 🚀 快速开始

### 安装

```bash
# 1. 克隆代码
git clone https://github.com/aisong78/financial_report_scraper.git
cd financial_report_scraper

# 2. 安装依赖
pip install -r requirements.txt

# 3. 测试
python test_phase0.py  # 测试下载功能
python test_phase1.py  # 测试解析功能
```

### 配置（可选）

**A股和港股**：无需配置，直接可用！

**美股**：需要配置邮箱（SEC要求）

```bash
cp config.json.example config.json
# 编辑 config.json，把邮箱改成你的真实邮箱
```

### 使用

```bash
# 下载财报演示
python demo_download.py  # 选1下载A股财报
```

**详细教程：** 📖 [快速开始.md](快速开始.md)

---

## 📦 开发进度

### ✅ Phase 0（已完成）：财报下载
- ✅ A股下载（巨潮资讯）
- ✅ 港股下载（巨潮资讯）
- ✅ 美股下载（SEC EDGAR）
- ✅ 智能市场识别
- ✅ 配置管理和日志系统
- ✅ 数据库设计

**测试结果：** 4/4 通过 ✅

### ✅ Phase 1（已完成）：财报解析
- ✅ PDF解析器（A股/港股）
- ✅ HTML解析器（美股）
- ✅ 三大报表自动识别
- ✅ 46个核心指标提取
- ✅ 衍生指标计算（增长率、比率等）
- ✅ 数据验证和一致性检查
- ✅ 数据库存储（支持5年历史）
- ✅ 自动文件管理（保留2期）

**测试结果：** 5/5 通过 ✅
**代码量：** 3200+ 行
**完成时间：** 2024-11-21

**详细说明：** 📖 [Phase1完成总结.md](Phase1完成总结.md)

### ⏳ Phase 2（开发中）：智能分析
- ⏳ 价值投资分析框架（巴菲特风格）
- ⏳ 成长投资分析框架（彼得·林奇风格）
- ⏳ 评分系统（0-100分）
- ⏳ 投资建议生成
- ⏳ CLI工具（一键分析）
- ⏳ 分析报告生成

**预计完成：** 3-4天

### 🔜 Phase 3（计划中）：自动化
- 🔜 财报季自动监控
- 🔜 定时任务调度
- 🔜 结果推送通知

### 🔮 Phase 4（未来）：产品化
- 🔮 Web界面
- 🔮 多用户支持
- 🔮 自定义分析框架
- 🔮 AI辅助分析

---

## 📊 功能清单

| 功能 | 状态 | 说明 |
|------|------|------|
| **下载A股财报** | ✅ 可用 | 从巨潮资讯下载 |
| **下载港股财报** | ✅ 可用 | 从巨潮资讯下载 |
| **下载美股财报** | ✅ 可用 | 从SEC下载，需配置邮箱 |
| **解析PDF财报** | ✅ 可用 | 自动识别三大报表 |
| **解析HTML财报** | ✅ 可用 | 支持SEC EDGAR格式 |
| **提取46个指标** | ✅ 可用 | 包括营收、利润、ROE等 |
| **计算衍生指标** | ✅ 可用 | 增长率、比率、周转率等 |
| **数据验证** | ✅ 可用 | 一致性检查+置信度评分 |
| **数据库存储** | ✅ 可用 | SQLite，支持历史查询 |
| **文件管理** | ✅ 可用 | 自动清理，节省空间 |
| 分析公司好坏 | ⏳ Phase 2 | 基于分析框架打分 |
| 投资建议 | ⏳ Phase 2 | 买入/持有/卖出 |
| CLI工具 | ⏳ Phase 2 | 一键分析 |
| 自动监控 | 🔜 Phase 3 | 财报季提醒 |

---

## 📖 文档

### 📘 新手文档（强烈推荐）
- **[快速开始.md](快速开始.md)** - 完整使用教程，每一步都有说明
- **[Phase1完成总结.md](Phase1完成总结.md)** - Phase 1详细说明（小白版本）

### 📗 产品规划
- [需求分析.md](docs/01-产品规划/需求分析.md) - 产品需求和功能设计
- [产品架构设计.md](docs/01-产品规划/产品架构设计.md) - 技术架构
- [分阶段实施计划.md](docs/01-产品规划/分阶段实施计划.md) - 开发计划

### 📕 技术文档
- [财务指标体系.md](docs/02-技术文档/财务指标体系.md) - 92个指标详细说明
- [Phase1实施计划.md](docs/02-技术文档/Phase1实施计划.md) - Phase 1技术设计

---

## 💡 使用示例

### 示例1：下载并解析财报

```python
from src.scrapers import scrape_a_stock
from src.parsers import PDFParser
from src.extractors import MetricExtractor
from datetime import datetime

# 1. 下载贵州茅台财报
files = scrape_a_stock("600519", lookback_days=365)
print(f"下载了 {len(files)} 份财报")

# 2. 解析第一份财报
parser = PDFParser()
data = parser.parse(files[0])

# 3. 提取财务指标
extractor = MetricExtractor()
metrics = extractor.extract(data, stock_id=1, report_date=datetime(2024,12,31))

# 4. 查看结果
print(f"营收：{metrics['revenue']:,.0f} 元")
print(f"净利润：{metrics['net_profit']:,.0f} 元")
print(f"ROE：{metrics['roe']:.2%}")
print(f"毛利率：{metrics['gross_margin']:.2%}")
```

### 示例2：批量分析（Phase 2完成后）

```python
# Phase 2 完成后可用
from src.cli import analyze_stock

# 分析单只股票
result = analyze_stock("600519")
print(f"评分：{result.score}/100")
print(f"建议：{result.recommendation}")
print(f"理由：{result.reason}")
```

---

## 📊 支持的财务指标

### 15个P0核心指标
营业收入、净利润、总资产、总负债、股东权益、营收增长率、利润增长率、资产负债率、ROE、毛利率、净利率、经营现金流、PE、PB、EPS

### 31个P1补充指标
营业成本、各项费用、流动资产、非流动资产、货币资金、应收账款、存货、固定资产、商誉、流动负债、借款、应付账款、自由现金流、资产周转率、存货周转率、应收周转率、现金周转周期等

### P2扩展指标（预留）
92个指标体系，支持杜邦分析、现金转换周期等交叉计算

**详细说明：** 📖 [财务指标体系.md](docs/02-技术文档/财务指标体系.md)

---

## 🏗️ 项目结构

```
financial_report_scraper/
├── src/                        # 源代码
│   ├── scrapers/              # 爬虫（下载财报）
│   ├── parsers/               # 解析器（读懂财报）✨ Phase 1
│   ├── extractors/            # 提取器（提取指标）✨ Phase 1
│   ├── database/              # 数据库
│   └── utils/                 # 工具类
│
├── docs/                       # 文档
│   ├── 01-产品规划/
│   └── 02-技术文档/
│
├── test_phase0.py             # Phase 0 测试
├── test_phase1.py             # Phase 1 测试 ✨
├── demo_download.py           # 下载演示
├── Phase1完成总结.md          # Phase 1说明 ✨
├── 快速开始.md                # 使用教程 ✨
└── README.md                  # 本文件
```

---

## 🛠️ 技术栈

- **语言**：Python 3.9+
- **数据库**：SQLite（可升级PostgreSQL）
- **爬虫**：requests + sec-edgar-downloader
- **解析**：pdfplumber（PDF）+ BeautifulSoup（HTML）
- **数据处理**：pandas + numpy
- **ORM**：SQLAlchemy 2.0
- **日志**：Python logging
- **测试**：pytest

---

## ❓ 常见问题

### Q1: 需要付费吗？
**A:** 完全免费！代码开源，数据来自公开渠道。

### Q2: 需要服务器吗？
**A:** 不需要！程序在你自己电脑上运行。

### Q3: 数据准确吗？
**A:** 程序会自动验证数据一致性，给出置信度评分。建议重要决策前人工核对。

### Q4: 支持哪些股票？
**A:** A股、港股、美股。只要能公开获取财报的都支持。

### Q5: 我不懂代码怎么办？
**A:** Phase 2会提供命令行工具，不需要写代码。现在可以先看 [快速开始.md](快速开始.md) 学习。

### Q6: 能替代人工分析吗？
**A:** 可以作为辅助工具，但不能完全替代。投资决策还需要考虑宏观环境、行业趋势等因素。

### Q7: 有什么风险？
**A:**
- 数据解析可能有误差（置信度<80%需人工检查）
- 历史数据不代表未来表现
- 投资有风险，决策需谨慎

**更多问题：** 查看 [快速开始.md](快速开始.md) 的常见问题章节

---

## 🎓 适合什么人？

### ✅ 适合你，如果你是：
- 📈 股票投资者（想分析公司基本面）
- 💼 价值投资者（关注ROE、毛利率等）
- 🚀 成长投资者（关注增长率）
- 🎯 量化投资者（需要批量分析）
- 👨‍💻 开发者（想学习财报分析）

### ❌ 不适合你，如果你是：
- 🎰 短线交易者（本工具关注基本面，不做短线）
- 📊 技术分析者（本工具不看K线图）
- ⚡ 高频交易者（不适合秒级决策）

---

## 🧪 测试结果

### Phase 0 测试
```
✓ 通过  配置管理
✓ 通过  日志系统
✓ 通过  数据库
✓ 通过  爬虫模块

总计: 4/4 项测试通过 ✅
```

### Phase 1 测试
```
✓ 通过  数据库扩展
✓ 通过  解析器
✓ 通过  指标提取器
✓ 通过  文件管理器
✓ 通过  端到端流程

总计: 5/5 项测试通过 ✅
```

---

## ⚠️ 重要提示

### 免责声明
本工具仅供学习和研究使用，不构成投资建议。股市有风险，投资需谨慎。

### 安全配置
**请勿将包含敏感信息的配置文件提交到 Git！**
- `config.json` - 包含你的邮箱和自选股配置
- `.env` - 包含 API 密钥等敏感信息

这些文件已添加到 `.gitignore`。

---

## 🤝 贡献

欢迎提Issue和PR！

**开发路线图：**
- [ ] Phase 2：分析框架（预计1周）
- [ ] Phase 3：自动化（预计1周）
- [ ] Phase 4：Web界面（预计2周）

---

## 🎊 更新日志

### v1.0.0 (2024-11-21) - Phase 1完成 ✅
- ✅ 实现财报解析功能
- ✅ 支持46个财务指标提取
- ✅ 数据验证和一致性检查
- ✅ 自动文件管理
- ✅ 完善文档系统
- ✅ 新增详细的新手指南

### v0.1.0 (2024-11-20) - Phase 0完成 ✅
- ✅ 实现财报下载功能
- ✅ 支持A股、港股、美股
- ✅ 配置管理和日志系统
- ✅ 数据库设计

---

## 🙏 致谢

感谢以下开源项目：
- [sec-edgar-downloader](https://github.com/jadchaar/sec-edgar-downloader) - 美股财报下载
- [pdfplumber](https://github.com/jsvine/pdfplumber) - PDF解析
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM框架

---

## 📄 许可证

MIT License

---

## 👤 作者

Sonia - 个人投资者

---

## 📞 联系方式

- **GitHub：** https://github.com/aisong78/financial_report_scraper
- **Issues：** https://github.com/aisong78/financial_report_scraper/issues

---

**⭐ 如果这个项目对你有帮助，请给个Star！**

**📈 祝你投资顺利！**

---

**最后更新：** 2024-11-21
**当前版本：** Phase 1.0 ✅
**下一版本：** Phase 2.0（开发中）⏳
