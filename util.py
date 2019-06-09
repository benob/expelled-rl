import rl

import actors
import scenes
import ui

def capitalize(text):
    return text[0].upper() + text[1:]

def line_iter(x1, y1, x2, y2):
    rl.walk_line_start(x1, y1, x2, y2)
    while True:
        result = rl.walk_line_next()
        if result is None:
            break
        yield (result[0], result[1])


def wrap_text(text, width):
    output = ['']
    x = 0
    for word in text.replace('\n', ' \n ').split(' '):
        if word == '\n':
            x = 0
            output += ['']
            continue
        if x + rl.size_text(word)[0] > width:
            x = 0
            output += ['']
        output[-1] += word + ' '
        x += rl.size_text(word + ' ')[0]
    return output

 
def visible_monsters(target):
    enemies = []
    for object in level.objects:
        if isinstance(object, actors.Monster) and object.alive and object is not target and target.can_see(object):
            enemies.append(object)
    return enemies
 
def friends_and_foes(target):
    monsters = visible_monsters(target)
    friends = []
    foes = []
    for monster in monsters:
        if target.is_hostile(monster):
            foes.append(monster)
        else:
            friends.append(monster)
    return friends, foes

def closest_hostile(monster, max_range):
    closest_enemy = None
    closest_dist = max_range + 1  # start with (slightly more than) maximum range
 
    for object in level.objects:
        if isinstance(object, actors.Monster) and object.alive and object.is_hostile(monster) and monster.can_see(object):
            # calculate distance between this object and the monster
            dist = monster.distance_to(object)
            if dist < closest_dist:  # it's closer, so remember it
                closest_enemy = object
                closest_dist = dist
    return closest_enemy

def target_tile(prompt, callback, max_range=None):
    game.push_scene(scenes.TargetTile(prompt, callback, max_range))
 
def target_monster(prompt, callback, max_range=None):
    finished = False
    def selected_tile(x, y):
        if x is None:
            callback(None)
            return
        for obj in level.objects:
            if isinstance(obj, actors.Monster) and obj.alive and obj.x == x and obj.y == y and obj is not player:
                callback(obj)
                return
        ui.message("That's not a monster.")
        target_tile(prompt, selected_tile, max_range)

    target_tile(prompt, selected_tile, max_range)
 
