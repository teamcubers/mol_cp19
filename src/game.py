#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import math
import time
import json
import pygame
import socket
from .utils import *
from .globals import *
from .broadcast import *
from .invitation import *
from pygame import gfxdraw
from random import SystemRandom

# pygameMenu
import pygameMenu
from pygameMenu.locals import *

rand = SystemRandom()


class Game:
    def __init__(self, width=MIN_WIDTH, height=MIN_HEIGHT, fps=100):
        """
        Game class.

        :param width: int, Width desired.
        :param height: int, Height desired.
        :param fps: int, Frames per second desired.
        """
        self.__width = width if width >= MIN_WIDTH else MIN_WIDTH
        self.__height = height if height >= MIN_HEIGHT else MIN_HEIGHT
        self.__is_running = True
        self.__level = LEVEL_EASY
        self.__pc_move_offset = 20
        self.__score = [0, 0]
        self.__max_score = 5
        self.__fps = fps
        self.__username_max_len = 10
        self.__settings = {"username": "user"}
        self._read_settings()

        # Socket server
        self.__server = None
        self.__client = None
        self.__client_username = None
        self.__lan_mode = MODE_LAN_SERVER

        # Grid
        self.__grid_width = int(min(self.__height, self.__width) / 8)
        self.__grid_radius = int(min(self.__height, self.__width) / 100)
        self.__grid_x_offset = int(((self.__width % self.__grid_width) + self.__grid_width) / 2)
        self.__grid_y_offset = int(((self.__height % self.__grid_width) + self.__grid_width) / 2)

        # Rectangles
        self.__r_max_speed = 3
        self.__r_hard_speed_offset = 1
        self.__height_r = 50
        self.__width_r = 50
        # self.__x_r1 = -self.__width_r / 2
        # self.__x_r2 = self.__width - self.__width_r - self.__x_r1

        # Ball
        self.__ball_radius = int(min(self.__height, self.__width) / 45)
        self.__ball_start_speed = 2
        self.__ball_speed_step = 0.2
        self.__ball_max_speed = 10
        self.__has_collided = False
        self.__has_collided_with_top_bottom = False

        self.__max_ball_angle = math.radians(60)
        self.__max_collision_angle = math.radians(60)
        self.__collision_coefficient = self.__max_collision_angle / math.pow(self.__height_r / 2.0, 3)

        # Init pygame
        pygame.mixer.pre_init(44100, -16, 2, 2048)
        pygame.mixer.init()
        pygame.init()

        self.__screen = pygame.display.set_mode((self.__width, self.__height))
        pygame.mouse.set_visible(False)
        # noinspection PyUnresolvedReferences
        icon = pygame.image.load("resources/images/logo.png")
        pygame.display.set_icon(icon)
        pygame.display.set_caption("Air Hokey")
        self.__clock = pygame.time.Clock()

        # Sounds
        self.__sound_blip = pygame.mixer.Sound("resources/sounds/blip.wav")
        self.__sound_lose = pygame.mixer.Sound("resources/sounds/lose.wav")
        self.__sound_main = pygame.mixer.Sound("resources/sounds/main.wav")
        self.__sound_scored = pygame.mixer.Sound("resources/sounds/scored.wav")
        self.__sound_wall = pygame.mixer.Sound("resources/sounds/wall.wav")

    def _read_settings(self):
        """
        Read the game settings.

        :return: None
        """
        if os.path.exists(SETTINGS):
            with open(SETTINGS, "r") as fd:
                try:
                    data = json.load(fd)
                except Exception as e:
                    print("Error reading settings -", e)
                else:
                    self.__settings.update(data)

    def _save_settings(self):
        """
        Save settings to file.

        :return: None
        """
        with open(SETTINGS, "w") as fd:
            json.dump(self.__settings, fd)

    def _start_menu(self):
        """
        Draw the main menu. This is the start point of the game.

        :return: bool, Execution OK
        """
        single_player_menu = pygameMenu.Menu(
            self.__screen,
            window_width=self.__width,
            window_height=self.__height,
            font=GAME_FONT,
            title="Single Player",
            menu_color_title=COLOR_BLACK,
            menu_color=COLOR_NEV,
            dopause=False
        )

        single_player_menu.add_option("Play", self._keep_playing, MODE_SINGLE_PLAYER)
        single_player_menu.add_selector("Difficulty", [("Easy", LEVEL_EASY),
                                                       ("Medium", LEVEL_MEDIUM),
                                                       ("Hard", LEVEL_HARD),
                                                       ("Impossible", LEVEL_IMPOSSIBLE)],
                                        onreturn=None,
                                        onchange=self.set_difficulty)
        single_player_menu.add_option("Return to main menu", PYGAME_MENU_BACK)

        about_menu = pygameMenu.TextMenu(
            self.__screen,
            window_width=self.__width,
            window_height=self.__height,
            font=GAME_FONT,
            title="About",
            menu_color_title=COLOR_BLACK,
            menu_color=COLOR_NEV,
            dopause=False
        )

        for line in ABOUT:
            about_menu.add_line(line)
        about_menu.add_line(TEXT_NEWLINE)
        about_menu.add_option("Return to menu", PYGAME_MENU_BACK)

        menu = pygameMenu.Menu(
            self.__screen,
            window_width=self.__width,
            window_height=self.__height,
            font=GAME_FONT,
            title="Main Menu",
            menu_color_title=COLOR_BLACK,
            menu_color=COLOR_NEV,
            dopause=False
        )

        menu.add_option("Single Player", single_player_menu)
        menu.add_option("2 Players", self._keep_playing, MODE_2_PLAYERS)
        menu.add_option("2 Players (LAN)", self._lan_menu)
        menu.add_option("About", about_menu)
        menu.add_option("Exit", self._quit)

        while self.__is_running:
            # Application events
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self._quit()
                    return False

            self.__screen.fill(COLOR_LIGHT_GRAY)
            menu.mainloop(events)
            self.__clock.tick(self.__fps)

    def _edit__username_menu(self):
        """
        Custom menu for editing the username.

        :return: bool, Execution OK
        """
        inner_width = int(self.__width - self.__width / 5)
        username = self.username

        text2, width2, height2 = generate_wrapped_text("Press [Esc] to go back or [Return] to save", GAME_FONT,
                                                       COLOR_GRAY, inner_width, self.__height / 10)
        x2 = int((self.__width - width2) / 2)
        y2 = int(5 * self.__height / 6 - height2 / 2)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._quit()
                    return False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return True
                    elif event.key == pygame.K_RETURN:
                        if len(username):
                            self.__settings["username"] = username
                            return True
                    elif event.key == pygame.K_BACKSPACE:
                        if len(username):
                            username = username[:-1]
                    elif pygame.K_a <= event.key <= pygame.K_z and len(username) < self.__username_max_len:
                        username += chr(ord("a") + event.key - pygame.K_a)
                    elif pygame.K_0 <= event.key <= pygame.K_9 and len(username) < self.__username_max_len:
                        username += chr(ord("0") + event.key - pygame.K_0)

            self.__screen.fill(COLOR_LIGHT_GRAY)

            text1, width1, height1 = generate_wrapped_text("Username: <%s>" % username, GAME_FONT, COLOR_GRAY,
                                                           inner_width, self.__height / 10)

            x1 = int((self.__width - width1) / 2)
            y1 = int(self.__height / 3 - height1 / 2)

            self.__screen.blit(text1, (x1, y1))
            self.__screen.blit(text2, (x2, y2))

            pygame.display.flip()
            self.__clock.tick(self.__fps)

    def _info_screen(self, line1, line2):
        """
        Show info message.

        :param line1: first line
        :param line2: second line
        :return: None
        """
        inner_width = int(self.__width - self.__width / 5)
        self.__screen.fill(COLOR_LIGHT_GRAY)

        text1, width1, height1 = generate_wrapped_text(line1, GAME_FONT, COLOR_GRAY, inner_width, self.__height / 10)
        text2, width2, height2 = generate_wrapped_text(line2, GAME_FONT, COLOR_GRAY, inner_width, self.__height / 10)

        x1 = int((self.__width - width1) / 2)
        y1 = int(self.__height / 3 - height1 / 2)
        x2 = int((self.__width - width2) / 2)
        y2 = int(5 * self.__height / 6 - height2 / 2)

        self.__screen.blit(text1, (x1, y1))
        self.__screen.blit(text2, (x2, y2))

        pygame.display.flip()

    def _invitation_request_menu(self, username):
        """
        Custom menu to give notice someone is inviting to play.

        :param username: str, Second player username
        :return: bool, Execution OK
        """
        self._info_screen("<%s> is inviting you to play!" % username,
                          "Press [Esc]/[N] to refuse or [Return]/[Y] to accept")

        start_time = time.time()
        while time.time() - start_time < INVITATION_TIMEOUT:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._quit()
                    return False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_n:
                        return False
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_y:
                        return True

            self.__clock.tick(self.__fps)

        return False

    def _start_server(self):
        """
        Starts the main server used for playing over LAN.

        :return: None
        """
        if self.__server is None:
            self.__server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.__server.bind(("0.0.0.0", TCP_PORT))
            self.__server.listen(1)

    def _close_server(self):
        """
        Closes the main server used for playing over LAN.

        :return: None
        """
        if self.__server is not None:
            self.__server.close()
            self.__server = None

    def _invite_user(self, user, on_execution_start, on_execution_end):
        """
        Custom menu to be shown while an invitiation request is being made.

        :param user: (str, str), User parameters, i.e., username and ip address.
        :param on_execution_start: Handle to be run before execution starts.
        :param on_execution_end:  Handle to be run after execution ends.
        :return: bool, Execution OK/Invitation Accepted
        """
        if user is None:
            return False

        # Do graphical part
        username, ip = user

        self._info_screen("Waiting for <%s> response..." % username, "We are almost there!")

        # Connect with server
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(INVITATION_TIMEOUT)
        client.connect((ip, TCP_PORT))
        try:
            InvitationPacket(self.username).send_to(client)
            packet = InvitationAcceptedPacket()
            status = packet.receive_from(client)
        except (socket.timeout, ConnectionAbortedError):
            pass
        else:
            if status:
                client.settimeout(TIMEOUT)
                self.__client_username = packet.username
                self.__client = client
                on_execution_start()
                self._keep_playing_lan(MODE_LAN_CLIENT)
                on_execution_end()
                self.__client = self.__client_username = None
        client.close()

    def _lan_menu(self):
        """
        2 Players (Lan) menu. While on this menu, the application is sending/listening for invitation packets.

        :return: bool, Execution OK
        """
        lan_menu = pygameMenu.Menu(
            self.__screen,
            window_width=self.__width,
            window_height=self.__height,
            font=GAME_FONT,
            title="2 Players (LAN)",
            menu_color_title=COLOR_BLACK,
            menu_color=COLOR_NEV,
            dopause=False
        )

        # Start server
        self._start_server()

        # Do broadcast
        do_broadcast = DoBroadcast(self)
        do_broadcast.start()

        # Get broadcasts
        get_broadcast = GetBroadcast()
        get_broadcast.start()

        # Get connection
        get_connection = GetConnection(self.__server)
        get_connection.start()

        def stop_threads():
            do_broadcast.stop()
            get_broadcast.stop()
            get_connection.stop()

        def join_threads():
            do_broadcast.join()
            get_broadcast.join()
            get_connection.join()

        def stop_and_join_threads():
            stop_threads()
            join_threads()

        def on_user_accept():
            stop_threads()
            lan_menu.disable()
            self._close_server()

        no_users = [("no users", None)]
        elements = no_users
        selector_id = lan_menu.add_selector("Play with", elements, onchange=None,
                                            onreturn=lambda user: self._invite_user(user, on_user_accept, join_threads))
        lan_menu.add_option("Edit username", self._edit__username_menu)
        lan_menu.add_option("Return to main menu", lan_menu.disable)

        while self.__is_running and lan_menu.is_enabled():
            # Application events
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self._quit()
                    stop_and_join_threads()
                    self._close_server()
                    return False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
                    lan_menu.disable()

            if get_broadcast.data:
                _elements = get_broadcast.data
            else:
                _elements = no_users

            if _elements != elements:
                elements = list(_elements)
                lan_menu.update_selector(selector_id, elements)

            self.__screen.fill(COLOR_LIGHT_GRAY)
            lan_menu.mainloop(events)
            self.__clock.tick(self.__fps)

            # Check for invitations
            if get_connection.has_connection:
                if lan_menu.is_enabled() and self._invitation_request_menu(get_connection.username):
                    self.__client = get_connection.connection
                    self.__client_username = get_connection.username
                    try:
                        InvitationAcceptedPacket(self.username).send_to(self.__client)
                    except (socket.timeout, ConnectionAbortedError):
                        self.__client = self.__client_username = None
                        get_connection.refuse_connection()
                    else:
                        self.__client.settimeout(TIMEOUT)
                        get_connection.accept_connection()
                        lan_menu.disable()
                        stop_threads()
                        self._keep_playing_lan(MODE_LAN_SERVER)
                        join_threads()
                        self.__client.close()
                        self.__client = self.__client_username = None
                        self._close_server()
                        return True
                else:
                    get_connection.refuse_connection()

        stop_and_join_threads()
        self._close_server()
        return True

    def _score_screen(self, screen_type):
        """
        Draw a specific score screen. Multiple screen types are allowed:
          SCORE_SCREEN_PAUSE - Game is paused.
          SCORE_SCREEN_SCORED - Player scored (single player).
          SCORE_SCREEN_LOSE - Player lose (single player).
          SCORE_SCREEN_PLAYER1_SCORED - Player 1 scored (2 players).
          SCORE_SCREEN_PLAYER2_SCORED - Player 2 scored (2 players).

        :param screen_type: enum, Type of the screen to be displayed.
        :return: Execution OK.
        """
        x = round(self.__width / 10)
        y = round(self.__height / 10)
        width = self.__width - 2 * x
        height = self.__height - 2 * y
        inner_width = int(width - width / 5)

        title = "Score"
        if screen_type == SCORE_SCREEN_PAUSE:
            label = "Press [P] or [pause] to continue"
        elif screen_type == SCORE_SCREEN_SCORED:
            label = "Nice one!"
            if self.__max_score in self.__score:
                title = "You win!"
            self.__sound_scored.play()
        elif screen_type == SCORE_SCREEN_LOSE:
            label = "Bad luck... Don't give up!"
            if self.__max_score in self.__score:
                title = "You lose!"
            self.__sound_lose.play()
        elif screen_type == SCORE_SCREEN_PLAYER1_SCORED:
            label = "Player 1 scored!"
            if self.__max_score in self.__score:
                title = "Player 1 win!"
            self.__sound_scored.play()
        else:
            label = "Player 2 scored!"
            if self.__max_score in self.__score:
                title = "Player 2 win!"
            self.__sound_scored.play()

        aa_rounded_rect(self.__screen, (x, y, width, height), COLOR_GRAY, 0.1)

        text1, width1, height1 = generate_wrapped_text(title, GAME_FONT, COLOR_SILVER, inner_width, height / 4)
        text2, width2, height2 = generate_wrapped_text("%s - %s" % (self.__score[0], self.__score[1]), GAME_FONT,
                                                       COLOR_SILVER, inner_width, height / 3)
        text3, width3, height3 = generate_wrapped_text(label, GAME_FONT, COLOR_SILVER, inner_width, height / 6)

        text_total_height = height1 + height2 + height3
        margin = (height - text_total_height) / 2
        self.__screen.blit(text1, (int((self.__width - width1) / 2), int(y + margin)))
        self.__screen.blit(text2, (int((self.__width - width2) / 2), int(y + margin + height1)))
        self.__screen.blit(text3, (int((self.__width - width3) / 2), int(y + margin + height1 + height2)))

        pygame.display.flip()

        passed_time = 0
        while screen_type == SCORE_SCREEN_PAUSE or passed_time < self.__fps * 5:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._quit()
                    return False
                elif screen_type == SCORE_SCREEN_PAUSE and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p or event.key == pygame.K_PAUSE:
                        return True

            passed_time += 1
            self.__clock.tick(self.__fps)

    def _can_move_up(self, y_rectangle, x_ball):
        """
        Checks if the board can move up, ie, has not passed through the wall.

        :param y_rectangle: int, y coordinate of the board.
        :param x_ball: int, x coordinate of the ball.
        :return: bool, Can move up
        """
        return y_rectangle > 0 and 0 < x_ball < self.__width

    def _can_move_down(self, y_rectangle, x_ball):
        """
        Checks if the board can move down, ie, has not passed through the wall.

        :param y_rectangle: int, y coordinate of the board.
        :param x_ball: int, x coordinate of the ball.
        :return: bool, Can move down
        """
        return y_rectangle + self.__height_r < self.__height and 0 < x_ball < self.__width

    def _can_move_left(self, x_rectangle, x_ball, player):
        """
        Checks if the board can move left, ie, has not passed through the wall.
        :param x_rectangle: int, x coordinate of the board.
        :param x_ball: int, x coordinate of the ball.
        :return: bool, Can move left
        """
        if(player == 2):
            return x_rectangle > self.__width / 2 and 0 < x_ball < self.__width
        else:
            return x_rectangle < self.__width / 2 and 0 < x_ball < self.__width

    def _can_move_right(self, x_rectangle, x_ball, player):
        """
        Checks if the board can move left, ie, has not passed through the wall.
        :param x_rectangle: int, x coordinate of the board.
        :param x_ball: int, x coordinate of the ball.
        :return: bool, Can move left
        """
        if(player == 2):
            return x_rectangle > self.__width / 2 and 0 < x_ball < self.__width
        else:
            return x_rectangle < self.__width / 2 and 0 < x_ball < self.__width
        

    @staticmethod
    def _is_right_direction(ball_angle):
        """
        Check if the ball is moving from left to right.

        :param ball_angle: float, Ball angle in rads
        :return: bool, Has right direction
        """
        return -math.pi / 2 < wrap_to_pi(ball_angle) < math.pi / 2

    def _collided_with_top_bottom(self, y_ball):
        """
        Check if the ball collided with the top or bottom part of the wall.

        :param y_ball: y coordinate of the ball
        :return: bool, Has collided
        """
        return not (self.__ball_radius < y_ball < self.__height - self.__ball_radius)

    class _ServerData(Packet):
        """
        ServerData packet.
        """

        def __init__(self):
            self.__methods = []
            self.y_r1 = 0
            self.x_r1 = 0
            self.x_ball = 0
            self.y_ball = 0

        def do_sound_wall(self):
            """
            Registers sound_wall method to be run.

            :return: None
            """
            self.__methods.append(("sound_wall", ()))

        def do_sound_blip(self):
            """
            Registers sound_blip method to be run.

            :return: None
            """
            self.__methods.append(("sound_blip", ()))

        def do_score_screen(self, screen_type):
            """
            Registers score_screen method to be run.

            :param screen_type: Type of the screen as in _score_screen function.
            :return: None
            """
            self.__methods.append(("score_screen", (screen_type,)))

        def do_update_score(self, has_scored):
            """
            Registers update_score method to be run.

            :param has_scored: Has scorded flag as in _update_score function.
            :return: None
            """
            self.__methods.append(("update_score", (has_scored,)))

        def handle_methods(self, **kwargs):
            """
            Execute all registered methods.

            :return: None
            """
            for method, args in self.__methods:
                kwargs[method](*args)

        def clear(self):
            """
            Clear all registered methods.

            :return: None
            """
            self.__methods = []

    class _ClientData(Packet):
        """
        ClientData packet.
        """

        def __init__(self):
            self.y_r2 = 0
            self.x_r2 = 0

    def _play(self, mode):
        """
        Play one round, i.e., until someone loses. Three different modes are accepted:
          MODE_SINGLE_PLAYER - Single player versus PC.
          MODE_2_PLAYERS - 2 players in the same instance.
          MODE_LAN_SERVER - 2 players over LAN, where player 1 is the server.

        :param mode: enum, Mode of game.
        :return: bool, Execution OK.
        """
        y_r1 = (self.__height - self.__height_r) / 2
        y_r2 = y_r1

        x_r1 = 30
        x_r2 = self.__width - 80

        x_ball = int(self.__width / 2)
        y_ball = int(self.__height / 2)
        ball_angle = rand.choice([(math.pi / 4) + (i * math.pi / 2) for i in range(4)])
        ball_speed = self.__ball_start_speed

        min_distance_ratio = 0
        server_data = self._ServerData()
        client_data = self._ClientData()

        while True:
            # Gat all events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._quit()
                    return False
                elif event.type == pygame.KEYDOWN:
                    if not mode == MODE_LAN_SERVER:
                        if event.key == pygame.K_ESCAPE:
                            return False
                        elif event.key == pygame.K_p or event.key == pygame.K_PAUSE:
                            # Check if user quit
                            if not self._score_screen(SCORE_SCREEN_PAUSE):
                                return False

            # Get all pressed keys
            pressed = pygame.key.get_pressed()

            if mode == MODE_2_PLAYERS:
                if pressed[pygame.K_w] and self._can_move_up(y_r1, x_ball):
                    y_r1 -= self.__r_max_speed
                elif pressed[pygame.K_s] and self._can_move_down(y_r1, x_ball):
                    y_r1 += self.__r_max_speed
                elif pressed[pygame.K_a] and self._can_move_left(x_r1, x_ball, 1):
                    x_r1 -= self.__r_max_speed
                elif pressed[pygame.K_d] and self._can_move_right(x_r1, x_ball, 1):
                    x_r1 += self.__r_max_speed

                if pressed[pygame.K_UP] and self._can_move_up(y_r2, x_ball):
                    y_r2 -= self.__r_max_speed
                elif pressed[pygame.K_DOWN] and self._can_move_down(y_r2, x_ball):
                    y_r2 += self.__r_max_speed
                elif pressed[pygame.K_LEFT] and self._can_move_left(x_r2, x_ball, 2):
                    x_r2 -= self.__r_max_speed
                elif pressed[pygame.K_RIGHT] and self._can_move_right(x_r2, x_ball, 2):
                    x_r2 += self.__r_max_speed
            else:
                if pressed[pygame.K_UP] and self._can_move_up(y_r1, x_ball):
                    y_r1 -= self.__r_max_speed
                elif pressed[pygame.K_DOWN] and self._can_move_down(y_r1, x_ball):
                    y_r1 += self.__r_max_speed
                elif pressed[pygame.K_LEFT] and self._can_move_left(x_r1, x_ball, 1):
                    x_r1 -= self.__r_max_speed
                elif pressed[pygame.K_RIGHT] and self._can_move_right(x_r1, x_ball, 1):
                    x_r1 += self.__r_max_speed

            # PC move
            if mode == MODE_SINGLE_PLAYER:
                y_desired = None
                if self.__level == LEVEL_IMPOSSIBLE:
                    if self._is_right_direction(ball_angle):
                        d = (x_r2 - x_ball) / math.cos(ball_angle)
                        y_desired = round(d * math.sin(ball_angle) + y_ball)
                        i = 0
                        while y_desired > self.__height:
                            y_desired -= self.__height
                            i += 1
                        while y_desired < 0:
                            y_desired += self.__height
                            i += 1
                        if i % 2:
                            y_desired = self.__height - y_desired
                    else:
                        y_desired = self.__height / 2

                elif self.__level == LEVEL_HARD or (self._is_right_direction(ball_angle) and (
                        self.__level == LEVEL_MEDIUM or x_ball / self.__width >= min_distance_ratio)):
                    y_desired = y_ball

                if y_desired is not None:
                    if y_desired > y_r2 + (self.__height_r + self.__pc_move_offset) / 2 and \
                            self._can_move_down(y_r2, x_ball):
                        y_r2 += self.__r_max_speed
                        if self.__level == LEVEL_HARD:
                            y_r2 += self.__r_hard_speed_offset
                    elif y_desired < y_r2 + (self.__height_r - self.__pc_move_offset) / 2 and \
                            self._can_move_up(y_r2, x_ball):
                        y_r2 -= self.__r_max_speed
                        if self.__level == LEVEL_HARD:
                            y_r2 -= self.__r_hard_speed_offset
            elif mode == MODE_LAN_SERVER:
                # Get data from client
                if not client_data.receive_from(self.__client):
                    return False
                y_r2 = client_data.y_r2
                x_r2 = client_data.x_r2
                # Update data to send to client
                server_data.y_r1 = y_r1
                server_data.x_r1 = x_r1
                server_data.x_ball = x_ball
                server_data.y_ball = y_ball

            # Check collisions
            if self._collided_with_top_bottom(y_ball):
                if not self.__has_collided_with_top_bottom:
                    # Play sound
                    self.__sound_wall.play()
                    if MODE_LAN_SERVER:
                        server_data.do_sound_wall()
                    # Update ball angle
                    ball_angle = -ball_angle
                    self.__has_collided_with_top_bottom = True
            elif self.__has_collided_with_top_bottom:
                self.__has_collided_with_top_bottom = False

            collision1 = rounded_rect_collided_with_circle((x_r1, y_r1, self.__width_r, self.__height_r),
                                                           1, (x_ball, y_ball), self.__ball_radius)

            collision2 = rounded_rect_collided_with_circle((x_r2, y_r2, self.__width_r, self.__height_r),
                                                           1, (x_ball, y_ball), self.__ball_radius)

            if collision1 is not None or collision2 is not None:
                if not self.__has_collided:
                    # Play sound
                    self.__sound_blip.play()
                    if MODE_LAN_SERVER:
                        server_data.do_sound_blip()
                    # Change ball speed
                    if ball_speed < self.__ball_max_speed:
                        ball_speed += self.__ball_speed_step
                    # For easy level, generate distance ratio for computer to follow the ball
                    if self.__level == LEVEL_EASY and not self._is_right_direction(ball_angle):
                        min_distance_ratio = rand.uniform(0, 0.7)
                        # min_distance_ratio = random.triangular(0, 0.7)
                    # Change ball angle
                    ball_angle = math.pi - ball_angle

                    if collision1 is not None:
                        ball_angle += math.pow(collision1[1] - y_r1 - self.__height_r / 2,
                                               3) * self.__collision_coefficient
                        if wrap_to_pi(ball_angle) < -self.__max_ball_angle:
                            ball_angle = -self.__max_ball_angle
                        elif wrap_to_pi(ball_angle) > self.__max_ball_angle:
                            ball_angle = self.__max_ball_angle
                    else:
                        ball_angle -= math.pow(collision2[1] - y_r2 - self.__height_r / 2,
                                               3) * self.__collision_coefficient
                        if 0 < wrap_to_pi(ball_angle) < math.pi - self.__max_ball_angle:
                            ball_angle = math.pi - self.__max_ball_angle
                        elif self.__max_ball_angle - math.pi < wrap_to_pi(ball_angle) < 0:
                            ball_angle = self.__max_ball_angle - math.pi
                    # Set collision flag
                    self.__has_collided = True
            elif self.__has_collided and \
                    x_r1 + self.__width_r + self.__ball_radius < x_ball < x_r2 - self.__ball_radius:
                # Clear collision flag only if there is no risk of a new collision in the same place
                self.__has_collided = False

            if -self.__ball_radius <= x_ball <= self.__width + self.__ball_radius:
                # Move ball
                x_ball += math.cos(ball_angle) * ball_speed
                y_ball += math.sin(ball_angle) * ball_speed
            else:
                # Update score
                has_scored = self._is_right_direction(ball_angle)
                self._update_score(has_scored)
                if mode == MODE_2_PLAYERS:
                    screen_type = SCORE_SCREEN_PLAYER1_SCORED if has_scored else SCORE_SCREEN_PLAYER2_SCORED
                else:
                    screen_type = SCORE_SCREEN_SCORED if has_scored else SCORE_SCREEN_LOSE
                    if mode == MODE_LAN_SERVER:
                        server_data.do_update_score(has_scored)
                        server_data.do_score_screen(SCORE_SCREEN_LOSE if has_scored else SCORE_SCREEN_SCORED)
                        # Send server data
                        server_data.send_to(self.__client)
                self._score_screen(screen_type)
                return True

            if mode == MODE_LAN_SERVER:
                # Send server data
                server_data.send_to(self.__client)
                server_data.clear()

            # Do graphic part
            self._do_graphics(y_r1, x_r1, y_r2, x_r2, x_ball, y_ball)
            self.__clock.tick(self.__fps)

    def _do_graphics(self, y_r1, x_r1, y_r2, x_r2, x_ball, y_ball):
        """
        Draw the main game graphics.

        :param y_r1: y coordinate of the first pad
        :param y_r2: y coordinate of the second pad
        :param x_r1: x coordinate of the first pad
        :param x_r2: x coordinate of the second pad
        :param x_ball: x coordinate of the ball
        :param y_ball: y coordinate of the ball
        :return: None
        """
        self.__screen.fill(COLOR_NEV)
        aa_rounded_rect(self.__screen, (x_r1, y_r1, self.__width_r, self.__height_r), COLOR_BLUE_2, 1)
        aa_rounded_rect(self.__screen, (x_r2, y_r2, self.__width_r, self.__height_r), COLOR_RED_2, 1)
        gfxdraw.aacircle(self.__screen, round(x_ball), round(y_ball), self.__ball_radius, COLOR_WHITE)
        gfxdraw.filled_circle(self.__screen, round(x_ball), round(y_ball), self.__ball_radius, COLOR_WHITE)
        pygame.draw.line(self.__screen, COLOR_WHITE, (430, 0), (430, 500))

        pygame.display.flip()

    def _keep_playing_client(self):
        """
        Keeps playing and communicating with the server.

        :return: bool, Execution OK
        """
        server_data = self._ServerData()
        client_data = self._ClientData()

        client_data.y_r2 = (self.__height - self.__height_r) / 2
        client_data.x_r2 = (self.__width - self.__width_r) / 2
        self._reset_score()

        while True:
            # Gat all events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._quit()
                    return False
            # Get all pressed keys
            pressed = pygame.key.get_pressed()
            if pressed[pygame.K_UP] and self._can_move_up(client_data.y_r2, server_data.x_ball):
                client_data.y_r2 -= self.__r_max_speed
            elif pressed[pygame.K_DOWN] and self._can_move_down(client_data.y_r2, server_data.x_ball):
                client_data.y_r2 += self.__r_max_speed
            elif pressed[pygame.K_LEFT] and self._can_move_left(x_r2, x_ball, 2):
                client_data.x_r2 -= self.__r_max_speed
            elif pressed[pygame.K_RIGHT] and self._can_move_right(x_r2, x_ball, 2):
                client_data.x_r2 += self.__r_max_speed

            # Send data to server
            client_data.send_to(self.__client)
            # Receive data from server
            if not server_data.receive_from(self.__client):
                return False

            server_data.handle_methods(
                sound_wall=self.__sound_wall.play,
                sound_blip=self.__sound_blip.play,
                score_screen=self._score_screen,
                update_score=self._update_score,
            )

            # Do graphic part
            self._do_graphics(server_data.y_r1, server_data.x_r1, client_data.y_r2, client_data.x_r2, server_data.x_ball, server_data.y_ball)

    def _keep_playing(self, mode):
        """
        Keep playing until one of the players reaches max score.

        :param mode: enum, Mode of game as described in _play function.
        :return: bool, Execution OK.
        """
        self._reset_score()
        while self.__score[0] < self.__max_score and self.__score[1] < self.__max_score and self.__is_running:
            if not self._play(mode):
                return False
        return True

    def _keep_playing_lan(self, mode):
        """
        Keep playing until one of the players reaches max score. Only lan modes are accepted:
          MODE_LAN_CLIENT, MODE_LAN_SERVER

        :param mode: Mode of the game
        :return: None
        """
        try:
            if mode == MODE_LAN_SERVER:
                self._keep_playing(MODE_LAN_SERVER)
            else:
                self._keep_playing_client()
        except (socket.timeout, ConnectionAbortedError, ConnectionResetError):
            print("Something failed with the client/server..")

    def _reset_score(self):
        """
        Resets the score.

        :return: None
        """
        self.__score = [0, 0]

    def _update_score(self, has_scored):
        """
        Updates the score.

        :param has_scored: bool, Flag indicating player one has scored
        :return: None
        """
        self.__score[0 if has_scored else 1] += 1

    def _quit(self):
        """
        Stops the game execution and game engine.

        :return: None
        """
        self.__is_running = False
        pygame.quit()
        self._save_settings()

    @property
    def username(self):
        """
        Get player 1 username

        :return: str, Username
        """
        return self.__settings["username"]

    def set_fps(self, fps):
        """
        Set game frames per second.

        :param fps: int, Frames per second
        :return: None
        """
        self.__fps = fps

    def set_difficulty(self, difficulty):
        """
        Set game difficulty. Allowed values: LEVEL_EASY, LEVEL_MEDIUM, LEVEL_HARD, LEVEL_IMPOSSIBLE

        :param difficulty: enum, Game difficulty
        :return: None
        """
        if difficulty not in [LEVEL_EASY, LEVEL_MEDIUM, LEVEL_HARD, LEVEL_IMPOSSIBLE]:
            raise AssertionError("Unknown difficulty")
        self.__level = difficulty

    def play(self):
        """
        Starts the game. This can only be executed once.

        :return: None
        """
        if not self.__is_running:
            raise AssertionError("Game can only be started once")
        self.__sound_main.play()
        while self.__is_running:
            self._start_menu()
