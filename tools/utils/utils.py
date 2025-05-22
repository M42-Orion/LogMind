#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@文件    :utils.py
@说明    :
@时间    :2025/05/22 14:14:10
@作者    :ljw
@版本    :1.0
'''

import os
import shutil
import hashlib
import tempfile
import zipfile
from pathlib import Path
from typing import Optional



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
