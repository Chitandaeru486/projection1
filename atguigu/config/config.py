import os
import dotenv
dotenv.load_dotenv()
#mineru的配置相关
class Config:
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