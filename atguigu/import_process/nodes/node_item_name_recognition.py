# atguigu/import_process/nodes/node_item_name_recognition.py
import json


from langchain.chat_models import init_chat_model
from pymilvus import DataType

from atguigu.config.config import LLMConfig, MilvusConfig
from atguigu.config.prompt import ITEM_NAME_SYSTEM_PROMPT, ITEM_NAME_USER_PROMPT_TEMPLATE
from atguigu.import_process.base import NodeBase
from atguigu.import_process.state import ImportGraphState
from atguigu.tool.bge_m3_tool import get_embedding
from atguigu.tool.creat_milvus_client import get_milvus_client
from atguigu.tool.json_format_tool import json_format
from atguigu.tool.logger import logger

class NodeItemNameRecognition(NodeBase):
    """
    主体识别节点：主体识别与标签提取
    """

    name = "node_item_name_recognition"

    def process(self, state: ImportGraphState):
        # 判断切片和文件名是否存在
        chunks = state["chunks"]
        file_title = state["file_title"]
        if not chunks:
            logger.error("chunks not exist")
            raise Exception("chunks not exist")
        if not file_title:
            logger.error("file_title not exist")
            raise Exception("file_title not exist")
        chunks_need_list = chunks[:6]
        chunks_merge = ""
        max_length = 10000

        for idx,chunk in enumerate(chunks_need_list):
            content = chunk["content"]
            title = chunk["title"]
            chunk_merge = f"切片{idx}\n{file_title}\n{title}\n{content}"
            chunks_merge += chunk_merge
            if len(chunks_merge) > max_length:
                break
        chunks_merge = chunks_merge[:max_length]
        # 用大模型识别出文章主体
        llm = init_chat_model(
            model=LLMConfig.LLM_DEFAULT_MODEL,
            model_provider="openai",
            base_url=LLMConfig.OPEN_BASE_URL,
            api_key=LLMConfig.OPEN_API_KEY,
            temperature=LLMConfig.LLM_DEFAULT_TEMPERATURE
        )
        messages=[{
            "role":"system",
            "content":ITEM_NAME_SYSTEM_PROMPT
        },
        {
            "role":"user",
            "content":ITEM_NAME_USER_PROMPT_TEMPLATE.format(context=chunks_merge,file_title=file_title),
        }]
        res = llm.invoke(messages)
        item_name=res.content
        if not item_name:
            item_name=file_title
        # 删除多余空字符串
        item_name = item_name.replace("\n","").replace(" ","").replace("\t","")

#         向量化数据并创建Milus表
        embeddings=get_embedding([item_name])
        dense_vector=embeddings["dense"][0]
        sparse_vector=embeddings["sparse"][0]
        milvus_client=get_milvus_client()
        if not milvus_client:
            logger.error("milvus client initialization faulted")
            raise Exception("milvus client initialization faulted")
        collection_name = MilvusConfig.item_name_collection
        if not milvus_client.has_collection(collection_name):
            schema=milvus_client.create_schema(
                auto_id=True,
            )
            schema.add_field(
                field_name="id",
                datatype=DataType.INT64,
                is_primary=True,
            ).add_field(
                field_name="item_name",
                datatype=DataType.VARCHAR,
                max_length=300
            ).add_field(
                field_name="file_title",
                datatype=DataType.VARCHAR,
                max_length=300
            ).add_field(
                field_name="dense_vector",
                datatype=DataType.FLOAT_VECTOR,
                dim=1024
            ).add_field(
                field_name="sparse_vector",
                datatype=DataType.SPARSE_FLOAT_VECTOR,
            )
            # 创建索引
            index_params = milvus_client.prepare_index_params()
            index_params.add_index(
                field_name="dense_vector",
                index_name="dense_vector_index",
                index_type="IVF_FLAT",  # 优化的暴力搜索
                metric_type="COSINE",  # 计算相似度算法
                params={"nlist": 128, "nprobe": 10}  # 分了多少簇，查找每次查几个簇

            )
            index_params.add_index(
                field_name="sparse_vector",
                index_name="sparse_vector_index",
                index_type="SPARSE_INVERTED_INDEX",  # 优化的暴力搜索
                metric_type="IP",  # 计算稀疏向量的相似度算法（为了计算值）
                params={
                    "inverted_index_algo": "DAAT_MAXSCORE",
                    # 高效的稀疏检索算法
                    "normalize": True,
                    # ↑ L2 归一化，让内积 (IP) 等价于余弦相似度
                    "quantization": "none"}
                # ↑ 关闭量化，保持原始精度：模型生成的向量已经压缩的一半的精度了（BGE_FP16=1），这里就不再压缩了
                # "quantization": "none" → 存储原始向量，不压缩
                # "quantization": "sq8" → 存储压缩后的向量（8-bit 量化
            )
            milvus_client.create_collection(
                collection_name=collection_name,
                index_params=index_params,
                schema=schema,
            )
        milvus_client.load_collection(collection_name)
        item_name=item_name.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
        filter=f"item_name=='{item_name}'"
        milvus_client.delete(
            collection_name=collection_name,
            filter=filter)
        data={
            "item_name":item_name,
            "file_title":file_title,
            "dense_vector":dense_vector,
            "sparse_vector":sparse_vector,
        }
        milvus_client.insert(
            collection_name=collection_name,
            data=data,
        )

        for chunk in chunks:

            chunk["item_name"]=item_name

        with open(r"D:\pojie\渊哥\hak180产品安全手册\chunk.json","w",encoding="utf-8") as d:
            d.write(json_format(chunks))
        return {
            "chunks":chunks
        }








if __name__=="__main__":
    p=NodeItemNameRecognition()
    with open(r"D:\pojie\渊哥\hak180产品安全手册\chunk.json","r",encoding="utf-8") as f:
        data=f.read()
    init_state={
        "chunks":json.loads(data),
        "file_title":"hak180产品安全手册"
    }
    p(init_state)