#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@文件    :middleware.py
@说明    :
@时间    :2025/05/22 15:29:09
@作者    :ljw
@版本    :1.0
'''

import os
from fastapi import FastAPI
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_redoc_html,
    get_swagger_ui_oauth2_redirect_html,
)

def register_static(app: FastAPI, setting):
    ''' 注册静态文件 '''
    @app.get('/docs', include_in_schema=False)
    async def custom_swagger_ui_html():
        ''' Swagger UI '''
        # 这里的openapi_url是FastAPI自动生成的OpenAPI文档的URL，通常是"/openapi.json"
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,  # type:ignore
            title=app.title + " - Swagger UI",
            oauth2_redirect_url=os.path.join(
                setting.STATIC_DIR, "swaggerstatic", "oauth2-redirect.html"),
            swagger_js_url="/swaggerstatic/swagger-ui-bundle.js",
            swagger_css_url="/swaggerstatic/swagger-ui.css",
        )

    @app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False) # type:ignore
    def swagger_ui_redirect(parameter_list):
        return get_swagger_ui_oauth2_redirect_html()

    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url=app.openapi_url,  # type:ignore
            title=app.title + " - ReDoc",
            redoc_js_url="/swaggerstatic/redoc.standalone.js"
        )