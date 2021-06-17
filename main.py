from random import randint
from kivy.app import App
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
    # Массивы с обьектами (ловушки и еда)
    cobwebs = []
    blood_bags = []
    bits = []
    drinks = []
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
        self.check_collision_bit()
        self.check_collision_blood()
        self.check_collision_drink()

    # Проверяем на столкновение с паутиной
    def check_collision_web(self):
        ururu = self.root.ids.ururu
        for web in self.cobwebs:
            # Проверяем что позиция сетки по горизонту 20 +/- "толщина" сетки "тольщина" Ури
            if (web.pos[0] < 20 + (Window.height / 20)+ (Window.height / 20 * 0.6)) and (web.pos[0] > 20 - (Window.height / 20) - (Window.height / 20 * 0.6)):
                # Проверяем что разница центров Ури и паутины меньше сумарного их половинного размера
                if abs(web.pos[1] - ururu.pos[1]) < Window.height / 7:
                    MainApp.energy -= int(10 * MainApp.сomplexity)
                    ururu.source = "ururu_web.png"
                    self.root.remove_widget(web)
                    self.cobwebs.remove(web)
        if ururu.y < 100 and not self.is_down:
            ururu.velocity = - ururu.velocity
            MainApp.energy -= int(10 * MainApp.сomplexity)
            ururu.source = "ururu_bonk.png"
            self.is_down = True

        if ururu.top > Window.height:
            MainApp.energy -= int(10 * MainApp.сomplexity)
            ururu.velocity -= (Window.height / 3) * MainApp.сomplexity
            ururu.source = "ururu_bonk.png"

    # Проверяем на столкновение с битой
    def check_collision_bit(self):
        ururu = self.root.ids.ururu
        for bit in self.bits:
            # Проверяем что позиция биты по горизонту 20 +/- "толщина" биты и "тольщина" Ури
            if (bit.pos[0] < 20 + (Window.height / 20)+ (Window.height / 20 * 0.6)) and (bit.pos[0] > 20 - (Window.height / 20) - (Window.height / 20 * 0.6)):
                # Проверяем что разница центров Ури и биты меньше сумарного их половинного размера
                if abs(bit.pos[1] - ururu.pos[1]) < Window.height / 7:
                    MainApp.energy -= int(30 * MainApp.сomplexity)
                    ururu.source = "ururu_bonk.png"
                    self.root.remove_widget(bit)
                    self.bits.remove(bit)

    # Проверяем на столкновение с кровушкой
    def check_collision_blood(self):
        ururu = self.root.ids.ururu
        for blood in self.blood_bags:
            # Проверяем что позиция сетки по горизонту 20 +/- "толщина" кровушки и "тольщина" Ури
            if (blood.pos[0] < 20 + (Window.height / 32) + (Window.height / 20 * 0.6)) and (blood.pos[0] > 20 - (Window.height / 32) - (Window.height / 20 * 0.6)):
                # Проверяем что разница центров Ури и кровушки меньше сумарного их половинного размера
                if abs(blood.pos[1] - ururu.pos[1]) < Window.height / 7:
                    MainApp.energy += int(30 / MainApp.сomplexity)
                    if MainApp.energy >= MainApp.max_energy:
                        MainApp.energy = int(200)
                    ururu.source = "ururu_blood.png"
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
                    MainApp.energy += int(20 / MainApp.сomplexity)
                    if MainApp.energy >= MainApp.max_energy:
                        MainApp.energy = int(200)
                    ururu.source = "ururu_drink.png"
                    self.root.remove_widget(drink)
                    self.drinks.remove(drink)

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
        self.root.ids.energy.opacity = 0

    def next_frame(self, time_passed):
        self.move_ururu(time_passed)
        self.move_cobwebs(time_passed)
        self.move_bits(time_passed)
        self.move_blood_bags(time_passed)
        self.move_driks(time_passed)
        self.root.ids.background.scroll_textures(time_passed)
        self.add_scrole(time_passed)
        self.check_game_over(time_passed)

    def start_game(self):
        self.root.ids.score.text = "0"
        MainApp.energy = int(100)
        self.root.ids.energy.text = "Энергия: " + str(MainApp.energy) + " / " + str(MainApp.max_energy)
        # Таймер
        self.frames = Clock.schedule_interval(self.next_frame, 1/60.)

        # Скрываем кнопку "об игре"
        self.root.ids.about_game_button.disabled = True
        self.root.ids.about_game_button.opacity = 0

        # Создать паутину
        for i in range(200):
            distance_between_web = randint((Window.height / 3) / MainApp.сomplexity, (Window.height / 2.5) / MainApp.сomplexity)
            web = SpiderWeb()
            web.web_position = randint(50, self.root.height - 100)
            web.size_hint = (None, None)
            web.pos = (Window.width + i * distance_between_web, web.web_position)
            web.size = (Window.height / 5, Window.height / 5)

            self.cobwebs.append(web)
            self.root.add_widget(web)

        # Создать биты
        for i in range(100):
            distance_between_bit = randint((Window.height * 4) / MainApp.сomplexity, (Window.height * 6) / MainApp.сomplexity)
            bit = Bit()
            bit.bit_position = randint(50, self.root.height - 100)
            bit.size_hint = (None, None)
            bit.pos = (250 + Window.width + i * distance_between_bit, bit.bit_position)
            bit.size = (Window.height / 5, Window.height / 5)

            self.bits.append(bit)
            self.root.add_widget(bit)

        # Создать кровушку
        for i in range(200):
            distance_between_blood = randint((Window.height * 4) * MainApp.сomplexity, (Window.height * 6) * MainApp.сomplexity)
            blood = BloodBag()
            blood.blood_position = randint(50, self.root.height - 100)
            blood.size_hint = (None, None)
            blood.pos = (700 + Window.width + i * distance_between_blood, blood.blood_position)
            blood.size = (Window.height / 5, Window.height / 5)

            self.blood_bags.append(blood)
            self.root.add_widget(blood)

        # Создать энергосик
        for i in range(200):
            distance_between_drink = randint((Window.height * 2) * MainApp.сomplexity, (Window.height * 3) * MainApp.сomplexity)
            drink = EnergyDrink()
            drink.drink_position = randint(50, self.root.height - 100)
            drink.size_hint = (None, None)
            drink.pos = (500 + Window.width + i * distance_between_drink, drink.drink_position)
            drink.size = (Window.height / 5, Window.height / 5)

            self.drinks.append(drink)
            self.root.add_widget(drink)

    # Двигаем и генерируем новую павутинку
    def move_cobwebs(self, time_passed):
        # Двигаем паутину
        for web in self.cobwebs:
            web.x -= time_passed * 900 * self.сomplexity
            # Если паутина ушла за границу - удаляем ее
            if (web.pos[0] < - Window.width):
                self.root.remove_widget(web)
                self.cobwebs.remove(web)

        # Если за экраном справа нет паутины - создаем еще 20 штук
        web_xs = list(map(lambda web: web.x, self.cobwebs))
        right_most_x = max(web_xs)
        if right_most_x <= Window.width:
            distance_between_web = randint((Window.height / 3) / MainApp.сomplexity, (Window.height / 2.5) / MainApp.сomplexity)
            for i in range(20):
                web = SpiderWeb()
                web.web_position = randint(50, self.root.height - 100)
                web.size_hint = (None, None)
                web.pos = (Window.width + i * distance_between_web, web.web_position)
                web.size = (Window.height / 5, Window.height / 5)

                self.cobwebs.append(web)
                self.root.add_widget(web)

    # Двигаем и генерируем новые биты
    def move_bits(self, time_passed):
        # Двигаем биты
        for bit in self.bits:
            bit.x -= time_passed * 900 * self.сomplexity
            # Если бита ушла за границу - удаляем ее
            if (bit.pos[0] < - Window.width):
                self.root.remove_widget(bit)
                self.bits.remove(bit)

        # Если за экраном справа нет бит - создаем еще 5 штук
        bit_xs = list(map(lambda bit: bit.x, self.bits))
        right_most_x = max(bit_xs)
        if right_most_x <= Window.width:
            for i in range(5):
                distance_between_bit = randint((Window.height * 4) / MainApp.сomplexity, (Window.height * 6) / MainApp.сomplexity)
                bit = Bit()
                bit.bit_position = randint(50, self.root.height - 100)
                bit.size_hint = (None, None)
                bit.pos = (Window.width + i * distance_between_bit, bit.bit_position)
                bit.size = (Window.height / 5, Window.height / 5)

                self.bits.append(bit)
                self.root.add_widget(bit)

    # Двигаем и генерируем новую кровушку
    def move_blood_bags(self, time_passed):
        # Двигаем кровушку
        for blood in self.blood_bags:
            blood.x -= time_passed * 1200 * self.сomplexity
            # Если кровушка ушла за границу - удаляем ее
            if (blood.pos[0] < - Window.width):
                self.root.remove_widget(blood)
                self.blood_bags.remove(blood)

        # Если за экраном справа нет кровушки - создаем еще 20 штук
        blood_xs = list(map(lambda blood: blood.x, self.blood_bags))
        right_most_x = max(blood_xs)
        if right_most_x <= Window.width:
            for i in range(20):
                distance_between_blood = (Window.height * 5) * MainApp.сomplexity
                blood = BloodBag()
                blood.blood_position = randint(50, self.root.height - 100)
                blood.size_hint = (None, None)
                blood.pos = (Window.width + i * distance_between_blood, blood.blood_position)
                blood.size = (Window.height / 5, Window.height / 5)

                self.blood_bags.append(blood)
                self.root.add_widget(blood)

    # Двигаем и генерируем новые энергосики
    def move_driks(self, time_passed):
        # Двигаем энергосики
        for drink in self.drinks:
            drink.x -= time_passed * 1200 * self.сomplexity
            # Если энергосик ушел за границу - удаляем его
            if (drink.pos[0] < - Window.width):
                self.root.remove_widget(drink)
                self.drinks.remove(drink)

        # Если за экраном справа нет энергосиков - создаем еще 20 штук
        drink_xs = list(map(lambda drink: drink.x, self.drinks))
        right_most_x = max(drink_xs)
        if right_most_x <= Window.width:
            for i in range(20):
                distance_between_drink = randint((Window.height * 2) * MainApp.сomplexity, (Window.height * 3) * MainApp.сomplexity)
                drink = EnergyDrink()
                drink.drink_position = randint(50, self.root.height - 100)
                drink.size_hint = (None, None)
                drink.pos = (500 + Window.width + i * distance_between_drink, drink.drink_position)
                drink.size = (Window.height / 5, Window.height / 5)

                self.drinks.append(drink)
                self.root.add_widget(drink)


if __name__ == "__main__":
    MainApp().run()