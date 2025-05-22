#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@文件    :router.py
@说明    :
@时间    :2025/05/22 14:05:40
@作者    :ljw
@版本    :1.0
'''

import os

from fastapi import APIRouter, File, Request, UploadFile

from config import setting


parse_router = APIRouter(prefix="/api/files")


@parse_router.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    parse_immediately: bool = False,
    parser_type: str = "自动匹配",
):
    """
    接收上传的文件并保存到本地
    :param file: 上传的文件对象
    :param parse_immediately: 是否立即解析，默认为 False
    :param parser_type: 解析器类型，默认为自动匹配
    :param user_id: 用户 ID，从 cookie 中获取
    """
    # 从请求的 state 中获取用户 ID
    user_id = request.state.user_id
    try:
        # 定义文件保存路径，这里简单保存到当前目录下的 uploads 文件夹
        file_path = os.path.join(
            setting.TEMP_DIR, file.filename)  # type: ignore
        # 以二进制写入模式打开文件并写入上传文件的内容
        with open(file_path, "wb") as buffer:
            contents = await file.read()
            buffer.write(contents)
        return {
            "message": f"文件 {file.filename} 上传成功",
            "file_path": file_path,
            "parse_immediately": parse_immediately,
            "parser_type": parser_type,
            "user_id": user_id
        }
    except Exception as e:
        return {"message": f"文件上传失败: {str(e)}"}
    finally:
        await file.close()


@parse_router.post("/upload")
async def get_score():
    """获取excel成绩单模板"""
    return {"score": "score"}
