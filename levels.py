import math
import rl

import rooms
import actors
import const
import graphics
from graphics import Tile
import monsters
import util

class Level:
    def __init__(self, width, height):
        self.tiles = rl.Array(width, height)
        self.blocked = rl.Array(width, height)
        self.visited_tiles = rl.Array(width, height)
        self.visited = rl.Array(width, height)
        self.fov = rl.Array(width, height)
        self.width = width
        self.height = height
        self.objects = []

        self.tiles.fill(1)
        self.tiles.line(0, 0, width - 1, 0, 2)
        self.tiles.line(width - 1, 0, width - 1, height - 1, 2)
        self.tiles.line(width - 1, height - 1, 0, height - 1, 2)
        self.tiles.line(0, height - 1, 0, 0, 2)

    def __setitem__(self, index, tile):
        self.tiles[index] = tile.num
        self.blocked[index] = tile.blocked

    def __getitem__(self, index):
        num = self.tiles[index]
        if num >= 0 and num < len(Tile.mapping):
            return Tile.mapping[num]
        return None

    def __contains__(self, what):
        if hasattr(what, 'x') and hasattr(what, 'y'):
            x, y = what.x, what.y
        else:
            x, y = what
        return x >= 0 and y >= 0 and x < self.width and y < self.height

    def compute_fov(self):
        self.fov = self.blocked.field_of_view(player.x, player.y, player.sight_radius, 1, True)
        self.fov.copy_masked(self.visited, self.fov)

    def compute_autoexplore(self):
        self.to_visit = self.visited.copy()
        self.to_visit.replace(1, 2)
        self.blocked.copy_masked(self.to_visit, self.blocked, 1)
        water = self.tiles.equals(Tile.WATER)
        water.copy_masked(self.to_visit, water, 1)
        lava = self.tiles.equals(Tile.LAVA)
        lava.copy_masked(self.to_visit, lava, 1)
        self.to_visit.replace(1, -1)
        self.to_visit.replace(2, rl.INT_MAX)
        self.to_visit.dijkstra()

    def tile_in_fov(self, x, y):
        if x >= 0 and x < self.width and y >= 0 and y < self.height:
            return self.fov[x, y] == 1
        return False

    def is_blocked(self, x, y):
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return True
        # first test the map tile
        if self[x, y].blocked or self.blocked[x, y]:
            return True
     
        # now check for any blocking objects
        for object in self.objects:
            if object.blocks and object.x == x and object.y == y:
                return True
     
        return False
 
 
    def fill_circle(self, x, y, r, tile):
        for i in range(int(x - r), int(x + r)):
            for j in range(int(y - r), int(y + r)):
                if i >= 0 and i < self.width and j >= 0 and j < self.height:
                    distance = math.sqrt((x - i) ** 2 + (y - j) ** 2)
                    if distance < r:
                        self[i, j] = Tile.mapping[tile]

    def create_river(self, tile):
        center_x = self.width // 2
        center_y = self.height // 2
        # from one side towards the other
        configs = [(center_x, 0, 90), (center_x, self.height - 1, -90), (0, center_y, 0), (self.width - 1, center_y, 180)]
        choice = rl.random_int(0, len(configs) - 1)
        x, y, angle = configs[choice]
        #x, y, angle = center_x, center_y, rl.random_int(0, 359)
        width = 2
        finished = False
        while not finished:
            #if player.distance(x, y) < 10:
            #    break
            dx = int(math.cos(math.pi * angle / 180) * 5)
            dy = int(math.sin(math.pi * angle / 180) * 5)
            for i, j in util.line_iter(x, y, x + dx, y + dy):
                if i < 0 or i >= self.width or j < 0 or j >= self.height:
                    finished = True
                    break
                self.fill_circle(i, j, width, tile)
            x += dx
            y += dy
            angle += rl.random_int(0, 60) - 30
            width += (rl.random_int(0, 100) - 50) / 100
            if width < 2:
                width = 2
            if width > 5:
                width = 5

    def create_room(self, room, tile=Tile.FLOOR):
        # go through the tiles in the rectangle and make them passable
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                self[x, y] = Tile.mapping[tile]
     
     
    def create_h_tunnel(self, x1, x2, y, tile=Tile.FLOOR):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self[x, y] = Tile.mapping[tile]
     
     
    def create_v_tunnel(self, y1, y2, x, tile=Tile.FLOOR):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self[x, y] = Tile.mapping[tile]
     
