# Stock Analyzer CLI 使用指南

命令行股票分析工具，支持评分分析、筛选、数据更新等功能。

## 📥 安装依赖

```bash
pip install click rich sqlalchemy pyyaml
```

## 🚀 快速开始

### 1. 查看帮助

```bash
python stock_analyzer.py --help
```

### 2. 列出所有可用框架

```bash
python stock_analyzer.py list-frameworks
```

输出：
```
可用的分析框架:

评分型框架（Scoring）:
  • value_investing - 价值投资框架（巴菲特风格）
  • growth_investing - 成长投资框架（彼得·林奇风格）

筛选型框架（Screening）:
  • quality_stock_screener - 优质白马股筛选框架
```

## 📊 主要命令

### `screen` - 筛选股票（Pass/Fail）

筛选股票是否符合硬性标准。

**基本用法：**
```bash
# 筛选单只股票
python stock_analyzer.py screen 600519

# 筛选多只股票
python stock_analyzer.py screen 600519 000858 002594

# 使用指定框架
python stock_analyzer.py screen 600519 --framework quality_stock_screener

# 简化输出（只显示结果，不显示详情）
python stock_analyzer.py screen 600519 --no-detail
```

**输出示例：**
```
使用筛选框架: quality_stock_screener

正在筛选: 600519

╭────────────────────────── 筛选报告 ──────────────────────────╮
│ 贵州茅台                                                       │
│ 框架: 优质白马股筛选框架                                       │
│ ❌ 筛选结果: FAIL                                             │
│ 通过率: 18.8%                                                 │
╰──────────────────────────────────────────────────────────────╯

❌ 核心财务指标  (56% 通过)
❌ 估值与性价比  (14% 通过)
✅ 风险控制  (0% 通过)
```

---

### `analyze` - 分析股票（评分 0-100）

对股票进行多维度评分分析。

**基本用法：**
```bash
# 分析单只股票
python stock_analyzer.py analyze 600519

# 分析多只股票（对比）
python stock_analyzer.py analyze 600519 000858

# 使用成长投资框架
python stock_analyzer.py analyze 600519 --framework growth_investing

# 简化输出
python stock_analyzer.py analyze 600519 --no-detail
```

**输出示例：**
```
使用分析框架: value_investing

正在分析: 600519

╭───────────── 分析报告 ─────────────╮
│ 贵州茅台                            │
│ 框架: 价值投资框架                  │
│ 总分: 72.5/100                     │
│ 评级: 中等                          │
╰────────────────────────────────────╯

          各维度得分
╭───────────┬────┬──────┬──────╮
│ 维度      │ 得分 │ 权重 │ 评价 │
├───────────┼────┼──────┼──────┤
│ 盈利能力  │ 85.0│  40% │ 优秀 │
│ 财务健康  │ 70.0│  30% │ 良好 │
│ 成长性    │ 60.0│  20% │ 一般 │
│ 估值      │ 55.0│  10% │ 一般 │
╰───────────┴────┴──────┴──────╯
```

---

### `info` - 查看股票信息

查看股票基本信息和数据库中的财务数据摘要。

**用法：**
```bash
python stock_analyzer.py info 600519
```

**输出：**
```
股票信息: 600519

股票代码          600519
股票名称          贵州茅台
市场              A
交易所            SSE
行业              白酒

财务数据: 5 条记录
最新数据日期: 2025-12-31
```

---

### `update-data` - 更新市场数据

获取并更新股票的市值、分红等市场数据。

**用法：**
```bash
# 更新最近5年数据（默认）
python stock_analyzer.py update-data 600519

# 更新最近10年数据
python stock_analyzer.py update-data 600519 --years 10
```

**输出：**
```
更新市场数据: 600519

正在获取 5 年市场数据...

✓ 市场数据更新成功！

      估值历史
╭──────┬────────┬──────────╮
│ 年份 │   PE   │   市值   │
├──────┼────────┼──────────┤
│ 2025 │  125.6 │ 25124亿  │
│ 2024 │  105.6 │ 23239亿  │
│ 2023 │   83.7 │ 20099亿  │
│ 2022 │   65.2 │ 16958亿  │
│ 2021 │   53.8 │ 15074亿  │
╰──────┴────────┴──────────╯
```

---

## 🔄 完整工作流示例

### 场景1：筛选优质白马股

