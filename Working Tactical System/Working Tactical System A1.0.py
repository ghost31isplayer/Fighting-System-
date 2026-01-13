import random
import sys

# ------------------------------------------
# MERCENARY DATABASE (HP + Armor + Stats)
# ------------------------------------------
MERCENARIES = {
    "Sellsword":     {"hp": 85, "armor": 70, "atk": 18, "def": 12, "init": 9,  "special": "Precision Strike"},
    "Raider":        {"hp": 75, "armor": 40, "atk": 21, "def": 10, "init": 12, "special": "Crush Armor"},
    "Footman":       {"hp": 90, "armor": 90, "atk": 16, "def": 14, "init": 8,  "special": "Guard"},
    "Swordmaster":   {"hp": 65, "armor": 35, "atk": 25, "def": 8,  "init": 15, "special": "Riposte"},
    "Knight":        {"hp": 100,"armor":120, "atk": 20, "def": 15, "init": 7,  "special": "Shield Wall"},
    "Archer":        {"hp": 55, "armor": 20, "atk": 28, "def": 6,  "init": 14, "special": "Power Shot"},
    "Berserker":     {"hp": 70, "armor": 20, "atk": 30, "def": 4,  "init": 11, "special": "Swing"},
    "Pikeman":       {"hp": 60, "armor": 30, "atk": 23, "def": 10, "init": 10, "special": "Long Thrust"},
}

# ------------------------------------------
# SPECIAL COSTS & FATIGUE
# ------------------------------------------
SPECIAL_COST = {
    "Swing": 6, "Power Shot": 6, "Crush Armor": 5, "Precision Strike": 5,
    "Guard": 4, "Shield Wall": 4, "Riposte": 4, "Long Thrust": 5
}

FATIGUE_GAIN = {
    "basic_attack": 8,
    "special": 14
}

