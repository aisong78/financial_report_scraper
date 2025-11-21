"""
Financial Report Parsers

Provides parsing functionality for PDF and HTML financial reports
"""

from .base_parser import BaseParser

# Lazy imports for parsers (to avoid dependency issues)
PDFParser = None
HTMLParser = None

try:
    from .pdf_parser import PDFParser
except:  # Catch all exceptions including system-level errors
    pass

try:
    from .html_parser import HTMLParser
except:  # Catch all exceptions including system-level errors
    pass

__all__ = [
    'BaseParser',
    'PDFParser',
    'HTMLParser',
]
