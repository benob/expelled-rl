import rl

import actors
import graphics
import powers
import controllers

def random_choice_index(chances):
    dice = rl.random_int(1, sum(chances))
    running_sum = 0
    choice = 0
    for w in chances:
        running_sum += w
        if dice <= running_sum:
            return choice
        choice += 1
 
def random_choice(chances_dict):
    chances = list(chances_dict.values())
    strings = list(chances_dict.keys())
 
    return strings[random_choice_index(chances)]
 
def from_dungeon_level(table):
    for (value, level) in reversed(table):
        if game.dungeon_level >= level:
            return value
    return 0
 
def make_monster(choice, x, y):
    monster = None
    if choice == 'orc':
        monster = actors.Monster(x, y, graphics.ORC, 'orc', color=rl.GREEN, max_hp=20, defense=0, power=4, possession_cooldown=35)

    elif choice == 'troll':
        monster = actors.Monster(x, y, graphics.TROLL, 'troll', rl.GREEN, max_hp=40, defense=0, power=8, possession_cooldown=100, max_mana=3, actions=[powers.FEAR])
    elif choice == 'rat':
        monster = actors.Monster(x, y, graphics.RAT, 'rat', rl.GREEN, max_hp=4, defense=0, power=1, possession_cooldown=10)
    elif choice == 'bat':
        monster = actors.Monster(x, y, graphics.BAT, 'bat', rl.GREEN, max_hp=5, defense=0, power=1, possession_cooldown=20, skills=['can_fly'])
    elif choice == 'fire_elemental':
        monster = actors.Monster(x, y, graphics.FIRE_ELEMENTAL, 'fire elemental', rl.RED, max_hp=25, defense=1, power=4, possession_cooldown=150, max_mana=14, actions=[powers.FIREBALL], skills=['immune_fire'])
    elif choice == 'octopus':
        monster = actors.Monster(x, y, graphics.OCTOPUS, 'octopus', rl.BLUE, max_hp=20, defense=1, power=4, possession_cooldown=150, max_mana=6, actions=[powers.FREEZE], skills=['can_swim'])
    elif choice == 'eye':
        monster = actors.Monster(x, y, graphics.EYE, 'eye', rl.GREEN, max_hp=5, defense=1, power=1, possession_cooldown=45, max_mana=8, actions=[powers.TELEPORT, powers.CONFUSE], skills=['see_invisible', 'fly'])
    elif choice == 'ghost':
        monster = actors.Monster(x, y, graphics.GHOST, 'ghost', rl.LIGHTGRAY, max_hp=20, defense=2, power=4, possession_cooldown=30, skills=['invisible', 'see_invisible'])
    elif choice == 'dwarf':
        monster = actors.Monster(x, y, graphics.DWARF, 'dwarf', rl.YELLOW, max_hp=30, defense=1, power=4, possession_cooldown=150, max_mana=12, actions=[powers.DIG])
    elif choice == 'skeleton':
        monster = actors.Monster(x, y, graphics.SKELETON, 'skeleton', rl.WHITE, max_hp=4, defense=0, power=3, possession_cooldown=70)
    elif choice == 'necromancer':
        monster = actors.Monster(x, y, graphics.NECROMANCER, 'necromancer', rl.WHITE, max_hp=20, defense=2, power=3, possession_cooldown=170, max_mana=60, actions=[powers.SUMMON_SKELETON])
    elif choice == 'wizard':
        monster = actors.Monster(x, y, graphics.WIZARD, 'wizard', rl.BLUE, max_hp=20, defense=2, power=2, possession_cooldown=270, max_mana=50, actions=[powers.SUMMON_RAT, powers.SUMMON_BAT, powers.LIGHTNING, powers.FIREBALL])
    elif choice == 'original-body':
        monster = actors.Monster(x, y, graphics.PLAYER, 'original body', rl.YELLOW, max_hp=60, defense=4, power=8, possession_cooldown=3500, max_mana=200, skills=['invisible'], actions=[powers.SUMMON, powers.FEAR, powers.DIG, powers.CONFUSE, powers.TELEPORT, powers.FREEZE, powers.LIGHTNING, powers.FIREBALL], controllers=[controllers.DoNothing()])

    elif choice == 'nuphrindas':
        monster = actors.Monster(x, y, graphics.BOSS, 'nuphrindas', rl.WHITE, max_hp=60, defense=3, power=5, possession_cooldown=3500, max_mana=60, actions=[powers.SUMMON], skills=['boss'])
    elif choice == 'ghoul':
        monster = actors.Monster(x, y, graphics.GHOUL, 'ghoul', rl.WHITE, max_hp=3, defense=0, power=1, possession_cooldown=10)
    else:
        raise ValueError('unknown choice of monster "%s"' % choice)
    return monster
 