# ------------------------------------------
# FATIGUE / AP (Action Points)
# ------------------------------------------
def regen_ap(unit):
    """Recover AP based on fatigue; higher fatigue = slower recovery"""
    recovered = max(2, 6 - unit["fatigue"] // 20)
    unit["ap"] = min(unit["max_ap"], unit["ap"] + recovered)

def apply_fatigue(unit, amount):
    """Increase fatigue and reduce max AP accordingly"""
    unit["fatigue"] = min(unit["max_fatigue"], unit["fatigue"] + amount)
    unit["max_ap"] = max(3, 9 - unit["fatigue"] // 15)

FATIGUE_THRESHOLDS = {"light": 20, "heavy": 40, "exhausted": 60}

# ------------------------------------------
# MORALE SYSTEM (Battle Brothers–style)
# ------------------------------------------

# Thresholds for morale states
MORALE_STATES = {
    "confident": 70,
    "steady": 40,
    "wavering": 20,
    "breaking": 0
}

# Optional stat modifiers (hit, defense, initiative)
MORALE_MODIFIERS = {
    "confident": {"hit": 10, "def": 5, "init": 2},
    "steady":    {"hit": 0,  "def": 0, "init": 0},
    "wavering":  {"hit": -10,"def": -5,"init": -2},
    "breaking":  {"hit": -20,"def": -10,"init": -4}
}

# ------------------------------------------
# MORALE HIT MODIFIER (for attacks)
# ------------------------------------------
def morale_hit_modifier(unit):
    """
    Returns an accuracy bonus/penalty based on morale state.
    Confident → + hit chance, Breaking → - hit chance
    """
    state = unit.get("morale_state", "steady")
    return MORALE_MODIFIERS.get(state, {"hit":0})["hit"]

# ------------------------------------------
# INITIALIZATION
# ------------------------------------------
def init_morale(unit):
    """Set starting morale and state for new units"""
    unit["morale"] = 100
    unit["morale_state"] = "confident"
    unit["fleeing"] = False

# ------------------------------------------
# STATE UPDATES
# ------------------------------------------
def update_morale_state(unit):
    """Adjust morale state according to current morale"""
    m = unit["morale"]
    if m >= MORALE_STATES["confident"]:
        unit["morale_state"] = "confident"
    elif m >= MORALE_STATES["steady"]:
        unit["morale_state"] = "steady"
    elif m >= MORALE_STATES["wavering"]:
        unit["morale_state"] = "wavering"
    else:
        unit["morale_state"] = "breaking"

# ------------------------------------------
# APPLY MORALE CHANGE
# ------------------------------------------
def apply_morale(unit, amount):
    """Increase or decrease morale and update state"""
    unit["morale"] = max(0, min(100, unit["morale"] + amount))
    update_morale_state(unit)

# ------------------------------------------
# MORALE LOSS FROM DAMAGE
# ------------------------------------------
def morale_hit(unit, damage):
    """Apply morale loss when a unit takes damage"""
    if unit["hp"] <= 0: return

    loss = random.randint(3, 6) + int(damage * 0.1)
    if unit.get("fatigue", 0) >= 40: loss += 3
    if unit.get("fatigue", 0) >= 60: loss += 5

    apply_morale(unit, -loss)
    print(f"😰 {unit['name']} loses {loss} morale from the hit! ({unit['morale_state']})")

# ------------------------------------------
# MORALE SHOCK ON DEATH
# ------------------------------------------
def morale_shock(dead_unit, allies):
    """Nearby allies lose morale when someone dies"""
    for u in allies:
        if u["hp"] <= 0: continue

        loss = random.randint(8, 15)
        if dead_unit.get("fleeing"): loss = int(loss * 0.6)
        if u.get("fatigue", 0) >= 40: loss += 5

        apply_morale(u, -loss)
        print(f"😰 {u['name']} loses {loss} morale! ({u['morale_state']})")

# ------------------------------------------
# MORALE GAIN ON KILL
# ------------------------------------------
def morale_gain_on_kill(killer, allies):
    """Gain morale for killer and nearby allies when unit is killed"""
    killer_gain = random.randint(20, 35)
    apply_morale(killer, killer_gain)
    print(f"😎 {killer['name']} gains {killer_gain} morale! ({killer['morale_state']})")

    for u in allies:
        if u is killer or u["hp"] <= 0: continue
        ally_gain = random.randint(10, 20)
        apply_morale(u, ally_gain)
        print(f"😎 {u['name']} gains {ally_gain} morale! ({u['morale_state']})")

# ------------------------------------------
# TURN CONTROL: PANIC & FLEE
# ------------------------------------------
def morale_turn_check(unit, allies):
    """
    Returns False if unit loses control of turn due to panic/fleeing.
    Handles BB-style breaking & fleeing mechanics.
    """
    if unit.get("fleeing"):
        print(f"🏃 {unit['name']} is fleeing and cannot act!")
        unit["ap"] = 0
        return False

    if unit["morale_state"] == "breaking":
        # Panic chance
        if random.random() < 0.25:
            print(f"😱 {unit['name']} panics and hesitates!")
            apply_morale(unit, -5)
            unit["ap"] = 0
            return False

        # Check if unit breaks and flees
        if check_flee(unit):
            check_panic_chain(unit, allies)
            return False

    return True

# ------------------------------------------
# FLEE CHECK (BB-STYLE)
# ------------------------------------------
def check_flee(unit):
    """Determine if a unit breaks and flees; influenced by HP and fatigue"""
    if unit["hp"] <= 0 or unit.get("fleeing"): return False
    if unit["morale_state"] != "breaking": return False

    hp_ratio = unit["hp"] / unit["max_hp"]
    base_chance = 0.15
    low_hp_bonus = (1 - hp_ratio) * 0.4
    fatigue_bonus = unit.get("fatigue", 0) / 100 * 0.2
    flee_chance = base_chance + low_hp_bonus + fatigue_bonus

    if random.random() < flee_chance:
        unit["fleeing"] = True
        unit["ap"] = 0
        print(f"🏃 {unit['name']} BREAKS and starts fleeing!")
        return True

    return False

# ------------------------------------------
# PANIC CHAIN
# ------------------------------------------
def check_panic_chain(unit, allies):
    """When a unit flees, nearby allies may also panic depending on morale/fatigue"""
    if not unit.get("fleeing"): return

    for ally in allies:
        if ally["hp"] <= 0 or ally.get("fleeing"): continue

        chance = 0.1  # base 10%
        if ally.get("fatigue", 0) >= 40: chance += 0.1
        if ally["morale_state"] == "wavering": chance += 0.05
        elif ally["morale_state"] == "breaking": chance += 0.15

        if random.random() < chance:
            ally["fleeing"] = True
            ally["ap"] = 0
            print(f"😨 {ally['name']} panics due to {unit['name']}'s fleeing!")

# ------------------------------------------
# UNIT CREATION
# ------------------------------------------
def create_unit(name, owner="player", ai_control=False):
    base = MERCENARIES[name]
    unit = {
        "name": name,
        "hp": base["hp"],
        "max_hp": base["hp"], 
        "armor": base["armor"],
        "atk": base["atk"],
        "def": base["def"],
        "init": base["init"],
        "special": base["special"],
        "max_ap": 9,
        "ap": 9,
        "fatigue": 0,
        "max_fatigue": 100,
        "guarding": None,
        "riposte": False,
        "owner": owner,
        "ai_control": ai_control  # please work
    }
    init_morale(unit)
    return unit


def print_unit(u):
    print(f"{u['name']} | HP:{u['hp']} ARM:{u['armor']} AP:{u['ap']} FAT:{u['fatigue']} | Morale: {u['morale_state'].upper()} | Spec:{u['special']}")



# ------------------------------------------
# HIT AND DAMAGE
# ------------------------------------------
def roll_to_hit(attacker, defender, bonus=0):
    base = 60
    hit_chance = base + (attacker["atk"] - defender["def"]) * 3
    hit_chance += bonus + morale_hit_modifier(attacker)
    hit_chance -= 5 if attacker["morale_state"] == "wavering" else 0
    hit_chance = max(5, min(95, hit_chance))
    roll = random.randint(1, 100)
    return roll <= hit_chance, hit_chance, roll

def deal_damage(attacker, defender, ignore_def=False, multiplier=1.0, bonus=0):
    raw = int(attacker["atk"] * multiplier) + bonus
    if not ignore_def:
        raw -= int(defender["def"] * 0.25)
    raw = max(1, raw)

    if defender["armor"] > 0:
        armor_hit = int(raw * 0.8)
        hp_hit = raw - armor_hit
        defender["armor"] -= armor_hit
        if defender["armor"] < 0:
            hp_hit += abs(defender["armor"])
            defender["armor"] = 0
        defender["hp"] -= hp_hit
    else:
        defender["hp"] -= raw

    return raw

def crush_armor(attacker, defender):
    if random.random() < 0.5:
        dmg = random.randint(15, 30)
        defender["armor"] = max(0, defender["armor"] - dmg)
        print(f"💥 {attacker['name']} SMASHES {defender['name']}'s armor for {dmg}!")
        return True
    return False

# ------------------------------------------
# TARGET SELECTION
# ------------------------------------------
def choose_target_player(team, message=""):
    alive = [u for u in team if u["hp"] > 0]
    if not alive:
        return None

    while True:
        print(f"\n{message}")
        for i, u in enumerate(alive):
            print(f"{i+1}. {u['name']} (HP:{u['hp']} ARM:{u['armor']})")
        pick = input("> ")
        if pick.isdigit() and 1 <= int(pick) <= len(alive):
            return alive[int(pick)-1]
        print("Invalid.")

def alive_units(team):
    return [u for u in team if u["hp"] > 0]

# ------------------------------------------
# DEATH CHECK
# ------------------------------------------
def check_death(unit, allies):
    if unit["hp"] <= 0 and not unit.get("dead", False):
        unit["dead"] = True
        unit["hp"] = 0
        print(f"💀 {unit['name']} has fallen!")
        morale_shock(unit, allies)
        return True
    return False

# ------------------------------------------
# SPECIALS (BB-style damage adjustments)
# ------------------------------------------
def use_special(attacker, allies, enemies):
    spec = attacker["special"]
    cost = SPECIAL_COST[spec]

    if attacker["ap"] < cost:
        print("❌ Not enough AP!")
        return False

    attacker["ap"] -= cost
    apply_fatigue(attacker, FATIGUE_GAIN["special"])

    # Helper: pick target safely
    def pick_enemy():
        if attacker["owner"] == "player":
            return choose_target_player(enemies, "Choose target:")
        else:
            return choose_target_ai(attacker, enemies)

    def pick_ally():
        if attacker["owner"] == "player":
            return choose_target_player(allies, "Choose ally:")
        else:
            return choose_target_ai(attacker, allies)

    # -------------------------
    # SWING (AOE)
    # -------------------------
    if spec == "Swing":
        print(f"\n⚔️ {attacker['name']} uses SWING!")
        apply_fatigue(attacker, 15)  # extra fatigue

        for e in enemies:
            if e["hp"] <= 0:
                continue
            dmg = deal_damage(attacker, e, ignore_def=True, multiplier=0.5)
            print(f"Hit {e['name']} for {dmg}!")
            morale_hit(e, dmg)
            check_death(e, enemies)
        return True

    # -------------------------
    # POWER SHOT
    # -------------------------
    if spec == "Power Shot":
        t = pick_enemy()
        if t is None:
            return False

        hit, chance, roll = roll_to_hit(attacker, t, bonus=10)
        if hit:
            dmg = deal_damage(attacker, t, ignore_def=True)
            print(f"🎯 POWER SHOT hits {t['name']} for {dmg}! ({roll} ≤ {chance}%)")
            morale_hit(t, dmg)
            check_death(t, enemies)
        else:
            print(f"🎯 POWER SHOT MISSES! ({roll} > {chance}%)")
            apply_morale(attacker, -2)
        return True

    # -------------------------
    # CRUSH ARMOR
    # -------------------------
    if spec == "Crush Armor":
        t = pick_enemy()
        if t is None:
            return False

        broken = crush_armor(attacker, t)
        if broken:
            morale_hit(t, 10)
            if random.random() < 0.25:
                dmg = random.randint(10, 20)
                t["hp"] -= dmg
                print(f"❗CRITICAL ARMOR BREAK deals {dmg} HP damage!")
                morale_hit(t, dmg)
                check_death(t, enemies)
        else:
            print(f"{attacker['name']} fails to crush armor.")
            apply_morale(attacker, -2)
        return True

    # -------------------------
    # PRECISION STRIKE
    # -------------------------
    if spec == "Precision Strike":
        t = pick_enemy()
        if t is None:
            return False

        hit, chance, roll = roll_to_hit(attacker, t)
        if hit:
            crit = random.random() < 0.35
            dmg = deal_damage(attacker, t, ignore_def=True, bonus=(10 if crit else 0))
            print(f"{attacker['name']} hits {t['name']} for {dmg}! ({roll} ≤ {chance}%)")
            if crit:
                print("🔥 CRITICAL HIT!")
            morale_hit(t, dmg)
            check_death(t, enemies)
        else:
            print(f"{attacker['name']} MISSES! ({roll} > {chance}%)")
            apply_morale(attacker, -2)
        return True

    # -------------------------
    # GUARD
    # -------------------------
    if spec == "Guard":
        ally = pick_ally()
        if ally is None:
            return False

        ally["guarding"] = attacker
        print(f"{attacker['name']} is guarding {ally['name']}!")
        return True

    # -------------------------
    # SHIELD WALL
    # -------------------------
    if spec == "Shield Wall":
        attacker["shield_wall"] = True
        print(f"{attacker['name']} raises SHIELD WALL! +10 DEF (1 round)")
        return True

    # -------------------------
    # RIPOSTE
    # -------------------------
    if spec == "Riposte":
        attacker["riposte"] = True
        print(f"{attacker['name']} prepares RIPOSTE!")
        return True

    # -------------------------
    # LONG THRUST
    # -------------------------
    if spec == "Long Thrust":
        t = pick_enemy()
        if t is None:
            return False

        hit, chance, roll = roll_to_hit(attacker, t)
        if hit:
            dmg = deal_damage(attacker, t, multiplier=1.2)
            print(f"{attacker['name']} LONG THRUST hits {t['name']} for {dmg}! ({roll} ≤ {chance}%)")
            morale_hit(t, dmg)
            check_death(t, enemies)
        else:
            print(f"{attacker['name']} LONG THRUST MISSES! ({roll} > {chance}%)")
            apply_morale(attacker, -2)
        return True

    return False

# ------------------------------------------
# AI USE SPECIAL DECISION
# ------------------------------------------
def ai_use_special(unit, allies, enemies):
    if unit["ap"] < SPECIAL_COST[unit["special"]]:
        return False
    roll = random.random()
    if AI_DIFFICULTY == "easy":
        return roll < 0.3
    elif AI_DIFFICULTY == "normal":
        return roll < 0.5
    elif AI_DIFFICULTY == "hard":
        return roll < 0.8
    return False




# ------------------------------------------
# TEAM SELECTION
# ------------------------------------------
def team_selection():
    chosen_names = []
    while len(chosen_names) < 4:
        print("\nChoose your mercenaries:")
        for i, m in enumerate(MERCENARIES.keys()):
            print(f"{i+1}. {m}")
        pick = input(f"Pick #{len(chosen_names)+1}: ")
        if pick.isdigit():
            idx = int(pick)
            names = list(MERCENARIES.keys())
            if 1 <= idx <= len(names):
                chosen_names.append(names[idx-1])
                continue
        print("Invalid.")

    team = [create_unit(n, "player") for n in chosen_names]
    return team

# ------------------------------------------
# AI DIFFICULTY SETTINGS
# ------------------------------------------
# Adjust the AI's behavior by setting this variable:
# "easy"   -> random targets, specials used occasionally
# "normal" -> prioritizes weak enemies and morale states
# "hard"   -> prioritizes weak/breaking enemies, smarter special use
AI_DIFFICULTY = "normal"  # options: "easy", "normal", "hard"




# ------------------------------------------
# AI AWARENESS RULES
# ------------------------------------------
# These functions define how "aware" the AI is when choosing actions

def choose_target_ai(attacker, enemies):
    """
    Return the enemy the AI should attack.
    Awareness is based on AI_DIFFICULTY:
    - easy: completely random target
    - normal: prefers low HP or breaking morale
    - hard: prefers low HP, breaking morale, or high threat (high ATK)
    """
    alive_enemies = [e for e in enemies if e["hp"] > 0]
    if not alive_enemies:
        return None

    # EASY: pure randomness
    if AI_DIFFICULTY == "easy":
        return random.choice(alive_enemies)

    # Prefer broken morale targets
    broken = [e for e in alive_enemies if e["morale_state"] == "breaking"]
    if broken and random.random() < 0.7:
        return random.choice(broken)

    # Sort by HP (weakest first)
    weakest = sorted(alive_enemies, key=lambda x: x["hp"])

    if AI_DIFFICULTY == "normal":
        return weakest[0] if random.random() < 0.6 else random.choice(alive_enemies)

    # HARD: broken > weakest > high threat
    if random.random() < 0.7:
        return weakest[0]
    return max(alive_enemies, key=lambda x: x["atk"])


# ------------------------------------------
# USAGE NOTES
# ------------------------------------------
# In your simulate_battle() loop, replace:
# target = random.choice(alive_enemies)
# with:
# target = choose_target(u, alive_enemies)
#
# And replace:
# if u["ap"] >= SPECIAL_COST[u["special"]] and random.random() < 0.5:
#     use_special(u, alive_allies, alive_enemies)
# with:
# if ai_use_special(u, alive_allies, alive_enemies):
#     use_special(u, alive_allies, alive_enemies)
#
# This makes the AI follow the difficulty rules defined above.


# ------------------------------------------
# TURN ORDER
# ------------------------------------------

def get_turn_order(all_units):
    """Determine order of units for this turn based on initiative + randomness"""
    alive = alive_units(all_units)
    for u in alive:
        u["init_roll"] = u["init"] + random.random()
    return sorted(alive, key=lambda u: u["init_roll"], reverse=True)


def show_morale(player_team, enemy_team):
    """Print morale status of all units"""
    print("\n--- MORALE STATUS ---")
    print("Player Team:")
    for u in player_team:
        print(f"{u['name']}: {u['morale_state'].upper()}")
    print("Enemy Team:")
    for u in enemy_team:
        print(f"{u['name']}: {u['morale_state'].upper()}")
    print("--------------------\n")


def take_turn(u, all_units):
    """
    Executes a single unit's turn:
    - Checks morale and fleeing
    - Allows multiple actions while unit has AP
    - Executes actions
    """
    if u["hp"] <= 0:
        return

    # Gather allies and enemies first
    allies = [x for x in all_units if x["owner"] == u["owner"] and x["hp"] > 0]
    enemies = [x for x in all_units if x["owner"] != u["owner"] and x["hp"] > 0]

    # --- Morale check: may panic or flee ---
    if not morale_turn_check(u, allies):
        if u.get("fleeing"):
            u["flee_turns"] = u.get("flee_turns", 0) + 1
            print(f"🏃 {u['name']} is fleeing! ({u['flee_turns']}/3)")
            if u["flee_turns"] >= 3:
                u["hp"] = 0
                u["escaped"] = True
                print(f"🏳️ {u['name']} has fled the battlefield!")
        return

    if not enemies:
        return

    # --- Multi-action loop ---
    actions_taken = 0
    max_actions = 3  # soft limit per turn to prevent spamming
    while u["ap"] >= 3 and u["hp"] > 0 and not u.get("fleeing") and actions_taken < max_actions:
        action = choose_action(u, allies, enemies)
        if action["type"] == "quit":
            return "quit"

        execute_action(u, action, allies, enemies)
        actions_taken += 1

        # Update enemy list in case some died
        enemies = [x for x in all_units if x["owner"] != u["owner"] and x["hp"] > 0]
        if not enemies:
            break




# ------------------------------------------
# CHOOSING ACTIONS
# ------------------------------------------

def choose_action(u, allies, enemies):
    """
    Determines the action for a unit.
    - Player chooses manually
    - AI chooses automatically
    """

    # Broken units flee
    if u["morale_state"] == "breaking":
        u["fleeing"] = True

    # -------------------------
    # PLAYER CHOICE
    # -------------------------
    if u["owner"] == "player":
        print(f"\n{u['name']} HP:{u['hp']} ARM:{u['armor']} AP:{u['ap']} FAT:{u['fatigue']}")
        options = ["1. Attack (3 AP)", "3. Skip", "4. Quit"]

        if u["morale_state"] != "breaking":
            options.insert(1, f"2. Special ({u['special']}) — {SPECIAL_COST[u['special']]} AP")

        print("\n".join(options))
        c = input("> ")

        if c == "4":
            return {"type": "quit"}
        if c == "3":
            return {"type": "skip"}
        if c == "2" and u["morale_state"] != "breaking":
            return {"type": "special"}

        target = choose_target_player(enemies, "Attack who?")
        return {"type": "attack", "target": target}

    # -------------------------
    # AI CHOICE
    # -------------------------
    valid_targets = [e for e in enemies if e["hp"] > 0]

    if not valid_targets:
        return {"type": "skip"}

    # AI special use
    if (
        u["morale_state"] != "breaking"
        and u["ap"] >= SPECIAL_COST[u["special"]]
        and random.random() < (0.2 if AI_DIFFICULTY == "easy" else 0.4 if AI_DIFFICULTY == "normal" else 0.6)
    ):
        return {"type": "special"}

    # Prefer non-fleeing targets
    non_fleeing = [e for e in valid_targets if not e.get("fleeing")]
    targets = non_fleeing if non_fleeing else valid_targets

    return {
        "type": "attack",
        "target": choose_target_ai(u, targets)
    }



# ------------------------------------------
# EXECUTING ACTIONS
# ------------------------------------------

def execute_action(u, action, allies, enemies):
    """
    Resolves the chosen action:
    - Skip, special, or attack
    - Handles damage, riposte, and morale effects
    """
    if action["type"] == "skip":
        return

    if action["type"] == "special":
        use_special(u, allies, enemies)
        return

    if action["type"] == "attack":
        if u["ap"] < 3:
            print("❌ Not enough AP!")
            return

        target = action["target"]
        hit, chance, roll = roll_to_hit(u, target)

        u["ap"] -= 3
        apply_fatigue(u, FATIGUE_GAIN["basic_attack"])

        # FLEEING DAMAGE MODIFIER
        dmg_multiplier = 1.25 if target.get("fleeing") else 1.0

        if hit:
            dmg = int(deal_damage(u, target) * dmg_multiplier)
            print(f"{u['name']} hits {target['name']} for {dmg}! ({roll} ≤ {chance}%)")
            morale_hit(target, dmg)
            check_death(target, allies=enemies)

            if target.get("riposte") and target["hp"] > 0:
                rdmg = int(target["atk"] * 0.6)
                u["hp"] -= rdmg
                print(f"⚡ RIPOSTE for {rdmg}!")
                check_death(u, allies=allies)

        else:
            print(f"{u['name']} MISSES {target['name']}! ({roll} > {chance}%)")


# ------------------------------------------
# BATTLE LOOP
# ------------------------------------------

def battle(player_team):
    """Main battle loop"""
    enemy_team = [create_unit(n, "enemy") for n in random.sample(list(MERCENARIES.keys()), 4)]
    all_units = player_team + enemy_team

    # Initialize flee counters
    for u in all_units:
        u["flee_turns"] = 0
        u["escaped"] = False

    print("\n⚔️ BATTLE START!\n")

    while True:
        # Check win/loss
        if not any(u["hp"] > 0 and u["owner"] == "player" for u in all_units):
            print("💀 Your party has been defeated!")
            return "end"

        if not any(u["hp"] > 0 and u["owner"] == "enemy" for u in all_units):
            print("🏆 Victory!")
            return "end"

        # Reset temporary flags each turn
        for u in all_units:
            u["guarding"] = None
            u["riposte"] = False
            regen_ap(u)

        # Determine turn order
        turn_order = get_turn_order(all_units)

        print("\n=== TURN ORDER ===")
        for u in turn_order:
            if u.get("escaped"):
                continue
            print(f"{u['name']} ({u['owner'][0].upper()}) INIT:{u['init']} AP:{u['ap']}")

        # Execute each unit's turn
        for u in turn_order:
            if u.get("escaped"):
                continue
            result = take_turn(u, all_units)
            if result == "quit":
                print("Exiting battle...")
                return "end"

# ------------------------------------------
# Simulator
# ------------------------------------------

def simulate_battle(player_team_names, enemy_team_names=None, verbose=True):
    """
    Simulate a battle automatically between two teams.
    - Player team and enemy team act automatically (AI controlled).
    - Handles AP, fatigue, morale, fleeing, riposte, specials, etc.
    
    :param player_team_names: List of mercenary names for player side
    :param enemy_team_names: List of mercenary names for enemy side (random if None)
    :param verbose: If True, prints battle progress
    """

    # ------------------------------
    # CREATE TEAMS
    # ------------------------------
    # Each unit is created using create_unit()
    # 'ai_control=True' means it will automatically make decisions
    player_team = [create_unit(name, "player", ai_control=True) for name in player_team_names]

    if enemy_team_names:
        enemy_team = [create_unit(name, "enemy", ai_control=True) for name in enemy_team_names]
    else:
        # Randomly pick 4 mercenaries for the enemy if none provided
        enemy_team = [create_unit(n, "enemy", ai_control=True) for n in random.sample(list(MERCENARIES.keys()), 4)]

    # Simple helper function to check if a team still has alive units
    def team_alive(team):
        return any(u["hp"] > 0 for u in team)

    round_count = 1

    if verbose:
        print("\n⚔️ SIMULATION START!\n")

    # ------------------------------
    # MAIN BATTLE LOOP
    # ------------------------------
    while team_alive(player_team) and team_alive(enemy_team):
        # Reset temporary flags at the start of each round
        for u in player_team + enemy_team:
            u["guarding"] = None  # Clear guarding
            u["riposte"] = False  # Clear riposte setup
            regen_ap(u)           # Restore AP based on fatigue

        # Determine turn order for all units based on initiative + randomness
        all_units = player_team + enemy_team
        turn_order = get_turn_order(all_units)

        if verbose:
            print(f"\n=== ROUND {round_count} ===")
            for u in turn_order:
                print(f"{u['name']} ({u['owner'][0].upper()}) INIT:{u['init']} AP:{u['ap']} Morale:{u['morale_state'].upper()}")

        # ------------------------------
        # EACH UNIT TAKES A TURN
        # ------------------------------
        for u in turn_order:
            if u["hp"] <= 0: 
                continue  # Skip dead units

            # Identify allies and enemies for this unit
            allies  = player_team if u["owner"]=="player" else enemy_team
            enemies = enemy_team if u["owner"]=="player" else player_team

            alive_enemies = alive_units(enemies)
            alive_allies = alive_units(allies)

            if not alive_enemies: 
                break  # End if no enemies left

            # ------------------------------
            # AI DECISION: Special or Basic Attack
            # ------------------------------
            action_taken = False
            # Try to use special attack if enough AP and random chance allows
            if u["ap"] >= SPECIAL_COST[u["special"]] and random.random() < 0.5:
                action_taken = use_special(u, alive_allies, alive_enemies)

            if not action_taken:
                # Use basic attack if special was not used
                target = random.choice(alive_enemies)  # Random target
                hit, chance, roll = roll_to_hit(u, target)
                ap_cost = min(u["ap"], 3)
                u["ap"] -= ap_cost
                apply_fatigue(u, FATIGUE_GAIN["basic_attack"])

                # Extra damage if target is fleeing
                dmg_multiplier = 1.25 if target.get("fleeing") else 1.0

                if hit:
                    dmg = int(deal_damage(u, target) * dmg_multiplier)
                    if verbose:
                        print(f"{u['name']} hits {target['name']} for {dmg}! ({roll} ≤ {chance}%)")
                    morale_hit(target, dmg)  # Reduce morale based on damage
                    check_death(target, allies=enemies)  # Check if target dies
                else:
                    if verbose:
                        print(f"{u['name']} MISSES {target['name']}! ({roll} > {chance}%)")
                    apply_morale(u, -2)  # Missing reduces morale slightly

                # Check if target has riposte ready and deal damage back
                if target.get("riposte") and target["hp"] > 0:
                    rdmg = int(target["atk"] * 0.6)
                    u["hp"] -= rdmg
                    if verbose:
                        print(f"⚡ RIPOSTE for {rdmg}!")
                    check_death(u, allies=allies)

        # Optionally show morale after round
        if verbose:
            show_morale(player_team, enemy_team)

        round_count += 1

    # ------------------------------
    # DETERMINE WINNER
    # ------------------------------
    winner = "Player" if team_alive(player_team) else "Enemy"

    if verbose:
        print(f"\n🏆 SIMULATION END — {winner} WINS!")
        print("\n--- FINAL STATUS ---")
        print("Player Team:")
        for u in player_team: 
            print_unit(u)
        print("Enemy Team:")
        for u in enemy_team: 
            print_unit(u)

    # Return results as a dictionary
    return {
        "winner": winner,
        "rounds": round_count - 1,
        "player_team": player_team,
        "enemy_team": enemy_team
    }


# ------------------------------------------
# AI DIFFICULTY SELECTION
# ------------------------------------------
def choose_ai_difficulty():
    """
    Allows the player to choose AI difficulty.
    Sets the global AI_DIFFICULTY variable.
    """
    global AI_DIFFICULTY

    print("\n⚔️  CHOOSE YOUR CHALLENGE  ⚔️")
    print("1. Easy    — The enemy stumbles and hesitates.")
    print("2. Normal  — Veterans who know fear, but fight on.")
    print("3. Hard    — They smell weakness. They show no mercy.")
    print("\nYou think you are worthy?\n")

    choice = input("> ")

    if choice == "1":
        AI_DIFFICULTY = "easy"
    elif choice == "3":
        AI_DIFFICULTY = "hard"
    else:
        AI_DIFFICULTY = "normal"

    print(f"\n🧠 Enemy tactics set to: {AI_DIFFICULTY.upper()}\n")


# ------------------------------------------
# MAIN MENU
# ------------------------------------------
def main():
    while True:
        print("\n=== BATTLE BROTHERS SIM — AP & FATIGUE EDITION ===")
        print("1. Create Team (Manual Battle)")
        print("2. Exit")
        print("3. Simulate Battle (Auto)")

        c = input("> ")

        if c == "2":
            sys.exit()

        elif c == "1":
            team = team_selection()
            choose_ai_difficulty()  # ← Ask for AI difficulty before battle
            battle(team)
            print("\nReturning to main menu...\n")

        elif c == "3":
            # Ask user which team to simulate
            print("\nChoose your 4 mercenaries for simulation:")
            chosen_names = []
            while len(chosen_names) < 4:
                for i, m in enumerate(MERCENARIES.keys()):
                    print(f"{i+1}. {m}")
                pick = input(f"Pick #{len(chosen_names)+1}: ")
                if pick.isdigit():
                    idx = int(pick)
                    names = list(MERCENARIES.keys())
                    if 1 <= idx <= len(names):
                        chosen_names.append(names[idx-1])
                        continue
                print("Invalid.")

            choose_ai_difficulty()  # ← Ask for AI difficulty before auto battle
            print("\nSimulating battle...\n")
            simulate_battle(player_team_names=chosen_names, verbose=True)

        else:
            print("Invalid choice.")

main()
