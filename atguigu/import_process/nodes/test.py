""""
第二遍

"""
import shutil
import time
import zipfile
from pathlib import Path
from atguigu.config.config import MineruConfig
from atguigu.import_process.base import NodeBase
from atguigu.import_process.state import ImportGraphState
from atguigu.tool.logger import logger
import requests



# node_pdf_to_md
class NodePDFToMD2(NodeBase):
    name = "PDFToMD2"
    def process(self, state:ImportGraphState):
        # 获取pdf_path，路径文件检验
        pdf_path = state.get("pdf_path")
        if not pdf_path:
            logger.error("pdf_path is null")
            raise Exception("pdf_path is null")
        pdf_path_obj = Path(pdf_path)
        if not pdf_path_obj.exists():
            logger.error("pdf_path_obj is not exist")
            raise Exception("pdf_path is not exist")
        # 获取local_dir,路径文件检验，目录不存在创建
        local_dir = state.get("local_dir")
        if not local_dir:
            logger.error("local_dir must be get")
            raise Exception("local_dir must be get")
        local_dir_obj = Path(local_dir)
        if not local_dir_obj.exists():
            local_dir_obj.mkdir(parents=True, exist_ok=True)

        # 上传pdf文件到mineru，获取batch_id
        token = f"{MineruConfig.mineru_token}"
        url = "https://mineru.net/api/v4/file-urls/batch"
        header = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        data = {
            "files": [
                {"name": f"{pdf_path_obj.name}", "data_id": "abcd"}
            ],
            "model_version": "vlm"
        }
        file_path = [str(pdf_path_obj)]
        response = requests.post(url,headers=header,json=data)
        if response.status_code != 200:
            logger.error("Interface return exception")
            raise Exception("Interface return exception")
        res2=response.json()
        if res2["code"] != 0:
            logger.error("business return exception")
            raise Exception("business return exception")
        batch_id = res2["data"]["batch_id"]
        urls = res2["data"]["file_urls"]
        # 上传文件
        for i in range(0, len(urls)):
            with open(file_path[i], "rb") as f:
                res3 = requests.put(urls[i], data=f)
                if res3.status_code != 200:
                    logger.error("upload exception")
                    raise Exception("upload exception")
        logger.info("upload success")

        # 根据mineru官网轮询获取pdf解析成markdown压缩包的url
        max_time = 300
        total_time = 0
        while True:

            try:
                token = f"{MineruConfig.mineru_token}"
                batch_id = batch_id
                url = f"https://mineru.net/api/v4/extract-results/batch/{batch_id}"
                header = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}"
                }
                start_time=time.time()
                response = requests.get(url, headers=header)
                time.sleep(2)
                if response.status_code != 200:
                    logger.error("zip interface return exception")
                    raise Exception("zip interface return exception")
                res = response.json()
                if res["code"] != 0:
                    logger.error("zip business return exception")
                    raise Exception("zip business return exception")
                res2 = res["data"]["extract_result"][0]
                if res2["state"] != "done":
                    logger.error("decompression not completed or failed")
                    raise Exception("decompression not completed or failed")
                urls = res2["full_zip_url"]
                logger.info("decompression success")
                break
            except:
                end_time = time.time()
                total_time += end_time - start_time
                if total_time >= max_time:
                    raise Exception("time exceed")

        # 根据url下载markdown的压缩包
        response = requests.get(urls,timeout=100)
        if response.status_code != 200:
            logger.error("load interface return exception")
            raise Exception("load interface return exception")
        content = response.content
        zip_file_path_obj=local_dir_obj/f"{pdf_path_obj.stem}.zip"
        with open(zip_file_path_obj, "wb") as f:
            f.write(content)
        # 解压下载好地压缩包并改名
        unzip_file_path_obj=zipfile.ZipFile(zip_file_path_obj)
        unzip_file_path = local_dir_obj/f"{pdf_path_obj.stem}"
        if unzip_file_path.exists():
            shutil.rmtree(unzip_file_path)
        unzip_file_path.mkdir(parents=True, exist_ok=True)
        unzip_file_path_obj.extractall(unzip_file_path)
        origin_file_obj=unzip_file_path/"full.md"
        new_file_obj=unzip_file_path/f"{pdf_path_obj.stem}.md"
        origin_file_obj.rename(new_file_obj)
        with open(new_file_obj, "rb") as f:
            md_content = f.read()
        return {
            "md_path":new_file_obj,
            "md_content":md_content

        }







if __name__ == '__main__':
    p=NodePDFToMD2()
    init_state={"local_dir":r"D:\pojie\渊哥",
                "pdf_path":r"D:\pojie\渊哥\hak180产品安全手册.pdf"

    }
    res=p(init_state)
    print(res)
