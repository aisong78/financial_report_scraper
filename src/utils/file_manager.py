"""
财报文件管理器

管理财报文件的生命周期，自动清理旧文件
"""

import os
import gzip
import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from ..database.db import session_scope
from ..database.models import FinancialReport
from ..utils.logger import get_logger


class FileManager:
    """财报文件管理器"""

    def __init__(self, keep_recent: int = 2):
        """
        初始化

        Args:
            keep_recent: 保留最近N期文件（默认2期）
        """
        self.keep_recent = keep_recent
        self.logger = get_logger()

    def cleanup_old_files(self, stock_id: int) -> int:
        """
        清理旧文件

        Args:
            stock_id: 股票ID

        Returns:
            删除的文件数量
        """
        deleted_count = 0

        try:
            with session_scope() as session:
                # 1. 查询该股票所有已解析的财报（按日期降序）
                reports = session.query(FinancialReport).filter(
                    FinancialReport.stock_id == stock_id,
                    FinancialReport.is_parsed == True,  # 只处理已解析的
                    FinancialReport.file_path != None  # 有文件路径的
                ).order_by(
                    FinancialReport.report_date.desc()
                ).all()

                if len(reports) <= self.keep_recent:
                    self.logger.info(f"股票 {stock_id} 财报数量 <= {self.keep_recent}，无需清理")
                    return 0

                # 2. 保留最近N期，删除其余
                to_delete = reports[self.keep_recent:]

                for report in to_delete:
                    if report.file_path and os.path.exists(report.file_path):
                        try:
                            os.remove(report.file_path)
                            self.logger.info(f"删除旧文件: {report.file_path}")
                            deleted_count += 1

                            # 更新数据库：清空 file_path，但保留记录和指标
                            report.file_path = None

                        except Exception as e:
                            self.logger.error(f"删除文件失败 {report.file_path}: {e}")

                session.commit()

        except Exception as e:
            self.logger.exception(f"清理旧文件失败: {e}")

        self.logger.info(f"股票 {stock_id} 清理完成，删除 {deleted_count} 个文件")
        return deleted_count

    def cleanup_all_stocks(self) -> int:
        """
        清理所有股票的旧文件

        Returns:
            总删除的文件数量
        """
        total_deleted = 0

        try:
            with session_scope() as session:
                # 获取所有有财报的股票ID
                stock_ids = session.query(FinancialReport.stock_id).distinct().all()
                stock_ids = [sid[0] for sid in stock_ids]

            self.logger.info(f"开始清理 {len(stock_ids)} 个股票的旧文件...")

            for stock_id in stock_ids:
                deleted = self.cleanup_old_files(stock_id)
                total_deleted += deleted

        except Exception as e:
            self.logger.exception(f"批量清理失败: {e}")

        self.logger.info(f"批量清理完成，共删除 {total_deleted} 个文件")
        return total_deleted

    def archive_file(self, file_path: str) -> Optional[str]:
        """
        归档文件（压缩）

        Args:
            file_path: 文件路径

        Returns:
            压缩后的文件路径，失败返回None
        """
        if not os.path.exists(file_path):
            self.logger.warning(f"文件不存在: {file_path}")
            return None

        try:
            archive_path = file_path + ".gz"

            # 压缩文件
            with open(file_path, 'rb') as f_in:
                with gzip.open(archive_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # 删除原文件
            os.remove(file_path)

            self.logger.info(f"文件已归档: {file_path} -> {archive_path}")
            return archive_path

        except Exception as e:
            self.logger.error(f"归档文件失败 {file_path}: {e}")
            return None

    def get_file_size(self, file_path: str) -> int:
        """
        获取文件大小

        Args:
            file_path: 文件路径

        Returns:
            文件大小（字节），失败返回0
        """
        try:
            return os.path.getsize(file_path)
        except Exception:
            return 0

    def get_stock_storage_info(self, stock_id: int) -> dict:
        """
        获取股票的存储信息

        Args:
            stock_id: 股票ID

        Returns:
            存储信息字典
        """
        info = {
            'stock_id': stock_id,
            'report_count': 0,
            'files_with_path': 0,
            'total_size': 0,
            'files': []
        }

        try:
            with session_scope() as session:
                reports = session.query(FinancialReport).filter(
                    FinancialReport.stock_id == stock_id
                ).all()

                info['report_count'] = len(reports)

                for report in reports:
                    if report.file_path and os.path.exists(report.file_path):
                        info['files_with_path'] += 1
                        size = self.get_file_size(report.file_path)
                        info['total_size'] += size

                        info['files'].append({
                            'report_id': report.id,
                            'report_date': report.report_date,
                            'file_path': report.file_path,
                            'file_size': size,
                            'file_size_mb': round(size / 1024 / 1024, 2)
                        })

        except Exception as e:
            self.logger.error(f"获取存储信息失败: {e}")

        info['total_size_mb'] = round(info['total_size'] / 1024 / 1024, 2)
        return info

    def get_all_storage_info(self) -> dict:
        """
        获取所有股票的存储统计

        Returns:
            统计信息字典
        """
        summary = {
            'total_stocks': 0,
            'total_reports': 0,
            'total_files': 0,
            'total_size': 0,
            'stocks': []
        }

        try:
            with session_scope() as session:
                stock_ids = session.query(FinancialReport.stock_id).distinct().all()
                stock_ids = [sid[0] for sid in stock_ids]

            summary['total_stocks'] = len(stock_ids)

            for stock_id in stock_ids:
                stock_info = self.get_stock_storage_info(stock_id)
                summary['total_reports'] += stock_info['report_count']
                summary['total_files'] += stock_info['files_with_path']
                summary['total_size'] += stock_info['total_size']

                summary['stocks'].append({
                    'stock_id': stock_id,
                    'files': stock_info['files_with_path'],
                    'size_mb': stock_info['total_size_mb']
                })

        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")

        summary['total_size_mb'] = round(summary['total_size'] / 1024 / 1024, 2)
        summary['total_size_gb'] = round(summary['total_size'] / 1024 / 1024 / 1024, 2)

        return summary


# 便捷函数

def cleanup_old_files(stock_id: int, keep_recent: int = 2) -> int:
    """
    清理旧文件（便捷函数）

    Args:
        stock_id: 股票ID
        keep_recent: 保留最近N期

    Returns:
        删除的文件数量
    """
    manager = FileManager(keep_recent=keep_recent)
    return manager.cleanup_old_files(stock_id)


def get_storage_stats() -> dict:
    """
    获取存储统计（便捷函数）

    Returns:
        统计信息
    """
    manager = FileManager()
    return manager.get_all_storage_info()


if __name__ == '__main__':
    # 测试
    print("FileManager模块")
    print("\n获取存储统计...")
    stats = get_storage_stats()
    print(f"总股票数: {stats['total_stocks']}")
    print(f"总财报数: {stats['total_reports']}")
    print(f"总文件数: {stats['total_files']}")
    print(f"总大小: {stats['total_size_mb']} MB ({stats['total_size_gb']} GB)")
