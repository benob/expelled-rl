import math
import rl

import debug
import util
import controllers
import graphics
import actors
import ui
import const
import powers
import actions

class Scene:
    def __init__(self):
        pass

    def render(self):
        pass

    def update(self, event):
        pass

    def end(self):
        pass

    def focus_changed(self, focus):
        pass

class MessageBox(Scene):
    def __init__(self, title, text):
        self.title = title
        self.text = text

    def update(self, event):
        if event > 0:
            game.pop_scene()

    def render(self):
        lines = self.text.split('\n')
        sizes = [rl.size_text(font, text) for text in [self.title] + lines]
        width = max([size[0] for size in sizes])
        height = 8 + sum([size[1] for size in sizes])
        x = (game.WIDTH - width) // 2
        y = (game.HEIGHT - height) // 2

        rl.fill_rect(x - 8, y - 8, width + 16, height + 16, rl.color(0, 0, 0, 192))

        rl.draw_text(font, x, y, self.title, rl.YELLOW)
        for i, line in enumerate(lines):
            rl.draw_text(font, x, y + (2 + i) * 8, line)

class Menu(Scene):
    def __init__(self, title, items, callback):
        self.title = title
        self.items = items
        self.selected = 0
        self.callback = callback

    def update(self, event):
        if event == rl.UP:
            self.selected -= 1
        elif event == rl.DOWN:
            self.selected += 1
        elif event == rl.ESCAPE:
            game.pop_scene()
        elif event == rl.RETURN:
            self.callback(self.selected)
        self.selected = self.selected % len(self.items)

    def render(self):
        sizes = [rl.size_text(font, text) for text in [self.title] + self.items]
        width = max([size[0] for size in sizes])
        height = 8 + sum([size[1] for size in sizes])
        x = (game.WIDTH - width) // 2
        y = (game.HEIGHT - height) // 2

        rl.fill_rect(x - 8, y - 8, width + 16, height + 16, rl.color(0, 0, 0, 192))

        rl.draw_text(font, x, y, self.title, rl.YELLOW)
        for i, item in enumerate(self.items):
            color = rl.WHITE if i == self.selected else rl.DARKGRAY
            rl.draw_text(font, x, y + (2 + i) * 8, item, color)


class MainMenu(Menu):
    def __init__(self):
        super().__init__('Main Menu', ['New game', 'New game (no story)', 'Quit'], self.on_select)

    def on_select(self, item):
        game.pop_scene()
        if item == 0:
            game.push_scene(Story())
            game.new()
        elif item == 1:
            game.new()
        elif item == 2:
            rl.quit()


