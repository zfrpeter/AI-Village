import os
import json
import urllib.request
import random

# 1. 初始化世界与村民
state = {"day": 1, "villagers": []}
if os.path.exists('villagers.json'):
    try:
        with open('villagers.json', 'r', encoding='utf-8') as f:
            state = json.load(f)
    except Exception:
        pass

if not state.get("villagers"):
    print("正在生成2000个村民...")
    locations = ["森林", "农田", "矿洞", "村庄中心"]
    state = {"day": 1, "villagers": []}
    for i in range(1, 2001):
        state["villagers"].append({
            "name": f"村民{i}",
            "memory": "我醒来了，周围有很多人，但我不认识他们。",
            "life": 100,
            "food": 100,
            "age": 0,
            "location": random.choice(locations),
            "relationships": {}
        })
    with open('villagers.json', 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    print("成功生成2000个村民！")

with open('world_rules.txt', 'r', encoding='utf-8') as f:
    rules = f.read()

api_key = os.environ.get("ZHIPU_API_KEY")
global_disaster = None  # 记录当前是否处于天灾

def log_history(text):
    with open('history.log', 'a', encoding='utf-8') as f:
        f.write(text + "\n")

def tick_village():
    global global_disaster
    # 每次随机抽取5个村民（增加互动概率）
    for _ in range(5):
        villager = random.choice(state["villagers"])
        
        # 构建提示词，加入位置、好感度、天灾信息
        location_people = [v["name"] for v in state["villagers"] if v["location"] == villager["location"] and v["name"] != villager["name"]]
        relation_text = "，".join([f"{k}(好感度{v})" for k, v in villager["relationships"].items()]) or "暂无熟人"
        disaster_text = f"当前正在发生【{global_disaster}】，食物消耗翻倍！" if global_disaster else "当前风调雨顺。"
        
        prompt = f"""
        你叫{villager['name']}，你当前在【{villager['location']}】。你当前生命值{villager['life']}，食物{villager['food']}。
        {disaster_text}
        村子里有2000个人，在你附近的有：{location_people}。
        你的人际关系：{relation_text}。
        世界规则：{rules}。
        你的记忆：{villager['memory']}。
        为了活下去，你可以去打猎、采集、找人借粮、帮助别人或攻击别人。你想做什么？请用一句话描述你的行动或话语。
        """
        
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
            
            # 消耗机制
            villager['life'] -= 1
            villager['food'] -= 5
            villager['age'] += 1
            
            # 天灾机制
            if global_disaster:
                villager['food'] -= 5

            # 饥饿机制
            if villager['food'] <= 0:
                villager['life'] -= 10
                villager['food'] = 0
                log_history(f"第{state['day']}天，{villager['name']}食物耗尽，生命垂危！")

            # 简单动作解析（移动、结盟、繁衍）
            if "去" in action and any(loc in action for loc in ["森林", "农田", "矿洞", "村庄中心"]):
                for loc in ["森林", "农田", "矿洞", "村庄中心"]:
                    if loc in action:
                        villager['location'] = loc
                        log_history(f"第{state['day']}天，{villager['name']}移动到了{loc}。")
                        break
            
            # 更新关系（如果提到别人名字）
            for other in state["villagers"]:
                if other["name"] in action and other["name"] != villager["name"]:
                    if "帮助" in action or "给" in action:
                        villager['relationships'][other['name']] = villager['relationships'].get(other['name'], 0) + 10
                    elif "攻击" in action or "抢" in action:
                        villager['relationships'][other['name']] = villager['relationships'].get(other['name'], 0) - 20

            # 记忆压缩
            villager['memory'] += f" | 第{state['day']}天：{action}"
            if len(villager['memory']) > 300:
                villager['memory'] = villager['memory'][-300:]
            
            print(f"{villager['name']} 行动完毕，生命：{villager['life']}，食物：{villager['food']}，位置：{villager['location']}")
            
            # 繁衍机制（100岁以上，食物充足）
            if villager['age'] >= 100 and villager['food'] > 50 and random.random() < 0.1:
                new_name = f"新生{random.randint(1000, 9999)}"
                state["villagers"].append({
                    "name": new_name,
                    "memory": f"我出生于第{state['day']}天，我的父母是{villager['name']}。",
                    "life": 100,
                    "food": 100,
                    "age": 0,
                    "location": villager['location'],
                    "relationships": {}
                })
                log_history(f"第{state['day']}天，{villager['name']}繁衍了后代 {new_name}！")

            # 死亡机制
            if villager['life'] <= 0:
                state["villagers"].remove(villager)
                log_history(f"第{state['day']}天，{villager['name']}因生命耗尽去世，享年{villager['age']}岁。")
                print(f"{villager['name']} 去世了。")
                
        except Exception as e:
            print("裁判遇到问题：", e)
            break

    # 天灾机制（每天开始时判断）
    state["day"] += 1
    if random.random() < 0.1:
        global_disaster = random.choice(["寒冬", "干旱", "瘟疫"])
        log_history(f"--- 第{state['day']}天，发生【{global_disaster}】，万物凋零！---")
        print(f"天灾发生：{global_disaster}")
    else:
        global_disaster = None
    
    # 存回状态
    with open('villagers.json', 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

tick_village()
