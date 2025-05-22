#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@文件    :app.py
@说明    :
@时间    :2025/05/22 11:18:23
@作者    :ljw
@版本    :1.0
'''


import uvicorn
from fastapi import FastAPI
from core.router import router
from config import setting

app = FastAPI(
    **setting.PROJECE_CONFIG
)
app.include_router(router)

if __name__ == "__main__":

    uvicorn.run(app, **setting.STARTUP_CONFIG)
