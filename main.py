import ast
import os
from random import randint
from kivy.app import App
from kivy.config import ConfigParser
from kivy.core.audio import SoundLoader
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, NumericProperty
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.clock import Clock

from food import BloodBag, EnergyDrink
from traps import SpiderWeb, Bit


# Задний фон
class Background(Widget):
    cloud_texture = ObjectProperty(None)
    city_texture = ObjectProperty(None)

    # Создаем текстуры
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Создаем текстуру облаков
        self.cloud_texture = Image(source="Images/cloud.png").texture
        self.cloud_texture.wrap = 'repeat'
        self.cloud_texture.uvsize = (Window.width / self.cloud_texture.width, -1)

        # Создаем текстуру города
        self.city_texture = Image(source="Images/city.png").texture
        self.city_texture.wrap = 'repeat'
        self.city_texture.uvsize = (Window.width / self.city_texture.width, -1)

    # Обновление облаков и города - эмитация их движения
    def scroll_textures(self, time_passed):
        self.cloud_texture.uvpos = (self.cloud_texture.uvpos[0] - time_passed * (0.9 + 0.11 * MainApp.speed)) % Window.width, self.cloud_texture.uvpos[1]
        self.city_texture.uvpos = (self.city_texture.uvpos[0] + time_passed * (0.9 + 0.11 * MainApp.speed)) % Window.width, self.city_texture.uvpos[1]

        texture = self.property('cloud_texture')
        texture.dispatch(self)

        texture = self.property('city_texture')
        texture.dispatch(self)


class Ururu(Image):
    velocity = NumericProperty(0)

    def on_touch_down(self, touch):
        if not MainApp.is_stop_marker:
            self.source = "Images/ururu2.png"
            self.velocity = (Window.height / 3) * (0.9 + 0.11 * MainApp.speed)
            MainApp.energy -= 1
            super().on_touch_down(touch)
        else:
            self.source = "Images/ururu_bonk.png"

    def on_touch_up(self, touch):
        if not MainApp.is_stop_marker:
            self.source = "Images/ururu1.png"
            super().on_touch_up(touch)
        else:
            self.source = "Images/ururu_bonk.png"


