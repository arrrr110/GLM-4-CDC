import zhipuai
from zhipuai import ZhipuAI

import os
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file
zhipuai.api_key = os.getenv("ZHIPU_API_KEY")
client = ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY")) # 填写您自己的APIKey
# 异步调用
def get_completion_sse(prompt, model="glm-4"):
    response = zhipuai.model_api.sse_invoke(
        model= model,
        prompt=[
            {"role": "user", "content": prompt},
        ],
        temperature=0.95,
        top_p=0.7,
        incremental=True
    )
    return response.events()

# for event in response.events():
#   if event.event == "add":
#       print(event.data)
#       print("*"*10)
#   elif event.event == "error" or event.event == "interrupted":
#       print(event.data)
#   elif event.event == "finish":
#       print(event.data)
#       print(event.meta)
#   else:
#       print(event.data)
# 同步调用

def get_completion(prompt, model="glm-4"):
    response = client.chat.completions.create(
        model= model,  # 填写需要调用的模型名称
        messages=[
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    # web_search
    response = client.chat.completions.create(
        model="glm-4",  # 填写需要调用的模型名称
        messages=[
                {"role": "user", "content": "请告诉我上海新华医院儿童发育保健科主任李斐的信息"},
            ],
        tools=[
            {
                "type":"web_search",
                "web_search":{
                    "enable": True,
                }
            }
        ],
    )
    print(response.choices[0].message)