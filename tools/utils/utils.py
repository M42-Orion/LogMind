#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@文件    :utils.py
@说明    :
@时间    :2025/05/22 14:14:10
@作者    :ljw
@版本    :1.0
'''

import asyncio
import hashlib
import json
import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, Optional


def create_directory(path: str,
                     exist_ok: bool = True,
                     delete_if_exists: bool = False) -> None:
    """
    创建目录（支持递归创建）

    Args:
        path (str): 要创建的目录路径
        exist_ok (bool): 如果为 True，目录已存在时不会抛出异常，默认为 True
        delete_if_exists (bool): 如果为 True，目录已存在时会先删除该目录再重建，默认为 False
    """
    if delete_if_exists and os.path.exists(path) and os.path.isdir(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=exist_ok)


def delete_directory(path: str) -> None:
    """删除目录（递归删除所有内容）"""
    if os.path.exists(path) and os.path.isdir(path):
        shutil.rmtree(path)


def delete_file(path: str) -> None:
    """删除文件"""
    if os.path.exists(path) and os.path.isfile(path):
        os.remove(path)


def calculate_file_md5(file_path: str) -> str:
    """计算文件的MD5哈希值"""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


async def calculate_file_hash_async(file_path: str) -> str:
    """异步计算文件哈希"""
    return await asyncio.to_thread(calculate_file_md5, file_path)


def unzip_file(zip_file_path: str, extract_dir: Optional[str] = None) -> str:
    """
    解压ZIP文件到指定目录

    Args:
        zip_file_path: 压缩文件路径
        extract_dir: 解压目标目录，默认为压缩文件同级目录下的同名文件夹

    Returns:
        解压后的目录路径
    """
    if not os.path.isfile(zip_file_path):
        raise FileNotFoundError(f"压缩文件不存在: {zip_file_path}")

    # 如果未指定解压目录，使用压缩文件同名目录
    if extract_dir is None:
        base_name = os.path.basename(zip_file_path)
        extract_dir = os.path.splitext(base_name)[0]
        extract_dir = os.path.join(os.path.dirname(zip_file_path), extract_dir)

    # 创建解压目录
    create_directory(extract_dir)

    # 解压文件
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

    return extract_dir


def get_file_extension(file_name: str) -> str:
    """获取文件扩展名（小写，不带点）"""
    return Path(file_name).suffix.lower().lstrip('.')


def safe_filename(filename: str, replacement: str = '_') -> str:
    """将文件名转换为安全文件名，移除不安全字符"""
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, replacement)
    return filename


def get_temp_file(suffix: str = "") -> str:
    """获取临时文件路径"""
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)  # 关闭文件描述符，由调用者负责打开和关闭文件
    return path


def get_temp_directory() -> str:
    """获取临时目录路径"""
    return tempfile.mkdtemp()


def move_file(src: str, dst: str) -> bool:
    """移动文件到指定目录"""
    try:
        if not os.path.isfile(src):
            raise FileNotFoundError(f"源文件不存在: {src}")
        create_directory(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)
        return True
    except Exception as e:
        return False


def move_directory(src: str, dst: str) -> None:
    """移动目录到指定目录"""
    if not os.path.isdir(src):
        raise FileNotFoundError(f"源目录不存在: {src}")
    create_directory(dst, exist_ok=True)
    shutil.move(src, dst)


def copy_file(src: str, dst: str) -> None:
    """复制文件到指定目录"""
    if not os.path.isfile(src):
        raise FileNotFoundError(f"源文件不存在: {src}")
    create_directory(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


def copy_directory(src: str, dst: str) -> None:
    """复制目录到指定目录"""
    if not os.path.isdir(src):
        raise FileNotFoundError(f"源目录不存在: {src}")
    create_directory(dst, exist_ok=True)
    shutil.copytree(src, dst, dirs_exist_ok=True)

def extract_and_parse_json(output: str) -> Optional[Dict[str, Any]]:
    """
    从大模型输出中提取并解析JSON数据
    
    Args:
        output: 大模型输出的文本，可能包含Markdown格式的JSON包裹
        
    Returns:
        解析后的JSON对象，若提取或解析失败则返回None
    """
    try:
        # 1. 使用正则表达式提取JSON内容
        # 匹配 ```json 或 ``` 包裹的JSON数据
        match = re.search(
            r'```(?:json)?\s*([\s\S]*?)```',
            output
        )
        if not match:
            # 尝试直接解析是否为JSON
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                print("未找到JSON包裹格式，且直接解析失败")
                return None
        # 2. 提取JSON字符串并去除前后空格
        json_str = match.group(1).strip()
        # 3. 解析JSON
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        return None
    except Exception as e:
        print(f"处理过程中发生错误: {e}")
        return None