```bash
# 1. 筛选多只候选股票
python stock_analyzer.py screen 600519 000858 002594 600036

# 2. 对通过筛选的股票进行详细分析
python stock_analyzer.py analyze 600519 000858

# 3. 查看具体股票的详细信息
python stock_analyzer.py info 600519

# 4. 更新市场数据以获取最新估值
python stock_analyzer.py update-data 600519
```

### 场景2：价值投资分析

```bash
# 使用价值投资框架分析
python stock_analyzer.py analyze 600519 --framework value_investing

# 对比多只价值股
python stock_analyzer.py analyze 600519 000858 601318 --framework value_investing
```

### 场景3：成长股筛选

```bash
# 使用成长投资框架
python stock_analyzer.py analyze 300750 002415 --framework growth_investing
```

---

## 💡 使用提示

### 1. 批量操作

对多只股票同时操作时，结果会显示汇总对比：

```bash
python stock_analyzer.py screen 600519 000858 002594
```

会在最后显示：
```
═══ 筛选汇总 ═══

╭──────────────┬────────┬────────╮
│ 股票         │ 结果   │ 通过率 │
├──────────────┼────────┼────────┤
│ 贵州茅台     │ FAIL   │  18.8% │
│ 五粮液       │ PASS   │  87.5% │
│ 宁德时代     │ FAIL   │  43.8% │
╰──────────────┴────────┴────────╯

统计:
  通过: 1
  未通过: 2
```

### 2. 简化输出模式

当你只需要看结果而不需要详细信息时，使用 `--no-detail`：

```bash
python stock_analyzer.py screen 600519 000858 --no-detail
```

输出：
```
  ❌ 贵州茅台: FAIL (通过率: 18.8%)
  ✅ 五粮液: PASS (通过率: 87.5%)
```

### 3. 查看命令帮助

每个命令都有详细的帮助信息：

```bash
python stock_analyzer.py screen --help
python stock_analyzer.py analyze --help
python stock_analyzer.py info --help
python stock_analyzer.py update-data --help
```

---

## 🎯 框架选择建议

### 评分型框架（用于 `analyze` 命令）

| 框架 | 适用场景 | 关注重点 |
|-----|---------|---------|
| `value_investing` | 价值投资者 | ROE、负债率、自由现金流 |
| `growth_investing` | 成长投资者 | 营收增速、利润增速、研发投入 |

### 筛选型框架（用于 `screen` 命令）

| 框架 | 适用场景 | 特点 |
|-----|---------|------|
| `quality_stock_screener` | 优质白马股 | 硬性门槛、连续5年、高标准 |

---

## 📝 注意事项

1. **数据要求**：
   - 股票必须先在数据库中有记录
   - 需要有财务数据才能进行分析和筛选
   - 使用 `update-data` 命令补充市场数据

2. **当前限制**：
   - 目前使用模拟数据源（MockDataSource）
   - 如需真实数据，需安装并配置 AkShare

3. **性能考虑**：
   - 批量操作时会依次处理每只股票
   - 大量股票可能需要较长时间

---

## 🔧 高级用法

### 创建别名（Linux/Mac）

在 `~/.bashrc` 或 `~/.zshrc` 中添加：

```bash
alias sa='python /path/to/stock_analyzer.py'
```

然后就可以使用：

```bash
sa screen 600519
sa analyze 600519
sa info 600519
```

### 结合Shell命令

```bash
# 从文件读取股票代码批量筛选
cat watchlist.txt | xargs python stock_analyzer.py screen

# 筛选结果保存到文件
python stock_analyzer.py screen 600519 000858 > report.txt
```

---

## 🆘 常见问题

**Q: 为什么显示"数据库中未找到股票"？**

A: 使用 `info` 或 `update-data` 命令先获取股票信息并保存到数据库。

**Q: 筛选结果为什么通过率很低？**

A: 优质白马股筛选框架的标准很严格（连续5年ROE>15%、毛利率>30%等），大部分股票难以全部满足。

**Q: 如何获取真实的市场数据？**

A: 安装 AkShare (`pip install akshare`)，然后修改数据源配置使用 `AkShareSource`。

**Q: 分析结果分数为什么偏低？**

A: 检查数据库中的财务数据是否完整，缺失的指标会导致得分降低。

---

## 📧 反馈与建议

如有问题或建议，请提交 Issue 或 PR。
