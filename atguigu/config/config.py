import os
import dotenv
dotenv.load_dotenv()
#mineru的配置相关
class MineruConfig:
    mineru_token=os.getenv("MINERU_TOKEN")
#大模型配置相关
class LLMConfig:
    OPEN_API_KEY=os.getenv("OPEN_API_KEY")
    OPEN_BASE_URL=os.getenv("OPEN_BASE_URL")
    LLM_DEFAULT_MODEL = os.getenv("LLM_DEFAULT_MODEL")
    LLM_DEFAULT_TEMPERATURE = os.getenv("LLM_DEFAULT_TEMPERATURE")
    VL_MODEL = os.getenv("VL_MODEL")
    ITEM_MODEL = os.getenv("ITEM_MODEL")
#minio配置相关
class MinioClientConfig:
    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
    MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME")
    MINIO_IMG_DIR = os.getenv("MINIO_IMG_DIR")
# bge_m3切入模型
class EmbeddingConfig:
    bge_m3_path=os.getenv("BGE_M3_PATH")
    bge_m3=os.getenv("BGE_M3")
    bge_device=os.getenv("BGE_DEVICE")
    # 特殊处理：将.env中的1/0转为布尔值，兼容常见的数字/字符串格式
    bge_fp16=os.getenv("BGE_FP16")
class MilvusConfig:
    milvus_uri=os.getenv("MILVUS_URI")
    chunks_collection=os.getenv("CHUNKS_COLLECTION")
    item_name_collection=os.getenv("ITEM_NAME_COLLECTION")
