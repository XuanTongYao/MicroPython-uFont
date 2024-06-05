#   Github: https://github.com/AntonVanke/MicroPython-uFont
#   Gitee: https://gitee.com/liio/MicroPython-uFont
#   Tools: https://github.com/AntonVanke/MicroPython-ufont-Tools
#   Videos:
#       https://www.bilibili.com/video/BV12B4y1B7Ff/
#       https://www.bilibili.com/video/BV1YD4y16739/
__version__ = 3

import utime
import struct
import gc
import framebuf, micropython

DEBUG = True

# 索引分块(起始与结束)
# 拉丁字母
BLOCK_LATIN_S = const(0)
BLOCK_LATIN_E = const(0x024F)

# 西里尔字母
BLOCK_CYRILLIC_S = const(0x0400)
BLOCK_CYRILLIC_E = const(0x052F)

# 中日韩统一表意文字
BLOCK_CJK_S = const(0x4E00)
BLOCK_CJK_E = const(0x9FFF)


def timed_function(f, *args, **kwargs):
    """测试函数运行时间"""
    # 当交叉编译后无法获取函数名
    try:
        _name = f.__name__
    except AttributeError:
        _name = "Unknown"

    def new_func(*args, **kwargs):
        if DEBUG:
            t = utime.ticks_us()
            result = f(*args, **kwargs)
            delta = utime.ticks_diff(utime.ticks_us(), t)
            print("Function {} Time = {:6.3f}ms".format(_name, delta / 1000))
            return result
        else:
            return f(*args, **kwargs)

    return new_func


