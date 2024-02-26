import zhipuai
from zhipuai import ZhipuAI
import json  
from json_check import extract_outermost_json

import os
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file
zhipuai.api_key = os.getenv("ZHIPU_API_KEY")
client = ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY")) # 填写您自己的APIKey

# 流式调用
def get_completion_sse_from_messages(history, model="glm-4"):
    response = client.chat.completions.create(
    model=model,  # 填写需要调用的模型名称
    messages=history,
    stream=True,
    )
    print('sse', response)
    return response

# 同步调用

def get_completion(messages, model="glm-4"):
    response = client.chat.completions.create(
        model= model,  # 填写需要调用的模型名称
        messages=messages,
        tools=tools,
    )
    return response

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


# 使用模型生成的参数调用函数  迁移

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
    # print(age_list,age_num,age_dict)
    

## 定义处理 Function call 的函数：
def parse_function_call(model_response,messages):
    # 处理函数调用结果，根据模型返回参数，调用对应的函数。
    # 调用函数返回结果后构造tool message，再次调用模型，将函数结果输入模型
    # 模型会将函数调用结果以自然语言格式返回给用户。
    if model_response.choices[0].message.tool_calls:
        tool_call = model_response.choices[0].message.tool_calls[0]
        args = tool_call.function.arguments
        function_result = {}
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

# 检查是否触发函数   迁移
def get_function_result(model_response): 
    # 处理函数调用结果，根据模型返回参数，调用对应的函数。
    # 调用函数返回结果后构造tool message，再次调用模型，将函数结果输入模型
    # 模型会将函数调用结果以自然语言格式返回给用户。
    if model_response.choices[0].message.tool_calls:
        tool_call = model_response.choices[0].message.tool_calls[0]
        args = tool_call.function.arguments
        function_result = {}
        if tool_call.function.name == "get_milestone_question":
            function_result = get_milestone_question(**json.loads(args))
        # print('function_result:', function_result)
        return function_result
    else:
        return None
param = '123'
report = ''
tips = ''

# 对话背景切换


state_list = [
    {
        'state':'Age',
        'system_prompt':f"""你是一个儿童康复师Bot，为了开展CDC儿童早期发育评估，正在为家长登记信息。
你首先问候用户，然后只需要询问参与评估儿童的月龄，也就是从出生起到现在经历了几个月。
不要假设或猜测传入函数的参数值。如果用户的描述不明确，请要求用户提供必要信息。
""",
        'parameter':[]
    },
    {
        'state':'Scale',
        'system_prompt':f"""你是一个儿童康复师Bot，正在为儿童做问卷评估。
问卷的内容是（选项为“是"，“否”或“说不清”）：
```
{param}
```
请确保澄清所有选项、格式和内容，保证电子病历内容的合理性。
你的回复应该是简短的、极具对话性和友好的风格，不要涉及到JSON等机器语言。

你首先问候用户，然后一个一个问题的收集用户的反馈，不要一次发出所有问题。
你等待收集所有信息，然后进行总结并检查最后一次以确保顾客是否想改变其他东西。
最后，你仅以JSON格式输出所有的信息，除JSON以外不要有任何信息。

JSON信息包括：
月龄month_age
问卷记录table
""",
        'parameter':[]
    },
    {
        'state':'Report',
        'system_prompt':f"""你是一个儿童康复师Bot，已经获得用户的评估结果，正在对结果进行解读。
'''结果
{report}
'''
'''育儿指南
{tips}
'''
        """,
        'parameter':[]
    },
]

system_text = """你是一个儿童康复师Bot，正在为一名4月龄的儿童做问卷评估。
问卷的内容是（选项为“是"，“否”或“说不清”）：
```
社交/情感 ：# 自发地笑，引起您的注意\n# 当您逗宝宝时，宝宝会咯咯地笑（还不是大笑）\n# 看着您，做动作，或发出声音来吸引或保持您的注意力",
```
请确保澄清所有选项、格式和内容，保证电子病历内容的合理性。
你的回复应该是简短的、极具对话性和友好的风格，不要涉及到JSON等机器语言。

你首先问候用户，然后一个一个问题的收集用户的反馈，不要一次发出所有问题。
你等待收集所有信息，然后进行总结并检查最后一次以确保顾客是否想改变其他东西。
最后，你仅以JSON格式输出所有的信息，除JSON以外不要有任何信息。

JSON信息包括：
月龄month_age
问卷记录table

"""