class MainApp(App):
    # Для реализации замедления про ударе битой
    bonk_factor = 1
    is_stop_marker = False
    # Для корректного списывания баллов при падении
    is_down = False
    # Размеры экрана
    window_width = Window.width
    window_height = Window.height
    # Энергия
    energy = int(100)
    max_energy = int(200)
    # Настройки
    complexity = None
    speed = 1
    increasing_speed = None
    increasing_complexity = None
    max_score = None
    # Массивы с обьектами (ловушки и еда)
    cobwebs = []
    blood_bags = []
    bits = []
    drinks = []
    # Гравитация
    GRAVITY = (Window.height / 1.5) * (0.9 + 0.11 * speed)
    # Таймеры для отсчета состояний
    timer_score = 0
    timer_is_down = 0
    timer_stop = 0
    timer_increasing = 0
    # Музыка
    sound_volume = 1
    sound = SoundLoader.load('music.mp3')
    sound.volume = 0.1 * sound_volume
    sound.play()

    # Инициализация записи
    def __init__(self, **kvargs):
        super(MainApp, self).__init__(**kvargs)
        self.config = ConfigParser()

    # Записываем по умолчанию
    def build_config(self, config):
        config.adddefaultsection('General')
        config.setdefault('General', 'speed', "1")
        config.setdefault('General', 'complexity', "1")
        config.setdefault('General', 'increasing_speed', "1")
        config.setdefault('General', 'increasing_complexity', "1")
        config.setdefault('General', 'max_score', "0")
        config.setdefault('General', 'is_music', "True")
        config.setdefault('General', 'sound_volume', "1")

    def set_value_from_config(self):
        self.config.read(os.path.join(self.directory, '%(appname)s.ini'))
        self.user_data = ast.literal_eval(self.config.get('General', 'speed'))
        self.user_data = ast.literal_eval(self.config.get('General', 'complexity'))
        self.user_data = ast.literal_eval(self.config.get('General', 'increasing_speed'))
        self.user_data = ast.literal_eval(self.config.get('General', 'increasing_complexity'))
        self.user_data = ast.literal_eval(self.config.get('General', 'max_score'))
        self.user_data = ast.literal_eval(self.config.get('General', 'is_music'))
        self.user_data = ast.literal_eval(self.config.get('General', 'sound_volume'))

    def get_application_config(self):
        return super(MainApp, self).get_application_config('{}/%(appname)s.ini'.format(self.directory))

    # Старт
    def on_start(self):
        Clock.schedule_interval(self.root.ids.background.scroll_textures, 1/60.)
        Clock.schedule_interval(self.timer_go, 1/60.)

        # Считывание данных при запуске
        self.app = App.get_running_app()
        MainApp.speed = int(self.app.config.get('General', 'speed'))
        MainApp.complexity = int(self.app.config.get('General', 'complexity'))
        MainApp.increasing_speed = int(self.app.config.get('General', 'increasing_speed'))
        MainApp.increasing_complexity = int(self.app.config.get('General', 'increasing_complexity'))
        MainApp.max_score = int(self.app.config.get('General', 'max_score'))

    # Заставляем Уруру двигаться вверх-вниз
    def move_ururu(self, time_passed):
        ururu = self.root.ids.ururu
        ururu.y = ururu.y + ururu.velocity * time_passed
        ururu.velocity = ururu.velocity - self.GRAVITY * time_passed / MainApp.bonk_factor
        self.check_collision_border()
        self.check_collision_web()
        self.check_collision_bit()
        self.check_collision_blood()
        self.check_collision_drink()

    # Проверка на столкновение с границами
    def check_collision_border(self):
        ururu = self.root.ids.ururu
        if ururu.y < 100:
            ururu.velocity = - ururu.velocity
            if not self.is_down:
                MainApp.energy -= int(10 * (0.9 + 0.11 * MainApp.complexity))
            ururu.source = "Images/ururu_bonk.png"
            self.is_down = False
            self.timer_is_down = 0

        if ururu.top > Window.height:
            MainApp.energy -= int(10 * MainApp.complexity)
            ururu.velocity -= (Window.height / 3) * (0.9 + 0.11 * MainApp.speed)
            ururu.source = "Images/ururu_bonk.png"

    # Проверяем на столкновение с паутиной
    def check_collision_web(self):
        ururu = self.root.ids.ururu
        for web in self.cobwebs:
            # Проверяем что позиция сетки по горизонту 20 +/- "толщина" сетки "тольщина" Ури
            if (web.pos[0] < 20 + (Window.height / 20)+ (Window.height / 20 * 0.6)) and (web.pos[0] > 20 - (Window.height / 20) - (Window.height / 20 * 0.6)):
                # Проверяем что разница центров Ури и паутины меньше сумарного их половинного размера
                if abs(web.pos[1] - ururu.pos[1]) < Window.height / 7:
                    MainApp.energy -= int(10 * (0.9 + 0.11 * MainApp.complexity))
                    if ururu.source != "Images/ururu_bonk.png":
                        ururu.source = "Images/ururu_web.png"
                    self.root.remove_widget(web)
                    self.cobwebs.remove(web)

    # Проверяем на столкновение с битой
    def check_collision_bit(self):
        ururu = self.root.ids.ururu
        for bit in self.bits:
            # Проверяем что позиция биты по горизонту 20 +/- "толщина" биты и "тольщина" Ури
            if (bit.pos[0] < 20 + (Window.height / 20)+ (Window.height / 20 * 0.6)) and (bit.pos[0] > 20 - (Window.height / 20) - (Window.height / 20 * 0.6)):
                # Проверяем что разница центров Ури и биты меньше сумарного их половинного размера
                if abs(bit.pos[1] - ururu.pos[1]) < Window.height / 7:
                    MainApp.energy -= int(30 * (0.9 + 0.11 * MainApp.complexity))
                    ururu.source = "Images/ururu_bonk.png"
                    self.root.remove_widget(bit)
                    self.bits.remove(bit)
                    self.timer_stop = 0
                    MainApp.bonk_factor = 4
                    MainApp.is_stop_marker = True

    # Проверяем на столкновение с кровушкой
    def check_collision_blood(self):
        ururu = self.root.ids.ururu
        for blood in self.blood_bags:
            # Проверяем что позиция сетки по горизонту 20 +/- "толщина" кровушки и "тольщина" Ури
            if (blood.pos[0] < 20 + (Window.height / 32) + (Window.height / 20 * 0.6)) and (blood.pos[0] > 20 - (Window.height / 32) - (Window.height / 20 * 0.6)):
                # Проверяем что разница центров Ури и кровушки меньше сумарного их половинного размера
                if abs(blood.pos[1] - ururu.pos[1]) < Window.height / 7:
                    MainApp.energy += int(30 / (0.9 + 0.11 * MainApp.complexity))
                    if MainApp.energy >= MainApp.max_energy:
                        MainApp.energy = int(200)
                    if ururu.source != "Images/ururu_bonk.png":
                        ururu.source = "Images/ururu_blood.png"
                    self.root.remove_widget(blood)
                    self.blood_bags.remove(blood)

    # Проверяем на столкновение с энергосиком
    def check_collision_drink(self):
        ururu = self.root.ids.ururu
        for drink in self.drinks:
            # Проверяем что позиция сетки по горизонту 20 +/- "толщина" банки и "тольщина" Ури
            if (drink.pos[0] < 20 + (Window.height / 32) + (Window.height / 20 * 0.6)) and (drink.pos[0] > 20 - (Window.height / 32) - (Window.height / 20 * 0.6)):
                # Проверяем что разница центров Ури и энергосика меньше сумарного их половинного размера
                if abs(drink.pos[1] - ururu.pos[1]) < Window.height / 7:
                    MainApp.energy += int(20 / (0.9 + 0.11 * MainApp.complexity))
                    if MainApp.energy >= MainApp.max_energy:
                        MainApp.energy = int(200)
                    if ururu.source != "Images/ururu_bonk.png":
                        ururu.source = "Images/ururu_drink.png"
                    self.root.remove_widget(drink)
                    self.drinks.remove(drink)

    # Циклим музыку и обновляем картинку
    def music_update(self, time_passed):
        if self.config.get('General', 'is_music') == "True" and self.sound.state == 'stop':
            self.sound.play()
            self.root.ids.music.background_normal = "Images/music_on.png"
            self.root.ids.music.background_down = "Images/music_on.png"
            print("play")
        if self.config.get('General', 'is_music') == "False" and self.sound.state == 'play':
            self.sound.stop()
            self.root.ids.music.background_normal = "Images/music_off.png"
            self.root.ids.music.background_down = "Images/music_off.png"
            print("stop")

    # Проверяем на конец игры
    def check_game_over(self, time_passed):
        if MainApp.energy <= 0:
            self.game_over()

    # Обновление энергии
    def energy_update(self, time_passed):
        self.root.ids.energy.text = "Энергия: " + str(MainApp.energy) + " / " + str(MainApp.max_energy)

    # Обновление усложнения игры
    def increasing_update(self, time_passed):
        self.timer_increasing += 1
        if self.timer_increasing > 100:
            MainApp.speed = MainApp.speed * (int(MainApp.increasing_speed) / 40 + 0.975)
            MainApp.complexity = MainApp.complexity * (int(MainApp.increasing_complexity) / 40 + 0.975)
            self.timer_increasing = 0

    # Обнуление проверки на замедление от удара
    def is_stop(self, time_passed):
        self.timer_stop += 1
        if self.timer_stop > 100:
            MainApp.bonk_factor = 1
            MainApp.is_stop_marker = False

    # Обнуление проверки на слолкновение с землей
    def is_down_update(self, time_passed):
        self.timer_is_down += 1
        if self.timer_is_down > 100:
            self.timer_is_down = 0
            self.is_down = False

    # Счетчик за жизнь
    def add_scrole(self, time_passed):
        self.timer_score += 1
        if self.timer_score > 100:
            self.root.ids.score.text = str(int(self.root.ids.score.text) + 1)
            self.timer_score = 0

    # Конец игры
    def game_over(self):
        # Обновление лучшего результата
        if int(self.root.ids.score.text) > MainApp.max_score:
            MainApp.max_score = int(self.root.ids.score.text)
            self.config.set('General', 'max_score', str(MainApp.max_score))
            self.app.config.write()
            self.root.ids.max_score.text = str("Лучший результат: " + str(self.config.get('General', 'max_score')))
        # Располагаем на начальное положение
        self.root.ids.ururu.source = "Images/ururu3.png"
        self.root.ids.ururu.pos = (20, self.root.height / 2.0)
        # Удаляем ловушки и еду
        for web in self.cobwebs:
            self.root.remove_widget(web)
        for bit in self.bits:
            self.root.remove_widget(bit)
        for blood in self.blood_bags:
            self.root.remove_widget(blood)
        for drink in self.drinks:
            self.root.remove_widget(drink)
        self.frames.cancel()
        # Делаем снова активными кнопки
        self.root.ids.start_game_button.disabled = False
        self.root.ids.start_game_button.opacity = 1
        self.root.ids.about_game_button.disabled = False
        self.root.ids.about_game_button.opacity = 1
        self.root.ids.setting_button.disabled = False
        self.root.ids.setting_button.opacity = 1
        # Сбрасываем энергию
        self.root.ids.energy.opacity = 0
        # Сбрасываем если были оглушены
        MainApp.bonk_factor = 1
        MainApp.is_stop_marker = False
        # Сбрасываем скорость
        MainApp.speed = int(self.app.config.get('General', 'speed'))

    # Запуск всего того, что должно работать с таймером при игре
    def next_frame(self, time_passed):
        self.move_ururu(time_passed)
        self.move_cobwebs(time_passed)
        self.move_bits(time_passed)
        self.move_blood_bags(time_passed)
        self.move_driks(time_passed)
        self.root.ids.background.scroll_textures(time_passed)
        self.add_scrole(time_passed)

    # Запуск всего того, что должно постоянно работать с таймером
    def timer_go(self, time_passed):
        self.check_game_over(time_passed)
        self.energy_update(time_passed)
        self.is_down_update(time_passed)
        self.is_stop(time_passed)
        self.increasing_update(time_passed)
        self.music_update(time_passed)

    def start_game(self):
        # Считывание данных
        MainApp.speed = int(self.app.config.get('General', 'speed'))
        MainApp.complexity = int(self.app.config.get('General', 'complexity'))
        MainApp.increasing_speed = self.app.config.get('General', 'increasing_speed')
        MainApp.increasing_complexity = self.app.config.get('General', 'increasing_complexity')
        MainApp.max_score = int(self.app.config.get('General', 'max_score'))
        MainApp.is_music = self.app.config.get('General', 'is_music')

        # Обнуление счета и энергии
        self.root.ids.score.text = "0"
        MainApp.energy = int(100)

        # Инициализируем массивы и делаем их пустыми (чтобы с прошлой игры не осталось)
        self.cobwebs = []
        self.blood_bags = []
        self.bits = []
        self.drinks = []
        self.root.ids.energy.text = "Энергия: " + str(MainApp.energy) + " / " + str(MainApp.max_energy)
        # Таймер
        self.frames = Clock.schedule_interval(self.next_frame, 1/60.)

        # Создать паутину
        for i in range(30):
            distance_between_web = randint(int(Window.height / 3), int(Window.height / 2.5))
            web = SpiderWeb()
            web.web_position = randint(50, Window.height - 100)
            web.size_hint = (None, None)
            web.pos = (Window.width + i * distance_between_web, web.web_position)
            web.size = (Window.height / 5, Window.height / 5)

            self.cobwebs.append(web)
            self.root.add_widget(web)

        # Создать биты
        for i in range(5):
            distance_between_bit = randint(int(Window.height * 4), int(Window.height * 6))
            bit = Bit()
            bit.bit_position = randint(50, Window.height - 100)
            bit.size_hint = (None, None)
            bit.pos = (250 + Window.width + i * distance_between_bit, bit.bit_position)
            bit.size = (Window.height / 5, Window.height / 5)

            self.bits.append(bit)
            self.root.add_widget(bit)

        # Создать кровушку
        for i in range(30):
            distance_between_blood = randint(int(Window.height * 4), int(Window.height * 6))
            blood = BloodBag()
            blood.blood_position = randint(50, Window.height - 100)
            blood.size_hint = (None, None)
            blood.pos = (700 + Window.width + i * distance_between_blood, blood.blood_position)
            blood.size = (Window.height / 5, Window.height / 5)

            self.blood_bags.append(blood)
            self.root.add_widget(blood)

        # Создать энергосик
        for i in range(30):
            distance_between_drink = randint(int(Window.height * 2), int(Window.height * 3))
            drink = EnergyDrink()
            drink.drink_position = randint(50, Window.height - 100)
            drink.size_hint = (None, None)
            drink.pos = (500 + Window.width + i * distance_between_drink, drink.drink_position)
            drink.size = (Window.height / 5, Window.height / 5)

            self.drinks.append(drink)
            self.root.add_widget(drink)

    # Двигаем и генерируем новую павутинку
    def move_cobwebs(self, time_passed):
        # Двигаем паутину
        for web in self.cobwebs:
            web.x -= time_passed * 900 * (0.9 + 0.11 * MainApp.speed) / MainApp.bonk_factor
            # Если паутина ушла за границу - удаляем ее
            if (web.pos[0] < - Window.width):
                self.root.remove_widget(web)
                self.cobwebs.remove(web)

        # Если за экраном справа нет паутины - создаем еще 20 штук
        web_xs = list(map(lambda web: web.x, self.cobwebs))
        right_most_x = max(web_xs)
        if right_most_x <= Window.width:
            distance_between_web = randint(int(Window.height / 3), int(Window.height / 2.5))
            for i in range(20):
                web = SpiderWeb()
                web.web_position = randint(50, Window.height - 100)
                web.size_hint = (None, None)
                web.pos = (Window.width + i * distance_between_web, web.web_position)
                web.size = (Window.height / 5, Window.height / 5)

                self.cobwebs.append(web)
                self.root.add_widget(web)

    # Двигаем и генерируем новые биты
    def move_bits(self, time_passed):
        # Двигаем биты
        for bit in self.bits:
            bit.x -= time_passed * 900 * (0.9 + 0.11 * MainApp.speed) / MainApp.bonk_factor
            # Если бита ушла за границу - удаляем ее
            if (bit.pos[0] < - Window.width):
                self.root.remove_widget(bit)
                self.bits.remove(bit)

        # Если за экраном справа нет бит - создаем еще 5 штук
        bit_xs = list(map(lambda bit: bit.x, self.bits))
        right_most_x = max(bit_xs)
        if right_most_x <= Window.width:
            for i in range(5):
                distance_between_bit = randint(int(Window.height * 4), int(Window.height * 6))
                bit = Bit()
                bit.bit_position = randint(50, Window.height - 100)
                bit.size_hint = (None, None)
                bit.pos = (Window.width + i * distance_between_bit, bit.bit_position)
                bit.size = (Window.height / 5, Window.height / 5)

                self.bits.append(bit)
                self.root.add_widget(bit)

    # Двигаем и генерируем новую кровушку
    def move_blood_bags(self, time_passed):
        # Двигаем кровушку
        for blood in self.blood_bags:
            blood.x -= time_passed * 1200 * (0.9 + 0.11 * MainApp.speed) / MainApp.bonk_factor
            # Если кровушка ушла за границу - удаляем ее
            if (blood.pos[0] < - Window.width):
                self.root.remove_widget(blood)
                self.blood_bags.remove(blood)

        # Если за экраном справа нет кровушки - создаем еще 20 штук
        blood_xs = list(map(lambda blood: blood.x, self.blood_bags))
        right_most_x = max(blood_xs)
        if right_most_x <= Window.width:
            for i in range(20):
                distance_between_blood = randint(int(Window.height * 4), int(Window.height * 6))
                blood = BloodBag()
                blood.blood_position = randint(50, Window.height - 100)
                blood.size_hint = (None, None)
                blood.pos = (Window.width + i * distance_between_blood, blood.blood_position)
                blood.size = (Window.height / 5, Window.height / 5)

                self.blood_bags.append(blood)
                self.root.add_widget(blood)

    # Двигаем и генерируем новые энергосики
    def move_driks(self, time_passed):
        # Двигаем энергосики
        for drink in self.drinks:
            drink.x -= time_passed * 1200 * (0.9 + 0.11 * MainApp.speed) / MainApp.bonk_factor
            # Если энергосик ушел за границу - удаляем его
            if (drink.pos[0] < - Window.width):
                self.root.remove_widget(drink)
                self.drinks.remove(drink)

        # Если за экраном справа нет энергосиков - создаем еще 20 штук
        drink_xs = list(map(lambda drink: drink.x, self.drinks))
        right_most_x = max(drink_xs)
        if right_most_x <= Window.width:
            for i in range(20):
                distance_between_drink = randint(int(Window.height * 2), int(Window.height * 3))
                drink = EnergyDrink()
                drink.drink_position = randint(50, Window.height - 100)
                drink.size_hint = (None, None)
                drink.pos = (500 + Window.width + i * distance_between_drink, drink.drink_position)
                drink.size = (Window.height / 5, Window.height / 5)

                self.drinks.append(drink)
                self.root.add_widget(drink)

    # Реализуем запись настроек скорости
    def set_config_speed(self, speed):
        if speed.isdigit():
            self.speed = str(speed)
            self.config.set('General', 'speed', str(speed))
            self.config.write()
        else:
            self.root.ids.input_speed.text = self.config.get('General', 'speed')

    # Реализуем запись настроек сложности
    def set_config_complexity(self, complexity):
        if complexity.isdigit():
            self.complexity = str(complexity)
            self.config.set('General', 'complexity', str(complexity))
        else:
            self.root.ids.input_complexity.text = self.config.get('General', 'complexity')

    # Записываем нарастание скорости
    def set_config_increasing_speed_setting(self, increasing_speed):
        if increasing_speed.isdigit():
            self.increasing_speed = str(increasing_speed)
            self.config.set('General', 'increasing_speed', str(increasing_speed))
        else:
            self.root.ids.input_increasing_speed.text = self.config.get('General', 'increasing_speed')

    # Записываем нарастание сложности
    def set_config_increasing_complexity_setting(self, increasing_complexity):
        if increasing_complexity.isdigit():
            self.increasing_complexity = str(increasing_complexity)
            self.config.set('General', 'increasing_complexity', str(increasing_complexity))
        else:
            self.root.ids.input_increasing_complexity.text = self.config.get('General', 'increasing_complexity')

    # Записываем громкость
    def set_config_volume(self, volume):
        if volume.isdigit():
            self.increasing_complexity = str(volume)
            self.config.set('General', 'volume', str(volume))
            self.sound.volume = int(volume) * 0.1
        else:
            self.root.ids.input_volume.text = self.config.get('General', 'volume')

    # Меняем состояние музыки
    def swap_music(self):
        if self.config.get('General', 'is_music') == "True":
            self.config.set('General', 'is_music', "False")
            self.app.config.write()
            self.root.ids.music.background_normal = "Images/music_on.png"
            self.root.ids.music.background_down = "Images/music_on.png"
            self.sound.play()
        else:
            self.config.set('General', 'is_music', "True")
            self.app.config.write()
            self.root.ids.music.background_normal = "Images/music_off.png"
            self.root.ids.music.background_down = "Images/music_off.png"
            self.sound.stop()

if __name__ == "__main__":
    MainApp().run()