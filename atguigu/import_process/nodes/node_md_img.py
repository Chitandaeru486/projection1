# atguigu/import_process/nodes/node_md_img.py
import base64
import re
import time
from collections import deque
from os import listdir
from pathlib import Path
from langchain.chat_models import init_chat_model
from atguigu.config.config import LLMConfig
from atguigu.import_process.base import NodeBase
from atguigu.import_process.state import ImportGraphState
from atguigu.tool.json_format_tool import json_format
from atguigu.tool.logger import logger


class NodeMDImg(NodeBase):
    """
    MarkDown图片处理节点：多模态图片理解
    """

    name = "node_md_img"

    def process(self, state: ImportGraphState):
        md_path = state.get('md_path')
        if md_path is None:
            logger.error("路径不存在")
            raise Exception('路径不存在')
        md_path_mdj = Path(md_path)
        if not md_path_mdj.exists():
            logger.error('路径文件不存在')
            raise Exception('路径文件不存在')
        with md_path_mdj.open('r', encoding='utf-8') as f:
            md_content = f.read()
        image_path_obj = Path(md_path_mdj.parent / 'images')
        if not image_path_obj.exists():
            logger.warning('图像路径文件不存在,跳过')
            return {
                "md_content": md_content,
            }
        image_name_list =listdir(image_path_obj)
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
            start, end = match.span()
            pre_content = md_content[max(start-300,0):start]
            suf_content = md_content[end:min(end+300,len(md_content))]
            image_context_list.append({
                "pre_content": pre_content,
                "suf_content": suf_content,
                "image_name": image_name,
                "image_path": str(md_path_mdj.parent / "images" / f'{image_name}'),
            })

        llm=init_chat_model(
            model= LLMConfig.VL_MODEL,
            model_provider="openai",
            base_url=LLMConfig.OPEN_BASE_URL,
            api_key=LLMConfig.OPEN_API_KEY,
            temperature=float(LLMConfig.LLM_DEFAULT_TEMPERATURE)
        )
        image_summary_list = []

        # 设置滑动门限制频率
        # 设置双向队列
        dq=deque(maxlen=30)
        # 获取每个图片对应的上下文和图内容
        for image_context in image_context_list:
            current_time = time.time()
            # 清理过期时间戳
            while dq and current_time - dq[0]>60:
                dq.popleft()
            # 判断队列是否是满的，满则等待
            if len(dq)>dq.maxlen:
                wait_time = 60-(current_time - dq[0])
                if wait_time>0:
                    time.sleep(wait_time)
                current_time = time.time()
                while dq and current_time-dq[0]>60:
                    dq.popleft()
            dq.append(current_time)
            with open(image_context.get("image_path"),'rb') as f:
                encode_data=base64.b64encode(f.read()).decode("utf-8")
                # print(encode_data)
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "data:image/jpeg;base64,"+encode_data
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
                "summary":res.content

            })

            logger.info(json_format(image_summary_list))









        logger.info("成功执行")


        # image_list


if __name__ == '__main__':
    p = NodeMDImg()
    init_state = {
        "md_path": r"D:\pojie\渊哥\hak180产品安全手册\hak180产品安全手册.md",
    }
    res = p(init_state)
    print(res)