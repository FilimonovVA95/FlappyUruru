from random import randint
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, NumericProperty
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.clock import Clock

from bloodBag import BloodBag
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

    # Обновление облаков и города - эмитация их движения
    def scroll_textures(self, time_passed):
        self.cloud_texture.uvpos = ((self.cloud_texture.uvpos[0] - time_passed * MainApp.сomplexity) % Window.width, self.cloud_texture.uvpos[1])
        self.city_texture.uvpos = ((self.city_texture.uvpos[0] + time_passed * MainApp.сomplexity) % Window.width, self.city_texture.uvpos[1])

        texture = self.property('cloud_texture')
        texture.dispatch(self)

        texture = self.property('city_texture')
        texture.dispatch(self)


class Ururu(Image):
    velocity = NumericProperty(0)

    def on_touch_down(self, touch):
        self.source = "ururu2.png"
        self.velocity = (Window.height / 3) * MainApp.сomplexity
        MainApp.energy -= 1
        super().on_touch_down(touch)

    def on_touch_up(self, touch):
        self.source = "ururu1.png"
        super().on_touch_up(touch)


class MainApp(App):
    # Размеры экрана
    window_width = Window.width
    window_height = Window.height
    # Сложность и энергия
    сomplexity = 1 # 1 , 1.5 , 2
    energy = int(100 / сomplexity)
    max_energy = int(200 / сomplexity)
    # Для корректного списывания баллов при падении
    is_down = False
    cobwebs = []
    blood_bags = []
    GRAVITY = (Window.height / 1.5) * сomplexity
    time = 0

    def on_start(self):
        Clock.schedule_interval(self.root.ids.background.scroll_textures, 1/60.)

    # Заставляем Уруру двигаться вверх-вниз
    def move_ururu(self, time_passed):
        ururu = self.root.ids.ururu
        ururu.y = ururu.y + ururu.velocity * time_passed
        ururu.velocity = ururu.velocity - self.GRAVITY * time_passed
        self.check_collision_web()
        self.check_collision_blood()

    # Проверяем на столкновение с паутиной
    def check_collision_web(self):
        ururu = self.root.ids.ururu
        for web in self.cobwebs:
            # Проверяем что позиция сетки по горизонту 20 +/- "толщина" сетки "тольщина" Ури
            if (web.pos[0] < 20 + (Window.height / 20)+ (Window.height / 20 * 0.6)) and (web.pos[0] > 20 - (Window.height / 20) - (Window.height / 20 * 0.6)):
                # Проверяем что разница центров Ури и паутины меньше сумарного их половинного размера
                if abs(web.pos[1] - ururu.pos[1]) < Window.height / 7:
                    MainApp.energy -= 10 * MainApp.сomplexity
                    ururu.source = "ururu3.png"
                    self.root.remove_widget(web)
                    self.cobwebs.remove(web)
        if ururu.y < 100 and not self.is_down:
            ururu.velocity = - ururu.velocity
            MainApp.energy -= 10 * MainApp.сomplexity
            ururu.source = "ururu3.png"
            self.is_down = True

        if ururu.top > Window.height:
            MainApp.energy -= 10 * MainApp.сomplexity
            ururu.velocity -= (Window.height / 3) * MainApp.сomplexity
            ururu.source = "ururu3.png"

    # Проверяем на столкновение с кровушкой
    def check_collision_blood(self):
        ururu = self.root.ids.ururu
        for blood in self.blood_bags:
            # Проверяем что позиция сетки по горизонту 20 +/- "толщина" сетки "тольщина" Ури
            if (blood.pos[0] < 20 + (Window.height / 32) + (Window.height / 20 * 0.6)) and (blood.pos[0] > 20 - (Window.height / 32) - (Window.height / 20 * 0.6)):
                # Проверяем что разница центров Ури и паутины меньше сумарного их половинного размера
                if abs(blood.pos[1] - ururu.pos[1]) < Window.height / 7:
                    MainApp.energy += int(30 / MainApp.сomplexity)
                    if MainApp.energy >= MainApp.max_energy:
                        MainApp.energy = int(200)
                    ururu.source = "ururu3.png"
                    self.root.remove_widget(blood)
                    self.blood_bags.remove(blood)

    # Проверяем на конец игры
    def check_game_over(self, time_passed):
        if MainApp.energy <= 0:
            self.game_over()

    # Счетчик за жизнь, обновление энергии и обнуление проверки на столкновение с землей
    def add_scrole(self, time_passed):
        self.time += 1
        self.root.ids.energy.text = "Энергия: " + str(MainApp.energy) + " / " + str(MainApp.max_energy)
        if self.time > 100:
            self.root.ids.score.text = str(int(self.root.ids.score.text) + 1)
            self.time = 0
            self.is_down = False

    def game_over(self):
        self.root.ids.ururu.source = "ururu3.png"
        self.root.ids.ururu.pos = (20, self.root.height / 2.0)
        # Удаляем паутину и кровушку
        for web in self.cobwebs:
            self.root.remove_widget(web)
        for blood in self.blood_bags:
            self.root.remove_widget(blood)
        self.frames.cancel()
        # Делаем снова активными кнопки
        self.root.ids.start_game_button.disabled = False
        self.root.ids.start_game_button.opacity = 1
        self.root.ids.about_game_button.disabled = False
        self.root.ids.about_game_button.opacity = 1
        self.root.ids.energy.opacity = 0

    def next_frame(self, time_passed):
        self.move_ururu(time_passed)
        self.move_cobwebs(time_passed)
        self.move_blood_bags(time_passed)
        self.root.ids.background.scroll_textures(time_passed)
        self.add_scrole(time_passed)
        self.check_game_over(time_passed)

    def start_game(self):
        self.root.ids.score.text = "0"
        self.cobwebs = []
        self.blood_bags = []
        MainApp.energy = int(100)
        self.root.ids.energy.text = "Энергия: " + str(MainApp.energy) + " / " + str(MainApp.max_energy)
        # Таймер
        self.frames = Clock.schedule_interval(self.next_frame, 1/90.)

        # Скрываем кнопку "об игре"
        self.root.ids.about_game_button.disabled = True
        self.root.ids.about_game_button.opacity = 0

        # Создать паутину
        num_web = 200
        distance_between_web = (Window.height / 3) / MainApp.сomplexity
        for i in range(num_web):
            web = SpiderWeb()
            web.web_position = randint(50, self.root.height - 100)
            web.size_hint = (None, None)
            web.pos = (Window.width + i*distance_between_web, web.web_position)
            web.size = (Window.height / 5, Window.height / 5)

            self.cobwebs.append(web)
            self.root.add_widget(web)

        # Создать кровушку
        num_blood = 100
        distance_between_blood = (Window.height * 3) * MainApp.сomplexity
        for i in range(num_blood):
            blood = BloodBag()
            blood.blood_position = randint(50, self.root.height - 100)
            blood.size_hint = (None, None)
            blood.pos = (Window.width + i*distance_between_blood, blood.blood_position)
            blood.size = (Window.height / 5, Window.height / 5)

            self.blood_bags.append(blood)
            self.root.add_widget(blood)

    # Двигаем паутинку
    def move_cobwebs(self, time_passed):
        for web in self.cobwebs:
            web.x -= time_passed * 600 * self.сomplexity

        # Зацикливание паутинки
        distance_between_web = Window.height
        web_xs = list(map(lambda web: web.x, self.cobwebs))
        right_most_x = max(web_xs)
        if right_most_x <= Window.width - distance_between_web:
            most_left_web = self.cobwebs[web_xs.index(min(web_xs))]
            most_left_web.x = Window.width

    # Двигаем кровушку
    def move_blood_bags(self, time_passed):
        for blood in self.blood_bags:
            blood.x -= time_passed * 800 * self.сomplexity

        # Зацикливание кровушку
        distance_between_blood = Window.height / 5
        blood_xs = list(map(lambda blood: blood.x, self.blood_bags))
        right_most_x2 = max(blood_xs)
        if right_most_x2 <= Window.width - distance_between_blood:
            most_left_blood2 = self.blood_bags[blood_xs.index(min(blood_xs))]
            most_left_blood2.x = Window.width

if __name__ == "__main__":
    MainApp().run()