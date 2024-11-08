# Micropython μFont

本仓库 fork 自[AntonVanke/MicroPython-uFont](https://github.com/AntonVanke/MicroPython-uFont)并进行了一些优化。

Micropython 的字体模块，可以用来显示 UTF16 编码的`Unicode`字符。

## 硬件要求

1. 运行`micropython`的开发板，且`micropython>=1.17`
2. 使用`SSD1306`驱动芯片的`OLED屏幕`或者是`ST7735`驱动芯片的`LCD`屏幕亦或是`1.54英寸的e-Paper`
   (只要是使用`FrameBuffer`的屏幕都支持，但本项目提供的驱动只有这三种)
3. 如果想要在`OLED`或者`e-Paper`上使用`ufont`显示支持`GB2312`的所有字符，则至少 `230Kbyte` 的空闲 ROM 空间和 `20 Kbyte`的空闲内存
   如果想要在`ST7735`上使用`ufont`显示支持`GB2312`的所有字符，则至少 `230Kbyte` 的空闲 ROM 空间和 `100 Kbyte`的空闲内存

## 快速上手

### 远程调试(无需安装)

该方法不会改变主机的文件系统，但运行速度很慢。

本人已经去 micropython 的仓库提 issue 了，现版本的 mpremote 应该支持显示 Unicode 字符了。
如果显示Unicode会崩溃的话，请把print中的内容都换成ASCII字符。

1. 准备运行`micropython`的开发板和一个`SSD1306`的`OLED`屏幕，并完成连接
2. 克隆或下载仓库到 PC 机本地
3. 打开`demos/remake_ssd1306_demo.py`

   ```python
   # 请修改为对应引脚
   i2c = I2C(id=0, scl=Pin(17), sda=Pin(16))
   ```

4. 下载官方的 [mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html#mpremote) 工具`pip3 install mpremote`
5. 挂载代码目录到主机(请确保运行命令时路径处于代码目录，串口不被其他程序占用)`mpremote mount .`
6. 运行简单演示`>>> import demos.remake_ssd1306_demo.py`

### 安装

1. 准备运行`micropython`的开发板和一个`SSD1306`的`OLED`屏幕，并完成连接
2. 克隆或下载仓库到 PC 机本地
3. 将`demos/ssd1306_demo.py`用编辑器打开

   ```python
   # 修改为对应的 Pin
   i2c = I2C(scl=Pin(2), sda=Pin(3)) # Line 29
   ```

4. 依次将`demos/ssd1306_demo.py`、`drivers/ssd1306.py`、`ufont.py`、`16x16ForDemos.bmf`上传到**开发板根目录**，运行`ssd1306_demo.py`即可

## 使用方法

仅需三步就能使用`ufont`:

```python
# 第一步：导入 ufont 库
import ufont
···
# 第二步：加载字体
font = ufont.BMFont("unifont-14-12917-16.v3.bmf")
···
# 第三步：显示文字
font.text(display, "你好", 48, 16, show=True)
```

### 详细参数

```python
text(display, # 显示对象
     string: str, # 显示文字
     x: int, # 字符串左上角 x 轴
     y: int, # 字符串左上角 y 轴
     color: int = 0xFFFF, # 字体颜色(RGB565)
     bg_color: int = 0, # 字体背景颜色(RGB565)
     font_size: int = None, # 字号大小
     half_char: bool = True, # 半宽显示 ASCII 字符
     auto_wrap: bool = False, # 自动换行
     show: bool = True, # 实时显示
     clear: bool = False, # 清除之前显示内容
     alpha_color: bool = 0, # 透明色(RGB565) 当颜色与 alpha_color 相同时则透明
     reverse: bool = False, # 逆置(MONO)
     color_type: int = -1, # 色彩模式 0:MONO 1:RGB565
     line_spacing: int = 0, # 行间距
     **kwargs)
```

### 使用你自己的显示驱动

在 text 函数中第一个参数为显示对象，如果要使用你自己的驱动文件，你需要创建一个继承自`framebuf.FrameBuffer`的类并实现以下属性：

```python
# 显示器像素宽高
width: int
height: int
# 帧缓存
buffer: bytearray
# 清除帧缓存数据并清屏
def clear(self):
    pass
# 将帧缓存同步到GDDRAM
def show(self):
    pass
```

单色显示器帧缓存长度为 ceil(width\*height/8)
RGB565 显示器帧缓存长度为 width\*height\*2

推荐在原有驱动的基础上创建一个中间类用来适配就可以了
示例：

```python
class ST7789_Compatibility(framebuf.FrameBuffer):
    def __init__(self, st7789: ST7789) -> None:
        self.st7789 = st7789
        st7789.set_fullscreen()
        self.width = st7789.width
        self.height = st7789.height
        self.buffer = bytearray(self.width * self.height * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)

    def clear(self):
        self.fill(0)
        self.st7789.write_gddram(self.buffer)

    def show(self):
        self.st7789.write_gddram(self.buffer)
```

## 字体制作工具

### GITHUB

[MicroPython-uFont-Tools/如何生成点阵字体文件.md at master · AntonVanke/MicroPython-uFont-Tools · GitHub](https://github.com/AntonVanke/MicroPython-uFont-Tools/blob/master/doc/如何生成点阵字体文件.md)

## 更多信息

### VIDEOS

1. [MicroPython 中文字库教程\_哔哩哔哩\_bilibili](https://www.bilibili.com/video/BV12B4y1B7Ff/)
2. [MicroPython 中文字库：自定义字体生成\_哔哩哔哩\_bilibili](https://www.bilibili.com/video/BV1YD4y16739/)

### GITEE(暂无权限)

[MicroPython-Chinese-Font: MicroPython 的中文字库，使 MicroPython 能够显示中文 当然，不止能够显示中文，还可以显示所有 Unicode 字符 (gitee.com)](https://gitee.com/liio/MicroPython-Chinese-Font)

[MicroPython-uFont-Tools: MicroPython uFont 工具 (gitee.com)](https://gitee.com/liio/MicroPython-uFont-Tools)
