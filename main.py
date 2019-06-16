import builtins
import sys
import rl

import actors
import actions
import controllers
import scenes
import levels
import graphics
import monsters
import ui

class Game:
    WIDTH = 320
    HEIGHT = 240

    def __init__(self):
        builtins.game = self # trick to make game a cross-module global
        self.messages = []
        self.scenes = []
        self.current = 0
        self.dungeon_level = 0

    def step(self):
        print('start turn')
        #TODO: lockup for unknown reason, maybe player death
        for actor in level.objects:
            if isinstance(actor, actors.Monster):
                actor.add_energy(actor.speed)
        while len(level.objects) > 0:
            if not player.alive:
                break
            actor = level.objects[self.current % len(level.objects)]
            if isinstance(actor, actors.Monster) and actor.alive:
                action = actor.get_action()
                while isinstance(action, actions.Action) and action.can_perform():
                    action = action.perform()
                    # cancel repeatable actions if there is a monster
                    if actor is player:
                        for object in level.objects:
                            if isinstance(object, actors.Monster) and object.is_hostile(player) and player.can_see(object):
                                player.action = None
                if action:
                    self.current += 1
                elif actor is player:
                    return
            else:
                self.current += 1

    def add_actor(self, actor):
        level.objects.append(actor)

    def push_scene(self, scene):
        if len(self.scenes) > 0:
            self.scenes[-1].focus_changed(False)
        self.scenes.append(scene)
        scene.focus_changed(True)

    def pop_scene(self):
        scene = self.scenes.pop()
        scene.focus_changed(False)
        scene.end()
        if len(self.scenes) > 0:
            self.scenes[-1].focus_changed(True)

    def next_level(self):
        level_message = [
                '',
                'You enter the dungeon. Strangely, it feels good to be back...',
                'You descent to the next level. You hear wings flapping in the distance...',
                'You descent to the next level. You hear the sound of a river flowing...',
                'You descent to the next level. Your vision is playing tricks on you...',
                'You descent to the next level. The atmosphere is pretty hot here...',
                'You descent to the next level. The atmosphere is putrid...',
                'You descent to the next level. The air is charged with magic...',
                'You descent to the next level. You feel the presence of a powerful entity...',
        ]

        self.dungeon_level += 1
        ui.message(level_message[self.dungeon_level], rl.BLUE)
        if self.dungeon_level == 0:
            builtins.level = levels.make_forest_map()
        elif self.dungeon_level < 8:
            builtins.level = levels.make_dungeon_map()  # create a fresh new level!
        else:
            builtins.level = levels.make_boss_map()

    def new(self):
        controllers.Player.keys = [] # reset any pending keystroke
        self.current = 0
        self.dungeon_level = -1
        builtins.player = monsters.make_monster('ghoul', 0, 0)
        self.next_level()
        player.push_controller(controllers.Player())
        self.state = 'playing'
        ui.message('Starting game')

    def load(self):
        raise OSError

rl.set_seed(0)
rl.init_display('ExpelledRL', Game.WIDTH, Game.HEIGHT)
rl.set_app_name('expelled-rl')
builtins.font = rl.Font('data/04B_03__.TTF', 8)
builtins.tileset = rl.Image('data/tileset.png', 8, 8)

game = Game()
game.new()
game.push_scene(scenes.Playing())
game.push_scene(scenes.Story())
#try:
#    game.load()
#except Exception as e:
#    sys.print_exception(e)
#    game.new()
#    game.push_scene(scenes.Story())

def update(event):
    if len(game.scenes) > 0:
        game.scenes[-1].update(event)
        # active scenes are drawn on top of eachother
        for scene in game.scenes:
            scene.render()

rl.run(update)

