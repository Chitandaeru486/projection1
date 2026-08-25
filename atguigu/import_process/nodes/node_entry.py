from os.path import exists
from pathlib import Path

from atguigu.import_process.base import NodeBase
from atguigu.import_process.state import ImportGraphState
from atguigu.tool.logger import logger


class NodeEntry(NodeBase):
    name = "node_entry"
    def process(self,state:ImportGraphState):
        local_file_path=state["local_file_path"]
        if local_file_path is None:
            logger.error("目标路径不存在")
            raise Exception("目标路径不存在")
        local_file_path_obj=Path(local_file_path)
        if not local_file_path_obj.exists():
            logger.error("目标文件不存在")
            raise ValueError("目标文件不存在")
        file_title=local_file_path_obj.stem
        file_suffix=local_file_path_obj.suffix
        if file_suffix.lower() == ".md":
            return {
                "is_md_read_enabled":True,
                "file_title":file_title,
                "md_path":str(local_file_path_obj)
            }
        elif file_suffix.lower() == ".pdf":
            return {
                "is_pdf_read_enabled":True,
                "file_title":file_title,
                "pdf_path":str(local_file_path_obj)
            }
        else:
            logger.error('文件格式错误')
            raise ValueError('  文件格式错误')

if __name__ == '__main__':
    p=NodeEntry()
    init_state_path={
        "local_file_path":r"D:\pojie\渊哥\hak180产品安全手册.pdf"
    }
    res=p(init_state_path)
    print(res)

