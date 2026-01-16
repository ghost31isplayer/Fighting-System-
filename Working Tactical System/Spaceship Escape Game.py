# ==========================================
# SPACE HULK – TERMINAL UI + LEGEND + ATTACK
# ==========================================

import random
 
# ==========================================
# Briefing
# ==========================================

def show_briefing():
    print("""
====================================================
 IMPERIAL BRIEFING – EYES ONLY
====================================================

SITUATION:
You are deployed aboard a derelict Space Hulk.
Hostile lifeforms detected: GENESTEALERS.

MISSION:
Advance through the Hulk.
Eliminate hostile contacts.
Reach the exit.

----------------------------------------------------
RULES OF ENGAGEMENT
----------------------------------------------------
• Turn-based operations.
• Actions consume Action Points (AP).
• When AP is expended, hostile units act.
• Contact with enemy results in mission failure.
• Visibility is limited. Unseen areas are unknown.
• Doors may be opened by either side.

----------------------------------------------------
TACTICAL ANALYSIS (METT-TC)
----------------------------------------------------
MISSION:
Reach the exit. Neutralize threats.

ENEMY:
Genestealers.
Close-range ambush predators.
Lethal on contact.

TERRAIN:
Confined corridors.
Limited visibility.
Restricted movement.
Doors and corners dominate engagements.

TROOPS:
Single Space Marine.
Limited action economy.
Sustained close combat expected.

TIME:
Turn-based execution.
Enemy phase follows player turn.

----------------------------------------------------
END STATE
----------------------------------------------------
• SUCCESS: Reach the exit.
• FAILURE: Enemy reaches your position.

----------------------------------------------------
Press ENTER to begin mission.
----------------------------------------------------
""")
    input()


# ==========================================
# CONSTANTS
# ==========================================

DIRECTIONS = ["N", "E", "S", "W"]
DIR_VECTORS = {
    "N": (0, -1),
    "E": (1, 0),
    "S": (0, 1),
    "W": (-1, 0)
}

DIR_ARROWS = {
    "N": "↑",
    "E": "→",
    "S": "↓",
    "W": "←"
}

TURN_COST = 1
MOVE_COST = 1
OPEN_DOOR_COST = 1
MELEE_AP_COST = 1
RANGED_AP_COST = 2

MAP_WIDTH = 80
MAP_HEIGHT = 40
VISION_RADIUS = 5  # how far the player can see


# ==========================================
# TROOPER SELECTION
# ==========================================



troopers = {
    "1": {"name": "Assault Marine", "max_ap": 6, "melee": 1, "range": 3},
    "2": {"name": "Heavy Gunner", "max_ap": 4, "melee": 1, "range": 5},
    "3": {"name": "Flamer", "max_ap": 5, "melee": 1, "range": 3, "flame": True},
    "4": {"name": "Sergeant", "max_ap": 6, "melee": 2, "range": 4},
    "5": {"name": "Scout", "max_ap": 7, "melee": 1, "range": 2}
}


print("Choose your trooper:")
for k, t in troopers.items():
    print(f"{k}. {t['name']} (AP: {t['max_ap']})")

choice = input("> ")
player = troopers.get(choice, troopers["1"])
input(f"\n{player['name']} locked and loaded. Press ENTER...")

show_briefing()

# ==========================================
# GAME STATE
# ==========================================

player_x = 0
player_y = 0
player_facing = "N"
player_ap = player["max_ap"]
player_alive = True

genestealers = []
current_level = 1
sector = 1
map_data = []

message_log = []  # logs last messages

# ==========================================
# CONSTANTS & MAP SETTINGS
# ==========================================

MAP_WIDTH = 40
MAP_HEIGHT = 20
VISION_RADIUS = 5  # how far the player can see

# ==========================================
# MAP GENERATION & FLOOR FINDING
# ==========================================

