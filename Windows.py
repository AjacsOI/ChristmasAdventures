from os.path import exists
from webbrowser import open as wb_open

import pygame
import pygame_gui
import pyganim

from Sprites import Ball, Player
from UI import Button, Label, Message, Text
from Utils import DataBase, Settings, Sounds


class Window:
    '''Базовый класс окна

     Аргументы инициализации:
         *settings — настройки из класса Settings.setting: dict
         *mode — Режим окна //примеры «main_window», «login_window»
                 и т. д.: ул.

     Методы:
         *get_screen — Окно возврата с выбранным заголовком и размером: pygame.Surface
    '''
    __slots__ = ['settings', 'fps', 'mode', 'background_filler',
                 'text_filler', 'clock', 'screen', 'manager',
                 'database', 'sounds']

    def __init__(self, settings: dict, mode: str):
        pygame.event.set_allowed(
            [pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.KEYUP,
             pygame.USEREVENT, pygame.MOUSEBUTTONUP])
        pygame.key.set_repeat(1, 50)
        self.settings: dict = settings
        db_path: str = self.settings['path'] + '/assets/database/'
        self.sounds = Sounds(db_path)
        self.manager = pygame_gui.UIManager(self.settings['window_size'])
        db_path = f'{self.settings["path"]}/assets/database/'
        self.database = DataBase(db_path)
        self.fps = self.settings['fps']
        self.mode = mode
        background_path = self.settings['path'] + \
            '/assets/sprites/background/background.png'
        self.background_filler = pygame.image.load(background_path)
        self.clock: pygame.time.Clock = pygame.time.Clock()
        icon_path = '/assets/sprites/icons/window_icons/icon_standart.png'
        icon = pygame.image.load(self.settings['path'] + icon_path)
        pygame.display.set_icon(icon)
        self.screen = self.get_screen(
            'Christmas Adventures', self.settings['window_size'])

    def get_screen(self, title: str, window_size: list) -> pygame.Surface:
        flags = pygame.DOUBLEBUF
        screen: pygame.Surface = pygame.display.set_mode(window_size, flags)
        screen.set_alpha(None)
        pygame.display.set_caption(title)
        return screen

    def is_button_event(self, event) -> bool:
        if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element.text == '':
                for button_name in self.buttons:
                    if event.ui_element == self.buttons[button_name]:
                        return True
        return False


