import json

def extract_outermost_json(text):  
    stack = []  
    start_index = None  
    end_index = None  
  
    for i, char in enumerate(text):  
        if char == '{':  
            if not stack:  # 如果是第一个开括号，记录其位置  
                start_index = i  
            stack.append(char)  
        elif char == '}':  
            stack.pop()  # 弹出栈顶的开括号  
            if not stack:  # 如果栈为空，说明找到了最外层的闭括号  
                end_index = i + 1  # 闭括号的位置是i+1，因为要包含闭括号本身  
                break  # 退出循环，因为我们已经找到了完整的JSON对象  
  
    if start_index is not None and end_index is not None:  
        # 提取并返回JSON数据  
        json_data = text[start_index:end_index]  
        try:  
            # 验证提取的数据是否是有效的JSON  
            # print('func', type(json.loads(json_data)))  
            # 返回str格式的内容
            return json_data
        except json.JSONDecodeError:  
            # 如果提取的数据不是有效的JSON，返回None  
            return None  
    else:  
        # 如果没有找到完整的JSON对象，返回None  
        return None  
  
# 示例文本  
text = """  
这里有一些文本，不是JSON。  
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
这里可能还有其他文本，但不是我们想要的JSON。  
"""  

if __name__ == "__main__":
  # 提取JSON数据  
  json_data = extract_outermost_json(text)  
  if json_data:  
      print("Extracted JSON:")  
      print(type(json_data))  
      # print(json.loads(json_data))  
      json_dict = json.loads(json_data)
      # 遍历对象的所有属性
      # print(json_res['table'])
      # 循环遍历字典中的键值对  
      for key, value in json_dict['table'].items():
          for ky, v in value.items(): # 遍历具体的问题及回答
            if v != '是':  
              print(f"Key: {ky}, Value: {v}")
              
            else:
                pass  

      # print(type(json_data))  
      # print(type(json.loads(json_data)))  
  else:  
      print("No complete JSON found.")