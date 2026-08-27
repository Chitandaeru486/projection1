from minio import Minio

from atguigu.config.config import MinioClientConfig
from atguigu.tool.json_format_tool import json_format

client = 0
def get_minio_client():
    global client
    if not client:
        client = Minio(
            endpoint=f"{MinioClientConfig.MINIO_ENDPOINT}",
            access_key=f"{MinioClientConfig.MINIO_ACCESS_KEY}",
            secret_key=f"{MinioClientConfig.MINIO_SECRET_KEY}",
            secure=False
        )
        bucket_name = f"{MinioClientConfig.MINIO_BUCKET_NAME}"
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name="zccimages")
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
                    "Resource": f"arn:aws:s3:::{bucket_name}",
                },
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket_name}/*",
                },
            ],
        }
        client.set_bucket_policy(bucket_name=f"{bucket_name}", policy=json_format(policy))

    return client
if __name__ == "__main__":
    try:
        client = get_minio_client()

        print("MinIO 客户端创建成功！")

        # 测试连接
        print("MinIO 连接测试成功")

        # 获取 Bucket 名称
        bucket_name = MinioClientConfig.MINIO_BUCKET_NAME
        # 判断 Bucket 是否存在
        if client.bucket_exists(bucket_name):
            print(f"Bucket [{bucket_name}] 存在")
        else:
            print(f"Bucket [{bucket_name}] 不存在")

    except Exception as e:
        print(f"MinIO 测试失败：{e}")