from zhipuai import ZhipuAI
import json

import os
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file

client = ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY")) # 填写您自己的APIKey
# 异步调用
def get_completion_sse_from_messages(history, model="glm-4"):
    response = client.chat.completions.create(
    model=model,  # 填写需要调用的模型名称
    messages=history,
    stream=True,
    )
    print('sse', response)
    return response

# assistant_text = ''
# for chunk in response:
#     # print(chunk.choices[0].delta.content)
#     assistant_text += chunk.choices[0].delta.content
#     message_placeholder.markdown(assistant_text)
# 同步调用

def get_completion(prompt, model="glm-4"):
    response = client.chat.completions.create(
        model= model,  # 填写需要调用的模型名称
        messages=[
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_flight_number",
            "description": "根据始发地、目的地和日期，查询对应日期的航班号",
            "parameters": {
                "type": "object",
                "properties": {
                    "departure": {
                        "description": "出发地",
                        "type": "string"
                    },
                    "destination": {
                        "description": "目的地",
                        "type": "string"
                    },
                    "date": {
                        "description": "日期",
                        "type": "string",
                    }
                },
                "required": [ "departure", "destination", "date" ]
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_ticket_price",
            "description": "查询某航班在某日的票价",
            "parameters": {
                "type": "object",
                "properties": {
                    "flight_number": {
                        "description": "航班号",
                        "type": "string"
                    },
                    "date": {
                        "description": "日期",
                        "type": "string",
                    }
                },
                "required": [ "flight_number", "date"]
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_wheather_stat",
            "description": "查询天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "description": "城市",
                        "type": "string",
                    },
                    "date": {
                        "description": "日期",
                        "type": "string",
                    }
                },
                "required": ["city", "date"]
            },
        }
    },
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

# 对话背景切换
completion_state = [
    {
        'state':'STATE_A',
        'system_prompt':f"""你是一个儿童康复师Bot，为了开展CDC儿童早期发育评估，正在为家长登记信息。
你首先问候用户，然后收集用户信息。
然后你要询问参与评估儿童的月龄，也就是从出生起到现在经历了几个月
""",
        'parameter':[]
    },
    {
        'state':'STATE_B',
        'system_prompt':f"""""",
        'parameter':[]
    },
    {
        'state':'STATE_C',
        'system_prompt':f"""""",
        'parameter':[]
    },
]

# 使用模型生成的参数调用函数
## 将所需的函数实现
# def get_flight_number(date:str , departure:str , destination:str):
#     flight_number = {
#         "北京":{
#             "上海" : "1234",
#             "广州" : "8321",
#         },
#         "上海":{
#             "北京" : "1233",
#             "广州" : "8123",
#         }
#     }
#     return { "flight_number":flight_number[departure][destination] }

# def get_ticket_price(date:str , flight_number:str):
#     return {"ticket_price": "1000"}


def find_closest_smaller_or_equal(arr:list, target:int):
   start, end = 0, len(arr) - 1
   closest_index = None  # 记录小于等于目标的最接近元素的索引
 
   while start <= end:
       mid = start + (end - start) // 2
 
       if arr[mid] <= target:
           # 当前元素小于等于目标，记录当前索引，并向右移动
           closest_index = mid
           start = mid + 1
       else:
           # 当前元素大于目标，向左移动
           end = mid - 1
 
   # 如果没有找到小于等于目标整数的元素，返回None或者数组的起始元素
   return arr[closest_index] if closest_index is not None else None
 
# 示例
# arr = [1, 3, 5, 7, 8, 9, 10]
# target = 6
# print(find_closest_smaller_or_equal(arr, target))  # 输出应为5


def get_milestone_question(age_of_month:str ):
    with open("GLM-4\cdc_data.json", "r", encoding='utf-8') as f:
        milestone_list = json.load(f)  
    
    age_list = [int(x['age_month']) for x in milestone_list]
    age_num = find_closest_smaller_or_equal(age_list, int(age_of_month))
    print('age:', age_num, age_of_month)
    # 匹配对应的月龄
    if age_num:
        age_dict = next((item for item in milestone_list if int(item['age_month']) == age_num))
    else: # 月龄太低则直接采用2月龄内容
        age_dict = next((item for item in milestone_list if int(item['age_month']) == 2))
    return age_dict


# 真实天气坐标

# def get_point(departure:str):
#     beijing = {'name':'北京', 'point': [116.46,39.92]}
#     shanghai = {'name':'上海', 'point': [121.48,31.22]}
#     tianjin = {'name':'天津', 'point': [117.2,39.13]}
#     wheather_map = [beijing, shanghai, tianjin]
#     # print([city for city in wheather_map if city['name'] == departure][0]['point'])
#     return [city for city in wheather_map if city['name'] == departure][0]['point']
    

