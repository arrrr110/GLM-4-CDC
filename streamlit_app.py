from zhipuai import ZhipuAI
import json
import streamlit as st
import os
# from transformers import AutoModel, AutoTokenizer
from json_check import extract_outermost_json

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file

client = ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY")) # 填写您自己的APIKey

# 基本接口工具
# 流式调用
def get_completion_sse_from_messages(history, model="glm-4"):
    response = client.chat.completions.create(
    model=model,  # 填写需要调用的模型名称
    messages=history,
    temperature = 0.01,
    tools=tools,
    stream=True,
    )
    return response

# 同步调用
# @st.cache_resource
def get_completion(prompt, model="glm-4"):
    response = client.chat.completions.create(
        model= model,  # 填写需要调用的模型名称
        messages=[
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content

def get_completion_from_messages(history, model="glm-4"):
    response = client.chat.completions.create(
        model= model,  # 填写需要调用的模型名称
        messages=history,
    )
    return response.choices[0].message.content

## 产品数据
# 对话背景状态参数


# 工具函数注册
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_milestone_question",
            "description": "根据儿童月龄查询里程碑，月龄是按月计算的年龄。",
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

## AI工具函数调用
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
    with open("cdc_data.json", "r", encoding='utf-8') as f:
        milestone_list = json.load(f)  

    age_list = [int(x['age_month']) for x in milestone_list]
    age_num = find_closest_smaller_or_equal(age_list, int(age_of_month))
    # 匹配对应的月龄
    if age_num:
        age_dict = next((item for item in milestone_list if int(item['age_month']) == age_num))
    else: # 月龄太低则直接采用2月龄内容
        age_dict = next((item for item in milestone_list if int(item['age_month']) == 2))
    return age_dict

## 定义处理 Function call 的函数：
# 检查是否触发函数   
def get_function_result(model_response): 
    # 处理函数调用结果，根据模型返回参数，调用对应的函数。
    # 调用函数返回结果后构造tool message，再次调用模型，将函数结果输入模型
    # 模型会将函数调用结果以自然语言格式返回给用户。
    if model_response.choices[0].delta.tool_calls:
        tool_call = model_response.choices[0].delta.tool_calls[0]
        args = tool_call.function.arguments
        function_result = {}
        if tool_call.function.name == "get_milestone_question":
            function_result = get_milestone_question(**json.loads(args))
        # print('function_result:', function_result)
        return function_result
    else:
        print('No function result Found!')
        return None

def parse_function_call_sse(model_response,messages):
    if model_response.choices[0].delta.tool_calls:
        tool_call = model_response.choices[0].delta.tool_calls[0]
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

st.set_page_config(
    page_title="ChatGLM3-glm-4 Simple Demo",
    page_icon=":robot:",
    layout="wide"
)

# 初始状态：Age

system_prompt = """不要假设或猜测传入函数的参数值。如果用户的描述不明确，请要求用户提供必要信息
你是一个儿童康复师Bot，为了开展CDC儿童早期发育评估，
首先告诉用户这是一个CDC儿童早期发育评估，然后询问参与评估儿童的月龄，除此之外不要和用户聊别的。
"""

if "history" not in st.session_state:
    st.session_state.state = 'Age'
    st.session_state.history = [{"role": "system", "content": system_prompt }]
    # print(system_prompt)
if "result" not in st.session_state:
    st.session_state.result = None

# buttonClean = st.sidebar.button("清理会话", key="clean")

# if buttonClean:
#     st.session_state.history = []
#     st.session_state.past_key_values = None
    # if torch.cuda.is_available():
    #     torch.cuda.empty_cache()
    # st.rerun()

st.sidebar.write('State:', st.session_state.state)

for i, message in enumerate(st.session_state.history):
    if message["role"] == "user":
        with st.chat_message(name="user", avatar="user"):
            st.markdown(message["content"])
    elif message["role"] == "assistant":
        with st.chat_message(name="assistant", avatar="assistant"):
            st.markdown(message["content"])

# 创建了两个聊天消息容器，然后，它创建了两个占位符，一个用于显示用户输入，另一个用于显示聊天机器人的响应。
with st.chat_message(name="user", avatar="user"):
    input_placeholder = st.empty()
with st.chat_message(name="assistant", avatar="assistant"):
    message_placeholder = st.empty()

prompt_text = st.chat_input("请输入您的问题")

# 对输入对话进行校验，校验聊天状态，

if prompt_text:
    input_placeholder.markdown(prompt_text)
    history = st.session_state.history + [{"role": "user", "content": prompt_text}]
    State = st.session_state.state
    result = st.session_state.result
    assistant_text = ''
    if State == "Age":
        response = get_completion_sse_from_messages(history)
        # 流式解包，同时校验一下函数调用
        for chunk in response:
            # print(chunk.choices[0].delta.tool_calls)
            if chunk.choices[0].delta.tool_calls:
                print('tools:',chunk.choices[0].delta.tool_calls)
                result = get_function_result(chunk)
                # print('res:',res)
                # 触发函数，函数值加入对话队列，进入下一个状态
                # 不需要将工具对象加入队列，自行处理即可
                # history.append({
                # "role": "tool",
                # "content": f"{json.dumps(result)}",
                # "tool_call_id":chunk.choices[0].delta.tool_calls[0].id
                # })
                st.session_state.result = result
                st.session_state.state = 'Scale'
                # 重新构建提示词
                param = '社交/情感:' + result['Social/Emotional'] + '\n' + '语言/沟通:' + result['Language/Communication'] + '\n' + '认知:' + result['Cognitive'] + '\n' + '运动/身体发育:' + result['Movement/Physical']
                new_system_prompt = f"""你是一个儿童康复师Bot，正在使用{result['age_month']}月龄儿童问卷开展评估。
问卷的内容都是选择题（选项为“是"，“否”或“说不清”）：
```
{param}
```
请确保澄清所有选项、格式和内容，保证电子病历内容的合理性。
你的回复应该是简短的、极具对话性和友好的风格，不要涉及到JSON等机器语言。

你首先问候用户，然后一个一个问题的收集用户的反馈，不要一次发出所有问题。
你等待收集所有信息，然后进行总结并检查最后一次以确保顾客是否想改变其他东西。
最后，你仅以JSON格式输出所有的信息，除JSON以外不要有任何信息。

JSON信息包括：
'社交/情感':
'语言/沟通':
'认知':
'运动/身体发育':
"""      
                # 修改对话背景
                history[0] = {"role": "system", "content": new_system_prompt}
                print(new_system_prompt)
                new_response = get_completion_sse_from_messages(history)
                assistant_text = f"==已加载" + result["age_month"] + "月数据，开始测评==\n"
                # 流式
                for item in new_response:
                    assistant_text += item.choices[0].delta.content
                    message_placeholder.markdown(assistant_text)
                # history.append({"role": "assistant", "content": "==已加载" + result["age_month"] + "月数据，开始测评==" + assistant_text})                        
            else:
                # print(chunk.choices[0].delta.content)
                assistant_text += chunk.choices[0].delta.content
                message_placeholder.markdown(assistant_text)
        st.session_state.history = history + [{"role": "assistant", "content":assistant_text}]        
    elif State == "Scale":
        response = get_completion_sse_from_messages(history)
        # 流式解包
        for chunk in response:
            # print(chunk.choices[0].delta.content)
            assistant_text += chunk.choices[0].delta.content
            message_placeholder.markdown(assistant_text)
        # json检测
        get_json = extract_outermost_json(assistant_text)
        if get_json:
            # print(get_json,type(get_json))
            json_dict = json.loads(get_json) # 转化成字典，条件语句外部，仍然可以引用
            # 循环遍历字典中的键值对
            report = "您的选择全都为“是”，恭喜您的宝宝语言发育正沿着正常的轨迹稳步向前。您需要更多该年龄段的育儿建议吗？"  
            for key, value in json_dict.items():
                for ky, v in value.items(): # 遍历具体的问题及回答
                    if v != '是':  
                        print(f"Key: {ky}, Value: {v}")
                        report = "您的选择有“否/说不清”的情况，婴儿可能存在发育迟缓的风险，家长应高度警惕，建议联系医生进一步咨询，详细评估早期干预。此外，您需要更多该年龄段的育儿建议吗？"
                    else:
                        pass
            history.append({"role": "assistant", "content": report + '您可以问我更多育儿的问题，谢谢！'})
            message_placeholder.markdown(report + '您可以问我更多育儿的问题，谢谢！')
            # 切换状态
            # st.session_state.state = 'Report'
            tips = result['Tips&Activities']             # 重新构建提示词
            new_system_prompt = f"""你是一个儿童康复师Bot，已经获得用户的评估结果，
如果用户提问有关问题，请以下面的资料回复，不要编造资料。
'''育儿指南
{tips}
'''
"""
            print('切换State to Report')
            # print(tips)
            history[0] = {"role": "system", "content": new_system_prompt}
            st.session_state.history = history
        else:
            st.session_state.history = history + [{"role": "assistant", "content":assistant_text}]
             
    # elif State == "Report":
    #     pass
    # print('assistant:',assistant_text)
    # st.session_state.history = history + [{"role": "assistant", "content": assistant_text}]
    # st.session_state.past_key_values = past_key_values
