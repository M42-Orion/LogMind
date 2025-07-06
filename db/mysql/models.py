#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@文件    :models.py
@说明    :
@时间    :2025/05/29 11:16:14
@作者    :ljw
@版本    :1.0
'''

import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapped_column

Base = declarative_base()


class FileMetadata(Base):
    __tablename__ = 'file_metadata'

    id = mapped_column(Integer,
                       primary_key=True,
                       autoincrement=True,
                       comment="文件元数据ID")
    file_name = mapped_column(String(255),
                              nullable=False,
                              comment="文件名")
    file_size = mapped_column(Integer,
                              nullable=False,
                              comment="文件大小")
    file_hash = mapped_column(String(32),
                              nullable=False,
                              comment="文件哈希值")
    file_type = mapped_column(String(100),
                              nullable=False,
                              comment="文件类型")  # 如：image/jpeg, application/pdf等
    file_label_list = mapped_column(String(100),
                                   default='[]',
                                   nullable=False,
                                   comment="文件标签列表")  # 如：[label1, label2, label3]
    file_description = mapped_column(String(255),
                                     default=None,
                                     nullable=True,
                                     comment="文件描述")
    created_at = mapped_column(DateTime,
                               default=datetime.datetime.now(datetime.UTC),
                               nullable=False,
                               comment="创建时间")
    updated_at = mapped_column(DateTime,
                               default=datetime.datetime.now(datetime.UTC),
                               onupdate=datetime.datetime.now(datetime.UTC),
                               nullable=False,
                               comment="更新时间")
    user_id = mapped_column(String(100),
                            default="0",
                            nullable=True,
                            comment="用户id")  # 如果支持多用户
    username = mapped_column(String(100),
                             default="0",
                             nullable=True,
                             comment="用户名")  # 如果支持多用户
    storage_path = mapped_column(String(255),
                                 default=None,
                                 nullable=False,
                                 comment="存储路径")
    storage_bucket = mapped_column(String(100),
                                   default=None,
                                   nullable=True,
                                   comment="存储桶")
    status = mapped_column(String(50),
                           default='uploaded',
                           nullable=False,
                           comment="文件状态")  # 如：uploaded, processing, processed, failed等
    status_message = mapped_column(String(255),
                                   default=None,
                                   nullable=True,
                                   comment="状态消息")
    permissions = mapped_column(String(100),
                                default='private',
                                nullable=False)  # 权限字段,如：private, public, shared, read-only等
    access_token = mapped_column(String(255),
                                 default=None,
                                 nullable=True,
                                 comment="访问令牌")
    business_file_type = mapped_column(String(100),
                                       default=None,
                                       nullable=True,
                                       comment="业务文件类型，描述文件用于的业务类型")
    metadata1 = mapped_column(Text, nullable=True)
    metadata2 = mapped_column(Text, nullable=True)
    metadata3 = mapped_column(Text, nullable=True)
