import os
import json
import urllib.request
import random
import time

# ========== 1. 读取或初始化世界 ==========
state = {"day": 1, "villagers": [], "disasters": []}
if os.path.exists('villagers.json'):
    try:
        with open('villagers.json', 'r', encoding='utf-8') as f:
            state = json.load(f)
    except Exception:
        pass

# 兼容处理：给测试版生成的白板村民补全缺失的属性
locations = ["森林", "农田", "矿洞", "村庄中心"]
if not state.get("villagers"):
    print("正在生成2000个村民...")
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
            "title": "",
            "tech": []
        })
else:
    # 如果是刚才测试版生成的数据，自动补全属性
    print(f"读取到 {len(state['villagers'])} 个村民，正在补全属性...")
    for v in state["villagers"]:
        v.setdefault("age", 0)
        v.setdefault("location", random.choice(locations))
        v.setdefault("relationships", {})
        v.setdefault("title", "")
        v.setdefault("tech", [])
        v.setdefault("life", 100)
        v.setdefault("food", 100)

# 保存一次补全后的状态
with open('villagers.json', 'w', encoding='utf-8') as f:
    json.dump(state, f, ensure_ascii=False, indent=2)

# 读取世界规则
with open('world_rules.txt', 'r', encoding='utf-8') as f:
    rules = f.read()

api_key = os.environ.get("ZHIPU_API_KEY")
global_disaster = None

def log_history(text):
    with open('history.log', 'a', encoding='utf-8') as f:
        f.write(text + "\n")

# ========== 2. 世界运转逻辑 ==========
def tick_village():
    global global_disaster
    print(f"--- 第 {state['day']} 天开始 ---")
    
    # 每次随机唤醒 3 个村民（避免免费API并发限制）
    for _ in range(3):
        # 过滤掉已经死亡的村民
        alive_villagers = [v for v in state["villagers"] if v.get("life", 0) > 0]
        if not alive_villagers:
            print("所有人都不在了……")
            break
            
        villager = random.choice(alive_villagers)
        
        # 提取附近的人
        location_people = [v["name"] for v in state["villagers"] if v["location"] == villager["location"] and v["name"] != villager["name"]]
        relation_text = "，".join([f"{k}(好感度{v})" for k, v in villager.get("relationships", {}).items()]) or "暂无熟人"
        disaster_text = f"当前正在发生【{global_disaster}】，食物消耗翻倍！" if global_disaster else "当前风调雨顺。"
        tech_text = "，".join(villager.get("tech", [])) if villager.get("tech", []) else "暂无发明"
        
        prompt = f"""
        你叫{villager['name']}{villager.get('title', '')}，你当前在【{villager['location']}】。
        你当前生命值{villager['life']}，食物{villager['food']}，年龄{villager['age']}岁。
        {disaster_text}
        村子里有很多人，在你附近的有：{location_people}。
        你的人际关系：{relation_text}。
        你掌握的科技：{tech_text}。
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
            
            # 1. 消耗机制
            villager['life'] -= 1
            villager['food'] -= 5
            villager['age'] += 1
            if global_disaster:
                villager['food'] -= 5

            # 2. 饥饿机制
            if villager['food'] <= 0:
                villager['life'] -= 10
                villager['food'] = 0
                log_history(f"第{state['day']}天，{villager['name']}食物耗尽，生命垂危！")

            # 3. 位置移动
            for loc in ["森林", "农田", "矿洞", "村庄中心"]:
                if loc in action and "去" in action:
                    villager['location'] = loc
                    break
            
            # 4. 关系与首领机制
            for other in state["villagers"]:
                if other["name"] in action and other["name"] != villager["name"]:
                    if "帮助" in action or "给" in action:
                        villager['relationships'][other['name']] = villager['relationships'].get(other['name'], 0) + 10
                    elif "攻击" in action or "抢" in action:
                        villager['relationships'][other['name']] = villager['relationships'].get(other['name'], 0) - 20

            # 5. 首领晋升（如果帮助了10个不同的人，好感度都大于20）
            good_relations = sum(1 for v in villager.get('relationships', {}).values() if v >= 20)
            if good_relations >= 10 and not villager.get('title', ''):
                villager['title'] = "[首领]"
                log_history(f"🎉 第{state['day']}天，{villager['name']}因为广受拥戴，成为了首领！")

            # 6. 发明科技
            if "发明" in action or "生火" in action or "制造" in action:
                if "火" in action and "火" not in villager.get("tech", []):
                    villager.setdefault("tech", []).append("火")
                    log_history(f"💡 第{state['day']}天，{villager['name']}发明了火！")
                elif "长矛" in action and "长矛" not in villager.get("tech", []):
                    villager.setdefault("tech", []).append("长矛")
                    log_history(f"💡 第{state['day']}天，{villager['name']}发明了长矛！")

            # 7. 记忆压缩（只保留最近200字）
            villager['memory'] += f" | 第{state['day']}天：{action}"
            if len(villager['memory']) > 200:
                villager['memory'] = villager['memory'][-200:]
            
            print(f"{villager['name']}{villager.get('title', '')} 行动：{action[:20]}...")
            
            # 8. 繁衍机制
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
                log_history(f"👶 第{state['day']}天，{villager['name']}繁衍了后代 {new_name}！")

            # 9. 死亡机制
            if villager['life'] <= 0:
                state["villagers"].remove(villager)
                log_history(f"💀 第{state['day']}天，{villager['name']}因生命耗尽去世，享年{villager['age']}岁。")
                
        except Exception as e:
            print("裁判遇到问题：", e)
            break
        
        # 每次请求间隔2秒，防止免费API被限流
        time.sleep(2)

    # 10. 天灾机制（每天结束时判定）
    state["day"] += 1
    if random.random() < 0.1:
        global_disaster = random.choice(["寒冬", "干旱", "瘟疫"])
        state.setdefault("disasters", []).append(f"第{state['day']}天：{global_disaster}")
        log_history(f"🌪️ --- 第{state['day']}天，发生【{global_disaster}】，万物凋零！---")
    else:
        global_disaster = None
    
    # 把最新状态存回文件（GitHub Actions会自动帮你提交回仓库）
    with open('villagers.json', 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

tick_village()
