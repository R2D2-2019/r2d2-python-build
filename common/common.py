"""
this module contains configuration and base Frame definitions
"""
import struct
from enum import Enum
import os

class BusConfig:
    "this class contains the configuration options for the bus"
    AUTH_KEY = b'r2d2'
    PORT = 5000
    if os.environ.get('AM_I_IN_A_DOCKER_CONTAINER', False):
        try:
            remote_ip = socket.gethostbyname( 'server_manager' )
        except socket.gaierror:
            print('Hostname could not be resolved. Falling back to default')
            remote_ip = '172.18.0.2'
        ADDRESS = (remote_ip, PORT)
    else:
        ADDRESS = ('127.0.0.1', PORT)


class AutoNumber(Enum):
    """this enum class automatily generates """
    def __new__(cls):
        value = len(cls.__members__)  # note no + 1
        new_object = object.__new__(cls)
        new_object._value_ = value
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

    def _pack_from_tuple(self, tuple) -> None:
        """
        This helper function will pack the data in the tuple
        into the data member of the Frame.

        :param tuple:
        :return:
        """

        self.data = struct.pack(self.format, *tuple)

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
            tmp = list(range(len(self.MEMBERS)))
            format_ = list(self.format.split(' '))
            for i, specifier in enumerate(format_):
                if specifier in ['?', 'c'] or str.endswith(specifier, 's'):
                    tmp[i] = chr(26)
            data = tuple(tmp)
            del tmp
        else:
            data = self.get_data()

        tmp = list(data)
        tmp[index] = value

        self._pack_from_tuple(tuple(tmp))

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

    def set_data(self, data):
        pass

    def get_data(self):
        if self.length == 0:
            return None

        return struct.unpack(self.format, self.data)

    def __str__(self):
        output = self.__class__.__name__ + '\n'
        for member in self.MEMBERS:
            output += '\t{}: {}'.format(member, self[member]) + '\n'

        return output


class FrameWrapper:
    def __init__(self, frame, pid, timestamp):
        self.frame = frame
        self.pid = pid
        self.timestamp = timestamp
