import rl

import environments

# graphics names from tileset
CAVE_ROCK = 0
CAVE_FLOOR = 1
CAVE_STAIRS = 2
BOSS_WALL = 3
BOSS_FLOOR = 4
BOSS_CARPET = 5
BLUE_WALL = 6
BLUE_FLOOR = 7
BLUE_STAIRS = 8
RED_WALL = 9
RED_FLOOR = 10
RED_STAIRS = 11
GRAY_WALL = 12
GRAY_FLOOR = 13
WOOD_WALL = 14
WOOD_FLOOR = 15

TREE = 22
GRASS = 17
ROCK_STAIRS = 18
LAVA = 19
WATER = 20

SWORD = 32
DAGGER = 33
SHIELD = 34
YENDOR_AMULET = 35

POTION = 49
SCROLL = 50
FIREBALL = 51
BOULDER = 52
BOULDER_SPLAT = 53

GHOUL = 64
ORC = 65
TROLL = 66
BAT = 67
FIRE_ELEMENTAL = 68
BOSS = 69
OCTOPUS = 70
GHOST = 71
EYE = 72
DWARF = 73
WIZARD = 74
NECROMANCER = 75
RAT = 76
SKELETON = 77
PLAYER = 78
CORPSE = 79
TOMB1 = 80
TOMB2 = 96

stairs_for_level = [
        CAVE_STAIRS, # level 0
        CAVE_STAIRS, # level 1 (no healing)
        CAVE_STAIRS, # level 2 (skills)
        BLUE_STAIRS, # level 3 (water)
        CAVE_STAIRS, # level 4 (invisibles)
        RED_STAIRS, # level 5 (lava)
        ROCK_STAIRS, # level 6 (necromancers)
        ROCK_STAIRS, # level 7 (wizards)
        ROCK_STAIRS, # level 8 (boss)
        ]

class Tile:
    def __init__(self, num, type, blocked, block_sight, graphics, effect=None):
        self.num = num
        self.type = type
        self.blocked = blocked
        self.block_sight = block_sight
        self._graphics = graphics
        self.effect = effect

    def draw(self, x, y):
        rl.draw_tile(tileset, x, y, self.graphics)

    @property
    def graphics(self):
        if type(self._graphics) == list:
            return self._graphics[game.dungeon_level]
        return self._graphics
 
    UNUSED = 0
    FLOOR = 1
    WALL = 2
    WATER = 3
    LAVA = 4
    GRASS = 5
    BOSS_WALL = 6
    BOSS_FLOOR = 7
    BOSS_CARPET = 8

Tile.mapping = [
        Tile(0, 'nothing', True, True, 21),
        Tile(1, 'floor', False, False, [
                CAVE_FLOOR, # level 0
                CAVE_FLOOR, # level 1 (no healing)
                CAVE_FLOOR, # level 2 (skills)
                BLUE_FLOOR, # level 3 (water)
                CAVE_FLOOR, # level 4 (invisibles)
                RED_FLOOR, # level 5 (lava)
                GRAY_FLOOR, # level 6 (necromancers)
                WOOD_FLOOR, # level 7 (wizards)
                BOSS_FLOOR, # level 8 (boss)
        ]),
        Tile(2, 'rock', True, True, [
                TREE, # level 0
                CAVE_ROCK, # level 1 (no healing)
                CAVE_ROCK, # level 2 (skills)
                BLUE_WALL, # level 3 (water)
                CAVE_ROCK, # level 4 (invisibles)
                RED_WALL, # level 5 (lava)
                GRAY_WALL, # level 6 (necromancers)
                WOOD_WALL, # level 7 (wizards)
                BOSS_WALL, # level 8 (boss)
        ]),
        Tile(3, 'water', False, False, WATER, environments.water_effect),
        Tile(4, 'lava', False, False, LAVA, environments.lava_effect),
        Tile(5, 'grass', False, False, GRASS),
        Tile(6, 'wall', True, True, BOSS_WALL),
        Tile(7, 'floor', False, False, BOSS_FLOOR),
        Tile(8, 'carpet', False, False, BOSS_CARPET),
    ]

