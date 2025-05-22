#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@文件    :router.py
@说明    :
@时间    :2025/05/22 11:32:01
@作者    :ljw
@版本    :1.0
'''

from fastapi import APIRouter

from apps.parse.router import parse_router


router = APIRouter()

router.include_router(parse_router)
