#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@文件    :db.py
@说明    :
@时间    :2025/05/29 11:52:09
@作者    :ljw
@版本    :1.0
'''

import os
from urllib.parse import quote_plus

from sqlalchemy import create_engine, func, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from config import setting

from .models import Base

DB_CONFIG = setting.MYSQLDB_CONFIG


def check_database_exists(engine, db_name):
    """检查数据库是否存在"""
    try:
        with engine.connect() as conn:
            # 执行一个简单的查询，检查数据库是否存在
            result = conn.execute(text(
                f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{db_name}'"))
            return result.fetchone() is not None
    except OperationalError as e:
        setting.log.warning(f"检查数据库存在性时出错: {e}")
        return False


def create_database(engine, db_name):
    """创建数据库"""
    try:
        # 连接到没有指定数据库的引擎
        with engine.connect() as conn:
            # 设置自动提交模式
            conn.execute(text("SET autocommit = 1"))
            # 创建数据库（如果不存在）
            conn.execute(text(
                f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            setting.log.info(f"成功创建数据库: {db_name}")
            return True
    except OperationalError as e:
        setting.log.error(f"创建数据库失败: {e}")
        return False


def check_tables_exist(engine):
    """检查表是否存在"""
    try:
        with engine.connect() as conn:
            # 获取元数据
            from sqlalchemy import MetaData
            metadata = MetaData()
            metadata.reflect(bind=conn)
            # 检查所有需要的表是否存在
            required_tables = Base.metadata.tables.keys()
            existing_tables = set(metadata.tables.keys())
            return all(table in existing_tables for table in required_tables)
    except Exception as e:
        setting.log.warning(f"检查表结构时出错: {e}")
        return False


def init_database():
    """初始化数据库：创建数据库(如果不存在)并创建表结构"""
    # 对密码进行URL编码，处理特殊字符
    encoded_password = quote_plus(DB_CONFIG['password'])
    # 首先创建一个不指定数据库的引擎，用于操作数据库
    base_engine = create_engine(
        f"mysql+pymysql://{DB_CONFIG['user']}:{encoded_password}@{DB_CONFIG['host']}:{DB_CONFIG['port']}",
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_recycle=3600
    )
    # 检查数据库是否存在
    db_exists = check_database_exists(base_engine, DB_CONFIG['database'])
    if not db_exists:
        # 创建数据库
        if not create_database(base_engine, DB_CONFIG['database']):
            raise RuntimeError("无法创建数据库")
    # 现在创建指定数据库的引擎
    db_engine = create_engine(
        f"mysql+pymysql://{DB_CONFIG['user']}:{encoded_password}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}",
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
        echo=os.getenv('DB_ECHO', 'False').lower() == 'true'
    )
    # 检查表结构是否完整
    tables_exist = check_tables_exist(db_engine)
    if not tables_exist:
        # 创建表结构
        Base.metadata.create_all(bind=db_engine)
        setting.log.info("成功创建表结构")
    else:
        setting.log.info("表结构已存在，跳过创建")
    return db_engine


# 初始化数据库引擎
engine = init_database()

# 创建Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class DatabaseManager:
    def __init__(self):
        self.session = SessionLocal()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """关闭会话"""
        self.session.close()

    def query(self, model, filters=None):
        """条件查询"""
        query = self.session.query(model)
        if filters:
            query = query.filter(*filters)
        return query.all()

    def get_one(self, model, filters=None):
        """获取单条记录"""
        query = self.session.query(model)
        if filters:
            query = query.filter(*filters)
        return query.first()

    def add(self, model, data: dict | list[dict], exists_action='ignore'):
        """新增记录
        :param model: 数据库模型类
        :param data: 要插入的数据，支持字典或字典列表形式
        :param exists_action: 存在时的操作，'ignore' 忽略，'replace' 覆盖
        """
        if isinstance(data, dict):
            data = [data]  # 将单条数据转换为列表形式，统一处理
        instances = []
        for item in data:
            if exists_action == 'ignore':
                existing = self.get_one(
                    model, [getattr(model, k) == v for k, v in item.items()])
                if existing:
                    instances.append(existing)
                    continue
            elif exists_action == 'replace':
                self.delete(model, [getattr(model, k) ==
                            v for k, v in item.items()])
            instance = model(**item)
            self.session.add(instance)
            instances.append(instance)
        self.session.commit()
        if len(instances) == 1:
            return instances[0]  # 如果是单条数据，返回单个实例
        return instances

    def delete(self, model, filters):
        """条件删除"""
        self.session.query(model).filter(*filters).delete()
        self.session.commit()

    def update(self, model, filters, update_data):
        """条件更改"""
        self.session.query(model).filter(*filters).update(update_data)
        self.session.commit()

    def count(self, model, filters=None):
        """获取总数"""
        query = self.session.query(func.count(model.id))
        if filters:
            query = query.filter(*filters)
        return query.scalar()

    def paginate(self, model, page=1, per_page=10, filters=None):
        """分页查询"""
        offset = (page - 1) * per_page
        query = self.session.query(model)
        if filters:
            query = query.filter(*filters)
        return query.offset(offset).limit(per_page).all()


# # 使用上下文管理器操作数据库
# with DatabaseManager() as db:
#     # 新增记录
#     new_file = db.create(FileMetadata, {
#         "file_name": "example.txt",
#         "file_size": 1024,
#         "file_md5": "abc123",
#         "file_type": "text/plain",
#         "storage_path": "/path/to/file",
#         "user_id": 1
#     }, exists_action='ignore')

#     # 条件查询
#     files = db.query(FileMetadata, [FileMetadata.user_id == 1])

#     # 条件删除
#     db.delete(FileMetadata, [FileMetadata.file_name == "example.txt"])

#     # 条件更改
#     db.update(FileMetadata, [FileMetadata.user_id == 1], {"file_type": "application/pdf"})

#     # 获取总数
#     total = db.count(FileMetadata, [FileMetadata.user_id == 1])

#     # 分页查询
#     page_files = db.paginate(FileMetadata, page=1, per_page=10, filters=[FileMetadata.user_id == 1])