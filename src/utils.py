#!/usr/bin/python
# -*- coding: UTF-8 -*-

import math
import json
import socket
import pygame
import itertools

__all__ = [
    "aa_rounded_rect",
    "rounded_rect_collided_with_circle",
    "generate_wrapped_text",
    "wrap_to_pi",
    "get_local_ip",
    "Packet",
    "InvalidData",
    "UnknownPacket"
]


def aa_rounded_rect(surface, rect, color, radius):
    """
    Draw a rounded rectangle.

    :param surface: Surface where to draw
    :param rect: Rectangle parameters (x, y, width, height)
    :param color: RGB Color (red, green, blue)
    :param radius: Border radius in percentage: 0 <= radius <= 1
    :return: Rect
    """
    rect = pygame.Rect(rect)
    color = pygame.Color(*color)
    alpha = color.a
    color.a = 0
    pos = rect.topleft
    rect.topleft = 0, 0
    rectangle = pygame.Surface(rect.size, pygame.SRCALPHA)

    circle = pygame.Surface([min(rect.size) * 3] * 2, pygame.SRCALPHA)
    pygame.draw.ellipse(circle, (0, 0, 0), circle.get_rect(), 0)
    circle = pygame.transform.smoothscale(circle, [int(min(rect.size) * radius)] * 2)

    radius = rectangle.blit(circle, (0, 0))
    radius.bottomright = rect.bottomright
    rectangle.blit(circle, radius)
    radius.topright = rect.topright
    rectangle.blit(circle, radius)
    radius.bottomleft = rect.bottomleft
    rectangle.blit(circle, radius)

    rectangle.fill((0, 0, 0), rect.inflate(-radius.w, 0))
    rectangle.fill((0, 0, 0), rect.inflate(0, -radius.h))

    rectangle.fill(color, special_flags=pygame.BLEND_RGBA_MAX)
    rectangle.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MIN)

    return surface.blit(rectangle, pos)


def rounded_rect_collided_with_circle(rect, radius, circle_pos, circle_radius):
    """
    Check if a circle has collided with a rounded rect.
    If so, returns collision coordinates, otherwise returns None.

    :param rect: Rectangle parameters (x, y, width, height)
    :param radius: Rectangle border radius in percentage: 0 <= radius <= 1
    :param circle_pos: Circle coordinates (x, y)
    :param circle_radius: Circle radius
    :return: Collision coordinates (x, y) / None
    """
    rect_x, rect_y, rect_width, rect_height = rect
    circle_x, circle_y = circle_pos

    rect_corner_diameter = min(rect_width, rect_height) * radius
    rect_corner_radius = rect_corner_diameter / 2

    if rect_y - circle_radius <= circle_y <= rect_y + rect_height + circle_radius and \
            rect_x - circle_radius <= circle_x <= rect_x + rect_width + circle_radius:
        if rect_y + rect_corner_radius <= circle_y <= rect_y + rect_height - rect_corner_radius:
            # Straight part of the rectangle along y
            if abs(rect_x - circle_x) <= circle_radius:
                return rect_x, circle_y
            elif abs(rect_x + rect_width - circle_x) <= circle_radius:
                return rect_x + rect_width, circle_y

        elif rect_x + rect_corner_radius <= circle_x <= rect_x + rect_width - rect_corner_radius:
            # Straight part of the rectangle along x
            if abs(rect_y - circle_y) <= circle_radius:
                return circle_x, rect_y
            elif abs(rect_y + rect_height - circle_y) <= circle_radius:
                return circle_x, rect_y + rect_height

        else:
            # Rounded part of the rectangle
            for ang in range(91):
                x = rect_corner_radius * math.cos(math.radians(ang))
                y = rect_corner_radius * math.sin(math.radians(ang))

                x_coordinates = [rect_x + rect_corner_radius - x, rect_x + rect_width - rect_corner_radius + x]
                y_coordinates = [rect_y + rect_corner_radius - y, rect_y + rect_height - rect_corner_radius + y]
                for coordinate in itertools.product(x_coordinates, y_coordinates):
                    distance = math.sqrt(sum([(a - b) ** 2 for a, b in zip(coordinate, circle_pos)]))
                    if distance <= circle_radius:
                        return coordinate

    return None


def generate_wrapped_text(text, font, color, width, height, min_font_size=20, max_font_size=100):
    """
    Wraps text to fit given width and height.

    :param text: str, Text to display
    :param font: str, Text font
    :param color: RGB Color (red, green, blue)
    :param width: int, Maximum width
    :param height: int, Maximum height
    :param min_font_size: int, Minimum font size
    :param max_font_size: int, Maximum font size
    :return: Surface, width, height
    """
    if max_font_size < min_font_size:
        raise AssertionError("Maximum font size must be greater or equal than min font size")
    while True:
        font_obj = pygame.font.Font(font, max_font_size)
        w, h = font_obj.size(text)
        if (w <= width and h <= height) or max_font_size <= min_font_size:
            break
        max_font_size -= 1

    return font_obj.render(text, True, color), w, h


def wrap_to_pi(angle):
    """
    Wrap the given angle to pi: -pi <= angle <= pi.

    :param angle: float, Angle to wrap in rads
    :return: float, Wrapped angle
    """
    while angle > math.pi:
        angle -= 2 * math.pi
    while angle < -math.pi:
        angle += 2 * math.pi
    return angle


def get_local_ip():
    """
    Get local ip address.

    :return: str, Local IP address
    """
    ip = socket.gethostbyname(socket.gethostname())
    if ip == "127.0.0.1":
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    return ip


class UnknownPacket(Exception):
    pass


class InvalidData(Exception):
    pass


class Packet:
    """
    General packet class
    """

    def dumps(self):
        """
        Serialize packet object to a JSON formatted string using the packet name as the tag.

        :return: str, JSON
        """
        return json.dumps({self.__class__.__name__: self.__dict__})

    def loads(self, data):
        """
        Deserialize data (instance containing a JSON document) and update packet object.
        Raises UnknownPacket or InvalidData if the data is not deserializable.

        :param data: bytes/str, JSON
        :return: None
        """
        tag = self.__class__.__name__
        try:
            _data = json.loads(data)
        except Exception:
            raise UnknownPacket
        if tag not in _data or not isinstance(_data[tag], dict) or set(_data[tag]) != set(self.__dict__):
            raise InvalidData
        self.__dict__.update(_data[tag])

    def receive_from(self, conn, buffer_size=512):
        """
        Receive data from a connection and load it to the packet.
        If there is an error loading data or no data is obtained, return False.

        :param conn: Socket connection
        :param buffer_size: int, Socket buffer size
        :return: bool, Success
        """
        if conn is None:
            return False
        data = conn.recv(buffer_size)
        if not data:
            return False
        try:
            self.loads(data)
        except (UnknownPacket, InvalidData):
            return False
        return True

    def send_to(self, conn):
        """
        Send data to connection.
        If no connection, return None.

        :param conn: Socket connection
        :return: int, Bytes sent
        """
        if conn is None:
            return None
        return conn.send(self.dumps().encode())
