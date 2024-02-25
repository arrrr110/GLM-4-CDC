import os

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file

print(os.getenv("ZHIPU_API_KEY")) # 填写您自己的APIKey

