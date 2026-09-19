import os
import json
import random

# 1. 强制生成2000个村民
print("正在生成2000个村民...")
state = {"day": 1, "villagers": []}
for i in range(1, 2001):
    state["villagers"].append({
        "name": f"村民{i}",
        "memory": "我醒来了，周围有很多人。",
        "life": 1000,
        "food": 100
    })

# 2. 立刻写入本地文件（在临时电脑上）
with open('villagers.json', 'w', encoding='utf-8') as f:
    json.dump(state, f, ensure_ascii=False, indent=2)
print("文件写入本地临时电脑成功！")

# 3. 写一句话到编年史
with open('history.log', 'a', encoding='utf-8') as f:
    f.write(f"第1天：2000个村民诞生了！\n")
print("编年史写入成功！")
