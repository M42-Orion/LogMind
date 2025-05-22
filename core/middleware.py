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
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.openapi.docs import (get_redoc_html, get_swagger_ui_html,
                                  get_swagger_ui_oauth2_redirect_html)


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


async def add_user_id_middleware(request: Request, call_next):
    ''' 添加用户 ID 中间件 '''
    # 从 cookie 中获取用户 ID
    user_id = request.cookies.get("user_id")
    if not user_id:
        # 若没有用户 ID，生成一个新的 UUID 作为用户 ID
        user_id = str(uuid.uuid4())
    # 将用户 ID 添加到请求的 state 中，方便后续路由使用
    request.state.user_id = user_id
    response: Response = await call_next(request)
    # 若 cookie 中没有用户 ID，将新生成的用户 ID 添加到 cookie 中
    if not request.cookies.get("user_id"):
        response.set_cookie(key="user_id", value=user_id)
    return response