class Level(Window):
    '''Класс базового уровня

     Аргументы инициализации:
         *settings - Dict с настройками из настроек класса: dict

     Методы:
         *game_cycle - Запустить окно(игру)
         *event_handler — Работа с событиями.
         *draw — Отобразить и нарисовать все объекты.
     '''
    __slots__ = ['santa', 'all_sprites', 'exit_sprites',
                 'gui_sprites', 'wall_sprites', 'sprite_groups', 'trap_sprites',
                 'move_direction', 'is_jumping', 'is_sitting', 'start_hit_points',
                 'animation_list', 'anims', 'brick_sprites', 'is_walking',
                 'buttons', 'texts', 'ball_sprites']

    def __init__(self, settings: dict):
        super().__init__(settings, mode='level')
        self.move_direction = False
        self.is_jumping = False
        self.is_sitting = False
        self.all_sprites = pygame.sprite.Group()
        self.exit_sprites = pygame.sprite.Group()
        self.gui_sprites = pygame.sprite.Group()
        self.wall_sprites = pygame.sprite.Group()
        self.trap_sprites = pygame.sprite.Group()
        self.brick_sprites = pygame.sprite.Group()
        self.ball_sprites = pygame.sprite.Group()
        self.anims = {}
        self.sprite_groups = {'all': self.all_sprites,
                              'exit': self.exit_sprites,
                              'brick': self.brick_sprites,
                              'gui': self.gui_sprites,
                              'wall': self.wall_sprites,
                              'trap': self.trap_sprites,
                              'ball': self.ball_sprites}
        self.texts = self.database.get_text()
        self.buttons = self.get_buttons()
        load = pygame.image.load
        relative_background_path = '/assets/sprites/background/background_level.png'
        background_path = f'{self.settings["path"]}{relative_background_path}'
        self.background_filler = load(background_path)
        self.santa: Player = Player(
            [65, self.settings['window_size'][1] - 216],
            2, Settings(self.settings['file']).settings['skin'],
            self.all_sprites,
            self.settings)
        self.start_hit_points = self.santa.hit_points
        self.get_animations()
        self.animation_list = []
        self.is_walking = False

    def reset(self):
        self.move_direction = False
        self.is_jumping = False
        self.is_sitting = False
        self.is_walking = False

    def get_animations(self):
        self.anims['chainsaw'] = pyganim.PygAnimation(
            [(self.settings['path']
              + f'/assets/sprites/traps/chainsaw/chainsaw_{i}.png', 100)
             for i in range(0, 6)])
        self.anims['chainsaw'].play()
        self.anims['vulkan'] = pyganim.PygAnimation(
            [(self.settings['path']
              + f'/assets/sprites/traps/vulkan/vulkan_{i}.png', 100)
             for i in range(0, 26)])
        self.anims['vulkan'].play()
        self.anims['ball'] = pyganim.PygAnimation(
            [(self.settings['path'] +
              f'/assets/sprites/traps/ball/ball_{i}.png', 100)
             for i in range(0, 6)])
        self.anims['ball'].play()
        self.anims['box_glover'] = pyganim.PygAnimation(
            [(self.settings['path'] +
              f'/assets/sprites/traps/box_glover/box_glover_{i}.png', 100)
             for i in range(0, 36)])
        self.anims['box_glover'].play()

    def draw_animation(self, key, position):
        self.anims[key].blit(self.screen, (*position,))

    def get_sprite(self, image, position,
                   sprite_groups=[]) -> pygame.sprite.Sprite:
        sprite = pygame.sprite.Sprite()
        sprite.image = pygame.image.load(image)
        sprite.mask = pygame.mask.from_surface(sprite.image)
        sprite.rect = pygame.Rect((*position,), (*sprite.mask.get_size(),))
        self.all_sprites.add(sprite)
        if sprite_groups != []:
            for sprite_group in sprite_groups:
                sprite_group.add(sprite)
        return sprite

    def floor(self, position) -> pygame.sprite.Sprite:
        sprite_groups = [self.wall_sprites]
        rel_path = '/assets/sprites/wall/wall_800x60.png'
        floor_path = self.settings['path'] + rel_path
        return self.get_sprite(floor_path, position, sprite_groups)

    def wall(self, position) -> pygame.sprite.Sprite:
        sprite_groups = [self.wall_sprites]
        rel_path = '/assets/sprites/wall/wall_60x595.png'
        wall_path = self.settings['path'] + rel_path
        return self.get_sprite(wall_path, position, sprite_groups)

    def exit(self, position) -> pygame.sprite.Sprite:
        sprite_groups = [self.exit_sprites]
        rel_path = '/assets/sprites/icons/reward/trophey.png'
        trophey_path = self.settings['path'] + rel_path
        return self.get_sprite(trophey_path, position, sprite_groups)

    def thorn(self, position, turn='top') -> pygame.sprite.Sprite:
        sprite_groups = [self.trap_sprites]
        if turn == 'top':
            rel_path = '/assets/sprites/traps/thorns/thorn.png'
        elif turn == 'left':
            rel_path = '/assets/sprites/traps/thorns/thorn_left.png'
        elif turn == 'right':
            rel_path = '/assets/sprites/traps/thorns/thorn_right.png'
        elif turn == 'down':
            rel_path = '/assets/sprites/traps/thorns/thorn_down.png'
        thorn_path = self.settings['path'] + rel_path
        return self.get_sprite(thorn_path, position, sprite_groups)

    def thorns5x(self, position):
        sprite_groups = [self.trap_sprites]
        rel_path = '/assets/sprites/traps/thorns/thorns_x5.png'
        thorn_path = self.settings['path'] + rel_path
        return self.get_sprite(thorn_path, position, sprite_groups)

    def brick(self, position):
        sprite_groups = [self.wall_sprites, self.brick_sprites]
        rel_path = '/assets/sprites/brick/brick.png'
        brick_path = self.settings['path'] + rel_path
        return self.get_sprite(brick_path, position, sprite_groups)

    def borders(self):
        self.floor([0, 0])
        self.floor([0, 470])
        self.wall([0, 0])
        self.wall([750, 0])

    def ball(self, position):
        rel_path = '/assets/sprites/traps/ball/ball_0.png'
        ball_path = self.settings['path'] + rel_path
        ball = Ball(position, self.settings)
        self.all_sprites.add(ball)
        self.sprite_groups['trap'].add(ball)
        self.sprite_groups['ball'].add(ball)
        return ball

    def box_glover(self, position):
        self.animation_list.append(['box_glover', position])
        sprite_groups = [self.trap_sprites]
        rel_path = '/assets/sprites/traps/box_glover/box_glover_static.png'
        box_glover_path = self.settings['path'] + rel_path
        return self.get_sprite(box_glover_path, position, sprite_groups)

    def chainsaw(self, position):
        self.animation_list.append(['chainsaw', position])
        sprite_groups = [self.trap_sprites]
        rel_path = '/assets/sprites/traps/chainsaw/chainsaw_0.png'
        chainsaw_path = self.settings['path'] + rel_path
        return self.get_sprite(chainsaw_path, position, sprite_groups)

    def vulkan(self, position):
        self.animation_list.append(['vulkan', position])
        sprite_groups = [self.trap_sprites]
        rel_path = '/assets/sprites/traps/vulkan/vulkan_25.png'
        vulkan_path = self.settings['path'] + rel_path
        return self.get_sprite(vulkan_path, position, sprite_groups)

    def game_cycle(self) -> None:
        running = True
        while running:
            time_delta = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.manager.process_events(event)
                    running = self.event_handler(event)
                    if not running:
                        break
            if self.santa.is_collide(self.sprite_groups['exit']):
                self.mode = 'win'
                running = False
            if self.santa.is_collide(self.sprite_groups['trap']):
                self.santa.die()
            if self.santa.hit_points <= 0:
                self.sounds.play('lose')
                self.mode = 'lose'
                running = False
            self.clock.tick(self.fps)
            self.screen.blit(self.background_filler, [0, 0])
            self.draw()
            self.manager.draw_ui(self.screen)
            self.manager.update(time_delta)
            pygame.display.update()

    def event_handler(self, event: pygame.event) -> bool:
        if event.type == pygame.KEYDOWN:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_RIGHT]:
                self.move_direction = 'rigth'
            if keys[pygame.K_LEFT]:
                self.move_direction = 'left'
            if keys[pygame.K_DOWN]:
                self.is_sitting = True
            if keys[pygame.K_UP]:
                self.is_jumping = True
        elif event.type == pygame.USEREVENT and self.is_button_event(event):
            button_name = event.ui_element.code_name
            if button_name == 'faq':
                Message(self.texts['ordinary_level_tip'], 'Help',
                        self.manager, [170, 100], [400, 300], 'help_msg')
            elif button_name == 'menu':
                self.mode = 'main_window'
                return False
            elif button_name == 'replay':
                self.mode = 'replay'
                return False
        return True

    def draw(self) -> None:
        self.all_sprites.draw(self.screen)
        self.santa.update(
            self.sprite_groups['wall'], self.all_sprites,
            self.move_direction, self.is_jumping, self.is_sitting)
        self.is_sitting = False
        self.move_direction = False
        self.is_jumping = False
        self.santa.skin_group.draw(self.screen)
        self.draw_hearts()
        for animation_info in self.animation_list:
            animation_key, position = animation_info
            self.anims[animation_key].blit(self.screen, (*position,))
        for ball in self.sprite_groups['ball']:
            ball.update()

    def draw_hearts(self):
        hearts = pygame.sprite.Group()
        for i in range(self.start_hit_points - self.santa.hit_points):
            heart = pygame.sprite.Sprite()
            image_path = self.settings['path'] +\
                '/assets/sprites/icons/heart/red_heart.png'
            heart.rect = pygame.Rect((*[20 + i * 13, 20],), (*[0, 0],))
            heart.image = pygame.image.load(image_path)
            hearts.add(heart)
        hearts.draw(self.screen)
        for i in range(self.santa.hit_points):
            heart = pygame.sprite.Sprite()
            image_path = self.settings['path'] +\
                '/assets/sprites/icons/heart/red_heart.png'
            heart.image = pygame.image.load(image_path)
            heart.rect = pygame.Rect((*[20 + i * 15, 20],), (*[0, 0],))
            hearts.add(heart)
        hearts.draw(self.screen)

    def get_buttons(self) -> dict:
        images_name_list = ['menu', 'replay', 'faq']
        buttons = {}
        space = self.settings['window_size'][0] // (
            len(images_name_list) + 10)
        for index, name in enumerate(images_name_list):
            button = Button(
                '', name, self.manager,
                [5, index * space + 50])
            gui_path = self.settings['path'] + '/assets/sprites/icons/gui/'
            button.set_icon(gui_path + name + '.png')
            buttons[name] = button
        return buttons


