import random
import sys

# =============================
# SKILL EXECUTION FUNCTIONS
# =============================

def attack_damage(min_dmg, max_dmg):
    return random.randint(min_dmg, max_dmg)


def skill_hack(attacker, defender):
    dmg = attack_damage(20, 30)
    print(f"{attacker['name']} hacks {defender['name']} for {dmg} damage!")


def skill_chop(attacker, defender):
    dmg = attack_damage(25, 35)
    print(f"{attacker['name']} delivers a heavy chop for {dmg} damage!")


def skill_break_shield(attacker, defender):
    print(f"{attacker['name']} attempts to break {defender['name']}'s shield!")


def skill_mighty_swing(attacker, defender):
    dmg = attack_damage(35, 50)
    print(f"{attacker['name']} performs a mighty swing for {dmg} damage!")


def skill_slash(attacker, defender):
    dmg = attack_damage(18, 28)
    print(f"{attacker['name']} slashes {defender['name']} for {dmg} damage!")


def skill_lunge(attacker, defender):
    dmg = attack_damage(22, 32)
    print(f"{attacker['name']} lunges forward for {dmg} damage!")


def skill_thrust(attacker, defender):
    dmg = attack_damage(20, 30)
    print(f"{attacker['name']} thrusts the spear for {dmg} damage!")


def skill_spearwall(attacker, defender):
    print(f"{attacker['name']} sets up a spearwall!")


def skill_shoot_arrow(attacker, defender):
    dmg = attack_damage(25, 40)
    print(f"{attacker['name']} shoots an arrow for {dmg} damage!")


def skill_aimed_shot(attacker, defender):
    dmg = attack_damage(35, 55)
    print(f"{attacker['name']} fires an aimed shot for {dmg} damage!")


def skill_crossbow_shot(attacker, defender):
    dmg = attack_damage(40, 60)
    print(f"{attacker['name']} fires a crossbow bolt for {dmg} damage!")


def skill_reload(attacker, defender):
    print(f"{attacker['name']} reloads the crossbow.")


def skill_shieldwall(attacker, defender):
    print(f"{attacker['name']} raises a shield wall!")


def skill_shield_bash(attacker, defender):
    print(f"{attacker['name']} bashes with the shield!")


# =============================
# SKILLS DATABASE
# =============================

SKILLS = {
    # AXES
    "hack": {"name": "Hack", "ap": 4, "fat": 10, "execute": skill_hack},
    "chop": {"name": "Chop", "ap": 5, "fat": 14, "execute": skill_chop},
    "break_shield": {"name": "Break Shield", "ap": 6, "fat": 20, "execute": skill_break_shield},
    "mighty_swing": {"name": "Mighty Swing", "ap": 7, "fat": 25, "execute": skill_mighty_swing},

    # SWORDS
    "slash": {"name": "Slash", "ap": 4, "fat": 8, "execute": skill_slash},
    "lunge": {"name": "Lunge", "ap": 6, "fat": 15, "execute": skill_lunge},

    # SPEARS
    "thrust": {"name": "Thrust", "ap": 5, "fat": 10, "execute": skill_thrust},
    "spearwall": {"name": "Spearwall", "ap": 6, "fat": 20, "execute": skill_spearwall},

    # BOWS
    "shoot_arrow": {"name": "Shoot Arrow", "ap": 5, "fat": 12, "execute": skill_shoot_arrow},
    "aimed_shot": {"name": "Aimed Shot", "ap": 7, "fat": 25, "execute": skill_aimed_shot},

    # CROSSBOWS
    "crossbow_shot": {"name": "Crossbow Shot", "ap": 6, "fat": 15, "execute": skill_crossbow_shot},
    "reload": {"name": "Reload", "ap": 4, "fat": 5, "execute": skill_reload},

    # SHIELDS
    "shieldwall": {"name": "Shieldwall", "ap": 4, "fat": 15, "execute": skill_shieldwall},
    "shield_bash": {"name": "Shield Bash", "ap": 5, "fat": 12, "execute": skill_shield_bash},
}


# =============================
# WEAPONS
# =============================

WEAPONS = {
    # AXES
    "handaxe": {"name": "Handaxe", "skills": {"hack", "chop", "break_shield"}},
    "greataxe": {"name": "Greataxe", "skills": {"hack", "mighty_swing", "break_shield"}},

    # SWORDS
    "arming_sword": {"name": "Arming Sword", "skills": {"slash", "lunge"}},
    "longsword": {"name": "Longsword", "skills": {"slash", "lunge"}},

    # SPEARS
    "spear": {"name": "Spear", "skills": {"thrust", "spearwall"}},
    "pike": {"name": "Pike", "skills": {"thrust", "spearwall"}},

    # RANGED
    "bow": {"name": "Hunting Bow", "skills": {"shoot_arrow", "aimed_shot"}},
    "crossbow": {"name": "Crossbow", "skills": {"crossbow_shot", "reload"}},
}


# =============================
# SHIELDS
# =============================

SHIELDS = {
    "buckler": {
        "name": "Buckler",
        "block_chance": 0.10,
        "skills": {"shield_bash"},
    },
    "kite_shield": {
        "name": "Kite Shield",
        "block_chance": 0.20,
        "skills": {"shieldwall", "shield_bash"},
    }
}


# ======================================================
# UNIT CREATION
# ======================================================

