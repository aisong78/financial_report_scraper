# Phase 1 实施计划

> ⚠️ **状态更新**：Phase 1 已完成 ✅ (2025-11-22)
>
> **实际完成文档**: [Phase1.3实现总结.md](../../Phase1.3实现总结.md)
>
> 本文档为早期规划版本，保留用于参考原始计划。实际实现请参考上述完成总结文档。

---

## 🎯 目标

实现财报解析和财务指标提取功能

---

## 📋 核心功能

### 1. 财报解析器（Parser）
- 解析PDF格式财报（A股、港股）
- 解析HTML格式财报（美股）
- 提取三大报表数据

### 2. 指标提取器（Extractor）
- 从解析结果中提取46个关键指标（P0+P1）
- 计算衍生指标（增长率、比率等）
- 数据清洗和验证

### 3. 数据存储
- 保存到 `financial_metrics` 表
- 关联 `financial_reports` 表
- 支持历史5年数据

### 4. 文件管理
- 保留最近2期原始文件
- 自动清理旧文件
- 压缩归档选项

---

## 🏗️ 技术架构

```
原始财报（PDF/HTML）
    ↓
解析器（Parser）
    ↓
结构化数据（JSON）
    ↓
提取器（Extractor）
    ↓
财务指标（46个）
    ↓
数据库（financial_metrics表）
```

---

## 📦 模块设计

### 1. 解析器模块 `src/parsers/`

#### 1.1 `base_parser.py` - 基础解析器
```python
class BaseParser:
    """解析器基类"""

    def parse(self, file_path: str) -> dict:
        """解析财报文件"""
        pass

    def extract_tables(self, content) -> list:
        """提取表格"""
        pass

    def clean_data(self, data: dict) -> dict:
        """数据清洗"""
        pass
```

#### 1.2 `pdf_parser.py` - PDF解析器
```python
class PDFParser(BaseParser):
    """PDF财报解析器（中文）"""

    # 使用 pdfplumber 提取表格
    # 识别三大报表：
    # - 资产负债表
    # - 利润表（损益表）
    # - 现金流量表
```

#### 1.3 `html_parser.py` - HTML解析器
```python
class HTMLParser(BaseParser):
    """HTML财报解析器（美股）"""

    # 使用 BeautifulSoup 解析
    # SEC EDGAR 格式解析
    # XBRL标签识别
```

### 2. 提取器模块 `src/extractors/`

#### 2.1 `metric_extractor.py` - 指标提取器
```python
class MetricExtractor:
    """财务指标提取器"""

    def extract(self, parsed_data: dict) -> dict:
        """提取46个指标"""

        # P0: 15个核心指标
        metrics = {}
        metrics['revenue'] = self._extract_revenue(parsed_data)
        metrics['net_profit'] = self._extract_net_profit(parsed_data)
        # ...

        # P1: 31个补充指标
        # ...

        return metrics

    def calculate_ratios(self, metrics: dict) -> dict:
        """计算比率指标"""

        # 毛利率
        if metrics.get('revenue') and metrics.get('operating_cost'):
            metrics['gross_margin'] = (
                (metrics['revenue'] - metrics['operating_cost'])
                / metrics['revenue']
            )

        # ROE
        if metrics.get('net_profit') and metrics.get('total_equity'):
            metrics['roe'] = metrics['net_profit'] / metrics['total_equity']

        # 其他比率...

        return metrics

    def calculate_growth(self, stock_id: int, current_metrics: dict) -> dict:
        """计算增长率（需要历史数据）"""

        # 查询去年同期数据
        last_year = self._get_last_year_metrics(stock_id)

        if last_year:
            # 营收同比
            current_metrics['revenue_yoy'] = (
                (current_metrics['revenue'] - last_year['revenue'])
                / last_year['revenue']
            )

            # 利润同比
            current_metrics['net_profit_yoy'] = (
                (current_metrics['net_profit'] - last_year['net_profit'])
                / last_year['net_profit']
            )

        return current_metrics
```