class MainWindow(Window):
    __slots__ = ['background_filler', 'texts', 'main_text', 'buttons']

    def __init__(self, settings: dict):
        super().__init__(settings, mode='main_window')
        db_path = f'{self.settings["path"]}/assets/database/'
        database = DataBase(db_path)
        self.texts = database.get_text()
        sprites = f'{self.settings["path"]}/assets/sprites/'
        background_path = f'{sprites}/background/main_window_background.png'
        self.background_filler = pygame.image.load(background_path)
        self.main_text = Text('Christmas Adventures', 'main_text', settings)
        self.buttons = self.get_buttons()
        self.get_labels()
        self.sounds.play('theme')

    def draw(self) -> None:
        self.main_text.draw(self.screen)

    def get_labels(self) -> None:
        space = self.settings['window_size'][0] // len(
            list(self.buttons.keys()))
        for button in self.buttons:
            button = self.buttons[button]
            label = Label(self.texts[button.code_name],
                          button.code_name + '_label',
                          self.manager, [1, 1], [1, 1])
            label.connect_to_button(
                button, self.settings['window_size'], space)

    def get_buttons(self) -> dict:
        images_name_list = ['faq', 'shop', 'play']
        buttons = {}
        space = self.settings['window_size'][0] // len(images_name_list)
        for index, name in enumerate(images_name_list):
            button = Button(
                '', name, self.manager,
                [5 + index * space, self.settings['window_size'][1] - 55])
            gui_path = self.settings['path'] + '/assets/sprites/icons/gui/'
            button.set_icon(gui_path + name + '.png')
            buttons[name] = button
        return buttons

    def show_faq(self) -> Message:
        window = Message(self.texts['faq_text'], 'faq_text', self.manager,
                         [170, 100], [400, 300], 'FAQ')
        return window

    def game_cycle(self) -> None:
        running = True
        faq = None
        while running:
            time_delta = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                running, faq = self.event_handler(event, running, faq)
                self.manager.process_events(event)
            if faq != None and not faq.is_alive():
                faq.kill()
            self.clock.tick(self.fps)
            self.screen.blit(self.background_filler, [0, 0])
            self.draw()
            self.manager.draw_ui(self.screen)
            self.manager.update(time_delta)
            pygame.display.update()

    def is_button_event(self, event) -> bool:
        if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element.text == '':
                for button_name in self.buttons:
                    if event.ui_element == self.buttons[button_name]:
                        return True
        return False

    def event_handler(self, event, running, faq=None) -> (bool, None):
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                self.mode = 'level'
                running = False
        elif event.type == pygame.USEREVENT and self.is_button_event(event):
            button_name = event.ui_element.code_name
            if button_name == 'faq':
                faq = self.show_faq()
            elif button_name == 'play':
                self.mode = 'level'
                running = False
            elif button_name == 'shop':
                self.mode = 'shop_window'
                running = False
        if not running:
            self.sounds.stop_all()
        return (running, faq)


