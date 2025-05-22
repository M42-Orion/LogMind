#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@文件    :app.py
@说明    :
@时间    :2025/05/22 11:18:23
@作者    :ljw
@版本    :1.0
'''


import os

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import setting
from core.middleware import register_static
from core.router import router
from core.middleware import add_user_id_middleware


app = FastAPI(docs_url=None,
              **setting.PROJECE_CONFIG
              )
app.include_router(router)

app.mount('/swaggerstatic', StaticFiles(directory=os.path.join(
    setting.STATIC_DIR, "swaggerstatic")), name="swaggerstatic")
register_static(app, setting)

app.middleware("http")(add_user_id_middleware)


if __name__ == "__main__":
    uvicorn.run(app, **setting.STARTUP_CONFIG)
