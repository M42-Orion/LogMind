#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@文件    :chromadb_vector.py
@说明    :
@时间    :2025/06/06 15:04:59
@作者    :ljw
@版本    :1.0
'''

import json
import os
from typing import Any, Dict, List, Optional, Sequence

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from config import setting

from ..vectordb import VectorData, VectorDB

default_ef = embedding_functions.DefaultEmbeddingFunction()


class ChromaDB(VectorDB):
    """Chromadb向量数据库实现"""

    def __init__(self, client: Optional[chromadb.Client]|None = None,
                 persist_directory: str = "./chroma_db",
                 config: Dict[str, Any] = {},
                 curr_client: str = "persistent",):
        """
        初始化Chromadb实现
        Args:
            client: 自定义Chromadb客户端，默认为None
            persist_directory: 持久化目录，默认为None
        """
        if not (os.path.exists(persist_directory) and os.path.isdir(persist_directory)):
            persist_directory = os.path.join(
                setting.PROJ_PATH, "db", "vectordb", "chroma_db", persist_directory)
        self.embedding_function = config.get("embedding_function", default_ef)
        if curr_client == "persistent":  # 持久化客户端
            self.chroma_client = chromadb.PersistentClient(
                path=persist_directory, settings=Settings(
                    anonymized_telemetry=False)
            )
        elif curr_client == "in-memory":  # 内存客户端
            self.chroma_client = chromadb.EphemeralClient(
                settings=Settings(anonymized_telemetry=False)
            )
        self.client = self.chroma_client
        self.collections = {}  # 缓存集合对象

    def _get_collection(self, collection_name: str) -> Collection:
        """获取或创建集合"""
        if collection_name not in self.collections:
            try:
                self.collections[collection_name] = self.client.get_collection(
                    collection_name)
            except ValueError:
                self.collections[collection_name] = self.client.create_collection(
                    collection_name)
        return self.collections[collection_name]

    @staticmethod
    def _extract_documents(query_results,**kwargs) -> list:
        """
        从查询结果中提取文档的静态方法。

        参数：
            query_results (pd.DataFrame)：要使用的数据框。

        返回值：
            List[str] 或 None：提取的文档，如果发生错误，则返回空列表或单个文档。
        """
        if query_results is None:
            return []
        if "documents" in query_results:
            documents = query_results["documents"]
            if len(documents) == 1 and isinstance(documents[0], list):
                try:
                    documents = [json.loads(doc) for doc in documents[0]]
                    _dict = dict(zip(documents[0],query_results['distances'][0]))
                    documents = [i for i in _dict if _dict[i]<kwargs.get("distances",1)]
                except Exception as e:
                    return documents[0]
            return documents
        return []

    def generate_embedding(self, data: str, **kwargs) -> List[float]:
        """生成文本的向量表示"""
        embedding = self.embedding_function([data])
        if len(embedding) == 1:
            return embedding[0]
        return embedding

    def add(self, vectors: List[VectorData], collection_name: str)-> List[Any]:
        """向指定集合添加向量"""
        res_list = []
        if not vectors:
            return []
        collection = self._get_collection(collection_name)
        for vector in vectors:
            res = collection.add(
                ids=vector.id,
                embeddings=vector.embedding,
                documents=vector.documents,
            )
            res_list.append(res)
        return res_list

    def batch_add(self, 
                 vectors: List[VectorData], 
                 collection_name: str, 
                 batch_size: int = 100) -> List[str]:
        """批量添加向量"""
        all_ids = []
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i+batch_size]
            batch_ids = self.add(batch, collection_name)
            all_ids.extend(batch_ids)
        return all_ids

    def query(self, query_embedding: List[float] = [],
              collection_name: str = "",
              n_results: int = 5,
              where: Dict[str, Any] = {},
              **kwargs) -> Any:
        """查询相似向量"""
        collection = self._get_collection(collection_name)
        res_dict = collection.query(
            query_embeddings=self.generate_embedding(kwargs.get("query_texts", "")),
            query_texts=kwargs.get("query_texts", ""),
            n_results=n_results
        )
        # TODO rerank 重排序
        # self.generate_embedding(kwargs.get("query_texts", ""))
        if kwargs.get("unpro_data", False): # 不处理数据,返回原始结果
            return res_dict
        return self._extract_documents(res_dict, **kwargs)

    def delete(self, 
               ids: List[str], 
               collection_name: str) -> int:
        """删除指定ID的向量"""
        if not ids:
            return 0
        collection = self._get_collection(collection_name)
        collection.delete(ids=ids)
        return len(ids)

    def update(self, 
               vector: VectorData, 
               collection_name: str) -> bool:
        """更新指定ID的向量"""
        collection = self._get_collection(collection_name)
        try:
            collection.update(
                ids=vector.id,
                embeddings=vector.embedding,
                metadatas=vector.metadata
            )
            return True
        except Exception as e:
            print(f"更新向量失败: {e}")
            return False

    def get(self, 
            id: str, 
            collection_name: str) -> Optional[VectorData]:
        """获取指定ID的向量"""
        collection = self._get_collection(collection_name)
        try:
            result = collection.get(ids=[id])
            if not result["ids"]:
                return None
            return VectorData(
                id=result["ids"][0],
                embedding=result["embeddings"][0],
                metadata=result["metadatas"][0]
            )
        except Exception as e:
            print(f"获取向量失败: {e}")
            return None

    def list_collections(self) -> List[str]|Sequence[Collection]:
        """获取所有集合名称"""
        return self.client.list_collections()

    def create_collection(self, 
                          collection_name: str, 
                          metadata: Dict[str, Any]|None = None) -> bool:
        """创建新集合"""
        try:
            self.client.create_collection(collection_name, metadata=metadata)
            return True
        except Exception as e:
            print(f"创建集合失败: {e}")
            return False

    def delete_collection(self, collection_name: str) -> bool:
        """删除集合"""
        try:
            self.client.delete_collection(collection_name)
            if collection_name in self.collections:
                del self.collections[collection_name]
            return True
        except Exception as e:
            print(f"删除集合失败: {e}")
            return False