class LoseWindow(Window):
    def __init__(self, settings: dict):
        super().__init__(settings, mode='lose_window')
        self.buttons: list = self.get_buttons()
        self.main_text = Text('Game over', 'main_text', settings)
        background_path = self.settings['path'] + \
            '/assets/sprites/background/main_window_background.png'
        self.background_filler = pygame.image.load(background_path)

        self.sounds.stop_all()
        self.sounds.play('lose')

    def get_buttons(self) -> list:
        images_name_list = ['replay'] * 10
        buttons = []
        space = self.settings['window_size'][0] // len(images_name_list)
        for index, name in enumerate(images_name_list):
            button = Button(
                '', name, self.manager,
                [5 + index * space, self.settings['window_size'][1] - 55])
            gui_path = self.settings['path'] + '/assets/sprites/icons/gui/'
            button.set_icon(gui_path + name + '.png')
            buttons.append(button)
        return buttons

    def game_cycle(self) -> None:
        running = True
        while running:
            time_delta = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                running = self.event_handler(event, running)
                self.manager.process_events(event)
            self.clock.tick(self.fps)
            self.screen.blit(self.background_filler, [0, 0])
            self.draw()
            self.manager.draw_ui(self.screen)
            self.manager.update(time_delta)
            pygame.display.update()

    def draw(self):
        self.main_text.draw(self.screen)

    def is_button_event(self, event) -> bool:
        if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element.text == '':
                for button_name in self.buttons:
                    if event.ui_element == button_name:
                        return True
        return False

    def event_handler(self, event, running) -> (bool, None):
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                self.mode = 'level'
                running = False
        elif event.type == pygame.USEREVENT and self.is_button_event(event):
            button_name = event.ui_element.code_name
            if button_name == 'replay':
                self.mode = 'level'
                running = False
        if not running:
            self.sounds.stop_all()
        return running


class EndWindow(Window):
    def __init__(self, settings: dict):
        super().__init__(settings, mode='win_window')
        background_path = self.settings['path'] + \
            '/assets/sprites/background/win_background.png'
        self.background_filler = pygame.image.load(background_path)
        self.sounds.play('win')

    def game_cycle(self) -> None:
        running = True
        while running:
            time_delta = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                running = self.event_handler(event, running)
            self.clock.tick(self.fps)
            self.screen.blit(self.background_filler, [0, 0])
            pygame.display.update()

    def event_handler(self, event, running) -> bool:
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.mode = 'main_window'
            running = False
        if not running:
            self.sounds.stop_all()
        return running