def generate_map(width, height):
    """Generate a corridor-based map with doors and a single exit."""
    grid = [["#" for _ in range(width)] for _ in range(height)]

    # Start carving from the center
    x, y = width // 2, height // 2
    grid[y][x] = "."

    # Random corridor generation
    for _ in range((width * height) // 2):
        dx, dy = random.choice(list(DIR_VECTORS.values()))
        nx, ny = x + dx, y + dy
        if 1 < nx < width - 2 and 1 < ny < height - 2:
            x, y = nx, ny
            if grid[y][x] == "#":
                grid[y][x] = "."
                # 7% chance to add a closed door
                if random.random() < 0.07:
                    grid[y][x] = "D"

    # Place exit on a random floor tile
    while True:
        ex, ey = random.randint(1, width - 2), random.randint(1, height - 2)
        if grid[ey][ex] == ".":
            grid[ey][ex] = ">"
            break

    return grid

def find_floor():
    """Return coordinates of a random floor tile for player or enemies."""
    while True:
        x = random.randint(1, MAP_WIDTH - 2)
        y = random.randint(1, MAP_HEIGHT - 2)
        if map_data[y][x] == ".":
            return x, y

# ==========================================
# FIELD OF VIEW
# ==========================================

def in_fov(x, y):
    """Check if a tile is within the player's vision radius."""
    return abs(player_x - x) <= VISION_RADIUS and abs(player_y - y) <= VISION_RADIUS

# ==========================================
# DRAW MAP WITH FOG OF WAR
# ==========================================

def draw_map():
    """Draw the map with fog of war based on VISION_RADIUS."""
    print("\n" * 2)
    for y, row in enumerate(map_data):
        for x, tile in enumerate(row):
            if not in_fov(x, y):
                # Tile is out of vision radius
                print("?", end="")
            elif x == player_x and y == player_y:
                # Player position
                print(DIR_ARROWS[player_facing], end="")
            elif any(g["x"] == x and g["y"] == y for g in genestealers):
                # Enemy in vision
                print("G", end="")
            else:
                # Visible map tile
                print(tile, end="")
        print()


# ==========================================
# LEVEL SETUP
# ==========================================

def new_level():
    global map_data, player_x, player_y, genestealers, current_level, sector

    if current_level % 20 == 0:
        sector += 1
        input(f"\n=== ENTERING SECTOR {sector} ===")

    map_data = generate_map(MAP_WIDTH, MAP_HEIGHT)

    # Place player near center, fallback to random floor
    player_x, player_y = MAP_WIDTH // 2, MAP_HEIGHT // 2
    if map_data[player_y][player_x] == "#":
        player_x, player_y = find_floor()

    # Place genestealers
    genestealers = []
    for _ in range(2 + sector):
        while True:
            gx, gy = find_floor()
            if abs(gx - player_x) + abs(gy - player_y) > 3:
                genestealers.append({"x": gx, "y": gy})
                break

    current_level += 1
    message_log.append(f"New level {current_level} entered. Sector: {sector}")



def draw_ui():
    dx, dy = DIR_VECTORS[player_facing]
    nx, ny = player_x + dx, player_y + dy
    front_tile = map_data[ny][nx] if 0 <= nx < MAP_WIDTH and 0 <= ny < MAP_HEIGHT else "#"

    print("\n--------------------------------")
    print(f"Facing: {DIR_ARROWS[player_facing]}   AP: {player_ap}/{player['max_ap']}")
    print(f"Level: {current_level - 1}   Sector: {sector}")
    print("--------------------------------")

    print("\n--- Actions ---")
    print("[1] Move Forward (1 AP)")
    print("[2] Turn Left    (1 AP)")
    print("[3] Turn Right   (1 AP)")
    print("[4] Open Door    (1 AP)")
    print("[5] Melee Attack (1 AP, in front)")
    print("[6] Ranged Attack (2 AP, range depends on weapon)")
    print("[7] Overwatch    (2 AP, attacks enemies moving into range)")
    print("[8] End Turn")
    print("[Q] Quit")


    print("\nMAP LEGEND")
    print("#########")
    print("#  # = Wall")
    print("#  . = Corridor")
    print("#  D = Closed Door")
    print("#  O = Open Door")
    print("#  > = Exit to next level")
    print("#  ↑ → ↓ ← = Your Marine (Facing)")
    print("#  G = Genestealer")
    print("#########")

    if message_log:
        print("\n-- Last Action --")
        for msg in message_log[-5:]:  # show more for enemy moves
            print(msg)
        print("-----------------")


# ==========================================
# PLAYER ACTIONS – UPDATED WITH TROOPER STATS
# ==========================================

def move_forward():
    global player_x, player_y, player_ap, player_alive
    message_log.clear()

    if player_ap < MOVE_COST:
        message_log.append("Not enough AP to move!")
        return

    dx, dy = DIR_VECTORS[player_facing]
    nx, ny = player_x + dx, player_y + dy
    tile = map_data[ny][nx]

    if tile in "#D":
        message_log.append("Blocked! Cannot move forward.")
        return

    if tile == ">":
        message_log.append("You move to the next level!")
        new_level()
        return

    if any(g["x"] == nx and g["y"] == ny for g in genestealers):
        message_log.append("A Genestealer hits you while moving!")
        player_alive = False
        return

    player_x, player_y = nx, ny
    player_ap -= MOVE_COST
    message_log.append("You move forward.")

def turn_left():
    global player_facing, player_ap
    message_log.clear()
    if player_ap < TURN_COST:
        message_log.append("Not enough AP to turn!")
        return
    player_facing = DIRECTIONS[(DIRECTIONS.index(player_facing) - 1) % 4]
    player_ap -= TURN_COST
    message_log.append("You turn left.")

def turn_right():
    global player_facing, player_ap
    message_log.clear()
    if player_ap < TURN_COST:
        message_log.append("Not enough AP to turn!")
        return
    player_facing = DIRECTIONS[(DIRECTIONS.index(player_facing) + 1) % 4]
    player_ap -= TURN_COST
    message_log.append("You turn right.")

def open_door():
    global player_ap
    message_log.clear()
    if player_ap < OPEN_DOOR_COST:
        message_log.append("Not enough AP to open door!")
        return
    dx, dy = DIR_VECTORS[player_facing]
    nx, ny = player_x + dx, player_y + dy
    if map_data[ny][nx] == "D":
        map_data[ny][nx] = "O"
        player_ap -= OPEN_DOOR_COST
        message_log.append("You open the door.")
    else:
        message_log.append("No door to open!")

def melee_attack():
    global player_ap
    message_log.clear()
    if player_ap < MELEE_AP_COST:
        message_log.append("Not enough AP for melee attack!")
        return

    dx, dy = DIR_VECTORS[player_facing]
    nx, ny = player_x + dx, player_y + dy

    hit = False
    melee_strength = player.get("melee", 1)  # Use trooper-specific melee
    for _ in range(melee_strength):
        for g in genestealers:
            if g["x"] == nx and g["y"] == ny:
                hit = True
                genestealers.remove(g)
                message_log.append("You strike a Genestealer with your melee attack!")
                break
        if hit:
            break
    if not hit:
        message_log.append("Melee attack misses! No enemy in front.")
    player_ap -= MELEE_AP_COST

def ranged_attack():
    global player_ap
    message_log.clear()
    if player_ap < RANGED_AP_COST:
        message_log.append("Not enough AP for ranged attack!")
        return

    range_limit = player.get("range", 3)  # Use trooper-specific range
    hit = False
    dx, dy = DIR_VECTORS[player_facing]

    for dist in range(1, range_limit + 1):
        nx = player_x + dx * dist
        ny = player_y + dy * dist
        for g in genestealers:
            if g["x"] == nx and g["y"] == ny:
                hit = True
                genestealers.remove(g)
                message_log.append(f"You shoot a Genestealer at range {dist}!")
                break
        if hit:
            break
    if not hit:
        message_log.append("Ranged attack hits nothing.")
    player_ap -= RANGED_AP_COST

def flame_attack():
    """Special Flamer attack: hits 3 tiles in a line, affects all enemies in path"""
    global player_ap
    message_log.clear()
    FLAME_COST = 3
    if player_ap < FLAME_COST:
        message_log.append("Not enough AP for Flamer attack!")
        return

    flame_range = 3
    dx, dy = DIR_VECTORS[player_facing]
    hit_any = False

    for dist in range(1, flame_range + 1):
        nx = player_x + dx * dist
        ny = player_y + dy * dist
        to_remove = [g for g in genestealers if g["x"] == nx and g["y"] == ny]
        for g in to_remove:
            genestealers.remove(g)
            hit_any = True

    if hit_any:
        message_log.append("You unleash the Flamer, burning everything in front!")
    else:
        message_log.append("Flamer hits nothing.")
    player_ap -= FLAME_COST

# ==========================================
# PLAYER STATE
# ==========================================
player_overwatch = False  # Tracks if player is on overwatch this turn
player_weapon = "default"  # For weapon attack patterns
WEAPON_ATTACK_PATTERNS = {
    "default": {
        "N": [(0, -1), (-1, -1), (1, -1)],
        "S": [(0, 1), (-1, 1), (1, 1)],
        "E": [(1, 0), (1, -1), (1, 1)],
        "W": [(-1, 0), (-1, -1), (-1, 1)]
    }
}

# ==========================================
# GENESTEALER AI
# ==========================================

GENESTEALER_AP = 3  # Actions per Genestealer per turn

def is_in_overwatch(gx, gy):
    """Check if a Genestealer is in player's overwatch zone."""
    pattern = WEAPON_ATTACK_PATTERNS[player_weapon][player_facing]
    for ox, oy in pattern:
        if (player_x + ox, player_y + oy) == (gx, gy):
            return True
    return False

def damage_genestealer(g):
    """Remove or damage Genestealer."""
    if "hp" not in g:
        g["hp"] = 1
    g["hp"] -= 1
    if g["hp"] <= 0:
        genestealers.remove(g)
        message_log.append(f"Genestealer at ({g['x']},{g['y']}) destroyed by overwatch!")

def genestealer_turn():
    global player_alive, player_overwatch

    for g in genestealers:
        g_ap = GENESTEALER_AP
        while g_ap > 0 and player_alive:

            dx = player_x - g["x"]
            dy = player_y - g["y"]

            step_x = 0 if dx == 0 else int(dx / abs(dx))
            step_y = 0 if dy == 0 else int(dy / abs(dy))

            # Determine next step (prefer axis with longer distance)
            if abs(dx) > abs(dy):
                if random.random() < 0.8:
                    nx, ny = g["x"] + step_x, g["y"]
                else:
                    nx, ny = g["x"], g["y"] + step_y
            else:
                if random.random() < 0.8:
                    nx, ny = g["x"], g["y"] + step_y
                else:
                    nx, ny = g["x"] + step_x, g["y"]

            # -------------------------
            # Check Player Overwatch
            # -------------------------
            if player_overwatch and is_in_overwatch(g["x"], g["y"]):
                message_log.append(f"Overwatch! Genestealer at ({g['x']}, {g['y']}) fired upon!")
                damage_genestealer(g)
                g_ap = 0
                break  # stop this Genestealer's turn if hit

            # -------------------------
            # Check Map Tile
            # -------------------------
            if map_data[ny][nx] == "#":
                # Try moving along the other axis if blocked
                alt_nx, alt_ny = g["x"], g["y"]
                if nx != g["x"]: alt_nx = g["x"]
                if ny != g["y"]: alt_ny = g["y"]
                if map_data[alt_ny][alt_nx] == "#":
                    message_log.append("A Genestealer bumps into a wall.")
                    g_ap = 0
                    break
                else:
                    nx, ny = alt_nx, alt_ny

            elif map_data[ny][nx] == "D":
                map_data[ny][nx] = "O"
                message_log.append("A Genestealer opens a door.")
                g_ap -= 1
                continue

            elif (nx, ny) == (player_x, player_y):
                message_log.append("A Genestealer attacks you!")
                player_alive = False
                g_ap = 0
                break

            elif any(other["x"] == nx and other["y"] == ny for other in genestealers if other != g):
                message_log.append("A Genestealer waits for space to move.")
                g_ap = 0
                break

            # -------------------------
            # Move Genestealer
            # -------------------------
            else:
                old_x, old_y = g["x"], g["y"]
                g["x"], g["y"] = nx, ny

                move_dir = ""
                if nx > old_x: move_dir = "east"
                elif nx < old_x: move_dir = "west"
                elif ny > old_y: move_dir = "south"
                elif ny < old_y: move_dir = "north"

                message_log.append(f"Genestealer moves {move_dir}.")
                g_ap -= 1

    # Reset overwatch after all Genestealers finish their turn
    player_overwatch = False

# ==========================================
# PLAYER ACTION: Overwatch
# ==========================================

def player_overwatch_action():
    global player_ap, player_overwatch
    if player_ap >= 2:
        player_ap -= 2
        player_overwatch = True
        message_log.append("Overwatch ready! Any enemy moving into range will be fired upon.")
    else:
        message_log.append("Not enough AP for Overwatch!")

# ==========================================
# GAME LOOP
# ==========================================

new_level()

while player_alive:
    player_ap = player["max_ap"]

    while player_ap > 0:
        draw_map()
        draw_ui()

        cmd = input("> ").lower()

        if cmd == "q":
            exit()
        elif cmd == "1" or cmd == "w":
            move_forward()
        elif cmd == "2" or cmd == "a":
            turn_left()
        elif cmd == "3" or cmd == "d":
            turn_right()
        elif cmd == "4" or cmd == "o":
            open_door()
        elif cmd == "5" or cmd == "m":
            melee_attack()
        elif cmd == "6" or cmd == "r":
            ranged_attack()
        elif cmd == "7" or cmd == "e":
            break

    genestealer_turn()

print("\nMISSION FAILED. THE HULK CONSUMES ALL.")
