import json
from zhipuai import ZhipuAI

client = ZhipuAI(api_key="5c238273d3c113840d017c6b5a6b4ea8.JJ9dwAVQTwNP40rp") # 请填写您自己的APIKey

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_milestone_question",
            "description": "根据儿童月龄查询里程碑，每12个月龄为1周岁",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "age_of_month": "月龄",
                        "type": "string",
                    }
                },
                "required": ["age_of_month"]
            },
        }
    },
]

def get_milestone_question(age_of_month:str ):
    with open("GLM-4\cdc_data.json", "r", encoding='utf-8') as f:
        milestone_list = json.load(f)  
    print(milestone_list[0], type(milestone_list[0]))
    # obj = find_milestone_info(milestone_list, age_of_month)
    # 匹配对应的月龄
    obj = (item for item in milestone_list if item['age_month'] == age_of_month) # 得到一个生成器对象,已经不是dict了

    print(obj)
    return {"milestone_info": obj}


response = client.chat.completions.create(
    model="glm-4",  # 填写需要调用的模型名称
    messages=[
        {"role": "system", "content": "你是一个乐于解答各种问题的助手，你的任务是为用户提供专业、准确、有见地的建议。"},
        # {"role": "user", "content": "我对太阳系的行星非常感兴趣，特别是土星。请提供关于土星的基本信息，包括其大小、组成、环系统和任何独特的天文现象。"},
        {"role": "user", "content": "孩子9个月了。"},
    ],
    tools=tools,
    # stream=True,
)

print(response)
# for chunk in response:
#     print(chunk)