# atguigu/import_process/nodes/node_document_split.py
import re
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic_core.core_schema import none_schema

from atguigu.import_process.base import NodeBase
from atguigu.import_process.state import ImportGraphState
from atguigu.tool.json_format_tool import json_format
from atguigu.tool.logger import logger


class NodeDocumentSplit(NodeBase):
    """
    文档切分节点：智能文档切片
    """

    name = "node_document_split"

    def process(self, state: ImportGraphState):
        # check path
        md_path = state.get("md_path")
        if not md_path:
            logger.error("file path not exist")
            raise ValueError("file path not exist")
        md_path_obj = Path(md_path)
        if not md_path_obj.exists():
            logger.error("file  not exist")
            raise ValueError("file  not exist")
        file_title = state.get("file_title")
        if not file_title:
            logger.error("file title not exist")
            raise ValueError("file title not exist")
        # 提出内容并统一换行符
        with open(md_path_obj, "r", encoding="utf-8") as f:
            md_content = f.read()
        md_content = md_content.replace("\r\n","\n").replace("\r","\n")
        # 切成一行一行
        md_line_list = md_content.split("\n")
        # 找到标题,合并之前的.
        title_pattern = r'^\s*#{1,6}\s+.+'
        # 判断是否是代码块
        code_pattern = r"^(`{3,}|~{3,})"
        in_code_mark = False
        md_chunk_list = []
        current_index = 0
        for ind,md_line in enumerate(md_line_list):
            md_line = md_line.strip()
            code_match = re.match(code_pattern, md_line)
            # 代码围栏判断
            if code_match:
                marker = code_match.group(1)
                if not in_code_mark:
                    in_code_mark = True
                    code_title = marker
                    logger.info("进入到代码块围栏")

                if marker == code_title:
                    in_code_mark = False
                    code_title = None
                    logger.info("代码围栏结束")

            if not in_code_mark and re.match(title_pattern, md_line):
                md_chunk = md_line_list[current_index:ind]
                content = "\n".join(md_chunk)
                current_index = ind
                md_chunk_list.append({
                    "content": content,
                    "file_title": file_title,
                    "title": md_chunk[0] if content.startswith("#") else "神了",

                })
        last_md_line = md_line_list[current_index:]
        md_chunk_list.append({
            "content": "\n".join(last_md_line),
            "file_title": file_title,
            "title": last_md_line[0],
        })

#         细切(长切断合)
        max_size = 300
        spliter= RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", "。", "！", "？", "；", ".", "!", "?", ";", " "],
            chunk_size=max_size,
            chunk_overlap=50,
            length_function=len,
            add_start_index=False,
        )
        end_md_chunk_list = []
        for chunk in md_chunk_list:
            title = chunk["title"]
            content = chunk["content"]
            file_title = chunk["file_title"]
            real_content = content[len(title)+2:] if content.startswith("#") else content
            if len(real_content) <= max_size:
                end_md_chunk_list.append({
                    **chunk,
                    "part":0
                })
                continue
            if "<table>" in real_content:
                end_md_chunk_list.append({
                    **chunk,
                    "part":0
                })
                continue
            split_content_list = spliter.split_text(real_content)
            for index,split_content in enumerate(split_content_list):
                end_md_chunk_list.append({
                    **chunk,
                    "part":index+1,
                    "content":title+"\n\n"+split_content,
                })
        with open(r'D:\pojie\渊哥\hak180产品安全手册\chunk.json', "w", encoding="utf-8") as f:
            f.write(json_format(end_md_chunk_list))
        return {
            "chunks": end_md_chunk_list,
        }


if __name__ =="__main__":
    p = NodeDocumentSplit()
    init_state={
        "md_path": r"D:\pojie\渊哥\hak180产品安全手册\hak180产品安全手册_new.md",
        "file_title":"hak180产品安全手册"

    }
    p(init_state)
