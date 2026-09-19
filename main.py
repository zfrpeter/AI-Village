import os
import json
import urllib.request
import random
import time

# ================== 数字基因组库 ==================
GENOME_POOL = {
    # 认知类
    "空间想象": {"弱": 0, "中": 1, "强": 2},
    "模仿能力": {"慢": 0, "中": 1, "快": 2},
    "记忆力":   {"差": 0, "中": 1, "好": 2},
    "逻辑推理": {"弱": 0, "中": 1, "强": 2},
    # 心理类
    "情绪稳定": {"敏感": 0, "正常": 1, "稳重": 2},
    "共情能力": {"低": 0, "中": 1, "高": 2},
    "攻击倾向": {"温和": 0, "中等": 1, "好斗": 2},
    "风险偏好": {"保守": 0, "平衡": 1, "冒险": 2},
    # 社会类
    "领导意愿": {"低": 0, "中": 1, "高": 2},
    "从众心理": {"独立": 0, "中": 1, "盲从": 2},
    "信任倾向": {"多疑": 0, "中": 1, "轻信": 2},
    # 生理类
    "体力":     {"弱": 0, "中": 1, "强": 2},
    "代谢效率": {"低": 0, "中": 1, "高": 2},
    "寿命":     {"短": 0, "中": 1, "长": 2},
}

def generate_genome():
    """随机生成一套基因组"""
    genome = {}
    for gene_name, alleles in GENOME_POOL.items():
        chosen = random.choice(list(alleles.keys()))
        genome[gene_name] = {"版本": chosen, "值": alleles[chosen]}
    return genome

def get_genome_prompt(villager):
    """将基因组精简为提示词，控制token消耗"""
    g = villager.get("genome", {})
    parts = [
        f"空间想象:{g.get('空间想象',{}).get('版本','中')}",
        f"共情能力:{g.get('共情能力',{}).get('版本','中')}",
        f"攻击倾向:{g.get('攻击倾向',{}).get('版本','中等')}",
        f"风险偏好:{g.get('风险偏好',{}).get('版本','平衡')}",
        f"领导意愿:{g.get('领导意愿',{}).get('版本','中')}",
        f"信任倾向:{g.get('信任倾向',{}).get('版本','中')}",
    ]
    return "，".join(parts)

# ================== 1. 读取或初始化世界 ==================
state = {"day": 1, "villagers": [], "disasters": []}
if os.path.exists('villagers.json'):
    try:
        with open('villagers.json', 'r', encoding='utf-8') as f:
            state = json.load(f)
    except Exception:
        pass

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
            "tech": [],
            "emotion": "平静",
            "reputation": 50,
            "beliefs": "没有信仰",
            "genome": generate_genome()
        })
else:
    # 兼容旧数据：如果缺少新属性，自动补全
    print(f"读取到 {len(state['villagers'])} 个村民，正在检查属性...")
    for v in state["villagers"]:
        v.setdefault("age", 0)
        v.setdefault("location", random.choice(locations))
        v.setdefault("relationships", {})
        v.setdefault("title", "")
        v.setdefault("tech", [])
        v.setdefault("life", 100)
        v.setdefault("food", 100)
        v.setdefault("emotion", "平静")
        v.setdefault("reputation", 50)
        v.setdefault("beliefs", "没有信仰")
        if "genome" not in v:
            v["genome"] = generate_genome()

# 读取世界规则
with open('world_rules.txt', 'r', encoding='utf-8') as f:
    rules = f.read()

api_key = os.environ.get("ZHIPU_API_KEY")
global_disaster = None

def log_history(text):
    with open('history.log', 'a', encoding='utf-8') as f:
        f.write(text + "\n")

