#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@文件    :text2vec.py
@说明    :
@时间    :2025/06/11 09:47:08
@作者    :ljw
@版本    :1.0
'''

import uuid
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Any, Dict, List

import torch
from transformers import AutoModel, AutoTokenizer

from .vectordb import VectorData

# ------------------------
# 文本转向量抽象基类
# ------------------------


class Text2Vector(ABC):
    """文本转向量工具抽象基类"""

    @abstractmethod
    def to_vector(self, text: str) -> List[float]:
        """
        将单个文本转换为向量

        Args:
            text: 输入文本

        Returns:
            向量表示（列表形式）
        """
        pass

    @abstractmethod
    def to_vectors(self, texts: List[str]) -> List[List[float]]:
        """
        批量将文本列表转换为向量列表

        Args:
            texts: 输入文本列表

        Returns:
            向量列表（每个元素为列表形式的向量）
        """
        pass


# ------------------------
# Hugging Face 本地模型实现
# ------------------------
class HuggingFaceEmbedding(Text2Vector):
    """使用Hugging Face模型进行本地文本转向量"""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", device: str = "cpu"):
        """
        初始化Hugging Face Embedding

        Args:
            model_name: Hugging Face模型名称（支持sentence-transformers系列）
            device: 计算设备（"cpu"或"cuda"）
        """
        self.model_name = model_name
        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(device)
        self.model.eval()  # 切换为评估模式

    def _mean_pooling(self, model_output, attention_mask):
        """平均池化获取句向量"""
        token_embeddings = model_output[0]  # 模型输出的token嵌入
        input_mask = attention_mask.unsqueeze(
            -1).expand(token_embeddings.size())
        return torch.sum(token_embeddings * input_mask, 1) / torch.clamp(input_mask.sum(1), min=1e-9)

    def to_vector(self, text: str) -> List[float]:
        """单文本转向量（本地模型计算）"""
        return self.to_vectors([text])[0]

    def to_vectors(self, texts: List[str]) -> List[List[float]]:
        """批量文本转向量（本地模型计算）"""
        inputs = self.tokenizer(
            texts, padding=True, truncation=True, return_tensors="pt").to(self.device)
        with torch.no_grad():
            model_output = self.model(**inputs)
        embeddings = self._mean_pooling(
            model_output, inputs["attention_mask"]).cpu().numpy()
        return embeddings.tolist()


class Text2VectorFactory:
    """文本转向量工具工厂，支持动态注册不同实现"""

    def __init__(self):
        self.implementations = {
            "huggingface": HuggingFaceEmbedding
        }

    def create(self, provider: str, **kwargs) -> Text2Vector:
        """
        创建文本转向量工具

        Args:
            provider: 实现提供商（"openai"或"huggingface"）
            **kwargs: 初始化参数（如model、api_key等）

        Returns:
            文本转向量工具实例
        """
        if provider not in self.implementations:
            raise ValueError(f"不支持的文本转向量提供商: {provider}")
        return self.implementations[provider](**kwargs)


class CachedText2Vector(Text2Vector):
    """带LRU缓存的文本转向量工具包装类"""

    def __init__(self, base_model: Text2Vector, cache_size: int = 1000):
        """
        初始化缓存包装类

        Args:
            base_model: 基础文本转向量工具实例
            cache_size: 缓存大小
        """
        self.base_model = base_model
        self.to_vector = lru_cache(maxsize=cache_size)(
            self.base_model.to_vector)
        self.to_vectors = self.base_model.to_vectors  # 批量处理不缓存（避免内存占用过大）


class VectorDataGenerator:
    """向量数据生成工具，将文本数据转换为VectorData对象"""

    def __init__(self, text2vec: Text2Vector):
        """
        初始化向量数据生成器

        Args:
            text2vec: 文本转向量工具实例
        """
        self.text2vec = text2vec

    def generate(self, texts: List[str], metadata: List[Dict[str, Any]]|None = None) -> List[VectorData]:
        """
        生成向量数据列表

        Args:
            texts: 输入文本列表
            metadata: 每条文本的元数据列表（可选，长度需与texts一致）

        Returns:
            向量数据列表（VectorData对象）
        """
        if metadata and len(texts) != len(metadata):
            raise ValueError("文本列表与元数据列表长度必须一致")

        vectors = self.text2vec.to_vectors(texts)
        data = []
        for i, text in enumerate(texts):
            vec_id = str(uuid.uuid4())
            meta = metadata[i] if metadata else {"source": "text"}
            data.append(VectorData(
                id=vec_id, embedding=vectors[i], metadata=meta))
        return data
