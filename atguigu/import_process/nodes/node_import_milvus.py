# atguigu/import_process/nodes/node_import_milvus.py
import json

from pymilvus import DataType

from atguigu.config.config import MilvusConfig
from atguigu.import_process.base import NodeBase
from atguigu.import_process.state import ImportGraphState
from atguigu.tool.creat_milvus_client import get_milvus_client
from atguigu.tool.logger import logger


class NodeImportMilvus(NodeBase):
    """
    导入向量库节点：数据持久化
    """

    name = "node_import_milvus"

    def process(self, state: ImportGraphState):
        chunks = state.get("chunks")
        if not chunks:
            logger.error("chunks not exist")
            raise Exception("chunks not exist")
        file_title = chunks[0]["file_title"]
        milvus_client = get_milvus_client()
        if not milvus_client:
            logger.error("milvus client initialization failed")
            raise Exception("milvus client initialization failed")
        collection_name =MilvusConfig.chunks_collection
        if not milvus_client.has_collection(collection_name):
            schema = milvus_client.create_schema(auto_id=True)
            schema.add_field(
                field_name="id",
                datatype=DataType.INT64,
                is_primary=True,
            ).add_field(
                field_name="title",
                datatype=DataType.VARCHAR,
                max_length=1000,
            ).add_field(
                field_name="file_title",
                datatype=DataType.VARCHAR,
                max_length=1000,
            ).add_field(
                field_name="item_name",
                datatype=DataType.VARCHAR,
                max_length=1000,
            ).add_field(
                field_name="content",
                datatype=DataType.VARCHAR,
                max_length=5000,
            ).add_field(
                field_name="part",
                datatype=DataType.INT64,
            ).add_field(
                field_name="dense_vector",
                datatype=DataType.FLOAT_VECTOR,
                dim=1024
            ).add_field(
                field_name="sparse_vector",
                datatype=DataType.SPARSE_FLOAT_VECTOR,
            )
            index_params = milvus_client.prepare_index_params()
            index_params.add_index(
                field_name="dense_vector",
                index_name="dense_vector",
                index_type="AUTOINDEX",
                metric_type="L2"
            )
            index_params.add_index(
                field_name="sparse_vector",
                index_name="sparse_vector",
                index_type="SPARSE_INVERTED_INDEX",
                metric_type="IP",
                params={
                    "inverted_index_algo": "DAAT_MAXSCORE",
                    # 高效的稀疏检索算法
                    "normalize": True,
                    # ↑ L2 归一化，让内积 (IP) 等价于余弦相似度
                    "quantization": "none"
                    # ↑ 关闭量化，保持原始精度：模型生成的向量已经压缩的一半的精度了（BGE_FP16=1），这里就不再压缩了
                    # "quantization": "none" → 存储原始向量，不压缩
                    # "quantization": "sq8" → 存储压缩后的向量（8-bit 量化
                }
            )
            milvus_client.create_collection(
                collection_name=collection_name,
                index_params=index_params,
                schema=schema
            )
        milvus_client.load_collection(collection_name=collection_name)
        file_title=file_title.replace("\\", "\\\\").replace("'","\'").replace('"','\"')
        filter=f"file_title=='{file_title}'"
        milvus_client.delete(collection_name=collection_name,
                                        filter=filter)

        res = milvus_client.insert(
            collection_name=collection_name,
            data=chunks
        )
        ids=res.get("id")
        for i ,chunk in enumerate(chunks,start=1):
            chunk["id"]=ids[i]








if __name__ == "__main__":
    p=NodeImportMilvus()
    with open(r"D:\pojie\渊哥\hak180产品安全手册\chunk.json","r",encoding="utf-8") as f:
        chunks=f.read()
    init_state={
        "chunks":json.loads(chunks)
    }
    p(init_state)