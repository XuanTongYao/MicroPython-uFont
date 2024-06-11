"""
SSD1306(OLED 128*64) 屏幕中文测试
Micropython版本: 1.22.1
演示硬件:
    SSD1306(OLED 128*64 IIC)
    树莓派Pico RP2040
所需文件:
    ufont.py
    unifont-14-12917-16.v3.bmf
    ssd1306.py
链接引脚:
    SCL = 17
    SDA = 16
使用字体: unifont-14-12917-16.v3.bmf
"""

import time

from machine import I2C, Pin

import ufont
import driver.ssd1306 as ssd1306


def wait(info, _t=5):
    print(info)
    time.sleep(_t)


# 请修改为对应引脚
i2c = I2C(id=0, scl=Pin(17), sda=Pin(16))
display = ssd1306.SSD1306_I2C(128, 64, i2c)

# 载入字体
#   使用字体制作工具：https://github.com/AntonVanke/MicroPython_BitMap_Tools
font = ufont.BMFont("./unifont-14-12917-16.v3.bmf")

wait(
    """
# The easiest way to display “Hello”
#   where `show=True` is specified to keep the screen up-to-date
""",
    6,
)
font.text(display, "你好", 0, 0, show=True)

wait(
    """
# If you want the text to be displayed in the center of the screen, you can modify the display position by specifying the upper-left corner of the text position
""",
    5,
)
font.text(display, "你好", 48, 16, show=True)

wait(
    """
# At this point you will notice: the text displayed in the last display will not disappear. Because you did not specify the clear parameter: `clear=True`; let's try again!
#   Note, please use the modified `ssd1306.py` driver, otherwise call `display.fill(0)` yourself.
""",
    10,
)
font.text(display, "你好", 48, 16, show=True, clear=True)

wait(
    """
# What about displaying English?
""",
    3,
)
font.text(display, "He110", 48, 8, show=True, clear=True)
font.text(display, "你好", 48, 24, show=True)

wait(
    """
# You will notice that the width of a Chinese character is roughly twice the width of a letter, if you need to equalize the width, you can specify the parameter `half_char=False`.
""",
    6,
)
font.text(display, "HELLO", 32, 16, show=True, clear=True, half_char=False)

wait(
    """
# Display text that is very long and goes beyond the screen boundaries, for example:
""",
    3,
)
poem = "他日若遂凌云志，敢笑黄巢不丈夫!"
font.text(display, poem, 0, 8, show=True, clear=True)

wait(
    """
# In this case, you need to specify the parameter `auto_wrap=True` to automatically wrap the lines.
""",
    5,
)
font.text(display, poem, 0, 8, show=True, clear=True, auto_wrap=True)

wait(
    """
# Line spacing too small for auto line breaks?
#   Add `line_spacing: int` parameter to adjust line spacing, here specify 8 pixels.
""",
    8,
)
font.text(display, poem, 0, 8, show=True, clear=True, auto_wrap=True, line_spacing=8)

wait(
    """
# Adjust the font size by specifying the `font_size: int` parameter.
#   Note: This can seriously increase runtime
""",
    8,
)
font.text(display, "T:15℃", 24, 8, font_size=32, show=True, clear=True)

wait(
    """
# When you use an ink screen, the colors may be reversed. Or you actively want the colors to be inverted
#   The parameter `reverse=Ture` can be specified.
""",
    8,
)
font.text(display, "T:15℃", 24, 8, font_size=32, show=True, clear=True, reverse=True)
