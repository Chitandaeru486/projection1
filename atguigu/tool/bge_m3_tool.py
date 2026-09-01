from pymilvus.model.hybrid import BGEM3EmbeddingFunction

from atguigu.config.config import EmbeddingConfig

bge_embedding_model = None
def get_bge_embedding_model():
    global bge_embedding_model
    if not bge_embedding_model:
        bge_embedding_model = BGEM3EmbeddingFunction(
            model_name=EmbeddingConfig.bge_m3_path,
            device=EmbeddingConfig.bge_device,
            use_fp16=True if EmbeddingConfig.bge_fp16 in ("True", "1", 1, True) else False
        )
    return bge_embedding_model

def get_embedding(texts_list):
    model = get_bge_embedding_model()
    embedding = model.encode_documents(texts_list)
    res = [item.tolist() for item in embedding["dense"]]
    return {
        "dense": res,
        "sparse": [dict(zip(item.indices.tolist(),item.data.tolist())) for item in embedding["sparse"]]
    }

if __name__ == '__main__':
    get_embedding(["你好","世界"])