class Rect:
    # a rectangle on the map. used to characterize a room.
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h
 
    def center(self):
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return (center_x, center_y)
 
    def intersect(self, other):
        # returns true if this rectangle intersects with another one
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)
 
def make_forest_map():
    level = Level(const.MAP_WIDTH, const.MAP_HEIGHT)
    level.tiles.fill(Tile.GRASS)
    level.blocked.fill(0)

    center_x = level.width // 2
    center_y = level.height // 2
    radius = min([center_x, center_y])

    def contains_tree(x, y):
        d = math.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
        if d < 3:
            return False
        if d >= radius:
            return True
        p = 100 * d / radius
        v = rl.random_int(0, 100)
        return v < p

    level.objects = [player]
    player.x = center_x
    player.y = center_y
    for y in range(level.height):
        for x in range(level.width):
            if contains_tree(x, y):
                level[x, y] = Tile.mapping[Tile.WALL]
                #level.objects.append(actors.Actor(x, y, graphics.TREE, 'tree', rl.GREEN, always_visible=True))
                #level.blocked[x, y] = 1
    level.blocked = level.tiles.equals(Tile.WALL)
    
    angle = rl.random_int(0, 360)
    distance = rl.random_int(2, 3)
    level.stairs = actors.Actor(center_x + int(distance * math.cos(angle)), center_y + int(distance * math.sin(angle)), graphics.ROCK_STAIRS, 'stairs', rl.WHITE, always_visible=True, z=-2)
    level.objects.append(level.stairs)
    level.compute_fov()

    #distance = level.blocked.copy()
    #distance.replace(0, rl.INT_MAX)
    #distance.replace(1, -1)
    #distance[player.x, player.y] = 0
    #distance.dijkstra()
    #distance.replace(rl.INT_MAX, -1)
    #print(distance.max(), distance.argmax())

    return level

def make_boss_map():
    level = Level(const.MAP_WIDTH, const.MAP_HEIGHT)
    level.tiles.fill(Tile.BOSS_WALL)
    level.blocked.fill(1)

    center_x = level.width // 2
    center_y = level.height // 2
    level.create_room(Rect(center_x - 20, center_y - 20, 40, 40), Tile.BOSS_FLOOR)
    level.create_room(Rect(center_x - 30, center_y - 3, 6, 6), Tile.BOSS_FLOOR)
    level.create_h_tunnel(center_x - 24, center_x - 20, center_y, Tile.BOSS_FLOOR)
    level.fill_circle(center_x, center_y, 6, Tile.BOSS_CARPET)
    for angle in range(0, 360, 15):
        x = math.cos(math.pi * angle / 180) * 12 + center_x + 0.5
        y = math.sin(math.pi * angle / 180) * 12 + center_y + 0.5
        level[int(x), int(y)] = Tile.mapping[Tile.BOSS_WALL]

    for angle in range(0, 360, 45):
        x = math.cos(math.pi * angle / 180) * 6 + center_x + 0.5
        y = math.sin(math.pi * angle / 180) * 6 + center_y + 0.5
        level[int(x), int(y)] = Tile.mapping[Tile.BOSS_WALL]

    player.x = center_x - 27
    player.y = center_y - 1
    amulet = actors.Actor(center_x + 3, center_y, graphics.YENDOR_AMULET, 'Amulet of Yendor', rl.YELLOW)

    # need stairs to save game
    level.stairs = actors.Actor(0, 0, graphics.ROCK_STAIRS, 'stairs', rl.WHITE, always_visible=True, z=-2)
    level.objects = [level.stairs, amulet, player]

    level.objects.append(monsters.make_monster('original-body', center_x, center_y))
    level.objects.append(monsters.make_monster('nuphrindas', center_x - 3, center_y))
    level.compute_fov()
    return level

