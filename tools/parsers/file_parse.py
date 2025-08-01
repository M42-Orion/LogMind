#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@文件    :file_parse.py
@说明    :
@时间    :2025/05/22 17:19:19
@作者    :ljw
@版本    :1.0
'''


import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Generator, List, Optional
import pandas as pd

from .logparser import BaseLogSubParser


class FileParserStrategy(ABC):
    '''文件解析器策略接口'''
    @abstractmethod
    def parse(self, file_path: str) -> Any:
        """解析文件内容的抽象方法
        Args:
            file_path: 文件路径
        Returns:
            解析后的数据结构
        """
        pass

    @abstractmethod
    def supports(self, file_path: str) -> bool:
        """判断是否支持解析该文件
        Args:
            file_path: 文件路径
        Returns:
            True表示支持，False表示不支持
        """
        pass


class CSVParser(FileParserStrategy):
    '''CSV文件解析器，使用pandas进行分块读取以减少内存占用'''

    def parse(self, file_path: str) -> Generator[Dict[str, Any], None, None]:
        """解析CSV文件，返回生成器对象以减少内存占用
        Args:
            file_path: CSV文件路径
        Returns:
            生成器对象，每次迭代返回一行数据
        Raises:
            FileNotFoundError: 如果文件不存在
            pd.errors.ParserError: 如果解析文件时出错
        """
        try:
            # 使用 pandas 分块读取 CSV 文件
            for chunk in pd.read_csv(file_path, encoding='utf-8', chunksize=1000):
                for _, row in chunk.iterrows():
                    # 将 Series 转换为字典并返回
                    yield row.to_dict()
        except Exception as e:
            print(f"CSV解析错误: {e}")
            raise

    def supports(self, file_path: str) -> bool:
        return file_path.lower().endswith('.csv')


class JSONLParser(FileParserStrategy):
    '''JSONL文件解析器，逐行解析以减少内存占用'''

    def parse(self, file_path: str) -> Generator[Dict[str, Any], None, None]:
        """解析JSONL文件（每行一个JSON对象）
        Args:
            file_path: JSONL文件路径
        Yields:
            Dict[str, Any]: 每次迭代返回一个JSON对象
        Raises:
            json.JSONDecodeError: 如果JSON格式错误
            FileNotFoundError: 如果文件不存在
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    # 逐行解析并以生成器形式返回JSON对象
                    yield json.loads(line.strip())
        except json.JSONDecodeError as e:
            print(f"JSONL解析错误: {e}")
            raise
        except Exception as e:
            print(f"读取文件错误: {e}")
            raise

    def supports(self, file_path: str) -> bool:
        return file_path.lower().endswith(('.jsonl', '.ndjson'))


class LogParser(FileParserStrategy):
    """智能日志解析器，支持自动识别日志格式"""
    def __init__(self, sub_parsers: Optional[List["BaseLogSubParser"]] = None):
        """
        初始化智能日志解析器
        Args:
            sub_parsers: 可用的子解析器列表
        """
        self.sub_parsers = sub_parsers or []
        self._detected_parser = None

    def register_sub_parser(self, sub_parser: "BaseLogSubParser") -> None:
        """注册子解析器"""
        self.sub_parsers.append(sub_parser)

    def detect_format(self, file_path: str, sample_size: int = 10) -> Optional["BaseLogSubParser"]:
        """
        自动检测日志格式
        Args:
            file_path: 日志文件路径
            sample_size: 用于检测的行数
        Returns:
            匹配的子解析器，如果未找到匹配则返回None
        """
        if not self.sub_parsers:
            print("没有注册的子解析器，无法进行格式检测")
            return None
        # 读取样本行
        sample_lines = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for i, line in enumerate(file):
                    if i >= sample_size:
                        break
                    stripped_line = line.strip()
                    if stripped_line:
                        sample_lines.append(stripped_line)
        except Exception as e:
            print(f"读取样本行失败: {e}")
            return None
        # 尝试匹配每种解析器
        for parser in self.sub_parsers:
            match_count = 0
            for line in sample_lines:
                if parser.can_parse(line):
                    match_count += 1
            # 如果大部分样本行都能被解析，则认为匹配成功
            if match_count >= len(sample_lines) * 0.7:
                print(f"自动检测到日志格式: {parser.__class__.__name__}")
                return parser
        print("无法自动识别日志格式")
        return None

    def parse(self, file_path: str) -> Generator[Dict[str, Any], None, None]:
        """
        解析日志文件，自动选择合适的子解析器
        Args:
            file_path: 日志文件路径
        Yields:
            Dict[str, Any]: 解析出的日志字段
        Raises:
            ValueError: 如果无法识别日志格式
            FileNotFoundError: 如果文件不存在
        """
        # 自动检测日志格式
        parser = self.detect_format(file_path)
        if not parser:
            raise ValueError("无法识别日志格式，请手动指定子解析器")
        self._detected_parser = parser
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    stripped_line = line.strip()
                    if stripped_line:  # 跳过空行
                        parsed_data = parser.parse_line(stripped_line)
                        if parsed_data:
                            # 添加解析器类型元数据
                            parsed_data['_parser'] = parser.__class__.__name__
                            yield parsed_data
        except Exception as e:
            print(f"日志文件解析错误: {e}")
            raise

    def supports(self, file_path: str) -> bool:
        return file_path.lower().endswith('.log')


class TXTParser(FileParserStrategy):
    '''TXT文件解析器，逐行解析以减少内存占用'''

    def parse(self, file_path: str) -> Generator[str, None, None]:
        """解析TXT文件，逐行返回文本内容
        Args:
            file_path: TXT文件路径
        Yields:
            str: 每次迭代返回一行文本内容
        Raises:
            FileNotFoundError: 如果文件不存在
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    # 逐行返回文本内容
                    yield line.strip()
        except Exception as e:
            print(f"TXT文件解析错误: {e}")
            raise

    def supports(self, file_path: str) -> bool:
        return file_path.lower().endswith('.txt')


class FileParser:
    '''文件解析器上下文类，负责选择合适的解析策略并调用'''

    def __init__(self) -> None:
        self._strategies: List[FileParserStrategy] = [
            CSVParser(),
            JSONLParser(),
            LogParser(),
            TXTParser()
        ]

    def register_strategy(self, strategy: FileParserStrategy) -> None:
        """注册新的解析策略
        Args:
            strategy: 实现了FileParserStrategy接口的解析器
        """
        self._strategies.append(strategy)

    def parse(self, file_path: str) -> Any:
        """解析文件
        Args:
            file_path: 文件路径
        Returns:
            解析后的数据结构
        Raises:
            ValueError: 如果找不到支持该文件类型的解析器
        """
        # 查找支持该文件类型的策略
        strategy = self._find_strategy(file_path)
        if not strategy:
            raise ValueError(f"不支持的文件类型: {file_path}")

        # 使用找到的策略解析文件
        return strategy.parse(file_path)

    def _find_strategy(self, file_path: str) -> Optional[FileParserStrategy]:
        """查找支持该文件类型的解析策略
        Args:
            file_path: 文件路径
        Returns:
            支持该文件类型的解析策略，如果找不到则返回None
        """
        for strategy in self._strategies:
            if strategy.supports(file_path):
                return strategy
        return None


class ParserFactory:
    '''工厂类，用于创建文件解析器实例'''
    @staticmethod
    def create_parser() -> FileParser:
        """创建默认的文件解析器

        Returns:
            配置好的文件解析器实例
        """
        parser = FileParser()
        # 可以在这里添加更多默认策略
        return parser


if __name__ == "__main__":
    # 创建文件解析器
    parser_test = ParserFactory.create_parser()

    # 解析JSON文件
    try:
        json_data = parser_test.parse("example.json")
        print("JSON解析结果:")
        print(json.dumps(json_data, indent=2))
    except Exception as e:
        print(f"解析JSON时出错: {e}")