#### 2.2 `validator.py` - 数据验证器
```python
class MetricValidator:
    """指标验证器"""

    def validate(self, metrics: dict) -> tuple[bool, list]:
        """验证指标合理性"""

        errors = []

        # 1. 必填字段检查
        required = ['revenue', 'net_profit', 'total_assets']
        for field in required:
            if field not in metrics or metrics[field] is None:
                errors.append(f"缺少必填字段: {field}")

        # 2. 数值范围检查
        if metrics.get('asset_liability_ratio'):
            if metrics['asset_liability_ratio'] < 0 or metrics['asset_liability_ratio'] > 1:
                errors.append("资产负债率超出合理范围 [0, 1]")

        # 3. 逻辑一致性检查
        if metrics.get('total_assets') and metrics.get('total_liabilities') and metrics.get('total_equity'):
            if abs(metrics['total_assets'] - metrics['total_liabilities'] - metrics['total_equity']) > 0.01:
                errors.append("资产负债表不平衡")

        return len(errors) == 0, errors
```

### 3. 文件管理模块 `src/utils/file_manager.py`

```python
class FileManager:
    """财报文件管理器"""

    def __init__(self, stock_id: int):
        self.stock_id = stock_id
        self.keep_recent = 2  # 保留最近2期

    def cleanup_old_files(self):
        """清理旧文件"""

        # 1. 查询该股票所有财报
        reports = self._get_all_reports(self.stock_id)

        # 2. 按时间排序
        reports.sort(key=lambda x: x.report_date, reverse=True)

        # 3. 保留最近2期，删除其余
        to_delete = reports[self.keep_recent:]

        for report in to_delete:
            if report.file_path and os.path.exists(report.file_path):
                os.remove(report.file_path)
                self.logger.info(f"删除旧文件: {report.file_path}")

                # 更新数据库：清空 file_path
                report.file_path = None
                self.db.commit()

    def archive_file(self, file_path: str) -> str:
        """归档文件（压缩）"""

        archive_path = file_path + ".gz"

        with open(file_path, 'rb') as f_in:
            with gzip.open(archive_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        os.remove(file_path)
        return archive_path
```

---

## 🔧 数据库扩展

### 扩展 `financial_metrics` 表

需要添加 P1 优先级的字段（31个）：

```python
# src/database/models.py 扩展

class FinancialMetric(Base):
    # ... 现有字段 ...

    # 损益表补充
    operating_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    selling_expense: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    admin_expense: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    finance_expense: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    tax_expense: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    ebitda_margin: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    eps_diluted: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    bps: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))

    # 资产负债表补充
    non_current_assets: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    cash_and_equivalents: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    accounts_receivable: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    inventory: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    fixed_assets: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    intangible_assets: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    goodwill: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    non_current_liabilities: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    short_term_borrowing: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    long_term_borrowing: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    accounts_payable: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))

    # 现金流补充
    net_cash_flow: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    fcf_per_share: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    fcf_to_revenue: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    ocf_to_net_profit: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))

    # 运营效率
    asset_turnover: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    inventory_turnover: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    receivable_turnover: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    cash_conversion_cycle: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))

    # 其他
    peg_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))

    # 预留字段（P2指标）
    extra_metrics: Mapped[Optional[dict]] = mapped_column(JSON)
```

---

## 📝 实施步骤

### Step 1: 准备工作（已完成）
- ✅ 设计指标体系（92个指标，Phase 1 实现 46 个）
- ✅ 创建实施计划

### Step 2: 数据库扩展
1. 更新 `models.py`，添加 P1 字段
2. 创建数据库迁移脚本
3. 测试数据库

### Step 3: 开发解析器
1. 实现 `PDFParser`
   - 使用 pdfplumber 提取表格
   - 识别三大报表
   - 处理中文财报格式

2. 实现 `HTMLParser`
   - 解析 SEC EDGAR HTML
   - 识别 XBRL 标签
   - 提取美股数据

### Step 4: 开发提取器
1. 实现 `MetricExtractor`
   - P0 指标提取（15个）
   - P1 指标提取（31个）
   - 比率计算
   - 增长率计算

2. 实现 `MetricValidator`
   - 数据验证
   - 一致性检查

