from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ObjectProperty
from kivy.uix.image import Image
from kivy.core.window import Window


# Ловушка паутина
class SpiderWeb(Widget):
    # Центр паутины и текстура
    web_position = NumericProperty(0)
    web_texture = ObjectProperty(None)
    web_width = Window.height / 5
    web_height = Window.height / 5

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Создаем текстуру паутины
        self.web_texture = Image(source="Images/spider_web.png").texture
        self.web_texture.wrap = 'repeat'


# Ловушка бита
class Bit(Widget):
    # Центр паутины и текстура
    bit_position = NumericProperty(0)
    bit_texture = ObjectProperty(None)
    bit_width = Window.height / 5
    bit_height = Window.height / 5

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Создаем текстуру паутины
        self.bit_texture = Image(source="Images/bit.png").texture
        self.bit_texture.wrap = 'repeat'

