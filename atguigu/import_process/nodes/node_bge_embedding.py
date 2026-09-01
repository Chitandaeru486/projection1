# atguigu/import_process/nodes/node_bge_embedding.py
import json

from atguigu.tool.bge_m3_tool import get_embedding
from atguigu.tool.logger import logger
from atguigu.import_process.base import NodeBase
from atguigu.import_process.state import ImportGraphState
from atguigu.tool.json_format_tool import json_format


class NodeBGEEmbedding(NodeBase):
    """
    混合向量化节点：使用 BGE-M3 模型将文本转换为向量
    """

    name = "node_bge_embedding"

    def process(self, state: ImportGraphState):
        chunks=state.get("chunks")
        if not chunks:
            logger.error("chunks not exist")
            raise Exception("chunks not exist")
        for i in range(0, len(chunks),3):
            chunk_list=chunks[i:i+3]
            chunk_list_emerge=[f'{chunk.get("content")}{chunk.get("item_name")}' for chunk in chunk_list]
            embedding=get_embedding(chunk_list_emerge)
            for idx,chunk in enumerate(chunk_list):
                chunk["dense_vector"]=embedding["dense"][idx]
                chunk["sparse_vector"]=embedding["sparse"][idx]
        with open(r"D:\pojie\渊哥\hak180产品安全手册\chunk.json","w",encoding="utf-8") as f:
            f.write(json_format(chunks))
        return {
            "chunks":chunks
        }




if __name__ == "__main__":
    p=NodeBGEEmbedding()
    with open(r"D:\pojie\渊哥\hak180产品安全手册\chunk.json","r",encoding="utf-8") as f:
        chunks=f.read()
    init_state={
        "chunks":json.loads(chunks)
    }
    p(init_state)