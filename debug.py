import builtins
import rl

import powers
import const
import scenes
import util
import controllers
import monsters

active = True

def any_spell(caster):
    actions = [powers.LIGHTNING, powers.FEAR, powers.FIREBALL, powers.CONFUSE, powers.FREEZE, powers.TELEPORT, powers.DIG, powers.SUMMON]
    options = [action.name for action in actions]
    def callback(index):
        game.pop_scene()
        actions[index].effect(player)
    game.push_scene(scenes.Menu('Which spell?', options, callback))

def summon_hostile(caster):
    powers.cast_summon(caster, hostile=True)

def kill_monster(caster):
    def callback(monster):
        print('KILL', monster)
        monster.take_damage(monster.hp)
    util.target_monster('Which monster?', callback, player.sight_radius)

def choose_level(caster):
    global dungeon_level
    options = ['Level %d' % i for i in range(1, 9)]
    def callback(index):
        game.pop_scene()
        game.dungeon_level = index
        game.next_level()
    game.push_scene(scenes.Menu('Choose level', options, callback))

def see_ending(caster):
    options = ['rat', 'bat', 'orc', 'troll', 'ghost', 'eye', 'fire_elemental', 'octopus', 'necromancer', 'wizard', 'original-body', 'ghoul']
    def callback(index):
        game.pop_scene()
        player.pop_controller()
        builtins.player = monsters.make_monster(options[index], 0, 0)
        player.push_controller(controllers.Player())
        game.push_scene(scenes.Ending())
    game.push_scene(scenes.Menu('Choose character', options, callback))

def cleanse_self(caster):
    caster.current_possession_cooldown = 0
    caster.hp = caster.max_hp
    caster.mana = caster.max_mana
 
powers.DEBUG_SUMMON = powers.Power('Summon hostile', 0, const.NO_RANGE, effect=summon_hostile)
powers.DEBUG_LEVEL = powers.Power('Choose level', 0, const.NO_RANGE, effect=choose_level)
powers.DEBUG_ENDING = powers.Power('See ending', 0, const.NO_RANGE, effect=see_ending)
powers.DEBUG_SPELL = powers.Power('Cast spell', 0, const.NO_RANGE, effect=any_spell)
powers.DEBUG_KILL = powers.Power('Kill monster', 0, const.NO_RANGE, effect=kill_monster)
powers.DEBUG_CLEANSE = powers.Power('Drink a refresher', 0, const.NO_RANGE, effect=cleanse_self)

