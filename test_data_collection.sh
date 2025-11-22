#!/bin/bash

echo "=================================="
echo "财报数据采集系统 - 完整测试"
echo "=================================="
echo ""

echo "【测试1】检查数据完整性（不采集）"
echo "----------------------------------"
python collect_data.py 600519 --check-only
echo ""

echo "【测试2】采集单只股票数据"
echo "----------------------------------"
echo "采集贵州茅台(600519) 5年年报数据..."
python collect_data.py 600519 --reports annual --no-interactive
echo ""

echo "【测试3】增量更新模式"
echo "----------------------------------"
python collect_data.py 600519 --incremental --no-interactive
echo ""

echo "【测试4】批量采集测试"
echo "----------------------------------"
echo "采集3只股票: 600519, 000858, 601318"
python collect_data.py 600519 000858 601318 --reports annual --no-interactive
echo ""

echo "【测试5】分析已采集的数据"
echo "----------------------------------"
python stock_analyzer.py analyze 600519 --skip-fetch
echo ""

echo "【测试6】批量分析和对比"
echo "----------------------------------"
python stock_analyzer.py analyze 600519 000858 601318 --skip-fetch
echo ""

echo "=================================="
echo "测试完成！"
echo "=================================="
