"""
this module contains configuration and base Frame definitions
"""
import struct
import os
import socket
from dataclasses import dataclass
import logging
from enum import Enum
import common.config

@dataclass
class Address():
    """full ip:port address for use in socket's
    Note: socket expects a tuple type.
    either cast this Address to a tuple, or construct a tuple using parts of this address
    """
    ip: str
    port: int
    def tuple(self) -> tuple:
        """returns Address represented as a tuple"""
        return (self.ip, self.port)

@dataclass
class BusConfig:
    """this class contains all the configuration to connect with the python bus"""
    AUTH_KEY: bytes
    ADDRESS: Address

def get_bus_config(inside_docker_container):
    """get_bus_config returns the correct """
    logger = logging.getLogger("common.busconfig")
    default = BusConfig(AUTH_KEY=b'r2d2', ADDRESS=Address('127.0.0.1', 5000))
    if inside_docker_container is False:
        logger.info("using default bus config")
        return default
    logger.info("inside of docker container, using special bus config")
    try:
        address = Address(socket.gethostbyname("server_manager"), default.ADDRESS.port)
    except socket.gaierror:
        logger.warning("Hostname could not be resolved. Falling back to default")
        address = Address("172.18.0.2", default.ADDRESS.port)
    return BusConfig(AUTH_KEY=default.AUTH_KEY, ADDRESS=address)

class AutoNumber(Enum):
    """this enum class automatily generates """
    def __new__(cls):
        value = len(cls.__members__)  # note no + 1
        new_object = object.__new__(cls)
        new_object._value_ = value #pylint: disable=protected-access
        return new_object


class Priority(Enum):
    """
    Defines the priority of a package on the bus.
    """
    HIGH = 0
    NORMAL = 1
    LOW = 2
    DATA_STREAM = 3


class Frame:
    """Base data Frame
    this class gets subclassed by data frames in common/frames.py
    """
    # This will be overwritten by child classes
    MEMBERS = []

    def _get_member_index(self, key: str) -> int:
        """
        Get the index in the members list of the given
        key. If the key is not found in the list, the index function
        will raise a ValueError. Because this function is used in
        __getitem__ en __setitem__ a KeyError is raised instead of
        the ValueError for convenience.

        :param key:
        :return: int
        """

        try:
            return self.MEMBERS.index(key)
        except ValueError:
            raise KeyError

    def _pack_from_tuple(self, tuple_) -> None:
        """
        This helper function will pack the data in the tuple
        into the data member of the Frame.

        :param tuple:
        :return:
        """

        return self.set_data(*tuple_)
    
    def _default_fill(self):
        """fills data with standard data"""
        ls = []
        for specifier in self.format.split(' '):
            count, type_ = specifier[:-1], specifier[-1]
            if type_ in ("s", "c"):
                ls.append(b"\x1a")
            elif count:
                for _ in range(int(count)):
                    ls.append(0)
            else:
                ls.append(0)
        self.data = struct.pack(self.format, *ls)

    def __init__(self):
        # Set in child class
        self.format = ''

        self.type = None
        self.data = None
        self.length = 0
        self.request = False
        self.priority = Priority.NORMAL

    def __len__(self) -> int:
        """Returns the length of the members"""
        return len(self.MEMBERS)

    def __length_hint__(self):
        return self.__len__()

    def __getitem__(self, key: str):
        """
        Get the value of the member specified by key.
        A KeyError is raised if the key doesn't specify a valid
        member.

        :param key:
        :param value:
        :return:
        """

        return self.get_data()[
            self._get_member_index(key)
        ]

    def __setitem__(self, key: str, value):
        """
        Set the value of the member specified by key.
        A KeyError is raised if the key doesn't specify a valid
        member.

        :param key:
        :param value:
        :return:
        """

        index = self._get_member_index(key)

        # If the data is not yet set, we'll create an empty
        # tuple as filler
        if not self.data:
            self._default_fill()

        data = list(self.get_data())
        if isinstance(value, str):
            data[index] = bytes(value, encoding="UTF-8")
        else:
            data[index] = value

        for index, value in enumerate(data):
            if isinstance(value, str):
                data[index] = bytes(value, encoding="UTF-8")

        self._pack_from_tuple(tuple(data))

    def __iter__(self):
        """
        Return an iterator over the list
        of frame members.

        :return:
        """

        return iter(self.MEMBERS)

    def __contains__(self, key: str) -> bool:
        """
        Check if this frame type has a member
        by the given name.
        Enables the in operator with if statements

        :param key:
        :return:
        """

        return key in self.MEMBERS

    def set_data(self, *data):
        """this method should be implemented in the subclass
        it should set self.data to the result of struct.pack(self.data, ...)
        where ... is dependant on the frame itself
        """
        data_list = list()
        for index, specifier in enumerate(self.format.split(" ")):
            count = 1 if specifier[:-1] == '' else int(specifier[:-1])
            type_ = specifier[-1]
            if type_ == 's':
                if not data[index]:
                    data_list.append(b'\0')
                else:
                    data_list.append(data[index])
            elif type_ == 'c' and not data[index]:
                data_list.append(b'\x1A')
            elif count > 1:
                for item in data[index]:
                    data_list.append(item)
            else:
                data_list.append(data[index])
        self.data = struct.pack(self.format, *data_list)

    def get_data(self):
        """this method returns a tuple of subclass dependant data"""
        if self.length == 0:
            return None

        raw_data = struct.unpack(self.format, self.data)
        data = list()

        index = 0
        for specifier in self.format.split(" "):
            count = 1 if specifier[:-1] == '' else int(specifier[:-1])
            type_ = specifier[-1]
            if count == 1:
                if type_ == 'c':
                    data.append(
                        raw_data[index]
                        .decode(encoding="UTF-8")
                        .rstrip(chr(0))
                        .replace("\x1A", '')
                    )
                else:
                    data.append(raw_data[index])
                index += 1
            elif type_ == "s":
                data.append(raw_data[index].decode(encoding="UTF-8").rstrip(chr(0)))
                index += 1
            else:
                data.append(tuple(raw_data[index+i] for i in range(count)))
                index += count
        return tuple(data)

    def __str__(self):
        output = self.__class__.__name__ + '\n'
        for member in self.MEMBERS:
            output += '\t{}: {}'.format(member, self[member]) + '\n'

        return output

@dataclass
class FrameWrapper:
    """this class adds meta data to a Frame"""
    frame: Frame
    pid: int
    timestamp: int

# global settings
BUSCONFIG = get_bus_config(os.environ.get('AM_I_IN_A_DOCKER_CONTAINER', False))