### Step 5: 开发文件管理
1. 实现 `FileManager`
   - 自动清理旧文件
   - 归档功能

### Step 6: 集成和测试
1. 创建端到端流程
2. 编写测试用例
3. 运行测试并修复bug

---

## 🧪 测试计划

### 1. 单元测试
- `test_pdf_parser.py` - PDF解析器测试
- `test_html_parser.py` - HTML解析器测试
- `test_metric_extractor.py` - 指标提取测试
- `test_metric_validator.py` - 验证器测试
- `test_file_manager.py` - 文件管理测试

### 2. 集成测试
- `test_phase1.py` - Phase 1 完整流程测试

测试用例：
1. 下载贵州茅台（600519）2023年年报
2. 解析PDF，提取指标
3. 验证46个指标全部提取成功
4. 保存到数据库
5. 查询验证数据完整性
6. 清理旧文件

---

## 📦 依赖包

新增依赖：

```txt
# PDF 解析
pdfplumber==0.10.3

# HTML 解析
beautifulsoup4==4.12.2
lxml==4.9.3

# 数据处理
pandas==2.1.4
numpy==1.26.2

# XBRL（美股财报）
sec-xbrl==2.0.0  # 可选，如果需要深度解析
```

---

## 🎯 成功标准

Phase 1 完成的标志：

1. ✅ 能够解析 A股 PDF 财报
2. ✅ 能够解析美股 HTML 财报
3. ✅ 成功提取 46 个关键指标（P0+P1）
4. ✅ 数据验证通过
5. ✅ 保存到数据库
6. ✅ 自动清理旧文件（保留2期）
7. ✅ 测试覆盖率 > 80%
8. ✅ 端到端测试通过

---

## ⏱️ 时间估算

| 任务 | 预计时间 | 说明 |
|------|---------|------|
| 数据库扩展 | 0.5天 | 添加字段 + 迁移 |
| PDF解析器 | 1.5天 | 复杂度高 |
| HTML解析器 | 1天 | SEC格式相对标准 |
| 指标提取器 | 1天 | 46个指标逻辑 |
| 验证器 | 0.5天 | 规则编写 |
| 文件管理 | 0.5天 | 清理逻辑 |
| 集成测试 | 1天 | 端到端 + 调试 |
| **合计** | **6天** | **预留1天缓冲 = 7天** |

---

## 🚨 风险和挑战

### 1. PDF解析精度
- **风险**：不同公司财报格式差异大，表格识别可能失败
- **应对**：
  - 收集多家公司样本测试
  - 实现模板匹配和容错机制
  - 解析失败时标记为需要人工审核

### 2. 指标计算依赖
- **风险**：某些指标需要历史数据（如增长率），首次运行时无法计算
- **应对**：
  - 首次导入时下载5年历史财报
  - 增长率等指标设为可选

### 3. 美股XBRL格式
- **风险**：XBRL标签众多，提取逻辑复杂
- **应对**：
  - 使用成熟的 sec-xbrl 库
  - 先支持主流科技股（AAPL、MSFT等）
  - 逐步扩展行业覆盖

### 4. 数据质量
- **风险**：提取的数据可能有错误或不一致
- **应对**：
  - 严格的验证规则
  - 计算 confidence_score（置信度）
  - 低置信度数据标记预警

---

## 📄 交付物

1. **代码模块**
   - `src/parsers/` - 解析器
   - `src/extractors/` - 提取器
   - `src/utils/file_manager.py` - 文件管理

2. **数据库**
   - 扩展的 `financial_metrics` 表
   - 迁移脚本

3. **测试脚本**
   - `test_phase1.py`
   - 单元测试套件

4. **文档**
   - 本实施计划
   - 财务指标体系文档
   - API 使用文档

---

## 🔜 下一步（Phase 2）

Phase 1 完成后，进入 Phase 2：
- 实现价值投资分析框架
- 实现成长投资分析框架
- 生成评分和投资建议
- 开发 CLI 工具

---

**开始时间：** 2024-XX-XX
**预计完成：** 2024-XX-XX
**实际完成：** _待更新_
