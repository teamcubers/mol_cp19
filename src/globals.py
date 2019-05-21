#!/usr/bin/python
# -*- coding: UTF-8 -*-

ABOUT = ["Air-Hockey",
         "Creators : Hussain Mustafa , Burhanuddin Shabbar , Abdul Rehman , Waleed Ansari",
         "Section : BM "]

GAME_FONT = "resources/fonts/KaushanScript-Regular.otf"

# Minimum width and height
MIN_WIDTH = 800
MIN_HEIGHT = 400

# Game constants
LEVEL_EASY = 0
LEVEL_MEDIUM = 1
LEVEL_HARD = 2
LEVEL_IMPOSSIBLE = 3

SCORE_SCREEN_PAUSE = 4
SCORE_SCREEN_SCORED = 5
SCORE_SCREEN_LOSE = 6
SCORE_SCREEN_PLAYER1_SCORED = 7
SCORE_SCREEN_PLAYER2_SCORED = 8

MODE_SINGLE_PLAYER = 9
MODE_2_PLAYERS = 10
MODE_LAN_SERVER = 11
MODE_LAN_CLIENT = 12

# Colors
COLOR_BLUE = (0, 0, 255)
COLOR_RED = (255, 0, 0)
COLOR_BLUE_2 = (0, 128, 255)
COLOR_RED_2 = (255, 100, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_LIGHT_GRAY = (211, 211, 211)
COLOR_SILVER = (192, 192, 192)
COLOR_GRAY = (128, 128, 128)
COLOR_BLACK = (0, 0, 0)
COLOR_NEV=(5, 95, 135)
COLOR_YELLOW=(255, 246, 0)
COLOR_ORANGE=(255, 85, 7)

# TCP Sockets settings
TCP_PORT = 1010
TIMEOUT = 30
INVITATION_TIMEOUT = 10

# Broadcast settings
BROADCAST_TIMEOUT = 2
BROADCAST_PORT = 12345
BROADCAST_BUFFER_SIZE = 64
BROADCAST_IDENTIFIER = "air-hockey"

# Settings file
SETTINGS = "settings.json"
