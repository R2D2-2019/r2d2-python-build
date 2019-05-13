
import pytest

import tooling.frame_generator

# ! does not test get_gid and write_file.

def remove_leading_line(s:str)->str:
    "removes the first line"
    return '\n'.join(s.split('\n')[1:])


def test_type_formats():
    type_formats = tooling.frame_generator.TYPE_FORMATS
    assert isinstance(type_formats, dict)
    for key, value in type_formats.items():
        assert isinstance(key, str)
        assert isinstance(value, str)
        assert len(value) == 1

def test_type_sizes():
    type_sizes = tooling.frame_generator.TYPE_SIZES
    assert isinstance(type_sizes, dict)
    for key, value in type_sizes.items():
        assert isinstance(key, str)
        assert isinstance(value, int)
        assert value >= 0

def test_corresponding_types():
    corresponding_types = tooling.frame_generator.CORRESPONDING_TYPES
    assert isinstance(corresponding_types, dict)
    for key, value in corresponding_types.items():
        assert isinstance(key, str)
        assert isinstance(value, type)

def test_parse_frames():
    parse_frames = tooling.frame_generator.parse_frames
    input_string = """
    class frame_test_frame {
        bool flag;
    }
    """.strip()
    expected_output = [("frame_test_frame", ['bool flag'], [])]
    output = parse_frames(input_string)
    assert output == expected_output

def test_parse_frame_enum():
    # frame_id.?\{(.+?)\}
    parse_frame_enum = tooling.frame_generator.parse_frame_enum
    input_string = """
    enum frame_test : frame_id {
        NONE = 0,
        TEST,
        ALL,
        COUNT
    }
    """.strip()
    expected_output = ['NONE = 0', 'TEST', 'ALL', 'COUNT']
    output = parse_frame_enum(input_string)
    assert output == expected_output

def test_generate_frame_class():
    generate_frame_class = tooling.frame_generator.generate_frame_class
    input_frames = [("frame_test_frame", ['bool flag'], [])]
    expected_output = """
from .common import Frame
from common.frame_enum import FrameType
import struct


class FrameTestFra(Frame):
\tMEMBERS = ['flag']
\tDESCRIPTION = ""

\tdef __init__(self):
\t\tsuper(FrameTestFra, self).__init__()
\t\tself.type = FrameType.TEST_FRA
\t\tself.format = '?'
\t\tself.length = 1

\tdef set_data(self, flag: bool):
\t\tself.data = struct.pack(self.format, flag)


"""
    output = generate_frame_class(input_frames)
    assert remove_leading_line(output) == expected_output

def test_generate_frame_enums():
    generate_frame_enum = tooling.frame_generator.generate_frame_enum
    input_frames = ['NONE = 0', 'TEST', 'ALL', 'COUNT']
    expected_output = """
from common.common import AutoNumber


class FrameType(AutoNumber):
\tNONE = ()
\tTEST = ()
\tALL = ()
\tCOUNT = ()
"""
    output = generate_frame_enum(input_frames)
    assert remove_leading_line(output) == expected_output

def test_CLI_flag():
    parse_frames = tooling.frame_generator.parse_frames
    input_string = r"""
    /** @cond CLI COMMAND @endcondtest
     * Packet containing the state of 
     * a button.
     */
    struct frame_button_state_s {
        bool pressed;
    };
    """
    expected_output = [('frame_button_state_s', ['bool pressed'], ['Packet containing the state of', 'a button.'])]
    output = parse_frames(input_string)
    assert expected_output == output

def test_CLI_flag_parse_frames_negative():
    """this test makes sure only the correct c++ doc string gets parsed."""
    parse_frames = tooling.frame_generator.parse_frames
    input_string = r"""
    /** @cond CLI COMMAND @endcond
     * BAD comment
     */

    /** @cond CLI COMMAND @endcond
     * GOOD comment
    */
    struct frame_button_state_s {
        bool pressed;
    };
    """
    expected_output = [('frame_button_state_s', ['bool pressed'], ['GOOD comment'])]
    output = parse_frames(input_string)
    assert expected_output == output

def test_CLI_flag_generate_frame_class():
    generate_frame_class = tooling.frame_generator.generate_frame_class
    input_frames = [("frame_button_state_s", ['bool pressed'], ['Packet containing the state of', 'a button.'])]
    expected_output = """
from .common import Frame
from common.frame_enum import FrameType
import struct


class FrameButtonState(Frame):
\tMEMBERS = ['pressed']
\tDESCRIPTION = "Packet containing the state of\\na button.\\n"

\tdef __init__(self):
\t\tsuper(FrameButtonState, self).__init__()
\t\tself.type = FrameType.BUTTON_STATE
\t\tself.format = '?'
\t\tself.length = 1

\tdef set_data(self, pressed: bool):
\t\tself.data = struct.pack(self.format, pressed)


"""
    output = generate_frame_class(input_frames)
    assert remove_leading_line(output) == expected_output