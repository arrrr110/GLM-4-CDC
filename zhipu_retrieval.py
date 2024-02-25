import zhipuai
from zhipuai import ZhipuAI
import json
import requests
zhipuai.api_key = "5c238273d3c113840d017c6b5a6b4ea8.JJ9dwAVQTwNP40rp"
client = ZhipuAI(api_key="5c238273d3c113840d017c6b5a6b4ea8.JJ9dwAVQTwNP40rp") # 填写您自己的APIKey

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


response = client.chat.completions.create(
    model="glm-4",  # 填写需要调用的模型名称
    messages=[
        {"role": "user", "content": "你好！你叫什么名字"},
    ],
    tools=[
            {
                "type": "retrieval",
                "retrieval": {
                    "knowledge_id": "1697526742801395712",
                    "prompt_template":"""从文档\n
                    '''\n
                    {{knowledge}}\n
                    '''\n
                    中找问题\n
                    '''\n
                    {{question}}\n
                    '''\n
                    的答案，找到答案就仅使用文档语句回答，找不到答案就用自身知识回答并告诉用户该信息不是来自文档。\n

                    不要复述问题，直接开始回答。"""
                }
            }
            ],
    stream=True,
)
for chunk in response:
    print(chunk.choices[0].delta)


# if __name__ == "__main__":
#     pass