class Playing(Scene):
    def __init__(self):
        self.mouse_path = None

    def focus_changed(self, focus):
        if not focus:
            self.mouse_path = None
        else:
            self.update(rl.MOUSE)

    def update(self, event):
        if event == rl.ESCAPE:
            game.push_scene(MainMenu())
        elif event > 0:
            player.action = None
            controllers.Player.add_key(event)
            game.step()
            self.mouse_path = None
        elif event == rl.MOUSE:
            mouse_x, mouse_y, button = rl.mouse()
            x = mouse_x // 8 - const.SCREEN_WIDTH // 2 + player.x
            y = mouse_y // 8 - const.PANEL_Y // 2 + player.y
            if (x, y) in level and not level.blocked[x, y] and level.tile_in_fov(x, y):
                if button == 1:
                    player.set_action(actions.MoveTowards(player, x, y))
                    self.mouse_path = None
                else:
                    blocked_fov = level.fov.copy()
                    blocked_fov.replace(0, 2)
                    blocked_fov.replace(1, 0)
                    blocked_fov.replace(2, 1)
                    level.blocked.copy_masked(blocked_fov, level.blocked)
                    self.mouse_path = blocked_fov.shortest_path(player.x, player.y, x, y)
            else:
                self.mouse_path = None
        elif player.action:
            game.step()

    def render(self):
        x_offset = const.SCREEN_WIDTH // 2 - player.x
        y_offset = const.PANEL_Y // 2 - player.y

        rl.clear()

        # draw level
        for y in range(level.height):
            for x in range(level.width):
                screen_x = x + x_offset
                screen_y = y + y_offset
                if screen_x < 0 or screen_x >= const.SCREEN_WIDTH or screen_y < 0 or screen_y >= const.SCREEN_HEIGHT:
                    continue
                visible = level.tile_in_fov(x, y)
                if not visible:
                    if level.visited[x, y]:
                        level[x, y].draw(screen_x * 8, screen_y * 8)
                        rl.fill_rect(screen_x * 8, screen_y * 8, 8, 8, rl.color(0, 0, 0, 128))
                else:
                    level[x, y].draw(screen_x * 8, screen_y * 8)
                    if level.blocked[x, y] == 0:
                        # draw world border
                        if x == 0:
                            rl.draw_tile(tileset, (screen_x - 1) * 8, screen_y * 8, graphics.Tile.mapping[0].graphics)
                        if x == level.width - 1:
                            rl.draw_tile(tileset, (screen_x + 1) * 8, screen_y * 8, graphics.Tile.mapping[0].graphics)
                        if y == 0:
                            rl.draw_tile(tileset, screen_x * 8, (screen_y - 1) * 8, graphics.Tile.mapping[0].graphics)
                        if y == level.height - 1:
                            rl.draw_tile(tileset, screen_x * 8, (screen_y + 1) * 8, graphics.Tile.mapping[0].graphics)
     
        # draw all objects in the list
        level.objects.sort(key=lambda actor: actor.z)
        for object in level.objects:
            object.draw(x_offset, y_offset)

        # draw hp on top of actors
        for object in level.objects:
            if isinstance(object, actors.Monster) and object is not player:
                object.draw_hp_bar(x_offset, y_offset)
        player.draw_hp_bar(x_offset, y_offset)

        rl.fill_rect(0, const.PANEL_Y * 8, const.SCREEN_WIDTH * 8, const.SCREEN_HEIGHT * 8, rl.BLACK)

        # print the game messages
        y = 1
        for (line, color) in game.messages:
            rl.draw_text(font, const.MSG_X * 8, (const.PANEL_Y + y) * 8, line, color)
            y += 1
     
        # show the player's stats
        if player.alive:
            ui.render_bar(2, 1 + const.PANEL_Y, const.BAR_WIDTH, 'HP', player.hp, player.max_hp, rl.RED, rl.BLACK) 
            if player.max_mana > 0:
                ui.render_bar(2, 2 + const.PANEL_Y, const.BAR_WIDTH, 'MANA', player.mana, player.max_mana, rl.BLUE, rl.BLACK) 
        else:
            ui.render_bar(2, 1 + const.PANEL_Y, const.BAR_WIDTH, 'DEAD', 0, 0, rl.RED, rl.BLACK, show_value=False) 
        rl.draw_tile(tileset, 5, (const.PANEL_Y + 1) * 8, player.tile + 16)

        if player.current_possession_cooldown > 0:
            ui.render_bar(0, 0, const.SCREEN_WIDTH, 'Possession cooldown', player.current_possession_cooldown, player.possession_cooldown, rl.INDIGO, rl.BLACK)
        if game.dungeon_level == 0:
            rl.draw_text(font, 1 * 8, (const.PANEL_Y + 3) * 8, 'Outside', rl.LIGHTGRAY)
        else:
            rl.draw_text(font, 1 * 8, (const.PANEL_Y + 3) * 8, 'Dungeon level ' + str(game.dungeon_level), rl.LIGHTGRAY)

        # draw mouse path
        if self.mouse_path:
            for i, j in self.mouse_path[:-1]:
                rl.fill_rect((i + x_offset) * 8, (j + y_offset) * 8, 8, 8, rl.color(255, 255, 0, 128))
            i, j = self.mouse_path[-1]
            rl.draw_rect((i + x_offset) * 8, (j + y_offset) * 8, 9, 9, rl.color(255, 255, 0))
            #rl.draw_rect((x + x_offset) * 8, (y + y_offset) * 8, 8, 8, rl.color(255, 255, 0))


class GameOver(Scene):
    pass