def make_dungeon_map2():
                   #0  1   2   3   4   5   6   7   8
    num_monsters = [0, 10, 20, 30, 10, 30, 10, 20, 0]
    size =         [0, 10, 20, 30, 10, 30, 10, 20, 0]
    generated = rooms.generate_level(size[game.dungeon_level], rooms.room_templates[game.dungeon_level - 1])
    level = Level(generated.width(), generated.height())
    level.tiles = generated
    level.blocked = level.tiles.equals(Tile.WALL)
    if game.dungeon_level == 3:
        level.create_river(Tile.WATER)
    elif game.dungeon_level == 5:
        level.create_river(Tile.LAVA)
    #level.blocked.print_ascii('.#')

    x, y = level.tiles.find_random(Tile.FLOOR)
    level.stairs = actors.Actor(x, y, graphics.stairs_for_level[game.dungeon_level], 'stairs', rl.WHITE, always_visible=True, z=-2)
    level.objects = [player, level.stairs]
    player.x, player.y = level.tiles.find_random(Tile.FLOOR)
    for i in range(num_monsters[game.dungeon_level]):
        name = monsters.random_choice(monsters.get_monster_chances())
        while True:
            x, y = level.tiles.find_random(Tile.FLOOR)
            if player.distance(x, y) > player.sight_radius:
                break
        level.objects.append(monsters.make_monster(name, x, y))
    level.compute_fov()
    return level

def make_dungeon_map():
    level = Level(const.MAP_WIDTH, const.MAP_HEIGHT)
    level.tiles.fill(Tile.WALL)
    level.blocked.fill(1)
    level.objects = [player]
 
    rooms = []
    num_rooms = 0
 
    for r in range(const.MAX_ROOMS):
        if num_rooms == 0:
            w = rl.random_int(const.ROOM_MIN_SIZE - 1, const.ROOM_MIN_SIZE + 2)
            h = rl.random_int(const.ROOM_MIN_SIZE - 1, const.ROOM_MIN_SIZE + 2)
        else:
            w = rl.random_int(const.ROOM_MIN_SIZE, const.ROOM_MAX_SIZE)
            h = rl.random_int(const.ROOM_MIN_SIZE, const.ROOM_MAX_SIZE)

        x = rl.random_int(0, level.width - w - 1)
        y = rl.random_int(0, level.height - h - 1)
 
        new_room = Rect(x, y, w, h)
 
        failed = False
        for other_room in rooms:
            if new_room.intersect(other_room):
                failed = True
                break
 
        if not failed:
            level.create_room(new_room)
            (new_x, new_y) = new_room.center()
 
            if num_rooms == 0:
                player.x = new_x
                player.y = new_y
            else:
                (prev_x, prev_y) = rooms[num_rooms - 1].center()
 
                if rl.random_int(0, 1) == 1:
                    level.create_h_tunnel(prev_x, new_x, prev_y)
                    level.create_v_tunnel(prev_y, new_y, new_x)
                else:
                    level.create_v_tunnel(prev_y, new_y, prev_x)
                    level.create_h_tunnel(prev_x, new_x, new_y)
 
                monsters.place_objects(level, new_room)
 
            rooms.append(new_room)
            num_rooms += 1
 
    if game.dungeon_level == 3:
        level.create_river(Tile.WATER)
    elif game.dungeon_level == 5:
        level.create_river(Tile.LAVA)

    level.stairs = actors.Actor(new_x, new_y, graphics.stairs_for_level[game.dungeon_level], 'stairs', rl.WHITE, always_visible=True, z=-2)
    level.objects.append(level.stairs)
    level.compute_fov()
    return level


