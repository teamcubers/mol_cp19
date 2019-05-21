#!/usr/bin/python
# -*- coding: UTF-8 -*-

import time
import socket
import threading
from .utils import get_local_ip
from .globals import BROADCAST_PORT, BROADCAST_BUFFER_SIZE, BROADCAST_IDENTIFIER, BROADCAST_TIMEOUT

__all__ = [
    "GetBroadcast",
    "DoBroadcast",
]


class GetBroadcast(threading.Thread):
    """
    Threaded broadcast packet listener
    """

    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self.__is_running = False
        self.__ip = [get_local_ip(), "127.0.0.1"]
        self.__data = []

    def run(self):
        self.__is_running = True
        overall_timeout = 2 * BROADCAST_TIMEOUT + 1
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("", BROADCAST_PORT))
        s.settimeout(overall_timeout)

        while self.__is_running:
            data = []
            start_time = time.time()
            while time.time() - start_time < overall_timeout:
                try:
                    _data, (ip, _) = s.recvfrom(BROADCAST_BUFFER_SIZE)
                except socket.timeout:
                    continue
                username = self.__parse_data(_data)
                if username is not None:
                    user = (username, (username, ip))
                    if ip not in self.__ip and user not in data:
                        data.append(user)

            if self.__data != data:
                self.__data = list(data)

        s.close()

    @staticmethod
    def __parse_data(data):
        """
        Parse data from packet.

        :param data: bytes, Data as bytes.
        :return: str, Username from packet
        """
        data = data.decode("utf-8")
        if data.startswith("%s," % BROADCAST_IDENTIFIER):
            return data.split(",")[1]
        return None

    @property
    def data(self):
        """
        Get gathered data in format of [(username, (username, ip)), ...]

        :return: list, Gathered data
        """
        return self.__data

    def stop(self):
        """
        Stops the thread.

        :return: None
        """
        self.__is_running = False


class DoBroadcast(threading.Thread):
    """
    Threaded broadcast packet sender
    """

    def __init__(self, parent):
        threading.Thread.__init__(self)
        self.daemon = True
        self.__is_running = False
        self.__parent = parent

    def run(self):
        self.__is_running = True
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while self.__is_running:
            data = self.__construct_data(self.__parent.username)
            s.sendto(data, ("255.255.255.255", BROADCAST_PORT))
            time.sleep(BROADCAST_TIMEOUT)

    @staticmethod
    def __construct_data(username):
        """
        Constructs packet with the provided username

        :param username: str, Username
        :return: bytes, Packet
        """
        return bytes("%s,%s" % (BROADCAST_IDENTIFIER, username), "utf-8")

    def stop(self):
        """
        Stops the thread.

        :return: None
        """
        self.__is_running = False
