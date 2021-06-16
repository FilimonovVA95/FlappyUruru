from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ObjectProperty
from kivy.uix.image import Image


# Ловушка паутина
class SpiderWeb(Widget):
    # Центр паутины и текстура
    web_position = NumericProperty(0)
    web_texture = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Создаем текстуру паутины
        self.web_texture = Image(source="spider_web.png").texture
        self.web_texture.wrap = 'repeat'
