import os
import json
import urllib.request
import random
import time

# ================== 配置区 ==================
MAP_SIZE = 20
DAILY_ACTIONS = 20
ZHIPU_API_KEY = os.environ.get("ZHIPU_API_KEY")

# ================== 地图生成 ==================
def generate_map():
    terrain_types = ["海洋", "森林", "山地", "平原", "河流"]
    weights = [0.15, 0.30, 0.20, 0.25, 0.10]
    grid = {}
    for x in range(MAP_SIZE):
        for y in range(MAP_SIZE):
            grid[f"{x},{y}"] = random.choices(terrain_types, weights=weights)[0]
    return grid

def get_village_name(x, y):
    """根据坐标划分村落（东西南北中）"""
    mid = MAP_SIZE // 2
    if x < mid and y < mid: return "西北村"
    if x >= mid and y < mid: return "东北村"
    if x < mid and y >= mid: return "西南村"
    if x >= mid and y >= mid: return "东南村"
    return "中心村"

# ================== 数字基因组库 ==================
GENOME_POOL = {
    "空间想象": {"弱": 0, "中": 1, "强": 2},
    "模仿能力": {"慢": 0, "中": 1, "快": 2},
    "记忆力":   {"差": 0, "中": 1, "好": 2},
    "逻辑推理": {"弱": 0, "中": 1, "强": 2},
    "情绪稳定": {"敏感": 0, "正常": 1, "稳重": 2},
    "共情能力": {"低": 0, "中": 1, "高": 2},
    "攻击倾向": {"温和": 0, "中等": 1, "好斗": 2},
    "风险偏好": {"保守": 0, "平衡": 1, "冒险": 2},
    "领导意愿": {"低": 0, "中": 1, "高": 2},
    "从众心理": {"独立": 0, "中": 1, "盲从": 2},
    "信任倾向": {"多疑": 0, "中": 1, "轻信": 2},
    "体力":     {"弱": 0, "中": 1, "强": 2},
    "代谢效率": {"低": 0, "中": 1, "高": 2},
    "寿命":     {"短": 0, "中": 1, "长": 2},
}

def generate_genome():
    genome = {}
    for gene_name, alleles in GENOME_POOL.items():
        chosen = random.choice(list(alleles.keys()))
        genome[gene_name] = {"版本": chosen, "值": alleles[chosen]}
    return genome

def get_genome_prompt(villager):
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

# ================== 工具进化树 ==================
TOOL_TREE = [
    {"name": "手",         "min_tech": 0, "food_bonus": 0,   "atk_bonus": 0,  "requires": []},
    {"name": "打制石器",   "min_tech": 1, "food_bonus": 3,   "atk_bonus": 2,  "requires": ["石头"]},
    {"name": "磨制石器",   "min_tech": 2, "food_bonus": 5,   "atk_bonus": 4,  "requires": ["石头", "木头"]},
    {"name": "青铜器",     "min_tech": 4, "food_bonus": 8,   "atk_bonus": 8,  "requires": ["铜矿", "木炭"]},
    {"name": "铁器",       "min_tech": 6, "food_bonus": 12,  "atk_bonus": 15, "requires": ["铁矿", "木炭"]},
    {"name": "合金",       "min_tech": 9, "food_bonus": 18,  "atk_bonus": 25, "requires": ["铁矿", "铜矿", "木炭"]},
    {"name": "新型材料",   "min_tech": 12,"food_bonus": 25,  "atk_bonus": 35, "requires": ["铁矿", "铜矿", "稀有矿"]},
]

def try_evolve_tool(villager, tech_level, resources):
    current = villager.get("tool", "手")
    for tool in TOOL_TREE:
        if tool["name"] == current: continue
        if tech_level >= tool["min_tech"] and all(r in resources for r in tool["requires"]):
            if tool["name"] == "铁器":
                if random.random() < 0.05:
                    villager["tool"] = tool["name"]; return tool["name"]
            elif random.random() < 0.3:
                villager["tool"] = tool["name"]; return tool["name"]
    return None

# ================== 1. 读取或初始化世界 ==================
state = {"day": 1, "villagers": [], "disasters": [], "map": {}, "animals": [], "tech_level": 0}
if os.path.exists('villagers.json'):
    try:
        with open('villagers.json', 'r', encoding='utf-8') as f:
            state = json.load(f)
    except Exception:
        pass

if not state.get("map"):
    state["map"] = generate_map()

