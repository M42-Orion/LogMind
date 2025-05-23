#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@文件    :logparser.py
@说明    :
@时间    :2025/05/23 10:52:54
@作者    :ljw
@版本    :1.0
'''

import re
from typing import Dict, Any, Optional
from loguru import logger


class BaseLogSubParser:
    """日志子解析器基类，增强自动检测能力"""
    def can_parse(self, line: str) -> bool:
        """
        判断是否可以解析该行日志
        Args:
            line: 日志行内容
        Returns:
            bool: True表示可以解析，False表示不能解析
        """
        raise NotImplementedError("子类必须实现can_parse方法")

    def parse_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        解析单行日志
        Args:
            line: 日志行内容
        Returns:
            Dict[str, Any]: 解析出的字段字典，解析失败时返回None
        """
        raise NotImplementedError("子类必须实现parse_line方法")


class NginxLogSubParser(BaseLogSubParser):
    """增强型Nginx日志子解析器"""
    # 用于格式检测的正则表达式
    DETECTION_PATTERN = re.compile(
        r'^\S+ \S+ \S+ \[\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2} \+\d{4}\] '
        r'"[A-Z]+ \S+ \S+" \d+ \d+ ".*" ".*"'
    )
    # 默认的Nginx日志格式正则表达式
    PARSING_PATTERN = (
        r'(?P<remote_addr>\S+) \S+ \S+ \[(?P<time_local>[^]]+)\] '
        r'"(?P<request_method>\S+) (?P<request_uri>\S+) \S+" '
        r'(?P<status>\d+) (?P<body_bytes_sent>\d+) '
        r'"(?P<http_referer>[^"]*)" "(?P<http_user_agent>[^"]*)"'
    )
    def __init__(self, custom_pattern: str|None = None):
        """
        初始化Nginx日志解析器
        Args:
            custom_pattern: 自定义解析正则表达式
        """
        self.detection_pattern = self.DETECTION_PATTERN
        self.parsing_pattern = re.compile(
            custom_pattern or self.PARSING_PATTERN)

    def can_parse(self, line: str) -> bool:
        """判断是否为Nginx日志行"""
        return bool(self.detection_pattern.match(line))

    def parse_line(self, line: str) -> Optional[Dict[str, Any]]:
        """解析Nginx日志行"""
        match = self.parsing_pattern.search(line)
        if not match:
            logger.debug(f"无法解析Nginx日志行: {line}")
            return None
        # 提取并转换字段
        data = match.groupdict()
        # 类型转换逻辑保持不变...
        return data


class ApacheLogSubParser(BaseLogSubParser):
    """增强型Apache日志子解析器"""
    # 用于格式检测的正则表达式
    DETECTION_PATTERN = re.compile(
        r'^\S+ \S+ \S+ \[\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2} [+-]\d{4}\] '
        r'"[A-Z]+ \S+ HTTP/\d\.\d" \d+ \d+'
    )
    # Combined日志格式正则表达式
    PARSING_PATTERN = (
        r'(?P<remote_addr>\S+) \S+ \S+ \[(?P<time_local>[^]]+)\] '
        r'"(?P<request_method>\S+) (?P<request_uri>\S+) \S+" '
        r'(?P<status>\d+) (?P<body_bytes_sent>\d+) '
        r'"(?P<http_referer>[^"]*)" "(?P<http_user_agent>[^"]*)"'
    )

    def __init__(self):
        self.detection_pattern = self.DETECTION_PATTERN
        self.parsing_pattern = re.compile(self.PARSING_PATTERN)

    def can_parse(self, line: str) -> bool:
        """判断是否为Apache日志行"""
        return bool(self.detection_pattern.match(line))

    def parse_line(self, line: str) -> Optional[Dict[str, Any]]:
        """解析Apache日志行"""
        match = self.parsing_pattern.search(line)
        if not match:
            logger.debug(f"无法解析Apache日志行: {line}")
            return None
        # 提取并转换字段
        data = match.groupdict()
        # 类型转换逻辑保持不变...
        return data
