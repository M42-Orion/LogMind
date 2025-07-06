#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@文件    :deepseek.py
@说明    :
@时间    :2025/06/12 14:15:53
@作者    :ljw
@版本    :1.0
'''


import asyncio
import traceback
from typing import AsyncGenerator, Dict, Generator, List

import httpx
import openai
from openai import AsyncOpenAI, OpenAI


async def stream_openai_response(
    messages: List[Dict[str, str]],
    model: str = "deepseek-chat",
    temperature: float = 0.7,
    max_tokens: int = 8000,
    api_key: str = "sk-749444947b8a4fab8b99528287756aa2",
    base_url: str = "https://api.deepseek.com",
    stream: bool = True,
) -> AsyncGenerator[str, None]:
    """
    异步生成器：调用OpenAI API并流式返回模型响应

    Args:
        messages: 对话历史，格式为[{"role": "user", "content": "你好"}]
        model: 模型名称，默认为DeepSeek
        temperature: 温度参数，控制随机性
        max_tokens: 最大生成token数

    Yields:
        str: 模型生成的文本片段
    """
    try:
        custom_client = httpx.AsyncClient(verify=False)
        openai.http_client = custom_client
        openai.api_key = api_key
        openai.base_url = base_url
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        response = await client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=messages,  # type: ignore
            stream=stream,
        )
        async for chunk in response:
            if content := chunk.choices[0].delta.content or "":  # type: ignore
                yield content
    except Exception as e:
        # 错误处理示例
        print(f"OpenAI API调用错误: {e},{traceback.format_exc()}")
        # 可选择返回错误信息或重新抛出异常
        yield f"[系统错误] {str(e)}"


async def enhanced_stream_response(
    messages: List[Dict[str, str]],
    pre_hook: callable = None,  # type: ignore
    post_hook: callable = None,  # type: ignore
    **kwargs
) -> AsyncGenerator[str, None]:
    """
    增强版异步生成器：在调用OpenAI API前后执行额外操作

    Args:
        messages: 对话历史
        pre_hook: 调用API前执行的函数，接收messages参数
        post_hook: 调用API后执行的函数，接收完整响应参数
        **kwargs: 传递给stream_openai_response的参数

    Yields:
        str: 模型生成的文本片段
    """
    # 执行前置操作
    if pre_hook:
        await pre_hook(messages)
    # 存储完整响应
    full_response = []
    # 调用底层API生成器
    async for chunk in stream_openai_response(messages, **kwargs):
        full_response.append(chunk)
        yield chunk
    # 执行后置操作
    if post_hook:
        await post_hook(full_response)


def openai_response(
    messages: List[Dict[str, str]],
    model: str = "deepseek-chat",
    temperature: float = 0.7,
    max_tokens: int = 8000,
    api_key: str = "sk-749444947b8a4fab8b99528287756aa2",
    base_url: str = "https://api.deepseek.com",
    stream: bool = True,
) -> Generator[str, None, None]:
    """
    生成器：调用OpenAI API并流式返回模型响应

    Args:
        messages: 对话历史，格式为[{"role": "user", "content": "你好"}]
        model: 模型名称，默认为DeepSeek
        temperature: 温度参数，控制随机性
        max_tokens: 最大生成token数

    Yields:
        str: 模型生成的文本片段
    """
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=messages, # type: ignore
            stream=stream,
        ) # type: ignore
        
        if stream:
            for chunk in response:
                if content := chunk.choices[0].delta.content or "":
                    yield content
        else:
            # 非流式响应处理
            yield response.choices[0].message.content
    except Exception as e:
        # 错误处理示例
        print(f"OpenAI API调用错误: {e},{traceback.format_exc()}")
        # 可选择返回错误信息或重新抛出异常
        yield f"[系统错误] {str(e)}"

def enhanced_response(
    messages: List[Dict[str, str]],
    pre_hook: callable = None, # type: ignore
    post_hook: callable = None, # type: ignore
    **kwargs
) -> Generator[str, None, None]:
    """
    增强版生成器：在调用OpenAI API前后执行额外操作

    Args:
        messages: 对话历史
        pre_hook: 调用API前执行的函数，接收messages参数
        post_hook: 调用API后执行的函数，接收完整响应参数
        **kwargs: 传递给stream_openai_response的参数

    Yields:
        str: 模型生成的文本片段
    """
    # 执行前置操作
    if pre_hook:
        pre_hook(messages)
    
    # 存储完整响应
    full_response = []
    
    # 调用底层API生成器
    for chunk in openai_response(messages, **kwargs):
        full_response.append(chunk)
        yield chunk
    
    # 执行后置操作
    if post_hook:
        post_hook(full_response)


# 使用示例
if __name__ == "__main__":
    async def main():
        # 示例对话历史
        messages = [
            {"role": "user", "content": "你好，请介绍一下Python异步编程"}
        ]
        # 简单调用
        # async for chunk in stream_openai_response(messages):
        #     print(chunk, end="", flush=True)
        print("\n\n---\n")
        # 带钩子的增强调用

        async def log_messages(messages):
            print(f"发送消息到OpenAI: {messages}")

        async def save_response(response):
            with open("response.txt", "w", encoding="utf-8") as f:
                f.write("".join(response))

        async for chunk in enhanced_stream_response(
            messages,
            pre_hook=log_messages,
            post_hook=save_response,
            model="deepseek-chat",
            api_key="sk-749444947b8a4fab8b99528287756aa2",
            base_url="https://api.deepseek.com",
            stream=True,
        ):
            print(chunk, end="", flush=True)

    asyncio.run(main())