class Story(Scene):
    def __init__(self):
        self.story = [["You enter the final room of the dungeon, quite confident that all the power you have accumulated in your descent will lead you to victory.\n\nThe amulet of Yendor is right there, standing on an altar on the opposite side of the room. You start to move carefully, wary of any trap that could trigger...", graphics.PLAYER + 16, graphics.YENDOR_AMULET, graphics.BOSS_FLOOR],
            ["Suddenly you see a shadow forming between you and the altar. Nuphrindas, the damned king, is barring the access to the ultimate treasure.\n\nHe mumbles words in an unheard language, and you feel the very life starting to escape your body.\n\nYou try to resist but you are quickly overwhelmed by the unconquerable power of the spell. You feel your soul slowly being expelled from your body. Your vision blurs and you lose consciousness...", graphics.BOSS, graphics.PLAYER, graphics.BOSS_FLOOR],
            ["You wake up in the forest, just outside the dungeon entrance. Your sensations are strange, sluggish, inappropriate.\n\nYou are in complete dismay when you realize that the body you are incarnating is not yours, but rather that of an ugly, feeble creature. Yet, you feel that you have a special connection to the living and the animate...", graphics.GHOUL + 16, graphics.TREE, graphics.GRASS]
            ]
        self.current = 0

    def render(self):
        text, tile1, tile2, bg = self.story[self.current]
        rl.clear()
        lines = util.wrap_text(text, game.WIDTH - 64)
        rl.draw_text(font, 32, (game.HEIGHT - len(lines) * 8) // 2, '\n'.join(lines), rl.LIGHTGRAY)
        x = game.WIDTH // 2
        y = 8 + (game.HEIGHT + len(lines) * 8) // 2
        for i in range(4):
            rl.draw_tile(tileset, x - 12 + i * 8, y + 2, bg)
        rl.draw_tile(tileset, x - 8, y, tile1)
        rl.draw_tile(tileset, x + 8, y, tile2)

    def update(self, event):
        if event > 0:
            if event == rl.ESCAPE:
                game.pop_scene()
            else:
                self.current += 1
                if self.current >= len(self.story):
                    game.pop_scene()

    def end(self):
        ui.message('Putting yourself together, you decide to go back down the dungeon and settle this mess.', rl.LIGHTGRAY)
        ui.message('Press t for a tutorial. Press p to possess another monster.', rl.GREEN)
 

class Help(Scene):
    def __init__(self):
        super().__init__()

    def render(self):
        text = '''
Description:
  ExpelledRL is a roguelike built for the 2019 7DRL gamejam. It is set in a traditional RL theme, except for the fact that you can control any monster, through the possess spell. The objective is to recover your original body, and if time permits, the amulet of Yendor.

Controls:
  escape: menu
  h/j/k/l/y/u/b/n, arrows or keypad: move (shift = run)
  o: autoexplore
  5 or space: wait
  a: perform an action (such as casting a spell)
  p: cast the possess spell
  >: descent to the next level (on stairs)
  c: see character information
  t: this tutorial
  use arrow keys to select spell targets

                    press a key to continue
        '''
        lines = util.wrap_text(text, const.SCREEN_WIDTH * 8 - 64)
        rl.clear()
        rl.draw_text(font, 32, ((const.SCREEN_HEIGHT - len(lines)) // 2) * 8, '\n'.join(lines), rl.LIGHTGRAY)

    def update(self, event):
        if event > 0:
            game.pop_scene()


class Ending(Scene):
    def __init__(self):
        pass

    def render(self):
        holding = True
        tile1 = player.tile + 16
        tile2 = graphics.YENDOR_AMULET
        bg = graphics.GRASS
        text = 'The hideous creature breaths its last non-breath, and falls to the ground. Now that Nuphrindas is no more, your revenge is complete.\n\n'
        if player.name == 'original body':
            text += '''You have finally recovered your adored body. You feel all skilled, and powerful. You raise your hand towards the amulet of Yendor, imagining the fame that you will soon enjoy. Your hand stops as you are having second thoughts. Possessing all those bodies has changed your mind, and you are not sure you want the life of a hero. You turn back and leave the prized amulet for generations to come...'''
            tile2 = None
        elif player.name == 'orc':
            text += '''You grunt in victory. Your journey within the orc tribe has made you more aware of the fraternity that those creatures exhibit to each other. As part of the big orc family you will be able to enjoy large feasts, and adventurer squishing parties. This really warms your heart.'''
            tile2 = graphics.ORC
            bg = graphics.CAVE_FLOOR
            holding = False
        elif player.name == 'rat':
            text += '''You are a rat. Not the kind of rat that stumbles giant organizations, but the kind of rat that likes to eat cheese. Maybe the weakest are stronger than they seem. Numbers are what make feeble creatures standout. And your plan to conquer the world is to have a chat with your peers from the pantry. Together, you can do crazy things, and the amulet will be a great asset.'''
            bg = graphics.BOSS_FLOOR
            holding = False
        elif player.name == 'bat':
            text += 'You echo-locate your prey on the floor. It will no-longer move. You wonder whether you would like the taste of blood. Maybe one day you will become a vampire. You grab the amulet and fly towards a dark cave where you will rest and prepare new adventures.'
            bg = graphics.CAVE_FLOOR
            holding = False
        elif player.name == 'octopus':
            text += 'You grab the amulet with one of your tentacles. Touching its surface makes ripples of colored stripes crawl your tentacle towards your body as it touches your brains. You feel its power surge through you and a range of powers suddenly be available. You fire one of them and the dungeon is suddenly flowed in water, decorated with algae and filled with fish of various colors. What could be interpreted as a smile draw on your face...'
            bg = graphics.WATER
        elif player.name == 'skeleton':
            text += 'You feel the air flowing between your bones as the power of the old king flows through the room, towards mysterious eons. Magic slowly dissipates from the room... After grabbing the amulet, you stride towards the exit. Your joints start to feel unfit, and you fall on a knee while the rest of your leg crumbles. The energy that was holding you together is running away and your last though is that you should not have killed that necromancer.'
            tile1 = graphics.CORPSE + 16
            bg = graphics.BOSS_FLOOR
            holding = False
        elif player.name == 'ghost':
            text += 'As a ghost, your interactions with the real world are rather abstract. Holding the amulet is something that you can only contemplate. So you decide to just gaze at it for the eternity to come.'
            bg = graphics.BOSS_FLOOR
            holding = False
        elif player.name == 'ghoul':
            text += 'You have defeated the old king as the feeble creature he though would never be able to reach him. You contemplate the irony of the situation and fail to reckon the large stone falling above you. The distinctive splat noise of your head exploding is the last sound you hear.'
            player.tile = graphics.BOULDER_SPLAT
            tile1 = graphics.BOULDER_SPLAT
            bg = graphics.BOSS_FLOOR
            holding = False
        elif player.name == 'necromancer':
            text += '''Death is crawling under your fingers. You feel it twirling in the room, taking its toll and leaving the area for all it has been busy in the dungeon. Necromancy is a discipline, a science, no, an art which you no longer feel like leaving. Now that the room is all quiet, the idea grows in you to finally meet your destiny. You take Nuphrindas scepter from the ground and raise it to mark the eons with your new role in a new home. Finally the dungeon has a leader who will make terror reign as it should always have been.'''
            bg = graphics.BOSS_FLOOR
        elif player.name == 'troll':
            text += '''Trolls are strange creatures. At first they seem brutal, selfless and greedy. Yet, you realize that troll legends are well overstated and that trolls are actually very nice and sensitive creatures. While incarnating one, you have been given to meet a few which were actually kind of interesting beings and you can't wait to deepen your relationship with them. A lot of fun awaits.'''
            tile2 = graphics.TROLL
            holding = False
        elif player.name == 'wizard':
            text += '''All your life, you have been seeking knowledge and wisdom. Now, you have finally found it and your new wizard life will be full of spells and magic. If only you had more mana... Maybe the amulet provides that kind of power. You reach for it with the satisfaction that this time nothing will prevent you from succeeding your quest.'''
        elif player.name == 'eye':
            text += '''Seeing it all is what you prefer. Your latest adventures have opened your eyes to a new world of sightedness. Clearly, your power is way beyond those creatures blind to the real world. Can finally see the meaning of life. You can see it all, way above anything you could imagine, in its beauty and creepiness. As they say, seeing is believing.'''
            holding = False
        elif player.name == 'fire elemental':
            text += '''You take the amulet, and suddenly it catches fire. You realize that you should have been a tiny bit more careful and that it is now destroyed forever. Beyond all the magic that makes you, sorrow takes over and you start crying. Tears of lava.'''
            tile2 = graphics.FIREBALL
            bg = graphics.BOSS_FLOOR
        else:
            text += '''Your body was never worth it. You abandon it and take the amulet. Its immense power surges through you and you finally get to know that subtle feeling of accomplishment. '''
        rl.clear()
        lines = util.wrap_text(text, const.SCREEN_WIDTH * 8 - 64)
        rl.draw_text(font, 32, ((const.SCREEN_HEIGHT - len(lines)) // 2) * 8, '\n'.join(lines), rl.LIGHTGRAY)
        x = 8 * const.SCREEN_WIDTH // 2
        y = (1 + (const.SCREEN_HEIGHT + len(lines)) // 2) * 8
        for i in range(4):
            rl.draw_tile(tileset, x - 12 + i * 8, y + 2, bg)
        if holding:
            rl.draw_tile(tileset, x - 2, y, tile1)
            if tile2 is not None:
                rl.draw_tile(tileset, x + 2, y - 4, tile2)
        else:
            rl.draw_tile(tileset, x - 8, y, tile1)
            rl.draw_tile(tileset, x + 8, y, tile2)

    def update(self, event):
        if event > 0:
            game.pop_scene()

    def end(self):
        ui.message('Congratulations, you have finished ExpelledRL. Game over.', rl.PINK)
        ui.message('Press ESACAPE to bring the menu.')
        game.state = 'game-over'


class TargetTile(Scene):
    def __init__(self, prompt, callback, max_range=None):
        self.callback = callback
        if max_range is None:
            max_range = const.SCREEN_HEIGHT // 2
        self.max_range = max_range
        self.center_x = const.SCREEN_WIDTH // 2
        self.center_y = const.PANEL_Y // 2
        self.selected_x = self.center_x
        self.selected_y = self.center_y
        self.prompt = prompt
        self.prompt_size = rl.size_text(font, prompt)
        self.instructions = 'Use mouse or movement keys and ENTER/SPACE to select. ESCAPE to cancel.'
        self.instructions_size = rl.size_text(font, self.instructions)

    def render(self):
        max_range, center_x, center_y = self.max_range, self.center_x, self.center_y
        for i in range(const.SCREEN_WIDTH):
            for j in range(const.PANEL_Y):
                distance = math.sqrt((i - center_x) ** 2 + (j - center_y) ** 2) 
                if distance >= max_range:
                        rl.fill_rect(i * 8, j * 8, 8, 8, rl.color(255, 0, 0, 128))
        rl.draw_rect(self.selected_x * 8, self.selected_y * 8, 9, 9, rl.color(192, 192, 0))

        rl.draw_text(font, game.WIDTH // 2 - self.prompt_size[0] // 2, 8, self.prompt, rl.YELLOW)
        rl.draw_text(font, game.WIDTH // 2 - self.instructions_size[0] // 2, 8 * (const.PANEL_Y), self.instructions, rl.YELLOW)

    def update(self, key):
        dx = dy = 0
        x, y, button = -1, -1, -1
        if key > 0:
            dx, dy = controllers.get_movement_from_key(key)
            if rl.shift_pressed():
                dx *= 5
                dy *= 5
            x = self.selected_x + dx
            y = self.selected_y + dy
        elif key == rl.MOUSE:
            x, y, button = rl.mouse()
            x //= 8
            y //= 8
        distance = math.sqrt((x - self.center_x) ** 2 + (y - self.center_y) ** 2) 
        if distance < self.max_range:
            if x >= 0 and x < const.SCREEN_WIDTH and y >= 0 and y < const.PANEL_Y:
                self.selected_x, self.selected_y = x, y

        if key == rl.ESCAPE or button == 3:
            game.pop_scene()
            self.callback(None, None)
        if key == rl.RETURN or key == rl.SPACE or button == 1:
            game.pop_scene()
            x_offset = self.center_x - player.x
            y_offset = self.center_y - player.y
            self.callback(-x_offset + self.selected_x, -y_offset + self.selected_y)


class ActionMenu(Menu):
    def __init__(self):
        self.actions = list(player.actions)
        if debug.active:
            self.actions += [powers.DEBUG_SPELL, powers.DEBUG_SUMMON, powers.DEBUG_KILL, powers.DEBUG_LEVEL, powers.DEBUG_ENDING, powers.DEBUG_CLEANSE]
        options = [action.name for action in self.actions]
        if len(options) == 0:
            super().__init__('You rather unskilled', ['Cancel'], self.on_select)
        else:
            super().__init__('Choose what to perform:', options, self.on_select)

    def update(self, key):
        if key == rl.A:
            game.pop_scene()
        super().update(key)

    def on_select(self, item):
        game.pop_scene()
        if item >= 0 and item < len(self.actions):
            self.actions[item].perform(player)

 