class ShopWindow(Window):
    def __init__(self, settings):
        self.settings_manager = settings
        settings = settings.settings
        super().__init__(settings, mode='shop_window')
        self.all_sprites = pygame.sprite.Group()
        self.main_text = Text('Shop', 'main_text', settings)
        background_path = self.settings['path'] + \
            '/assets/sprites/background/main_window_background.png'
        self.background_filler = pygame.image.load(background_path)
        db_path = f'{self.settings["path"]}/assets/database/'
        database = DataBase(db_path)
        self.texts = database.get_text()
        self.skins = database.get_skins()
        self.buttons = self.get_buttons()
        self.show_skin()

    def show_skin(self, skin=''):
        if skin == '':
            skin = self.settings['skin']
        sprite = pygame.sprite.Sprite()
        sprite.image = pygame.transform.scale(pygame.image.load(
            self.settings['path'] + self.skins[skin]['stand']), [200, 200])
        sprite.mask = pygame.mask.from_surface(sprite.image)
        sprite.rect = pygame.Rect(([50, 100]), (*sprite.mask.get_size(),))
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(sprite)
        self.current_showing_skin = skin

    def get_buttons(self):
        images_name_list = ['red', 'mask', 'thief', 'blue_spirit',
                            'gold', 'invisible']
        buttons = {}
        space = self.settings['window_size'][0] // len(images_name_list)
        for index, name in enumerate(images_name_list):
            button = Button(
                '', name, self.manager,
                [5 + index * space, self.settings['window_size'][1] - 55])
            button.set_icon(
                self.settings['path'] + self.skins[name]['stand'], False)
            buttons[name] = button
        button = Button(
            '', 'yes', self.manager,
            [46, 347])
        gui_path = self.settings['path'] + '/assets/sprites/icons/gui/'
        button.set_icon(gui_path + 'yes.png')
        buttons['yes'] = button
        button = Button(
            '', 'no', self.manager,
            [126, 347])
        gui_path = self.settings['path'] + '/assets/sprites/icons/gui/'
        button.set_icon(gui_path + 'no.png')
        buttons['no'] = button
        return buttons

    def draw(self):
        self.all_sprites.draw(self.screen)
        self.main_text.draw(self.screen)

    def game_cycle(self) -> None:
        running = True
        faq = None
        while running:
            time_delta = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                running, faq = self.event_handler(event, running, faq)
                self.manager.process_events(event)
            if faq != None and not faq.is_alive():
                faq.kill()
            self.clock.tick(self.fps)
            self.screen.blit(self.background_filler, [0, 0])
            self.draw()
            self.manager.draw_ui(self.screen)
            self.manager.update(time_delta)
            pygame.display.update()

    def is_button_event(self, event) -> bool:
        if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element.text == '':
                for button_name in self.buttons:
                    if event.ui_element == self.buttons[button_name]:
                        return True
        return False

    def event_handler(self, event, running, faq=None) -> (bool, None):
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                self.mode = 'level'
                running = False
        elif event.type == pygame.USEREVENT and self.is_button_event(event):
            button_name = event.ui_element.code_name
            if button_name in self.skins:
                self.show_skin(button_name)
            elif button_name == 'no':
                running = False
                self.mode = 'main_window'
            elif button_name == 'yes':
                self.skin_applyer(self.current_showing_skin)
        if not running:
            self.sounds.stop_all()
        return (running, faq)

    def skin_applyer(self, skin):
        change = False
        if skin in ['red', 'mask']:
            change = True
        elif skin == 'golden':
            if self.settings['number_of_games'] >= 100:
                change = True
        elif skin == 'blue_spirit':
            if exists(self.settings['path'] + '/error_log.txt'):
                change = True
        elif skin == 'invisible':
            if self.settings['visited_github']:
                change = True
            else:
                self.settings['visited_github'] = 1
                self.settings_manager.save({'visited_github': '1'})
                wb_open('https://github.com/Ulbandus/ChristmasAdventures')
        elif skin == 'thief':
            if self.settings['step'] != 5 or self.settings['gravity'] != 0.5:
                change = True
        if change:
            self.settings_manager.save({'skin': skin})
        else:
            Message(self.texts['skin_blocked'], 'Skin Blocked', self.manager,
                    [170, 100], [400, 300], 'skin_error')
