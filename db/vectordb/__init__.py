#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@文件    :__init__.py
@说明    :
@时间    :2025/06/12 14:14:18
@作者    :ljw
@版本    :1.0
'''


import uuid
from typing import Any, Dict, List, Optional

from .chroma_db.chromadb_vector import ChromaDB
from .vectordb import VectorData, VectorDB


class VectorDBRegistry:
    """向量数据库注册表，用于管理不同的向量数据库实现"""
    
    def __init__(self):
        self.registries = {}
    
    def register(self, name: str, db_class: type):
        """
        注册向量数据库实现
        
        Args:
            name: 数据库名称
            db_class: 数据库实现类
        """
        if not issubclass(db_class, VectorDB):
            raise TypeError(f"{db_class} 不是 VectorDB 的子类")
        self.registries[name] = db_class
    
    def create(self, name: str, **kwargs) -> VectorDB:
        """
        创建向量数据库实例
        
        Args:
            name: 数据库名称
            **kwargs: 数据库初始化参数
            
        Returns:
            向量数据库实例
        """
        if name not in self.registries:
            raise ValueError(f"未注册的向量数据库: {name}")
        return self.registries[name](**kwargs)


class VectorDBManager:
    """向量数据库管理类，用于管理多个向量数据库实例"""
    
    def __init__(self, registry: VectorDBRegistry):
        """
        初始化向量数据库管理器
        
        Args:
            registry: 向量数据库注册表
        """
        self.registry = registry
        self.databases = {}
    
    def get_db(self, name: str, **kwargs) -> VectorDB:
        """
        获取向量数据库实例
        
        Args:
            name: 数据库名称
            **kwargs: 数据库初始化参数
            
        Returns:
            向量数据库实例
        """
        if name not in self.databases:
            self.databases[name] = self.registry.create(name, **kwargs)
        return self.databases[name]
    
    def sync_to_non_rel_db(self, vector_data: VectorData, non_rel_db: Any) -> bool:
        """
        同步向量数据到非关系型数据库
        
        Args:
            vector_data: 向量数据
            non_rel_db: 非关系型数据库实例
            
        Returns:
            同步是否成功
        """
        try:
            # 转换为适合非关系型数据库的格式
            data = vector_data.to_dict()
            # 假设非关系型数据库有save方法
            return non_rel_db.save(data["id"], data)
        except Exception as e:
            print(f"同步到非关系型数据库失败: {e}")
            return False
    
    def batch_sync_to_non_rel_db(self, vectors: List[VectorData], non_rel_db: Any) -> int:
        """
        批量同步向量数据到非关系型数据库
        
        Args:
            vectors: 向量数据列表
            non_rel_db: 非关系型数据库实例
            
        Returns:
            成功同步的数量
        """
        success_count = 0
        for vector in vectors:
            if self.sync_to_non_rel_db(vector, non_rel_db):
                success_count += 1
        return success_count


# 初始化注册表并注册数据库
vector_db_registry = VectorDBRegistry()
vector_db_registry.register("chroma", ChromaDB)
# 创建向量数据库管理器
manager = VectorDBManager(vector_db_registry)
vector_db = manager.get_db("chroma", persist_directory="chroma_db")
# 使用示例
if __name__ == "__main__":
    # 获取Chromadb实例
    chroma_db = manager.get_db("chroma", persist_directory="./chroma_db")
    
    # 创建集合
    chroma_db.create_collection("test_collection")
    
    # 准备向量数据
    vector1 = VectorData(
        id=str(uuid.uuid4()),
        embedding=[0.1, 0.2, 0.3],
        metadata={"type": "text", "content": "示例文本1"}
    )
    
    vector2 = VectorData(
        id=str(uuid.uuid4()),
        embedding=[0.4, 0.5, 0.6],
        metadata={"type": "text", "content": "示例文本2"}
    )
    # 添加向量
    chroma_db.add([vector1, vector2], "test_collection")
    # 查询向量
    results = chroma_db.query([0.2, 0.3, 0.4], "test_collection", n_results=2)
    print("查询结果:", results)
    # 假设的非关系型数据库接口
    class MockNonRelDB:
        def __init__(self):
            self.data = {}
        def save(self, id: str, data: Dict[str, Any]) -> bool:
            self.data[id] = data
            return True
        def get(self, id: str) -> Optional[Dict[str, Any]]:
            return self.data.get(id)
    # 同步到非关系型数据库
    non_rel_db = MockNonRelDB()
    manager.sync_to_non_rel_db(vector1, non_rel_db)
    print("非关系型数据库中的数据:", non_rel_db.data)
