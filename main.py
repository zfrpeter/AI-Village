import os
import json
import urllib.request
import random

# 1. 自动生成2000个村民（如果还没生成过）
if not os.path.exists('villagers.json') or os.path.getsize('villagers.json') < 10:
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
else:
    with open('villagers.json', 'r', encoding='utf-8') as f:
        state = json.load(f)

with open('world_rules.txt', 'r', encoding='utf-8') as f:
    rules = f.read()

api_key = os.environ.get("GROQ_API_KEY")

def tick_village():
    # 每次随机抽取3个村民进行互动
    for _ in range(3):
        villager = random.choice(state["villagers"])
        
        prompt = f"你叫{villager['name']}，你当前的生命值剩余{villager['life']}。世界规则：{rules}。你的记忆：{villager['memory']}。村子里有很多人。你想做什么？请用一句话描述你的行动或话语。"
        
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=json.dumps({
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": prompt}]
            }).encode('utf-8'),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        )
        try:
            response = urllib.request.urlopen(req)
            result = json.loads(response.read().decode('utf-8'))
            action = result['choices'][0]['message']['content']
            
            # 每次行动只扣除 1 点生命值
            villager['life'] -= 1
            
            # 更新记忆和天数
            villager['memory'] += f" | 第{state['day']}天：{action}"
            print(f"{villager['name']} 行动完毕，剩余生命值：{villager['life']}")
            
            # 如果生命值降到0，就把它永久移出村庄
            if villager['life'] <= 0:
                state["villagers"].remove(villager)
                print(f"{villager['name']} 生命耗尽，已被移出世界。")
                
        except Exception as e:
            print("裁判遇到问题：", e)
            break

    # 每天所有被唤醒的人共享同一天，一天结束后天数+1
    state["day"] += 1
    
    # 把最新的状态存回去
    with open('villagers.json', 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

tick_village()