class BMFont:

    @micropython.native
    @timed_function
    def text(
        self,
        display,
        string: str,
        x: int,
        y: int,
        color: int = 0xFFFF,
        bg_color: int = 0,
        font_size: int | None = None,
        half_char: bool = True,
        auto_wrap: bool = False,
        show: bool = True,
        clear: bool = False,
        alpha_color: int = 0,
        reverse: bool = False,
        color_type: int = -1,
        line_spacing: int = 0,
        **kwargs,
    ):
        """
        Args:
            display: 显示对象
            string: 显示文字
            x: 字符串左上角 x 轴
            y: 字符串左上角 y 轴
            color: 字体颜色(RGB565)
            bg_color: 字体背景颜色(RGB565)
            font_size: 字号大小
            half_char: 半宽显示 ASCII 字符
            auto_wrap: 自动换行
            show: 实时显示
            clear: 清除之前显示内容
            alpha_color: 透明色(RGB565) 当颜色与 alpha_color 相同时则透明
            reverse: 逆置(MONO)
            color_type: 色彩模式 0:MONO 1:RGB565
            line_spacing: 行间距
            **kwargs:

        Returns:
        MoreInfo: https://github.com/AntonVanke/MicroPython-uFont/blob/master/README.md
        """
        # 如果没有指定字号则使用默认字号
        font_size = font_size or self.font_size
        # 记录初始的 x 位置
        initial_x = x

        # 设置颜色类型
        if color_type == -1 and (display.width * display.height) > len(display.buffer):
            color_type = 0
        elif color_type == -1 or color_type == 1:
            palette = [
                [bg_color & 0xFF, (bg_color & 0xFF00) >> 8],
                [color & 0xFF, (color & 0xFF00) >> 8],
            ]
            color_type = 1

        # 处理黑白屏幕的背景反转问题
        if color_type == 0 and color == 0 != bg_color or color_type == 0 and reverse:
            reverse = True
            alpha_color = -1
        else:
            reverse = False

        # 清屏
        try:
            display.clear() if clear else 0
        except AttributeError:
            print("请自行调用 display.fill() 清屏")

        for char in range(len(string)):
            if auto_wrap and (
                (
                    x + font_size // 2 > display.width
                    and ord(string[char]) < 128
                    and half_char
                )
                or (
                    x + font_size > display.width
                    and (not half_char or ord(string[char]) > 128)
                )
            ):
                y += font_size + line_spacing
                x = initial_x

            # 对控制字符的处理
            if string[char] == "\n":
                y += font_size + line_spacing
                x = initial_x
                continue
            elif string[char] == "\t":
                x = ((x // font_size) + 1) * font_size + initial_x % font_size
                continue
            elif ord(string[char]) < 16:
                continue

            # 超过范围的字符不会显示*
            if x > display.width or y > display.height:
                continue

            # 获取字体的点阵数据
            byte_data = list(self.get_bitmap(string[char]))

            # 分四种情况逐个优化
            #   1. 黑白屏幕/无放缩
            #   2. 黑白屏幕/放缩
            #   3. 彩色屏幕/无放缩
            #   4. 彩色屏幕/放缩
            if color_type == 0:
                byte_data = self._reverse_byte_data(byte_data) if reverse else byte_data
                if font_size == self.font_size:
                    display.blit(
                        framebuf.FrameBuffer(
                            bytearray(byte_data),
                            font_size,
                            font_size,
                            framebuf.MONO_HLSB,
                        ),
                        x,
                        y,
                        alpha_color,
                    )
                else:
                    display.blit(
                        framebuf.FrameBuffer(
                            self._HLSB_font_size(byte_data, font_size, self.font_size),
                            font_size,
                            font_size,
                            framebuf.MONO_HLSB,
                        ),
                        x,
                        y,
                        alpha_color,
                    )
            elif color_type == 1 and font_size == self.font_size:
                display.blit(
                    framebuf.FrameBuffer(
                        self._flatten_byte_data(byte_data, palette),
                        font_size,
                        font_size,
                        framebuf.RGB565,
                    ),
                    x,
                    y,
                    alpha_color,
                )
            elif color_type == 1 and font_size != self.font_size:
                display.blit(
                    framebuf.FrameBuffer(
                        self._RGB565_font_size(
                            byte_data, font_size, palette, self.font_size
                        ),
                        font_size,
                        font_size,
                        framebuf.RGB565,
                    ),
                    x,
                    y,
                    alpha_color,
                )
            # 英文字符半格显示
            if ord(string[char]) < 128 and half_char:
                x += font_size // 2
            else:
                x += font_size

        display.show() if show else 0

    @micropython.native
    @timed_function
    def _get_index(self, word: str) -> int:
        """
        获取索引
        Args:
            word: 字符

        Returns:
        ESP32-C3: Function _get_index Time =  2.670ms
        """
        word_code = ord(word)
        start = 0x10
        end = self.start_bitmap
        if not self.EnableMemIndex:
            while start <= end:
                mid = ((start + end) // 4) * 2
                self.font.seek(mid, 0)
                target_code = struct.unpack(">H", self.font.read(2))[0]
                if word_code == target_code:
                    return (mid - 16) >> 1
                elif word_code < target_code:
                    end = mid - 2
                else:
                    start = mid + 2
        else:
            Cache = self.FontIndexCache
            start = 0
            end = (end - 0x10) // 2
            while start <= end:
                mid = (start + end) // 2
                target_code = Cache[mid]
                if word_code == target_code:
                    return mid
                elif word_code < target_code:
                    end = mid - 1
                else:
                    start = mid + 1
        return -1

    @micropython.native
    @timed_function
    def _Fast_get_index(self, word: str) -> int:
        """
        获取索引，利用分块加速的版本
        Args:
            word: 字符

        Returns:
        """
        word_code = ord(word)
        start = 0x10
        end = self.start_bitmap
        for i, BSE in enumerate(self.BlockBoundary):
            if BSE[0] <= word_code <= BSE[1] and self.BlockPos[i]:
                start, end = self.BlockPos[i]
                break

        if not self.EnableMemIndex:
            while start <= end:
                mid = ((start + end) // 4) * 2
                self.font.seek(mid, 0)
                target_code = struct.unpack(">H", self.font.read(2))[0]
                if word_code == target_code:
                    return (mid - 16) >> 1
                elif word_code < target_code:
                    end = mid - 2
                else:
                    start = mid + 2
        else:
            Cache = self.FontIndexCache
            start = (start - 0x10) // 2
            end = (end - 0x10) // 2
            while start <= end:
                mid = (start + end) // 2
                target_code = Cache[mid]
                if word_code == target_code:
                    return mid
                elif word_code < target_code:
                    end = mid - 1
                else:
                    start = mid + 1
        return -1

    # @timed_function
    # 不理解为什么类型提示为bytearray?明明调用的地方是传入list
    def _HLSB_font_size(
        self, byte_data: bytearray, new_size: int, old_size: int
    ) -> bytearray:
        old_size = old_size
        _temp = bytearray(new_size * ((new_size >> 3) + 1))
        _new_index = -1
        for _col in range(new_size):
            for _row in range(new_size):
                if (_row % 8) == 0:
                    _new_index += 1
                _old_index = int(_col / (new_size / old_size)) * old_size + int(
                    _row / (new_size / old_size)
                )
                _temp[_new_index] = _temp[_new_index] | (
                    (byte_data[_old_index >> 3] >> (7 - _old_index % 8) & 1)
                    << (7 - _row % 8)
                )
        return _temp

    # @timed_function
    # 不理解为什么类型提示为bytearray?明明调用的地方是传入list
    def _RGB565_font_size(
        self, byte_data: bytearray, new_size: int, palette: list, old_size: int
    ) -> bytearray:
        old_size = old_size
        _temp = []
        _new_index = -1
        for _col in range(new_size):
            for _row in range(new_size):
                if (_row % 8) == 0:
                    _new_index += 1
                _old_index = int(_col / (new_size / old_size)) * old_size + int(
                    _row / (new_size / old_size)
                )
                _temp.extend(
                    palette[byte_data[_old_index // 8] >> (7 - _old_index % 8) & 1]
                )
        return bytearray(_temp)

    # @timed_function
    # 不理解为什么类型提示为bytearray?明明调用的地方是传入list
    def _flatten_byte_data(self, _byte_data: bytearray, palette: list) -> bytearray:
        """
        渲染彩色像素
        Args:
            _byte_data:
            palette:

        Returns:

        """
        _temp = []
        for _byte in _byte_data:
            for _b in range(7, -1, -1):
                _temp.extend(palette[(_byte >> _b) & 0x01])
        return bytearray(_temp)

    # @timed_function
    # 不理解为什么类型提示为bytearray?明明调用的地方是传入list
    def _reverse_byte_data(self, _byte_data: bytearray) -> bytearray:
        for _pixel in range(len(_byte_data)):
            _byte_data[_pixel] = ~_byte_data[_pixel] & 0xFF
        return _byte_data

    @micropython.native
    @timed_function
    def get_bitmap(self, word: str) -> bytes:
        """获取点阵数据

        Args:
            word: 字符

        Returns:
            bytes 字符点阵
        """
        index = self._get_index(word)
        if index == -1:
            return (
                b"\xff\xff\xff\xff\xff\xff\xff\xff\xf0\x0f\xcf\xf3\xcf\xf3\xff\xf3\xff\xcf\xff?\xff?\xff\xff\xff"
                b"?\xff?\xff\xff\xff\xff"
            )

        self.font.seek(self.start_bitmap + index * self.bitmap_size, 0)
        return self.font.read(self.bitmap_size)

    @micropython.native
    # @timed_function
    def Fast_get_bitmap(self, word: str, buff: bytearray):
        """获取点阵数据"""
        index = 0
        if self.EnableBlockIndex:
            index = self._Fast_get_index(word)
        else:
            index = self._get_index(word)
        if index == -1:
            buff[0:31] = (
                b"\xff\xff\xff\xff\xff\xff\xff\xff\xf0\x0f\xcf\xf3\xcf\xf3\xff\xf3\xff\xcf\xff?\xff?\xff\xff\xff"
                b"?\xff?\xff\xff\xff\xff"
            )
            return

        self.font.seek(self.start_bitmap + index * self.bitmap_size, 0)
        self.font.readinto(buff)

    def __init__(self, font_file, EnableMemIndex=False, EnableBlockIndex=False):
        """
        Args:
            font_file: 字体文件路径
            EnableMemIndex: 内存索引，将索引信息全部载入内存，更快速，每个索引2字节，内存小的机器慎用
            EnableBlockIndex: 分块索引，根据unicode区段，先进行分块，初始化时间较长
        """
        self.font_file = font_file
        # 载入字体文件
        self.font = open(font_file, "rb")
        # 获取字体文件信息
        #   字体文件信息大小 16 byte ,按照顺序依次是
        #       文件标识 2 byte
        #       版本号 1 byte
        #       映射方式 1 byte
        #       位图开始字节 3 byte
        #       字号 1 byte
        #       单字点阵字节大小 1 byte
        #       保留 7 byte
        self.bmf_info = self.font.read(16)

        # 判断字体是否正确
        #   文件头和常用的图像格式 BMP 相同，需要添加版本验证来辅助验证
        if self.bmf_info[0:2] != b"BM":
            raise TypeError("字体文件格式不正确: " + font_file)
        self.version = self.bmf_info[2]
        if self.version != 3:
            raise TypeError("字体文件版本不正确: " + str(self.version))

        # 映射方式
        #   目前映射方式并没有加以验证，原因是 MONO_HLSB 最易于处理
        self.map_mode = self.bmf_info[3]

        # 位图开始字节
        #   位图数据位于文件尾，需要通过位图开始字节来确定字体数据实际位置
        self.start_bitmap = struct.unpack(">I", b"\x00" + self.bmf_info[4:7])[0]
        # 字体大小
        #   默认的文字字号，用于缩放方面的处理
        self.font_size = self.bmf_info[7]
        # 点阵所占字节
        #   用来定位字体数据位置
        self.bitmap_size = self.bmf_info[8]

        # 建立内存索引
        WordNum = (self.start_bitmap - 16) // 2
        self.EnableMemIndex = EnableMemIndex
        if EnableMemIndex:
            self.FontIndexCache = struct.unpack(
                f">{WordNum}H", self.font.read(self.start_bitmap - 16)
            )

        # 分块初始化
        self.EnableBlockIndex = EnableBlockIndex
        if EnableBlockIndex:
            self.BlockPos: list = list(None for _ in range(3))
            self.BlockBoundary = (
                (BLOCK_LATIN_S, BLOCK_LATIN_E),
                (BLOCK_CYRILLIC_S, BLOCK_CYRILLIC_E),
                (BLOCK_CJK_S, BLOCK_CJK_E),
            )
            BB = self.BlockBoundary
            LenBB = len(BB)
            self.font.seek(0x10, 0)
            Len = 1000
            NotEOF = True
            Block = 0
            FindStart = False
            Start, End = 0, 0

            while NotEOF:
                if Len + self.font.tell() > self.start_bitmap:
                    Len = self.start_bitmap - self.font.tell()
                    NotEOF = False
                Cache = struct.unpack(f">{Len//2}H", self.font.read(Len))
                for i, WordCode in enumerate(Cache):
                    # 满足分块并且是第一个 就记录此时索引
                    # 如果不满足分块并且已经找出了第一个索引，就记录此时索引
                    # 如果不满足分块但没找到第一个索引，就把此时索引记录为第一个
                    for j, B_SE in enumerate(BB):
                        if B_SE[0] <= WordCode <= B_SE[1]:
                            if FindStart:
                                break
                            else:
                                Block = j
                                FindStart = True
                                Start = self.font.tell() - Len + (i * 2)
                                break
                        elif FindStart and j == Block:
                            End = self.font.tell() - Len + (i * 2)
                            FindStart = False
                            self.BlockPos[Block] = (Start, End)

                    if Block == LenBB:
                        NotEOF = False
                        break
            if FindStart:
                self.BlockPos[Block] = (Start, self.start_bitmap)
        gc.collect()