# def get_wheather_stat(date:str ,city:str='北京'):
#     token = '6ebc4e352681160b2e6125e0c3dc6482'
#     point = get_point(city)
#     # 创建一个请求对象  
#     response = requests.get('https://api.open.geovisearth.com/weather/v1/fixed_point_forecast?token={}&point={}'.format(token, str(point[0])+','+str(point[1])))  
#     # 检查请求是否成功  
#     if response.status_code == 200:  
#         # 处理成功的响应  
#         data = response.json()  
#         print(data['data']['2T_instant']['data'])  
#         return {'pm': data['data']['calculationPM'][0]['pm'], 'temperature': data['data']['2T_instant']['data']}
#     else:  
#         # 处理失败的响应  
#         print(f"请求失败，状态码：{response.status_code}")
## 定义处理 Function call 的函数：
def parse_function_call(model_response,messages):
    # 处理函数调用结果，根据模型返回参数，调用对应的函数。
    # 调用函数返回结果后构造tool message，再次调用模型，将函数结果输入模型
    # 模型会将函数调用结果以自然语言格式返回给用户。
    if model_response.choices[0].message.tool_calls:
        tool_call = model_response.choices[0].message.tool_calls[0]
        args = tool_call.function.arguments
        function_result = {}
        # if tool_call.function.name == "get_flight_number":
        #     function_result = get_flight_number(**json.loads(args))
        # if tool_call.function.name == "get_ticket_price":
        #     function_result = get_ticket_price(**json.loads(args))
        # if tool_call.function.name == "get_wheather_stat":
        #     function_result = get_wheather_stat(**json.loads(args))
        if tool_call.function.name == "get_milestone_question":
            function_result = get_milestone_question(**json.loads(args))
        messages.append({
            "role": "tool",
            "content": f"{json.dumps(function_result)}",
            "tool_call_id":tool_call.id
        })
        response = client.chat.completions.create(
            model="glm-4",  # 填写需要调用的模型名称
            messages=messages,
            tools=tools,
        )
        print('step_1:', response.choices[0].message.model_dump())
        # messages.append(response.choices[0].message.model_dump())
        return response.choices[0].message.model_dump()


def parse_function_call_sse(model_response,messages):
    # 处理函数调用结果，根据模型返回参数，调用对应的函数。
    # 调用函数返回结果后构造tool message，再次调用模型，将函数结果输入模型
    # 模型会将函数调用结果以自然语言格式返回给用户。
    if model_response.choices[0].delta.tool_calls:
        tool_call = model_response.choices[0].delta.tool_calls[0]
        args = tool_call.function.arguments
        function_result = {}
        # if tool_call.function.name == "get_flight_number":
        #     function_result = get_flight_number(**json.loads(args))
        # if tool_call.function.name == "get_ticket_price":
        #     function_result = get_ticket_price(**json.loads(args))
        # if tool_call.function.name == "get_wheather_stat":
        #     function_result = get_wheather_stat(**json.loads(args))
        if tool_call.function.name == "get_milestone_question":
            function_result = get_milestone_question(**json.loads(args))
        messages.append({
            "role": "tool",
            "content": f"{json.dumps(function_result)}",
            "tool_call_id":tool_call.id
        })
        response = client.chat.completions.create(
            model="glm-4",  # 填写需要调用的模型名称
            messages=messages,
            tools=tools,
        )
        print('step_1:', response.choices[0].message.model_dump())
        # messages.append(response.choices[0].message.model_dump())
        return response.choices[0].message.model_dump()



if __name__ == "__main__":
    # get_milestone_question('2')
    # 清空对话
    messages = []
    
    # test
    messages.append({"role": "system", "content": "不要假设或猜测传入函数的参数值。如果用户的描述不明确，请要求用户提供必要信息"})
    # messages.append({"role": "system", "content": "使用外部 API 查询天气信息的功能。请根据用户的请求，调用相应的天气服务 API ，获取并展示最新的天气信息，包括温度、湿度、天气状况（如晴、雨等），风速和风向。例如，当用户询问‘北京今天的天气如何？’时，应调用API获取北京当前的天气数据，并以用户友好的方式展示结果。"})
    messages.append({"role": "user", "content": "帮我查询2岁的内容"})
    # messages.append({"role": "user", "content": "你能做什么？"})
    # messages.append({"role": "user", "content": "帮我查询2024年1月20日1234航班的票价"})
    # messages.append({"role": "assistant", "content": "北京今天的天气情况是晴天。"})
    # messages.append({"role": "user", "content": "1234航班的价格是多少？"})

    response = client.chat.completions.create(
        model="glm-4",  # 填写需要调用的模型名称
        messages=messages,
        tools=tools,
        # 强制触发某函数
        # tool_choice={"type": "function", "function": {"name": "get_ticket_price"}},
        # tool_choice=None,
        stream=True,
    )
    func_obj = ''
    # print('res:',response)
    for chunk in response:
        print('func test',chunk)
        if chunk.choices[0].delta.tool_calls:
            print('tools:',chunk.choices[0].delta.tool_calls)
            func_obj = chunk
        else:
            pass
    # print('step_0:', response.choices[0].message.model_dump())
    # messages.append(response.choices[0].message.model_dump())

    res = parse_function_call_sse(func_obj,messages)
    # messages.append(res)
    # get_wheather_stat(token)
    print('***'*10)
    # # print('mesgs:',messages)
    # get_point('北京')
