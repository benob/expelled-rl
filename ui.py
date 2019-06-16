import ure
import rl

import util
import const

last_message = None
def message(new_msg, color=rl.WHITE):
    global last_message
    if new_msg == last_message and len(game.messages) > 0:
        found = ure.search('\((\d+)\)$', game.messages[-1][0])
        if found:
            value = int(found.group(1)) + 1
            text = ' '.join(game.messages[-1][0].split(' ')[:-1]) + ' (%d)' % value
            game.messages[-1] = (text, game.messages[-1][1])
        else:
            game.messages[-1] = (game.messages[-1][0].rstrip() + ' (2)', game.messages[-1][1])
    else:
        last_message = new_msg

        # split the message if necessary, among multiple lines
        new_msg_lines = util.wrap_text(new_msg, const.MSG_WIDTH * 8)
     
        for line in new_msg_lines:
            # if the buffer is full, remove the first line to make room for the new one
            if len(game.messages) == const.MSG_HEIGHT:
                del game.messages[0]
     
            # add the new line as a tuple, with the text and the color
            game.messages.append((line, color))
 
def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color, show_value=True):
    bar_width = int(float(value) / maximum * total_width * 8) if maximum != 0 else 0
 
    rl.fill_rect(x * 8, y * 8, total_width * 8, 7, back_color)
    if bar_width > 0:
        rl.fill_rect(x * 8, y * 8, bar_width, 7, bar_color)
 
    if show_value:
        name += ': ' + str(value) + '/' + str(maximum)
    rl.draw_text(font, 8 * x + (8 * total_width // 2), y * 8, name, rl.WHITE, rl.ALIGN_CENTER)
 
class Button:
    pass

