import os

import dotenv

dotenv.load_dotenv()
class Config:
    mineru_token=os.getenv("MINERU_TOKEN")