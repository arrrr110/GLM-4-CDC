import csv  
import json  
  
# json_data = []
# # 打开CSV文件并读取内容  
# with open('GLM-4\cdc_001.csv', 'r', encoding='gbk') as csvfile:  
#     reader = csv.reader(csvfile) 
#     for index, row in enumerate(reader):
#         # print(row)
#         obj = {
#         "age_month":row[0],
#         "Social/Emotional":row[1],
#         "Language/Communication":row[2],
#         "Cognitive":row[3],
#         "Movement/Physical":row[4],
#         "Others":row[5],
#         "Tips&Activities":row[6],
#         "needCheck":row[7]
#         }
#         json_data.append(obj)
#         print(obj)
    # rows = list(reader)  

# print(json_data)
# 将CSV数据转换为JSON格式  
# json_data = json.dumps(rows, ensure_ascii=False)  
  
# # 打印JSON数据  
# # print(json_data)

# for index, row in enumerate(json_data):
#     print(index, row)

# # 将JSON数据保存到文件中  
# with open("GLM-4\cdc_db.json", "w", encoding='utf-8') as f:  
#     json.dump(json_data, f)

with open("GLM-4\cdc_data.json", "r", encoding='utf-8') as f:
    data = json.load(f)  
  
# 打印数据  
print(data,type(data))