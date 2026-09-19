import os
import json
import urllib.request
import random
import time

# 1. 初始化世界与村民
state = {"day": 1, "villagers": [], "disasters": []}
if os.path.exists('villagers.json'):
    try:
        with open('villagers.json', 'r', encoding='utf-8') as f:
            state = json.load(f)
    except Exception:
        pass

if not state.get("villagers"):
    print("正在生成2000个村民...")
    locations = ["森林", "农田", "矿洞", "村庄中心"]
    state = {"day": 1, "villagers": [], "disasters": []}
    for i in range(1, 2001):
        state["villagers"].append({
            "name": f"村民{i}",
            "memory": "我醒来了，周围有很多人，但我不认识他们。",
            "life": 100,
            "food": 100,
            "age": 0,
            "location": random.choice(locations),
            "relationships": {},
            "title": "",  # 头衔，比如首领
            "tech": []    # 科技，比如火
        })
    with open('villagers.json', 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    print("成功生成2000个村民！")

with open('world_rules.txt', 'r', encoding='utf-8') as f:
    rules = f.read()

api_key = os.environ.get("ZHIPU_API_KEY")
global_disaster = None

def log_history(text):
    with open('history.log', 'a', encoding='utf-8') as f:
        f.write(text + "\n")

def tick_village():
    global global_disaster
    # 每次随机抽取3个村民，加上排队延迟防止API并发报错
    for _ in range(3):
        villager = random.choice(state["villagers"])
        
        # 关系、位置、科技、天灾提示词
        location_people = [v["name"] for v in state["villagers"] if v["location"] == villager["location"] and v["name"] != villager["name"]]
        relation_text = "，".join([f"{k}(好感度{v})" for k, v in villager["relationships"].items()]) or "暂无熟人"
        disaster_text = f"当前【{global_disaster}】" if global_disaster else "风调雨顺"
        tech_text = "，".join(villager["tech"]) if villager["tech"] else "暂无发明"
        
        prompt = f"""
        你叫{villager['name']}{villager['title']}，在【{villager['location']}】。生命：{villager['life']}，食物：{villager['food']}，年龄：{villager['age']}。
        天气：{disaster_text}。你掌握的科技：{tech_text}。
        附近有：{location_people}。
        你的人际关系：{relation_text}。
        世界规则：{rules}。
        你的记忆：{villager['memory']}。
        为了活下去，你可以去打猎、采集、借粮、帮助、攻击，也可以尝试发明（如生火、制作长矛）。
        你想做什么？请用一句话描述你的行动或话语。
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
            if global_disaster:
                villager['food'] -= 5

            # 饥饿机制
            if villager['food'] <= 0:
                villager['life'] -= 10
                villager['food'] = 0
                log_history(f"第{state['day']}天，{villager['name']}食物耗尽，生命垂危！")

            # 位置移动
            for loc in ["森林", "农田", "矿洞", "村庄中心"]:
                if loc in action and "去" in action:
                    villager['location'] = loc
                    break
            
            # 关系与首领机制
            for other in state["villagers"]:
                if other["name"] in action and other["name"] != villager["name"]:
                    if "帮助" in action or "给" in action:
                        villager['relationships'][other['name']] = villager['relationships'].get(other['name'], 0) + 10
                    elif "攻击" in action or "抢" in action:
                        villager['relationships'][other['name']] = villager['relationships'].get(other['name'], 0) - 20

            # 如果一个人帮了很多人，自动成为首领
            good_relations = sum(1 for v in villager['relationships'].values() if v >= 20)
            if good_relations >= 10 and not villager['title']:
                villager['title'] = "[首领]"
                log_history(f"第{state['day']}天，{villager['name']}因为广受拥戴，成为了首领！")
                print(f"{villager['name']} 成为了首领！")

            # 发明科技
            if "发明" in action or "生火" in action or "制造" in action:
                if "火" in action and "火" not in villager['tech']:
                    villager['tech'].append("火")
                    log_history(f"第{state['day']}天，{villager['name']}发明了火！")
                elif "长矛" in action and "长矛" not in villager['tech']:
                    villager['tech'].append("长矛")
                    log_history(f"第{state['day']}天，{villager['name']}发明了长矛！")

            # 记忆压缩
            villager['memory'] += f" | 第{state['day']}天：{action}"
            if len(villager['memory']) > 300:
                villager['memory'] = villager['memory'][-300:]
            
            print(f"{villager['name']}{villager['title']} 行动完毕，生命：{villager['life']}，食物：{villager['food']}")
            
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
                    "relationships": {},
                    "title": "",
                    "tech": []
                })
                log_history(f"第{state['day']}天，{villager['name']}繁衍了后代 {new_name}！")

            # 死亡机制
            if villager['life'] <= 0:
                state["villagers"].remove(villager)
                log_history(f"第{state['day']}天，{villager['name']}因生命耗尽去世，享年{villager['age']}岁。")
                
        except Exception as e:
            print("裁判遇到问题：", e)
            break
        
        # ⚠️ 关键：每次循环排队等2秒，防止智谱API并发被限流
        time.sleep(2)

    # 天灾机制
    state["day"] += 1
    if random.random() < 0.1:
        global_disaster = random.choice(["寒冬", "干旱", "瘟疫"])
        state["disasters"].append(f"第{state['day']}天：{global_disaster}")
        log_history(f"--- 第{state['day']}天，发生【{global_disaster}】，万物凋零！---")
    else:
        global_disaster = None
    
    with open('villagers.json', 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

tick_village()