# ================== 2. 世界运转逻辑 ==================
def tick_village():
    global global_disaster
    print(f"--- 第 {state['day']} 天开始 ---")
    
    # 每次随机唤醒 3 个村民（避免免费API并发限制）
    for _ in range(3):
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
        genome_text = get_genome_prompt(villager)
        
        prompt = f"""
        你叫{villager['name']}{villager.get('title', '')}。
        你当前在【{villager['location']}】，生命值{villager['life']}，食物{villager['food']}，年龄{villager['age']}岁。
        
        【你的天赋与心理倾向】：{genome_text}
        【你当前的情绪】：{villager['emotion']}。
        【你的声望】：{villager['reputation']}。
        
        附近的人：{location_people}。
        你的人际关系：{relation_text}。
        你掌握的科技：{tech_text}。
        当前天气：{disaster_text}。
        世界规则：{rules}。
        你的记忆：{villager['memory']}。
        
        【核心指令】：你的行动必须与你的天赋和心理倾向一致。
        - 空间想象强的人，打猎和找路更厉害。
        - 共情能力高的人，更容易帮助别人。
        - 攻击倾向好斗的人，容易抢东西或打架。
        - 风险偏好冒险的人，在寒冬也敢出门。
        - 领导意愿高的人，会试图说服别人跟随自己。
        - 从众盲从的人，容易附和别人。
        - 信任轻信的人，容易被人骗。
        为了活下去，你可以去打猎、采集、借粮、帮助、攻击，也可以尝试发明（如生火、制作长矛）。
        请用一句话描述你的行动或话语。
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
            
            # 1. 消耗机制（受代谢基因影响）
            metabolism = villager['genome'].get("代谢效率", {}).get("值", 1)
            food_cost = max(1, 5 - metabolism)
            if global_disaster:
                food_cost *= 2
                
            villager['life'] -= 1
            villager['food'] -= food_cost
            villager['age'] += 1

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
            
            # 4. 关系与心理变化
            for other in state["villagers"]:
                if other["name"] in action and other["name"] != villager["name"]:
                    if "帮助" in action or "给" in action:
                        villager['relationships'][other['name']] = villager['relationships'].get(other['name'], 0) + 10
                        villager['emotion'] = "开心"
                        other['emotion'] = "感激"
                        other['relationships'][villager['name']] = other['relationships'].get(villager['name'], 0) + 20
                    elif "攻击" in action or "抢" in action:
                        villager['relationships'][other['name']] = villager['relationships'].get(other['name'], 0) - 20
                        villager['emotion'] = "愤怒"
                        other['emotion'] = "愤怒"
                        other['relationships'][villager['name']] = other['relationships'].get(villager['name'], 0) - 30

            # 5. 打猎与采集（受基因影响，新增日常记录）
            if "打猎" in action or "狩猎" in action:
                stamina = villager['genome'].get("体力", {}).get("值", 1)
                spatial = villager['genome'].get("空间想象", {}).get("值", 1)
                food_gain = random.randint(5, 15) + stamina * 5 + spatial * 3
                villager['food'] += food_gain
                log_history(f"🏹 第{state['day']}天，{villager['name']}打猎获得{food_gain}食物。")
            elif "采集" in action or "找食物" in action:
                spatial = villager['genome'].get("空间想象", {}).get("值", 1)
                food_gain = random.randint(3, 8) + spatial * 3
                villager['food'] += food_gain
                log_history(f"🌾 第{state['day']}天，{villager['name']}采集获得{food_gain}食物。")

            # 6. 首领晋升
            good_relations = sum(1 for v in villager.get('relationships', {}).values() if v >= 20)
            if good_relations >= 5 and villager.get('reputation', 0) > 70 and not villager.get('title', ''):
                villager['title'] = "[首领]"
                for other in state["villagers"]:
                    if other["location"] == villager["location"]:
                        other['emotion'] = villager['emotion']
                log_history(f"👑 第{state['day']}天，{villager['name']}凭借威望和感染力，成为了【首领】！")

            # 7. 发明科技
            if "发明" in action or "生火" in action or "制造" in action:
                if "火" in action and "火" not in villager.get("tech", []):
                    villager.setdefault("tech", []).append("火")
                    log_history(f"💡 第{state['day']}天，{villager['name']}发明了火！")
                elif "长矛" in action and "长矛" not in villager.get("tech", []):
                    villager.setdefault("tech", []).append("长矛")
                    log_history(f"💡 第{state['day']}天，{villager['name']}发明了长矛！")

            # 8. 记忆压缩
            villager['memory'] += f" | 第{state['day']}天：{action}"
            if len(villager['memory']) > 200:
                villager['memory'] = villager['memory'][-200:]
            
            print(f"{villager['name']}{villager.get('title', '')} 行动：{action[:20]}...")
            
            # 9. 繁衍机制（基因遗传 + 突变）
            if villager['age'] >= 100 and villager['food'] > 50 and random.random() < 0.15:
                possible_mates = [
                    v for v in state["villagers"]
                    if v['name'] != villager['name']
                    and v['location'] == villager['location']
                    and v['age'] >= 80
                    and v.get('relationships', {}).get(villager['name'], 0) >= 10
                ]
                
                if possible_mates:
                    mate = random.choice(possible_mates)
                    child_genome = {}
                    for gene_name, alleles in GENOME_POOL.items():
                        parent_a = villager['genome'].get(gene_name, {}).get('版本', '中')
                        parent_b = mate['genome'].get(gene_name, {}).get('版本', '中')
                        inherited = random.choice([parent_a, parent_b])
                        # 5%概率基因突变
                        if random.random() < 0.05:
                            inherited = random.choice(list(alleles.keys()))
                        child_genome[gene_name] = {"版本": inherited, "值": alleles[inherited]}
                    
                    new_name = f"新生{random.randint(1000, 9999)}"
                    state["villagers"].append({
                        "name": new_name,
                        "memory": f"我出生于第{state['day']}天，父母是{villager['name']}和{mate['name']}。",
                        "life": 100,
                        "food": 100,
                        "age": 0,
                        "location": villager['location'],
                        "relationships": {},
                        "title": "",
                        "tech": [],
                        "emotion": "平静",
                        "reputation": 50,
                        "beliefs": "没有信仰",
                        "genome": child_genome
                    })
                    log_history(f"👶 第{state['day']}天，{villager['name']}和{mate['name']}繁衍了后代 {new_name}！")
                    villager['food'] -= 20
                    mate['food'] -= 20

            # 10. 死亡机制（修复版：寿终正寝和饿死都会从名单移除）
            lifespan_gene = villager['genome'].get("寿命", {}).get("值", 1)
            max_age = 100 + lifespan_gene * 50
            if villager['age'] >= max_age or villager['life'] <= 0:
                villager['life'] = 0
                state["villagers"].remove(villager)
                reason = "寿终正寝" if villager['age'] >= max_age else "因生命耗尽去世"
                log_history(f"💀 第{state['day']}天，{villager['name']}{reason}，享年{villager['age']}岁。")
                
        except Exception as e:
            print("裁判遇到问题：", e)
            break
        
        # 每次请求间隔2秒，防止免费API被限流
        time.sleep(2)

    # 11. 天灾机制（每天结束时判定）
    state["day"] += 1
    if random.random() < 0.1:
        global_disaster = random.choice(["寒冬", "干旱", "瘟疫"])
        state.setdefault("disasters", []).append(f"第{state['day']}天：{global_disaster}")
        log_history(f"🌪️ --- 第{state['day']}天，发生【{global_disaster}】，万物凋零！---")
    else:
        global_disaster = None
    
    # 👇 新增：每日总结（确保历史书每天都会记录一笔）
    alive_count = len(state["villagers"])
    log_history(f"📊 第{state['day']}天结束：当前村庄共有 {alive_count} 人存活。")
    
    # 把最新状态存回文件（GitHub Actions会自动帮你提交回仓库）
    with open('villagers.json', 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

tick_village()
