from pymilvus import MilvusClient

from atguigu.config.config import MilvusConfig

milvus_clint = None
def get_milvus_client():
    global milvus_clint
    if not milvus_clint:
        milvus_clint = MilvusClient(
            uri=MilvusConfig.milvus_uri,
        )
        return milvus_clint