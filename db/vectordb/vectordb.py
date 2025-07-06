#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@文件    :vectordb.py
@说明    :
@时间    :2025/06/06 15:12:10
@作者    :ljw
@版本    :1.0
'''

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class VectorData:
    """向量数据类，用于存储向量及其元数据"""
    id: str
    embedding: List[float]|None|str
    metadata: Dict[str, Any]|None = None
    documents: List[str]|None = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于数据同步"""
        return {
            "id": self.id,
            "embedding": self.embedding,
            "metadata": self.metadata or {},
            "documents": self.documents or []
        }


class VectorDB(ABC):
    """向量数据库抽象基类，定义统一接口"""

    def generate_embedding(self, data: str, **kwargs) -> List[float]|None:
        """生成文本的向量表示"""
        pass

    @abstractmethod
    def add(self, vectors: List[VectorData], collection_name: str) -> List[str]:
        """
        向指定集合添加向量
        Args:
            vectors: 向量数据列表
            collection_name: 集合名称
        Returns:
            成功添加的向量ID列表
        """
        pass

    @abstractmethod
    def batch_add(self, vectors: List[VectorData], collection_name: str, batch_size: int = 100) -> List[str]:
        """
        批量添加向量，支持大数量向量分批次处理

        Args:
            vectors: 向量数据列表
            collection_name: 集合名称
            batch_size: 每批处理的向量数量

        Returns:
            成功添加的向量ID列表
        """
        pass

    @abstractmethod
    def query(self,
              query_embedding: List[float] = [],
              collection_name: str = "",
              n_results: int = 5,
              where: Dict[str, Any] = {},
              **kwargs) -> Any:
        """
        查询相似向量

        Args:
            query_embedding: 查询向量
            collection_name: 集合名称
            n_results: 返回结果数量
            where: 元数据过滤条件

        Returns:
            查询结果，包含匹配的向量ID、嵌入和元数据
        """
        pass

    @abstractmethod
    def delete(self, ids: List[str], collection_name: str) -> int:
        """
        删除指定ID的向量

        Args:
            ids: 要删除的向量ID列表
            collection_name: 集合名称

        Returns:
            成功删除的向量数量
        """
        pass

    @abstractmethod
    def update(self, vector: VectorData, collection_name: str) -> bool:
        """
        更新指定ID的向量

        Args:
            vector: 新的向量数据
            collection_name: 集合名称

        Returns:
            更新是否成功
        """
        pass

    @abstractmethod
    def get(self, id: str, collection_name: str) -> Optional[VectorData]:
        """
        获取指定ID的向量

        Args:
            id: 向量ID
            collection_name: 集合名称

        Returns:
            向量数据，不存在则返回None
        """
        pass

    @abstractmethod
    def list_collections(self) -> List[str]|Any:
        """
        获取所有集合名称

        Returns:
            集合名称列表
        """
        pass

    @abstractmethod
    def create_collection(self, collection_name: str, metadata: Dict[str, Any]|None = None) -> bool:
        """
        创建新集合

        Args:
            collection_name: 集合名称
            metadata: 集合元数据

        Returns:
            创建是否成功
        """
        pass

    @abstractmethod
    def delete_collection(self, collection_name: str) -> bool:
        """
        删除集合

        Args:
            collection_name: 集合名称

        Returns:
            删除是否成功
        """
        pass