def create_unit(name, weapon_id, ai=False):
    return {
        "name": name,
        "weapon": WEAPONS[weapon_id],
        "hp": 80,
        "max_hp": 80,
        "armor": 60,
        "melee_skill": 55,
        "melee_def": 20,
        "fatigue": 0,
        "fatigue_max": 100,
        "ap": 9,
        "ap_max": 9,
        "morale": 50,
        "morale_state": "steady",
        "fleeing": False,
        "ai": ai,
    }

# ======================================================
# CORE SYSTEMS
# ======================================================

def update_morale(unit):
    if unit["morale"] >= 60:
        unit["morale_state"] = "confident"
    elif unit["morale"] >= 30:
        unit["morale_state"] = "steady"
    elif unit["morale"] >= 10:
        unit["morale_state"] = "wavering"
    else:
        unit["morale_state"] = "breaking"

def apply_damage(unit, dmg):
    if unit["armor"] > 0:
        absorbed = min(unit["armor"], int(dmg * 0.7))
        unit["armor"] -= absorbed
        dmg -= absorbed
    unit["hp"] -= dmg
    unit["morale"] -= random.randint(3, 6)
    update_morale(unit)

def roll_to_hit(attacker, defender):
    chance = 60 + (attacker["melee_skill"] - defender["melee_def"])
    if attacker["morale_state"] == "confident":
        chance += 10
    if attacker["morale_state"] == "breaking":
        chance -= 20
    chance = max(5, min(95, chance))
    roll = random.randint(1, 100)
    return roll <= chance, chance, roll

def regen_ap(unit):
    regen = max(3, 6 - unit["fatigue"] // 20)
    unit["ap"] = min(unit["ap_max"], unit["ap"] + regen)

# ======================================================
# ACTIONS
# ======================================================

def attack(attacker, defender):
    if attacker["ap"] < 3:
        print("Not enough AP.")
        return
    attacker["ap"] -= 3
    attacker["fatigue"] += 8

    hit, chance, roll = roll_to_hit(attacker, defender)
    if hit:
        dmg = random.randint(15, 25)
        print(f"HIT! ({roll} ≤ {chance})")
        apply_damage(defender, dmg)
    else:
        print(f"MISS! ({roll} > {chance})")

def use_skill(attacker, defender, skill_id):
    skill = SKILLS[skill_id]
    if attacker["ap"] < skill["ap"]:
        print("Not enough AP.")
        return
    attacker["ap"] -= skill["ap"]
    attacker["fatigue"] += skill["fat"]
    skill["fn"](attacker, defender)

def rest(unit):
    unit["fatigue"] = max(0, unit["fatigue"] - 20)
    unit["ap"] = 0
    print(f"{unit['name']} catches their breath.")

# ======================================================
# TURN HANDLING
# ======================================================

def player_turn(player, enemy):
    while player["ap"] > 0 and not player["fleeing"]:
        print_status(player, enemy)
        print("\n1. Attack (3 AP)")
        print("2. Skill")
        print("3. Rest")
        print("4. Skip")
        print("5. Quit")

        c = input("> ")

        if c == "5":
            sys.exit()
        if c == "4":
            return
        if c == "3":
            rest(player)
            return
        if c == "1":
            attack(player, enemy)
        if c == "2":
            for i, sid in enumerate(player["weapon"]["skills"], 1):
                s = SKILLS[sid]
                print(f"{i}. {s['name']} (AP {s['ap']})")
            pick = input("> ")
            if pick.isdigit():
                sid = player["weapon"]["skills"][int(pick)-1]
                use_skill(player, enemy, sid)

def ai_turn(ai, enemy):
    if ai["morale_state"] == "breaking" and random.random() < 0.4:
        ai["fleeing"] = True
        print(f"{ai['name']} breaks and flees!")
        return

    if ai["ap"] >= 4 and random.random() < 0.6:
        sid = random.choice(ai["weapon"]["skills"])
        use_skill(ai, enemy, sid)
    else:
        attack(ai, enemy)

# ======================================================
# DISPLAY
# ======================================================

def print_status(p, e):
    print("\n----------------------------")
    print(f"{p['name']} | HP:{p['hp']} ARM:{p['armor']} AP:{p['ap']} FAT:{p['fatigue']} MOR:{p['morale_state']}")
    print(f"{e['name']} | HP:{e['hp']} ARM:{e['armor']} AP:{e['ap']} FAT:{e['fatigue']} MOR:{e['morale_state']}")
    print("----------------------------")

# ======================================================
# GAME LOOP
# ======================================================

def choose_weapon():
    print("Choose your weapon:")
    for i, w in enumerate(WEAPONS.keys(), 1):
        print(f"{i}. {WEAPONS[w]['name']}")
    pick = int(input("> "))
    return list(WEAPONS.keys())[pick-1]

def main():
    weapon = choose_weapon()
    player = create_unit("Brother", weapon)
    enemy = create_unit("Raider", random.choice(list(WEAPONS.keys())), ai=True)

    print("\n⚔️ BATTLE START ⚔️")

    while True:
        if player["hp"] <= 0:
            print("💀 You have fallen.")
            return
        if enemy["hp"] <= 0 or enemy.get("fleeing"):
            print("🏆 Victory!")
            return

        regen_ap(player)
        regen_ap(enemy)

        player_turn(player, enemy)
        if enemy["hp"] <= 0:
            continue
        ai_turn(enemy, player)

main()