json_test = {
  "社交/情感": {
    "离开后能平静下来": "是",
    "会注意到其他孩子并与他们一起玩耍": "是"
  },
  "语言/沟通": {
    "交谈时有至少两次来回交流": "是",
    "能回答‘谁’、‘什么’、‘哪里’或‘为什么’的问题": "是",
    "能描述图片或书中发生的事情": "是",
    "能说出自己的名字": "是",
    "大多数时候能和其他人很好地交流": "是"
  },
  "认知": {
    "能画圆圈": "是",
    "在提醒下不会去摸烫的东西": "是"
  },
  "运动/身体发育": {
    "能将物品串在一起": "是",
    "能自己穿一些衣服": "是",
    "会使用叉子": "是"
  }
}

'''
语言/沟通： "# 发出“喔”、“啊”（呀呀学语）等声音\n# 当您和宝宝说话时，宝宝会发出声音回应\n# 朝您声音的方向转头",
认知：  "# 如果饿了，宝宝看到乳房或奶瓶时会张开嘴\n# 会很有兴趣地看自己的手",
运动/身体发育：  "\n# 当您抱着宝宝时，宝宝不用支撑即可保持头部稳定\n# 当您把玩具放在宝宝手里时，宝宝会抓住玩具\n# 用手臂晃动玩具\n# 将手放在嘴巴里\n# 趴着时，尝试用手肘/前臂支起上身",

思路：
启动对话后，每轮校验是否触发AI函数，触发则调取工具函数，并切换状态；
每轮校验是否存在json内容，存在则强制触发AI函数，并切换状态

启动对话后：
每次res生成后，先筛选状态，在特定状态下检测res格式
- 初始状态（InitState）：用户输入孩子的月龄，激活相应的评估函数。
    该状态下进行月龄匹配，函数返回就近月龄资料（取低）
- 评估状态（AssessmentState）：AI通过对话方式对用户的孩子进行评估。
    该状态下进行res格式检测，出现json格式后配置对应的话术
- 报告状态（ReportState）：AI根据评估结果生成报告，并解释结果和提供科普信息。
    该状态下负责介绍评估结果、对应月龄科普以及推荐就医

关键词操作：重置状态和对话记录/reset
'''
if __name__ == "__main__":
    # 清空对话
    print("请输入内容（输入'exit'退出）: ")
    # 初始数据
    # state_map = ['Age', 'Scale', 'Report']
    State = 'Scale'
    messages = [{"role": "system", "content": ''}]
    result = ''
    if State == "Age":
        # 获取对应系统（背景）提示词
        system_prompt = """你是一个儿童康复师Bot，为了开展CDC儿童早期发育评估，正在为家长登记信息。
你首先问候用户，然后只需要询问参与评估儿童的月龄，也就是从出生起到现在经历了几个月。
不要假设或猜测传入函数的参数值。如果用户的描述不明确，请要求用户提供必要信息。
"""
        # print(system_prompt)
        messages[0] = {"role": "system", "content": system_prompt}
        messages.append({"role": "user", "content": '你好'})
        messages.append({"role": "assistant", "content": '好！为了进行CDC儿童早期发育评估，我需要先了解一下孩子的月龄。请问孩子从出生到现在经历了多少个月？如果不知道具体月数，也可以告诉我孩子的出生日期，我可以帮您计算。'})
        messages.append({"role": "user", "content": '1个月'})
        res = get_completion(messages)
        # print('step_0:', res)
        # 检查是否触发函数,触发则获取返回值
        result = get_function_result(res)
        # 触发函数，函数值加入对话队列，进入下一个状态
        if result:
            messages.append({
            "role": "tool",
            "content": f"{json.dumps(result)}",
            "tool_call_id":res.choices[0].message.tool_calls[0].id
            })
            State = 'Scale'
            # 修改系统提示词
            # new_system_prompt = next((x.format(param = param) for x in state_list if x['state'] == 'Scale'))['system_prompt']
            param = '社交/情感:' + result['Social/Emotional'] + '\n' + '语言/沟通:' + result['Language/Communication'] + '\n' + '认知:' + result['Cognitive'] + '\n' + '运动/身体发育:' + result['Movement/Physical']
            # 重新构建提示词
            new_system_prompt = f"""你是一个儿童康复师Bot，正在为儿童做问卷评估。
问卷的内容是（选项为“是"，“否”或“说不清”）：
```
{param}
```
请确保澄清所有选项、格式和内容，保证电子病历内容的合理性。
你的回复应该是简短的、极具对话性和友好的风格，不要涉及到JSON等机器语言。

你首先问候用户，然后一个一个问题的收集用户的反馈，不要一次发出所有问题。
你等待收集所有信息，然后进行总结并检查最后一次以确保顾客是否想改变其他东西。
最后，你仅以JSON格式输出所有的信息，除JSON以外不要有任何信息。

JSON信息包括：
月龄month_age
问卷记录table
"""
            # print(scale_text)
            # print(tips)
            messages[0] = {"role": "system", "content": new_system_prompt}
            print(new_system_prompt)
        else:
            messages.append(res.choices[0].message.model_dump())
    elif State == 'Scale':
        messages[0] = {"role": "system", "content": system_text}
        # messages.append({"role": "user", "content": '9月龄'})
        # messages.append({"role": "assistant", "content": '好！为了进行CDC儿童早期发育评估，我需要先了解一下孩子的月龄。请问孩子从出生到现在经历了多少个月？如果不知道具体月数，也可以告诉我孩子的出生日期，我可以帮您计算。'})
        messages.append({"role": "user", "content": '10个月'})
        messages.append({"role": "assistant", "content": '嗨！很高兴和您一起帮助宝宝进行评估。首先，我想了解宝宝在社交和情感方面的一些表现。请问，宝宝会自发地笑，来引起您的注意吗？是、否还是说不清？'})

        messages.append({"role": "user", "content": 'hello'})
        res = get_completion(messages)
        get_json = extract_outermost_json(res.choices[0].message.model_dump()['content'])
        if get_json:
            # print(get_json,type(get_json))
            json_dict = json.loads(get_json) # 转化成字典，条件语句外部，仍然可以引用
            # 循环遍历字典中的键值对
            report = json_dict + "您的选择全都为“是”，那么恭喜您的宝宝语言发育正沿着正常的轨迹稳步向前。"  
            for key, value in json_dict['table'].items():
                for ky, v in value.items(): # 遍历具体的问题及回答
                    if v != '是':  
                        # print(f"Key: {ky}, Value: {v}")
                        report = json_dict + "您的选择有“否/说不清”的情况，婴儿可能存在发育迟缓的风险，家长应高度警惕，建议联系医生进一步咨询，详细评估早期干预。"
                    else:
                        pass  
            # 切换状态
            State = 'Report'
            tips = result['Tips&Activities']             # 重新构建提示词
            new_system_prompt = f"""你是一个儿童康复师Bot，已经获得用户的评估结果，正在对结果进行解读。根据下面提供的信息回答问题，不要假设或猜测其他观点。
'''评估结果
{report}
'''
'''育儿指南
{tips}
'''
"""
            print('切换State to Report')
            # print(tips)
            messages[0] = {"role": "system", "content": new_system_prompt}
        else:
            print(res.choices[0].message.model_dump())
            messages.append(res.choices[0].message.model_dump())
    elif State == 'Report':
                # 示例文本  
        report = """  
        您的选择有“否/说不清”的情况，婴儿可能存在发育迟缓的风险，家长应高度警惕，建议联系医生进一步咨询，详细评估早期干预。
        {  
        "month_age": "4",  
        "table": {  
            "社交/情感": {  
            "自发地笑，引起您的注意": "是",  
            "当您逗宝宝时，宝宝会咯咯地笑（还不是大笑）": "是",  
            "看着您，做动作，或发出声音来吸引或保持您的注意力": "否"  
            }  
        }  
        }  
        """  
        tips = """对宝宝作出积极回应。在宝宝发出声音时，表现出兴奋，并对宝宝笑着说话。
        \n这会让宝宝学会互动交谈。
        \n在安全的情况下，让宝宝伸手去拿玩具、踢玩具，探索周围的事物。例如，将宝宝放在有\n安全玩具的毯子上。
        \n 允许宝宝将安全的东西放进嘴里去尝试。这就是婴儿的学习方式。比如，让宝宝看看、听听和触摸一些不锋利、不烫的大块（避免吞食导致窒息）物品。
        \n 对宝宝说话，给宝宝读书和唱歌。这将有助于宝宝将来学习说话和理解词汇。
        \n 仅在与亲人视频通话时使用屏幕设备（电视、手机、平板电脑等）。2 岁以下的儿童不建议使用屏幕设备。婴儿通过与他人交谈、玩耍和互动来学习。
        \n 只给宝宝喂母乳或配方奶。6 个月内的婴儿还不可以吃其他食物、水或其他饮料。\n 给宝宝一些安全的、容易拿的玩具，如摇铃或适合宝宝年龄的彩图布书。
        \n 让宝宝在一天中有时间活动，与人和物体互动。尽量不要让宝宝在秋千、婴儿车或摇椅上呆得太久。
        \n 有规律的睡眠和喂养。
        \n 让宝宝仰卧，给宝宝看颜色鲜艳的玩具。从左到右、从上到下慢慢移动玩具，看看宝宝是否注意到玩具的移动。
        \n 在您帮助宝宝“锻炼”（活动身体）的几分钟内，给宝宝唱歌并和宝宝说话。轻轻弯曲并上下移动宝宝的手臂和腿部。""",# 重新构建提示词
        new_system_prompt = f"""你是一个儿童康复师Bot，系统已经返回了用户的的评估结果。请你根据下面提供的信息回答问题，不要假设或猜测其他观点。
'''评估结果
{report}
'''
'''育儿指南
{tips}
'''
你的回复应该是简短的、极具对话性和友好的风格。
"""
        messages[0] = {"role": "system", "content": new_system_prompt}
        # messages.append({"role": "user", "content": '9月龄'})
        # messages.append({"role": "assistant", "content": '好！为了进行CDC儿童早期发育评估，我需要先了解一下孩子的月龄。请问孩子从出生到现在经历了多少个月？如果不知道具体月数，也可以告诉我孩子的出生日期，我可以帮您计算。'})
        # messages.append({"role": "user", "content": '10个月'})
        messages.append({"role": "user", "content": '评估结果是什么？'})
        messages.append({"role": "assistant", "content": '根据您提供的评估结果，宝宝在社交/情感方面可能存在一些发育迟缓的风险。宝宝能够自发地笑并回应您的逗弄，但在吸引或保持您的注意力方面还没有表现出相应的行为。这提示我们宝宝可能需要更多的互动来促进社交技能的发展。建议您联系医生进行更详细的评估，并考虑早期干预的措施。同时，您可以按照育儿指南中的建议，通过积极的互动和回应，帮助宝宝提高社交能力。如果您有任何疑问或需要帮助，请随时告诉我。'})
        messages.append({"role": "user", "content": '平时我应该怎么做？'})
        
        res = get_completion(messages)
        print(res)



    # while True:  
    #     user_input = input()  
    #     if user_input.lower() == 'exit':  
    #         break  
    #     else:
    #         # 状态校验
    #         if State == "Age":
    #             # 获取对应系统（背景）提示词
    #             system_prompt = next((x for x in state_list if x['state'] == 'Age'))['system_prompt']
    #             # print(system_prompt)
    #             messages[0] = {"role": "system", "content": system_prompt}
    #             messages.append({"role": "user", "content": user_input})
    #             res = get_completion(messages)
    #             print('step_0:', res.choices[0].message.model_dump()['content'])
    #             if res.choices[0].message.tool_calls:
    #                 res_2 = parse_function_call(res,messages)
    #                 messages.append(res_2)
    #             else:
    #                 messages.append(res)
                    
                
    #         elif State == 'Scale':
    #             pass
    #         elif State == 'Report':
    #             pass
    #         else:
    #             pass  
            # messages.append({"role": "user", "content": user_input})
            # response = client.chat.completions.create(
            #     model="glm-4",  # 填写需要调用的模型名称
            #     messages=messages,
            #     tools=tools,
            #     # 强制触发某函数
            #     # tool_choice={"type": "function", "function": {"name": "get_ticket_price"}},
            #     tool_choice=None,
            # )
            # text = response.choices[0].message.model_dump()['content']

            # print('step_0:', response.choices[0].message.model_dump()['content'])
            # messages.append(response.choices[0].message.model_dump())
            #   # 提取JSON数据  
            # json_data = extract_outermost_json(text)  
            # if json_data:  
            #     print("Extracted JSON:")  
            #     print(json.loads(json_data))  
            #     # print(type(json_data))  
            #     # print(type(json.loads(json_data)))  
            # else:  
            #     print("No complete JSON found.")


    
    print("程序已退出。")



# 核心业务类构建


