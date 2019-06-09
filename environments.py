import rl

import const
import util
import ui

def water_effect(monster):
    if monster.alive and len(set(['can_fly', 'can_swim']) & set(monster.skills)) == 0:
        if monster is player or player.can_see(monster):
            ui.message(util.capitalize(monster.get_name('{is}')) + ' drowning.', rl.RED)
        monster.take_damage(max(1, monster.max_hp // 3))
        return False
    return True

def lava_effect(monster):
    if monster.alive and 'immune_fire' not in monster.skills:
        if monster is player or player.can_see(monster):
            ui.message(util.capitalize(monster.get_name('{is}')) + ' burning.', rl.RED)
        monster.take_damage(50)
        return False
    return True

def fireball_effect(monster):
    if monster.alive and 'immune_fire' not in monster.skills:
        if monster is player or player.can_see(monster):
            ui.message(util.capitalize(monster.get_name('{is}')) + ' burning.', rl.RED)
        monster.take_damage(const.FIREBALL_DAMAGE)
        return False
    return True

