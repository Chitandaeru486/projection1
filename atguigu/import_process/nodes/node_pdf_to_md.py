# atguigu/import_process/nodes/node_pdf_to_md.py
import shutil
import time
from pathlib import Path
from typing import Any
from zipfile import ZipFile
from atguigu.config.config import MineruConfig, MinioClientConfig
from atguigu.import_process.base import NodeBase
from atguigu.import_process.state import ImportGraphState
from atguigu.tool import creat_minio_client
from atguigu.tool.logger import logger
import requests


class NodePDFToMD(NodeBase):
    """
    PDF 转 Markdown 节点：PDF结构化解析
    """

    name = "node_pdf_to_md"

    def process(self, state: ImportGraphState):
        # 判断路径
        pdf_path=state.get("pdf_path")
        pdf_path_file_obj=Path(pdf_path)
        # 判断路劲正确
        local_dir_obj = self.check_path(pdf_path, pdf_path_file_obj, state)
        # 获取batch_id
        batch_id, total_time, urls = self.submmit_file(pdf_path_file_obj)
        # 获取下载地址url
        urls = self.zip_url(batch_id, total_time, urls)
        # 解压压缩包并改名
        unzip_file_path_obj, zip_file_obj = self.load_unzip(local_dir_obj, pdf_path_file_obj, urls)

        return self.md_file(pdf_path_file_obj, unzip_file_path_obj, zip_file_obj)

    def md_file(self, pdf_path_file_obj: Path, unzip_file_path_obj: Path,
                zip_file_obj: ZipFile) -> dict[str, Path | str]:
        unzip_file_path_obj.mkdir(parents=True, exist_ok=True)
        zip_file_obj.extractall(unzip_file_path_obj)
        start_md_path_obj = unzip_file_path_obj / 'full.md'
        new_md_path_obj = unzip_file_path_obj / f'{pdf_path_file_obj.stem}.md'
        start_md_path_obj.rename(new_md_path_obj)
        with open(new_md_path_obj, "r", encoding="utf-8") as f:
            md_content = f.read()
        return {
            "md_path": new_md_path_obj,
            "md_content": md_content
        }

    def load_unzip(self, local_dir_obj: Path, pdf_path_file_obj: Path, urls) -> tuple[Path, ZipFile]:
        response = requests.get(urls, timeout=120)
        if response.status_code != 200:
            logger.error("网络接口2请求失败")
            raise Exception("网络接口2请求失败")
        content = response.content
        zip_file_path_obj = local_dir_obj / f"{pdf_path_file_obj.stem}.zip"
        with open(zip_file_path_obj, "wb") as f:
            f.write(content)
        logger.info("下载压缩包成功")
        import zipfile
        zip_file_obj = zipfile.ZipFile(zip_file_path_obj)
        unzip_file_path_obj = local_dir_obj / f'{pdf_path_file_obj.stem}'
        if unzip_file_path_obj.exists():
            shutil.rmtree(unzip_file_path_obj)
        return unzip_file_path_obj, zip_file_obj

    def zip_url(self, batch_id: str | Any, total_time: int, urls) -> Any:
        while True:
            token = f'{MineruConfig().mineru_token}'
            batch_id = f'{batch_id}'
            url = f"https://mineru.net/api/v4/extract-results/batch/{batch_id}"
            header = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }

            max_time = 300

            try:
                start_time = time.time()
                res = requests.get(url, headers=header)
                time.sleep(2)
                if res.status_code != 200:
                    logger.error("网络接口请求失败")
                    raise Exception("网络接口请求失败")
                result = res.json()
                if result["code"] != 0:
                    logger.error("查询batch任务失败")
                    raise Exception('查询batch任务失败')
                date = result["data"]
                if date["extract_result"][0]["state"] != "done":
                    logger.error("解析失败")
                    raise Exception("解析失败")
                urls = date["extract_result"][0]["full_zip_url"]
                print(f'成功获取{urls}')
                break
            except Exception as err:
                print(err)
                logger.error("请求数据失败")
                end_time = time.time()
                total_time += end_time - start_time
                if total_time > max_time:
                    logger.error("请求超时")
                    raise Exception("请求超时")
            continue
        return urls

    def submmit_file(self, pdf_path_file_obj: Path) -> tuple[Any, int, Any]:
        token = f'{MineruConfig().mineru_token}'
        url = "https://mineru.net/api/v4/file-urls/batch"
        header = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        data = {
            "files": [
                {"name": f"{pdf_path_file_obj.name}", "data_id": "abcd"}
            ],
            "model_version": "vlm"
        }
        file_path = [str(pdf_path_file_obj)]
        response = requests.post(url, headers=header, json=data)
        if response.status_code != 200:
            logger.error("上传请求失败")
            raise Exception("上传请求失败")
        result = response.json()
        if result["code"] != 0:
            logger.error("mineru返回错误")
            raise Exception("mineru返回错误")
        batch_id = result["data"]["batch_id"]
        urls = result["data"]["file_urls"]
        for i in range(0, len(urls)):
            with open(file_path[i], "rb") as f:
                res_upload = requests.put(urls[i], data=f)
                if res_upload.status_code != 200:
                    logger.error("上传文件失败")
                else:
                    logger.info("上传文件成功")
        total_time = 0
        return batch_id, total_time, urls

    def check_path(self, pdf_path: str, pdf_path_file_obj: Path, state: ImportGraphState) -> Path:
        if pdf_path is None:
            logger.error("目标路径不存在")
            raise ValueError("目标路径不存在")
        if not pdf_path_file_obj.exists():
            logger.error("目标文件不存在")
            raise ValueError("目标文件不存在")

        local_dir = state.get("local_dir")
        if local_dir is None:
            logger.error("必须指定一个本地路径")
            raise ValueError("必须指定一个本地路径")
        local_dir_obj = Path(local_dir)
        if not local_dir_obj.exists():
            local_dir_obj.mkdir(parents=True, exist_ok=True)
        return local_dir_obj


if __name__ == '__main__':
    p=NodePDFToMD()
    init_state={"local_dir":r"D:\pojie\渊哥",
                "pdf_path":r"D:\pojie\渊哥\hak180产品安全手册.pdf"

    }
    res=p(init_state)
    print(res)


