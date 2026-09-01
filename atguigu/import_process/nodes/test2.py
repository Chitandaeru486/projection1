import base64
import os
import re
import time
from collections import deque
from pathlib import Path

from langchain.chat_models import init_chat_model
from openai import OpenAI

from atguigu.config.config import LLMConfig
from atguigu.import_process.base import NodeBase
from atguigu.import_process.state import ImportGraphState
from atguigu.tool import creat_minio_client
from atguigu.tool.json_format_tool import json_format
from atguigu.tool.logger import logger


class NodeMDImg2(NodeBase):
    name="nodemdimg2"
    def process(self, state:ImportGraphState):
        md_path = state.get("md_path")
        if not md_path:
            logger.error("pdf_path is null")
            raise Exception("pdf_path is null")
        md_path_obj = Path(md_path)
        if not md_path_obj.exists():
            logger.error("pdf_path_obj is not exist")
            raise Exception("pdf_path is not exist")
        with open(md_path_obj, "rb") as f:
            md_content = f.read().decode("utf-8")
        md_images_path_obj = md_path_obj.parent / 'images'
        if not md_images_path_obj.exists():
            logger.warning(f"{md_images_path_obj} is not exist")
            return md_content
        list_images_name = os.listdir(md_images_path_obj)
        if not list_images_name:
            logger.warning(f"{md_images_path_obj} is none")
            return md_content
        IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
        image_content_list = []
        for image_name in list_images_name:
            suffix = Path(image_name).suffix.lower()
            if suffix not in IMAGE_EXTENSIONS:
                logger.warning(f"{image_name} invalid format")
            pattern = re.compile(r"!\[.*?\]\(.*?" + re.escape(image_name) + r"\)")
            match=pattern.search(md_content)
            if not match:
                logger.warning(f"{image_name} not find")
                continue
            start,end = match.span()
            pre_content = md_content[max(start-300,0):start]
            suf_content = md_content[end:min(end+300,len(md_content))]
            image_content_list.append(
                {"pre_content":pre_content,
                 "suf_content":suf_content,
                 "image_name":image_name,
                 "image_path":str(md_images_path_obj/image_name),})
        # 算法滑动门限制频率
        dq = deque(maxlen=30)
        llm =   init_chat_model(
            model = LLMConfig.VL_MODEL,
            provider = "openai",
            base_url = LLMConfig.OPEN_BASE_URL,
            api_key = LLMConfig.OPEN_API_KEY,
            temperature=float(LLMConfig.LLM_DEFAULT_TEMPERATURE)
        )
        image_summary_list = []
        try:
            for image_content in image_content_list:
                current_time = time.time()
                while current_time - dq[0] >60:
                    dq.popleft()
                if len(dq) >= 30:
                    if current_time - dq[0] > 60:
                        time.sleep(60-(current_time-dq[0]))
                    current_time = time.time()
                    while current_time - dq[0] > 60:
                        dq.popleft()
                dq.append(current_time)
                with open(image_content.get("image_path"), "rb") as f:
                     data = base64.b64encode(f.read()).decode("utf-8")

                messages = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": "data:image/jpeg;base64," + data
                                },
                            },
                            {"type": "text", "text": f"""这是一张图片，上文内容是{image_content.get("pre_content")}
                            下文内容是{image_content.get("suf_content")}，请用中文简要总结这张图片的摘要,字数在50字以内"""},
                        ],
                    },
                ],
                summary = llm.invoke(messages)
                image_summary_list.append(
                    {"summary":summary,
                     **image_content,}
                )
        except Exception("获取摘要异常") as e:
            logger.error(e)


        


if __name__ == '__main__':
    p = NodeMDImg2()
    init_state = {
        "md_path": r"D:\pojie\渊哥\hak180产品安全手册\hak180产品安全手册.md",
    }
    res = p(init_state)
