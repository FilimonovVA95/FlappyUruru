from random import randint

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, NumericProperty
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.clock import Clock
from spiderWeb import SpiderWeb


# Задний фон
class Background(Widget):
    cloud_texture = ObjectProperty(None)
    city_texture = ObjectProperty(None)

    # Создаем текстуры
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Создаем текстуру облаков
        self.cloud_texture = Image(source="cloud.png").texture
        self.cloud_texture.wrap = 'repeat'
        self.cloud_texture.uvsize = (Window.width / self.cloud_texture.width, -1)

        # Создаем текстуру города
        self.city_texture = Image(source="city.png").texture
        self.city_texture.wrap = 'repeat'
        self.city_texture.uvsize = (Window.width / self.city_texture.width, -1)

   # def on_size(self, *args):
    #    self.cloud_texture.uvsize = (self.width / self.cloud_texture.width, -1)
   #     self.city_texture.uvsize = (self.width / self.city_texture.width, -1)

    # Обновление облаков и города - эмитация их движения
    def scroll_textures(self, time_passed):
        # Update the uvpos of the texture
        self.cloud_texture.uvpos = ( (self.cloud_texture.uvpos[0] - time_passed/2.0)%Window.width , self.cloud_texture.uvpos[1])
        self.city_texture.uvpos = ( (self.city_texture.uvpos[0] + time_passed/1.5)%Window.width, self.city_texture.uvpos[1])

        # Redraw the texture
        texture = self.property('cloud_texture')
        texture.dispatch(self)

        texture = self.property('city_texture')
        texture.dispatch(self)


class Ururu(Image):
    velocity = NumericProperty(0)

    def on_touch_down(self, touch):
        self.source = "ururu2.png"
        self.velocity = 150
        super().on_touch_down(touch)

    def on_touch_up(self, touch):
        self.source = "ururu1.png"
        super().on_touch_up(touch)


class MainApp(App):
    cobwebs = []
    GRAVITY = 300
    time = 0

    def on_start(self):
        Clock.schedule_interval(self.root.ids.background.scroll_textures, 1/60.)

    # Заставляем Уруру двигаться вверх-вниз
    def move_ururu(self, time_passed):
        ururu = self.root.ids.ururu
        ururu.y = ururu.y + ururu.velocity * time_passed
        ururu.velocity = ururu.velocity - self.GRAVITY * time_passed
        self.check_collision_game_over()

    # Проверяем на столкновение на конец игры
    def check_collision_game_over(self):
        ururu = self.root.ids.ururu
        for web in self.cobwebs:
            # Проверяем что позиция сетки по горизонту 20 +/- "толщина" сетки
            if (web.pos[0] < 60) and (web.pos[0] > -20):
                # Проверяем что разница центров Ури и паутины меньше сумарного их половинного размера
                if abs(web.pos[1] - ururu.pos[1]) < 70:
                    self.game_over()
                    self.root.remove_widget(web)
                    self.cobwebs.remove(web)
        if ururu.y < 100:
            self.game_over()
        if ururu.top > Window.height:
            self.game_over()

    # Счетчик за жизнь
    def add_scrole(self, time_passed):
        self.time += 1
        if self.time > 100:
            self.root.ids.score.text = str(int(self.root.ids.score.text) + 1)
            self.time = 0

    def game_over(self):
        self.root.ids.ururu.source = "ururu3.png"
        self.root.ids.ururu.pos = (20, self.root.height / 2.0)
        for web in self.cobwebs:
            self.root.remove_widget(web)
        self.frames.cancel()
        # Делаем снова активными кнопки
        self.root.ids.start_game_button.disabled = False
        self.root.ids.start_game_button.opacity = 1
        self.root.ids.about_game_button.disabled = False
        self.root.ids.about_game_button.opacity = 1

    def next_frame(self, time_passed):
        self.move_ururu(time_passed)
        self.move_cobwebs(time_passed)
        self.root.ids.background.scroll_textures(time_passed)
        self.add_scrole(time_passed)

    def start_game(self):
        self.root.ids.score.text = "0"
        self.cobwebs = []
        # Таймер
        self.frames = Clock.schedule_interval(self.next_frame, 1/60.)

        # Скрываем кнопку "об игре"
        self.root.ids.about_game_button.disabled = True
        self.root.ids.about_game_button.opacity = 0

        # Создать паутину
        num_web = 50
        distance_between_web = 150
        for i in range(num_web):
            web = SpiderWeb()
            web.web_position = randint(50, self.root.height - 100)
            web.size_hint = (None, None)
            web.pos = (Window.width + i*distance_between_web, web.web_position)
            web.size = (218, 193)

            self.cobwebs.append(web)
            self.root.add_widget(web)

    def move_cobwebs(self, time_passed):
        for web in self.cobwebs:
            web.x -= time_passed * 200

        # Зацикливание паутинки
        distance_between_web = 150
        web_xs = list(map(lambda web: web.x, self.cobwebs))
        right_most_x = max(web_xs)
        if right_most_x <= Window.width - distance_between_web:
            most_left_web = self.cobwebs[web_xs.index(min(web_xs))]
            most_left_web.x = Window.width

if __name__ == "__main__":
    MainApp().run()
