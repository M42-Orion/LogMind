#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@文件    :db.py
@说明    :
@时间    :2025/05/23 09:57:03
@作者    :ljw
@版本    :1.0
'''

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from config import setting


class MongoDBConnection:
    '''MongoDB连接池单例类'''
    _instance = None
    _client = None

    def __new__(cls, uri: str = "mongodb://localhost:27017",
                max_pool_size: int = 100,
                min_pool_size: int = 10,
                connect_timeout: int = 30000,
                **kwargs):
        """
        初始化MongoDB连接池

        Args:
            uri: MongoDB连接URI
            max_pool_size: 最大连接数
            min_pool_size: 最小连接数
            connect_timeout: 连接超时时间(毫秒)
            **kwargs: 其他pymongo连接参数
        """
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._client = AsyncIOMotorClient(
                uri,
                maxPoolSize=max_pool_size,
                minPoolSize=min_pool_size,
                connectTimeoutMS=connect_timeout,
                **kwargs
            )
            # 测试连接
            try:
                # 对于MongoDB 3.0+版本，使用server_info()检查连接
                asyncio.get_event_loop().run_until_complete(cls._client.server_info())
                print("成功连接到MongoDB服务器")
            except ConnectionFailure as e:
                print(f"连接失败: {e}")
        return cls._instance

    @classmethod
    def get_client(cls) -> AsyncIOMotorClient:
        """获取MongoDB客户端实例"""
        return cls._client # type: ignore

    @classmethod
    def close(cls) -> None:
        """关闭MongoDB连接"""
        if cls._client:
            cls._client.close()
            print("MongoDB连接已关闭")

db = MongoDBConnection(
        uri=setting.MONGOCONFIG["uri"],
        max_pool_size=setting.MONGOCONFIG["max_pool_size"],
        min_pool_size=setting.MONGOCONFIG["min_pool_size"],
        connectTimeoutMS=setting.MONGOCONFIG["connect_timeout"]
    ).get_client().mydatabase


# ----------------------------
# 使用示例
# ----------------------------
async def example_usage():
    """示例使用MongoDB连接池"""
    # 获取连接池实例
    # 插入文档
    result = await db.users.insert_one({"name": "John", "age": 30})
    print(f"插入文档ID: {result.inserted_id}")

    # 查询文档
    user = await db.users.find_one({"name": "John"})
    print(f"查询结果: {user}")
    if user:
        # 批量操作示例
        async with await db.client.start_session() as session:
            async with session.start_transaction():
                await db.orders.insert_one({"user_id": user["_id"], "items": ["apple", "banana"]}, session=session)
                await db.users.update_one({"_id": user["_id"]}, {"$inc": {"points": 10}}, session=session)

# 运行示例
if __name__ == "__main__":
    asyncio.run(example_usage())
    # 应用退出时关闭连接
    MongoDBConnection.close()
