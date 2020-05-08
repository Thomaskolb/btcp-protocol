import struct
import math
import sys
import numpy as np
from btcp.constants import *


# Method that translates a 3-tuple to a 8 bit integer that can be used in a segment header
def flags_to_binary(ACK, SYN, FIN):
    total = 0
    if ACK:
        total += math.pow(2, 0)
    if SYN:
        total += math.pow(2, 1)
    if FIN:
        total += math.pow(2, 2)
    return np.uint8(total)


# Method that translates the 8 bit integer that was received from a packet to a 3-tuple with the elements ACK,
# SYN and FIN.
def binary_to_flags(flags_value):
    current = flags_value
    ACK = False
    SYN = False
    FIN = False
    if current >= 4:
        current -= 4
        FIN = True
    if current >= 2:
        current -= 2
        SYN = True
    if current >= 1:
        ACK = True
    return ACK, SYN, FIN


# Method that calculates the checksum of data
def calculate_checksum(data):
    data_buffer = []
    current_data = data

    # divide 1008 bytes into packets of 2 bytes (16 bit) and put them into the data_buffer
    for x in range(math.ceil(PAYLOAD_SIZE/2)):
        bit_buffer = current_data[:2]
        current_data = current_data[2:]
        if len(bit_buffer) > 0:
            if len(bit_buffer) == 1:
                (integer,) = struct.unpack('B', bit_buffer)
            else:
                (integer,) = struct.unpack('H', bit_buffer)
            data_buffer.append(integer)
        else:
            break

    # sum all integers in data_buffer
    wraparound = bin(sum(data_buffer))

    # take the last 16 bits and turn in into an integer
    new_sum = int(str(wraparound[10:]), 2)

    # add the carrys to the 16 bit integer
    carrys_to_add = wraparound[2:]
    for x in range(len(carrys_to_add)):
        if carrys_to_add[x] == 1:
            new_sum += math.pow(2, 7-x)

    # get checksum
    checksum = 65535 - new_sum
    return checksum


def unpack_segment(segment):
    header_segment = segment[:HEADER_SIZE]
    data_segment = segment[HEADER_SIZE:]
    (seq_number, ack_number, bin_flags, window, data_length, checksum) = struct.unpack(HEADER_FORMAT, header_segment)
    return seq_number, ack_number, binary_to_flags(bin_flags), window, data_length, checksum, data_segment


class Segment:
    def __init__(self, seq_number, ack_number, flags, window, data_length, checksum, data):
        self._seq_number = seq_number
        self._ack_number = ack_number
        self._flags = flags
        self._window = window
        self._data_length = data_length
        self._checksum = checksum
        self._data = data

    def create_segment(self):
        header_segment = struct.pack(HEADER_FORMAT, self._seq_number, self._ack_number, self._flags, self._window,
                                     self._data_length,
                                     self._checksum)
        segment = header_segment
        if self._data_length > 0:
            data_padding = bytes(PAYLOAD_SIZE - self._data_length)
            segment += self._data
        else:
            data_padding = bytes(PAYLOAD_SIZE)
        segment += data_padding
        return segment