if not state.get("animals"):
    animal_types = ["野鹿", "野猪", "狼", "兔子", "熊"]
    for i in range(100):
        atype = random.choice(animal_types)
        state["animals"].append({
            "name": f"{atype}{i}", "type": atype,
            "x": random.randint(0, MAP_SIZE-1), "y": random.randint(0, MAP_SIZE-1),
            "life": 50 if atype in ["狼", "熊"] else 30,
            "food_value": 20 if atype in ["野鹿", "野猪", "熊"] else 8,
            "danger": 3 if atype in ["狼", "熊"] else 1
        })

if not state.get("villagers"):
    print("正在生成2000个村民...")
    state["villagers"] = []
    for i in range(1, 2001):
        x, y = random.randint(0, MAP_SIZE-1), random.randint(0, MAP_SIZE-1)
        state["villagers"].append({
            "name": f"村民{i}", "memory": "我醒来了，周围有很多人。",
            "life": 100, "food": 100, "water": 100, "age": 0,
            "x": x, "y": y, "village": get_village_name(x, y),
            "relationships": {}, "title": "", "tech": [], "tool": "手",
            "resources": [], "emotion": "平静", "reputation": 50,
            "beliefs": "没有信仰", "genome": generate_genome()
        })
else:
    print(f"读取到 {len(state['villagers'])} 个村民，正在检查属性...")
    for v in state["villagers"]:
        v.setdefault("x", random.randint(0, MAP_SIZE-1))
        v.setdefault("y", random.randint(0, MAP_SIZE-1))
        v.setdefault("village", get_village_name(v.get("x",0), v.get("y",0)))
        v.setdefault("water", 100); v.setdefault("tool", "手"); v.setdefault("resources", [])
        v.setdefault("age", 0); v.setdefault("relationships", {}); v.setdefault("title", "")
        v.setdefault("tech", []); v.setdefault("life", 100); v.setdefault("food", 100)
        v.setdefault("emotion", "平静"); v.setdefault("reputation", 50); v.setdefault("beliefs", "没有信仰")
        if "genome" not in v: v["genome"] = generate_genome()

with open('world_rules.txt', 'r', encoding='utf-8') as f:
    rules = f.read()

api_key = ZHIPU_API_KEY
global_disaster = None

def log_history(text):
    with open('history.log', 'a', encoding='utf-8') as f:
        f.write(text + "\n")

