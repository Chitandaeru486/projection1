# atguigu/import_process/nodes/node_md_img.py
import base64
import re
import time
from collections import deque
from os import listdir
from pathlib import Path
from typing import Any

from langchain.chat_models import init_chat_model
from minio.deleteobjects import DeleteObject

from atguigu.config.config import LLMConfig, MinioClientConfig
from atguigu.import_process.base import NodeBase
from atguigu.import_process.state import ImportGraphState
from atguigu.tool import creat_minio_client
from atguigu.tool.json_format_tool import json_format
from atguigu.tool.logger import logger


class NodeMDImg(NodeBase):
    """
    MarkDown图片处理节点：多模态图片理解
    """

    name = "node_md_img"

    def process(self, state: ImportGraphState):
        # 获取md文件路径
        md_path = state.get('md_path')
        # 相关检验
        if md_path is None:
            logger.error("路径不存在")
            raise Exception('路径不存在')
        md_path_mdj = Path(md_path)
        if not md_path_mdj.exists():
            logger.error('路径文件不存在')
            raise Exception('路径文件不存在')
        with md_path_mdj.open('r', encoding='utf-8') as f:
            md_content = f.read()
        # 获取md文件同级别路径下的image路径
        image_path_obj = Path(md_path_mdj.parent / 'images')
        if not image_path_obj.exists():
            logger.warning('图像路径文件不存在,跳过')
            return {
                "md_content": md_content,
            }
        # listdir是Path的一个方法,获取这个目录下的所有文件
        image_context_list = self.prepare_image_context(image_path_obj, md_content, md_path_mdj)

        image_summary_list = self.generate_image_summary(image_context_list)

        image_load_url_list = self.upload_images_to_minio(image_summary_list)
        # sub替换md文件图片的注释,并生成新md文件
        md_content, new_md_path = self.sub_creat_new_md(image_load_url_list, md_content, md_path_mdj)
        return md_content, new_md_path






        # image_list

    def upload_images_to_minio(self, image_summary_list: list[Any]) -> list[Any]:
        upload_file = MinioClientConfig.MINIO_IMG_DIR
        client = creat_minio_client.get_minio_client()
        # 先去获得一个生成器对象,旧目录下的所有文件
        old_object_list = client.list_objects(
            bucket_name=MinioClientConfig.MINIO_BUCKET_NAME,
            prefix=upload_file,
            recursive=True
        )
        # 遍历生成器,生成一个DeleteObject对象 .object_name是实例化minio对象后的一个固定属性,用于获取
        delete_object_list = [DeleteObject(i.object_name) for i in old_object_list]

        # 幂等性清理旧数据
        errors = client.remove_objects(
            bucket_name=f"{MinioClientConfig.MINIO_BUCKET_NAME}",
            delete_object_list=delete_object_list
        )
        for error in errors:
            print("error occurred when deleting object", error)
        image_load_url_list = []
        for image_summary in image_summary_list:
            result = client.fput_object(
                bucket_name=f"{MinioClientConfig.MINIO_BUCKET_NAME}",
                object_name=f"{upload_file}" + "/" + image_summary["image_name"],
                file_path=f"{image_summary['image_path']}",
            )
            url = "http://" + f"{MinioClientConfig.MINIO_ENDPOINT}" + "/" + upload_file + "/" + image_summary[
                "image_name"]
            image_load_url_list.append({
                "url": url,
                **image_summary
            })
        return image_load_url_list

    def sub_creat_new_md(self, image_load_url_list: list[Any], md_content: str, md_path_mdj: Path) -> tuple[str, Path]:
        for image_load_url in image_load_url_list:
            pattern = re.compile(r"!\[.*?\]\(.*?" + re.escape(image_load_url["image_name"]) + r"\)")
            md_content = pattern.sub(
                lambda _: f"![{image_load_url.get('summary')}]({image_load_url.get('url')})",
                md_content
            )
        new_md_path = md_path_mdj.parent / f"{md_path_mdj.stem}_new.md"
        with open(new_md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        return md_content, new_md_path

    def generate_image_summary(self, image_context_list: list[Any]) -> list[Any]:
        llm = init_chat_model(
            model=LLMConfig.VL_MODEL,
            model_provider="openai",
            base_url=LLMConfig.OPEN_BASE_URL,
            api_key=LLMConfig.OPEN_API_KEY,
            temperature=float(LLMConfig.LLM_DEFAULT_TEMPERATURE)
        )
        image_summary_list = []

        # 设置滑动门限制频率
        # 设置双向队列
        dq = deque(maxlen=30)
        # 获取每个图片对应的上下文和图内容
        for image_context in image_context_list:
            current_time = time.time()
            # 清理过期时间戳
            while dq and current_time - dq[0] > 60:
                dq.popleft()
            # 判断队列是否是满的，满则等待
            if len(dq) >= dq.maxlen:
                wait_time = 60 - (current_time - dq[0])
                if wait_time > 0:
                    time.sleep(wait_time)
                current_time = time.time()
                while dq and current_time - dq[0] > 60:
                    dq.popleft()
            dq.append(current_time)
            with open(image_context.get("image_path"), 'rb') as f:
                encode_data = base64.b64encode(f.read()).decode("utf-8")
                # print(encode_data)
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "data:image/jpeg;base64," + encode_data
                            },
                        },
                        {"type": "text", "text": f"""这是一张图片，上文内容是{image_context.get("pre_content")}
                        下文内容是{image_context.get("suf_content")}，请用中文简要总结这张图片的摘要,字数在50字以内"""},
                    ],
                },
            ]
            res = llm.invoke(messages)
            image_summary_list.append({
                "image_name": image_context.get("image_name"),
                "image_path": image_context.get("image_path"),
                "summary": res.content

            })
        return image_summary_list

    def prepare_image_context(self, image_path_obj: Path, md_content: str, md_path_mdj: Path) -> list[Any]:
        image_name_list = listdir(image_path_obj)
        IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
        image_context_list = []
        for image_name in image_name_list:
            suffix = Path(image_name).suffix.lower()
            if suffix not in IMAGE_EXTENSIONS:
                logger.warning(f"文件格式不正确{image_name}")
                continue
            logger.info("文件格式正确")
            pattern = re.compile(r"!\[.*?\]\(.*?" + re.escape(image_name) + r"\)")
            match = pattern.search(md_content)
            if match is None:
                logger.warning(f"md文件中没有找到相关的图片{image_name}")
                continue
            # span是正则的一个方法,获取替换内容的切片位置
            start, end = match.span()
            pre_content = md_content[max(start - 300, 0):start]
            suf_content = md_content[end:min(end + 300, len(md_content))]
            image_context_list.append({
                "pre_content": pre_content,
                "suf_content": suf_content,
                "image_name": image_name,
                "image_path": str(md_path_mdj.parent / "images" / f'{image_name}'),
            })
        return image_context_list


if __name__ == '__main__':
    p = NodeMDImg()
    init_state = {
        "md_path": r"D:\pojie\渊哥\hak180产品安全手册\hak180产品安全手册.md",
    }
    res = p(init_state)
