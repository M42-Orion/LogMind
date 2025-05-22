#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@文件    :router.py
@说明    :
@时间    :2025/05/22 11:33:27
@作者    :ljw
@版本    :1.0
'''

from fastapi import APIRouter

parse_router = APIRouter(prefix="/api/score")

@parse_router.get("/score/get_template")
async def get_score():
    """获取excel成绩单模板"""
    return {"score": "score"}