# ================== 2. 世界运转逻辑 ==================
def tick_village():
    global global_disaster, state
    print(f"--- 第 {state['day']} 天开始 ---")
    
    for _ in range(DAILY_ACTIONS):
        alive_villagers = [v for v in state["villagers"] if v.get("life", 0) > 0]
        if not alive_villagers: break
        villager = random.choice(alive_villagers)
        
        terrain = state["map"].get(f"{villager['x']},{villager['y']}", "平原")
        villager["terrain"] = terrain
        villager["village"] = get_village_name(villager["x"], villager["y"])
        
        # 附近的人（相邻或同格）
        nearby = [v for v in state["villagers"]
                  if abs(v.get("x",0)-villager["x"]) + abs(v.get("y",0)-villager["y"]) <= 1
                  and v["name"] != villager["name"]]
        nearby_names = [v["name"] for v in nearby]
        
        nearby_animals = [a for a in state["animals"]
                         if abs(a["x"]-villager["x"]) + abs(a["y"]-villager["y"]) <= 1]
        nearby_animal_names = [a["type"] for a in nearby_animals]
        
        relation_text = "，".join([f"{k}(好感度{v})" for k, v in villager.get("relationships", {}).items()]) or "暂无熟人"
        disaster_text = f"当前正在发生【{global_disaster}】！" if global_disaster else "风调雨顺。"
        tech_text = "，".join(villager.get("tech", [])) if villager.get("tech", []) else "暂无发明"
        genome_text = get_genome_prompt(villager)
        
        prompt = f"""
        你叫{villager['name']}{villager.get('title', '')}。属于【{villager['village']}】。
        你位于【{terrain}】坐标({villager['x']},{villager['y']})。
        生命{villager['life']}，食物{villager['food']}，水{villager['water']}，年龄{villager['age']}。
        天赋：{genome_text}。情绪：{villager['emotion']}。工具：{villager.get('tool', '手')}。资源：{"，".join(villager.get("resources", [])) or "无"}。
        
        附近的人：{nearby_names}（属于其他村落）。
        附近的动物：{nearby_animal_names}。
        你的人际关系：{relation_text}。科技：{tech_text}。
        天气：{disaster_text}。规则：{rules}。记忆：{villager['memory']}。
        
        【核心指令】：
        1. 你可以自由移动（探索东、南、西、北的相邻格子）。
        2. 食物或水低于50，必须优先找食物或水。
        3. 海水不能直接喝（除非有滤水器）。森林有木头和猎物，山地有石头和矿，平原能种地，河流能喝水。
        4. 遇到其他村落的人（好感度低或你好斗），你可以选择攻击、抢夺或结盟。
        5. 攻击和打猎会消耗食物和水。武器（工具）越好，胜率越高。
        请用一句话描述你的行动。
        """
        
        req = urllib.request.Request(
            "https://open.bigmodel.cn/api/paas/v4/chat/completions",
            data=json.dumps({"model": "glm-4-flash", "messages": [{"role": "user", "content": prompt}]}).encode('utf-8'),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        )
        
        try:
            response = urllib.request.urlopen(req)
            result = json.loads(response.read().decode('utf-8'))
            action = result['choices'][0]['message']['content']
            
            # 1. 基础消耗
            metabolism = villager['genome'].get("代谢效率", {}).get("值", 1)
            food_cost = max(2, 8 - metabolism); water_cost = max(2, 8 - metabolism)
            if global_disaster: food_cost += 3; water_cost += 3
            villager['life'] -= 1; villager['food'] -= food_cost; villager['water'] -= water_cost; villager['age'] += 1

            # 2. 饥饿与口渴
            if villager['food'] <= 0: villager['life'] -= 10; villager['food'] = 0; log_history(f"⚠️ 第{state['day']}天，{villager['name']}食物耗尽！")
            if villager['water'] <= 0: villager['life'] -= 15; villager['water'] = 0; log_history(f"⚠️ 第{state['day']}天，{villager['name']}缺水！")

            # 3. 自由探索（随机移动机制）
            if random.random() < 0.3 or "探索" in action or "移动" in action:
                dx, dy = random.choice([(-1,0),(1,0),(0,-1),(0,1)])
                nx, ny = max(0, min(MAP_SIZE-1, villager['x']+dx)), max(0, min(MAP_SIZE-1, villager['y']+dy))
                villager['x'], villager['y'] = nx, ny
                villager['village'] = get_village_name(nx, ny)
                log_history(f"🚶 第{state['day']}天，{villager['name']}移动到了({nx},{ny})，进入{villager['village']}。")

            # 4. 地形行为（采集/打猎/喝水）
            if "河流" in terrain: villager['water'] += 30
            elif "森林" in terrain:
                if "打猎" in action or "狩猎" in action:
                    food_gain = random.randint(5, 15) + villager['genome'].get("体力", {}).get("值", 1) * 3 + 10
                    villager['food'] += food_gain
                    log_history(f"🏹 第{state['day']}天，{villager['name']}打猎获得{food_gain}食物。")
                if "采木" in action and "木头" not in villager["resources"]: villager["resources"].append("木头")
            elif "山地" in terrain:
                if "采石" in action and "石头" not in villager["resources"]: villager["resources"].append("石头")
                if "挖矿" in action and random.random() < 0.3:
                    ore = random.choice(["铜矿", "铁矿", "稀有矿"])
                    if ore not in villager["resources"]: villager["resources"].append(ore); log_history(f"⛏️ 第{state['day']}天，{villager['name']}挖到了{ore}！")
            elif "平原" in terrain:
                if "种地" in action: villager['food'] += 10

            # 5. 打猎动物
            if nearby_animals and ("打猎" in action or "攻击" in action):
                animal = random.choice(nearby_animals)
                villager['food'] += animal["food_value"]; villager['life'] -= animal["danger"]
                state["animals"].remove(animal)
                log_history(f"🐗 第{state['day']}天，{villager['name']}猎杀了{animal['type']}。")

            # 6. 村落冲突与打架
            if nearby and ("攻击" in action or "打" in action or "抢" in action or "杀" in action):
                target = random.choice(nearby)
                # 只有不同村落或者关系差才打架（防止同村误伤，但AI执意要打也没办法）
                if target["village"] != villager["village"] or villager['relationships'].get(target['name'], 0) < 0:
                    # 计算战斗力
                    atk_a = villager['genome'].get("攻击倾向", {}).get("值", 1) + villager['genome'].get("体力", {}).get("值", 1)
                    for t in TOOL_TREE:
                        if t["name"] == villager.get("tool", "手"): atk_a += t["atk_bonus"]
                    atk_b = target['genome'].get("攻击倾向", {}).get("值", 1) + target['genome'].get("体力", {}).get("值", 1)
                    for t in TOOL_TREE:
                        if t["name"] == target.get("tool", "手"): atk_b += t["atk_bonus"]
                    
                    # 消耗食物和水
                    villager['food'] -= 10; villager['water'] -= 10
                    target['food'] -= 10; target['water'] -= 10
                    
                    if atk_a > atk_b:
                        # A 胜利
                        loot = min(20, target['food'])
                        target['food'] -= loot; villager['food'] += loot
                        target['life'] -= 20
                        villager['reputation'] += 5
                        log_history(f"⚔️ 第{state['day']}天，{villager['village']}的{villager['name']}击败了{target['village']}的{target['name']}，抢走{loot}食物！")
                        if target['life'] <= 0:
                            log_history(f"💀 第{state['day']}天，{target['name']}在冲突中阵亡。")
                            state["villagers"].remove(target)
                    else:
                        # B 胜利
                        target['reputation'] += 5
                        villager['life'] -= 20
                        log_history(f"⚔️ 第{state['day']}天，{villager['village']}的{villager['name']}攻击{target['village']}的{target['name']}失败，反被重伤！")
                        if villager['life'] <= 0:
                            log_history(f"💀 第{state['day']}天，{villager['name']}在冲突中阵亡。")
                            state["villagers"].remove(villager)
                else:
                    log_history(f"🤝 第{state['day']}天，{villager['name']}试图攻击同村的{target['name']}，被制止了。")

            # 7. 发明与工具进化
            if "发明" in action or "制作" in action or "制造" in action:
                if "生火" in action and "火" not in villager.get("tech", []):
                    villager.setdefault("tech", []).append("火"); villager['reputation'] += 10
                    log_history(f"🔥 第{state['day']}天，{villager['name']}发明了火！")
                if "滤水器" in action and "滤水器" not in villager.get("tech", []):
                    if terrain == "海洋" and random.random() < 0.4:
                        villager.setdefault("tech", []).append("滤水器")
                        log_history(f"💧 第{state['day']}天，{villager['name']}发明了滤水器！")
                evolved = try_evolve_tool(villager, state.get("tech_level", 0), villager.get("resources", []))
                if evolved:
                    log_history(f"🔧 第{state['day']}天，{villager['name']}的工具进化为【{evolved}】！")
                    if evolved in ["青铜器", "铁器", "合金", "新型材料"]:
                        state["tech_level"] = max(state.get("tech_level", 0), TOOL_TREE[[t["name"] for t in TOOL_TREE].index(evolved)]["min_tech"])

            # 8. 关系与心理
            for other in nearby:
                if other["name"] in action:
                    if "帮助" in action or "给" in action:
                        villager['relationships'][other['name']] = villager['relationships'].get(other['name'], 0) + 10
                        villager['emotion'] = "开心"; other['emotion'] = "感激"
                        other['relationships'][villager['name']] = other['relationships'].get(villager['name'], 0) + 20
                    elif "攻击" in action or "抢" in action:
                        villager['relationships'][other['name']] = villager['relationships'].get(other['name'], 0) - 20
                        villager['emotion'] = "愤怒"; other['emotion'] = "愤怒"

            # 9. 首领晋升
            good_relations = sum(1 for v in villager.get('relationships', {}).values() if v >= 20)
            if good_relations >= 5 and villager.get('reputation', 0) > 70 and not villager.get('title', ''):
                villager['title'] = "[首领]"
                log_history(f"👑 第{state['day']}天，{villager['name']}成为了{villager['village']}的【首领】！")

            # 10. 记忆压缩
            villager['memory'] += f" | 第{state['day']}天：{action}"
            if len(villager['memory']) > 200: villager['memory'] = villager['memory'][-200:]
            print(f"{villager['name']}{villager.get('title', '')} 行动完毕。")
            
            # 11. 繁衍
            if villager['age'] >= 20 and villager['food'] > 50 and villager['water'] > 50 and random.random() < 0.15:
                possible_mates = [v for v in nearby if v['age'] >= 18 and v.get('relationships', {}).get(villager['name'], 0) >= 10]
                if possible_mates:
                    mate = random.choice(possible_mates)
                    child_genome = {}
                    for gene_name, alleles in GENOME_POOL.items():
                        parent_a = villager['genome'].get(gene_name, {}).get('版本', '中')
                        parent_b = mate['genome'].get(gene_name, {}).get('版本', '中')
                        inherited = random.choice([parent_a, parent_b])
                        if random.random() < 0.05: inherited = random.choice(list(alleles.keys()))
                        child_genome[gene_name] = {"版本": inherited, "值": alleles[inherited]}
                    new_name = f"新生{random.randint(1000, 9999)}"
                    state["villagers"].append({
                        "name": new_name, "memory": f"我出生于第{state['day']}天。", "life": 100,
                        "food": 100, "water": 100, "age": 0, "x": villager["x"], "y": villager["y"],
                        "village": villager["village"], "relationships": {}, "title": "", "tech": [],
                        "tool": "手", "resources": [], "emotion": "平静", "reputation": 50,
                        "beliefs": "没有信仰", "genome": child_genome
                    })
                    log_history(f"👶 第{state['day']}天，{villager['name']}和{mate['name']}生育了 {new_name}！")

            # 12. 死亡
            lifespan_gene = villager['genome'].get("寿命", {}).get("值", 1)
            max_age = 100 + lifespan_gene * 50
            if villager['age'] >= max_age or villager['life'] <= 0:
                villager['life'] = 0; state["villagers"].remove(villager)
                reason = "寿终正寝" if villager['age'] >= max_age else "死亡"
                log_history(f"💀 第{state['day']}天，{villager['name']}{reason}，享年{villager['age']}岁。")
                
        except Exception as e:
            print("裁判遇到问题：", e)
            break
        time.sleep(2)

    # 天灾与总结
    state["day"] += 1
    if random.random() < 0.1:
        global_disaster = random.choice(["寒冬", "干旱", "瘟疫"])
        log_history(f"🌪️ --- 第{state['day']}天，发生【{global_disaster}】！---")
    else: global_disaster = None
    
    if len(state["animals"]) < 200 and random.random() < 0.3:
        atype = random.choice(["野鹿", "野猪", "狼", "兔子", "熊"])
        state["animals"].append({
            "name": f"{atype}{random.randint(1000,9999)}", "type": atype,
            "x": random.randint(0, MAP_SIZE-1), "y": random.randint(0, MAP_SIZE-1),
            "life": 50 if atype in ["狼", "熊"] else 30,
            "food_value": 20 if atype in ["野鹿", "野猪", "熊"] else 8,
            "danger": 3 if atype in ["狼", "熊"] else 1
        })
    
    alive_count = len(state["villagers"])
    log_history(f"📊 第{state['day']}天结束：当前村庄共有 {alive_count} 人存活。")
    
    with open('villagers.json', 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    
    generate_map_html()

# ================== 3. 可视化地图 ==================
def generate_map_html():
    terrain_colors = {"海洋": "#1e90ff", "森林": "#228b22", "山地": "#8b4513", "平原": "#90ee90", "河流": "#00ced1"}
    terrain_symbols = {"海洋": "~", "森林": "♣", "山地": "▲", "平原": "_", "河流": "≈"}
    
    html = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>AI Village Map</title>
<style>
body { background: #111; color: #eee; font-family: monospace; }
table { border-collapse: collapse; margin: 20px auto; }
td { width: 30px; height: 30px; text-align: center; font-size: 16px; border: 1px solid #333; }
.villager { font-size: 10px; color: yellow; }
.animal { font-size: 10px; color: red; }
h1 { text-align: center; } .stat { text-align: center; margin-top: 20px; }
</style></head><body>
<h1>🗺️ AI Village Map - Day """ + str(state["day"]) + """</h1><table>"""
    
    for y in range(MAP_SIZE):
        html += "<tr>"
        for x in range(MAP_SIZE):
            terrain = state["map"].get(f"{x},{y}", "平原")
            color = terrain_colors.get(terrain, "#888")
            symbol = terrain_symbols.get(terrain, "?")
            here_villagers = [v for v in state["villagers"] if v.get("x")==x and v.get("y")==y]
            here_animals = [a for a in state["animals"] if a["x"]==x and a["y"]==y]
            if here_villagers: symbol = f"👤{len(here_villagers)}"
            elif here_animals: symbol = f"🐾{len(here_animals)}"
            html += f'<td style="background:{color}" title="{terrain} ({x},{y})">{symbol}</td>'
        html += "</tr>"
    html += "</table>"
    html += f"<div class='stat'>村民：{len(state['villagers'])} | 动物：{len(state['animals'])} | 科技等级：{state.get('tech_level', 0)}</div>"
    html += "</body></html>"
    
    with open('map.html', 'w', encoding='utf-8') as f:
        f.write(html)

tick_village()
