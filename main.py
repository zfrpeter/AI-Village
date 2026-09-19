import os
import json
import urllib.request
import random

# 读取状态文件
state = {"day": 1, "villagers": []}

# 如果文件存在，尝试读取
if os.path.exists('villagers.json'):
    try:
        with open('villagers.json', 'r', encoding='utf-8') as f:
            state = json.load(f)
    except Exception:
        pass

# 如果列表为空，或者没有村民，就自动生成2000个村民
if not state.get("villagers"):
    print("村民名单为空，正在生成2000个村民...")
    state = {"day": 1, "villagers": []}
    for i in range(1, 2001):
        state["villagers"].append({
            "name": f"村民{i}",
            "memory": "我醒来了，周围有很多人，但我不认识他们。",
            "life": 1000
        })
    with open('villagers.json', 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    print("成功生成2000个村民！")

# 读取世界规则
with open('world_rules.txt', 'r', encoding='utf-8') as f:
    rules = f.read()

# 读取智谱 API Key
api_key = os.environ.get("ZHIPU_API_KEY")

def tick_village():
    # 每次随机抽取3个村民进行互动
    for _ in range(3):
        villager = random.choice(state["villagers"])
        
        prompt = f"你叫{villager['name']}，你当前的生命值剩余{villager['life']}。世界规则：{rules}。你的记忆：{villager['memory']}。村子里有很多人。你想做什么？请用一句话描述你的行动或话语。"
        
        # 智谱接口
        req = urllib.request.Request(
            "https://open.bigmodel.cn/api/paas/v4/chat/completions",
            data=json.dumps({
                "model": "glm-4-flash",
                "messages": [{"role": "user", "content": prompt}]
            }).encode('utf-8'),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        )
        try:
            response = urllib.request.urlopen(req)
            result = json.loads(response.read().decode('utf-8'))
            action = result['choices'][0]['message']['content']
            
            # 扣除生命值
            villager['life'] -= 1
            
            # 更新记忆和天数
            villager['memory'] += f" | 第{state['day']}天：{action}"
            print(f"{villager['name']} 行动完毕，剩余生命值：{villager['life']}")
            
            # 生命值归零则删除
            if villager['life'] <= 0:
                state["villagers"].remove(villager)
                print(f"{villager['name']} 生命耗尽，已被移出世界。")
                
        except Exception as e:
            print("裁判遇到问题：", e)
            break

    # 天数+1
    state["day"] += 1
    
    # 存回文件
    with open('villagers.json', 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

tick_village()