def get_monster_chances():
    monster_chances = {}
    # monsters: rat bat orc troll
    # forest
    monster_chances[0] = {'rat': 1}
    # level 1: find that there is no healing, try possession
    monster_chances[1] = {'rat': 4, 'orc': 1}
    # level 2: find that you can use others competences
    monster_chances[2] = {'rat': 3, 'orc': 4, 'bat': 1}
    # level 3: water
    monster_chances[3] = {'rat': 1, 'orc': 4, 'bat': 3, 'octopus': 2, 'dwarf': 1}
    # level 4: invisibles
    monster_chances[4] = {'rat': 2, 'ghost': 4, 'eye': 1, 'troll': 1, 'dwarf': 1}
    # level 5: lava
    monster_chances[5] = {'rat': 1, 'bat': 1, 'fire_elemental': 4, 'troll': 2, 'dwarf': 1}
    # level 6: necromancers
    monster_chances[6] = {'rat': 1, 'bat': 1, 'necromancer': 4, 'orc': 1}
    # level 7: wizard
    monster_chances[7] = {'orc': 1, 'wizard': 4, 'troll': 2, 'dwarf': 1}
    # level 8: boss
    monster_chances[8] = {'rat': 5, 'bat': 5, 'orc': 1, 'troll': 1, 'fire_elemental': 1, 'octopus': 1, 'necromancer': 1, 'wizard': 1, 'ghost': 5, 'eye': 1, 'ghoul': 1}
    return monster_chances[game.dungeon_level]

def place_objects(level, room):
    # this is where we decide the chance of each monster or item appearing.
 
    # maximum number of monsters per room
    max_monsters = from_dungeon_level([[1, 1], [1, 2], [2, 3], [2, 4], [3, 5], [2, 6], [1, 7], [0, 8]])
    #max_monsters = game.dungeon_level
 
    # maximum number of items per room
    max_items = from_dungeon_level([[4, 1], [12, 2]])
 
    # chance of each item (by default they have a chance of 0 at level 1, which then goes up)
    item_chances = {}
    #item_chances['heal'] = 35  # healing potion always shows up, even if all other items have 0 chance
    item_chances['lightning'] = from_dungeon_level([[25, 1]])
    item_chances['fireball'] = from_dungeon_level([[25, 1]])
    item_chances['confuse'] = from_dungeon_level([[10, 1]])
    item_chances['sword'] = from_dungeon_level([[5, 1]])
    item_chances['shield'] = from_dungeon_level([[15, 1]])
 
    # choose random number of monsters
    num_monsters = rl.random_int(1, max_monsters)
 
    monster_type = random_choice(get_monster_chances())
    for i in range(num_monsters):
        # choose random spot for this monster
        x = rl.random_int(room.x1 + 1, room.x2 - 1)
        y = rl.random_int(room.y1 + 1, room.y2 - 1)
 
        # only place it if the tile is not blocked
        if not level.is_blocked(x, y):
            level.objects.append(make_monster(monster_type, x, y))
 
