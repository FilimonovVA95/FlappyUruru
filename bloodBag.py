from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ObjectProperty
from kivy.uix.image import Image
from kivy.core.window import Window


# Пакетик крови
class BloodBag(Widget):
    # Центр кровушки
    blood_position = NumericProperty(0)
    blood_texture = ObjectProperty(None)
    blood_width = Window.height / 8
    blood_height = Window.height / 8

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Создаем текстуру кровушки
        self.blood_texture = Image(source="bloodBag.png").texture
        self.blood_texture.wrap = 'repeat'
