import socket
import random
from btcp.lossy_layer import LossyLayer
from btcp.btcp_socket import BTCPSocket
from btcp.btcp_segment import *
from btcp.selective_repeat import *


# The bTCP server socket
# A server application makes use of the services provided by bTCP by calling accept, recv, and close
class BTCPServerSocket(BTCPSocket):
    def __init__(self, window, timeout):
        super().__init__(window, timeout)
        self._lossy_layer = LossyLayer(self, SERVER_IP, SERVER_PORT, CLIENT_IP, CLIENT_PORT)

        # Boolean variable that determines whether the server has a connection to the client
        self._connected_to_client = False

        # Boolean variable that is true when the server is listening for the clients initiation of the three-way handshake
        self._listening = False

        # Global variables that keep track of the sequence and the acknowledgement number that are send during
        # the three-way handshake
        self._x_value = 0
        self._y_value = 0

        # Selective repeater
        self._selective_repeater = SelectiveRepeaterReceiver(self._lossy_layer, self._window)

    # Called by the lossy layer from another thread whenever a segment arrives
    def lossy_layer_input(self, rec_data):
        (header, packet) = rec_data
        seg_info = unpack_segment(header)
        (seq_number, ack_number, (ack, syn, fin), window, data_length, checksum, data) = seg_info
        if syn and not ack and not fin:
            if self._listening:
                self.accept_syn_packet(seg_info)
        if not syn and ack and not fin:
            if ack_number != self._y_value+1:
                print("acknowledgement number incorrect:", ack_number, self._y_value+1)
            else:
                print("connected to client.")
                self._connected_to_client = True
                self._listening = False
        if not syn and not ack and fin:
            self.finish_client()
        if not syn and not ack and not fin:
            self._selective_repeater.ReceivePacket(seg_info)

    # Wait for the client to initiate a three-way handshake
    def accept(self):
        self._listening = True

    # accept a packet from the client with the syn flag and do the server part of the three-way handshake
    def accept_syn_packet(self, seg_info):
        (seq_number, ack_number, (ack, syn, fin), window, data_length, checksum, data) = seg_info
        self._x_value = seq_number
        self._y_value = random.randint(0, MAX_VALUE_16_BIT_INTEGER + 1)
        ack_syn_fin = flags_to_binary(True, True, False)
        segment = Segment(self._y_value, self._x_value + 1, ack_syn_fin, self._window, 0, 0, None)
        data = segment.create_segment()
        self._lossy_layer.send_segment(data)

    # Second step of termination handshake
    def finish_client(self):
        ack_syn_fin = flags_to_binary(True, False, True)
        segment = Segment(0, 0, ack_syn_fin, 0, 0, 0, None)
        data = segment.create_segment()
        self._lossy_layer.send_segment(data)
        self._connected_to_client = False
        print("disconnected to client")

    # Send any incoming data to the application layer
    def recv(self, output):
        data = bytes()
        collected_data = bytes()

        # Wait for data to be delivered
        while len(data) == 0:
            data = self._selective_repeater.DeliverData()

        # Write bytes to file with path "output"
        f = open(output, 'wb')
        f.write(data)
        f.close()
        print("Data Received")

    def clean(self):
        self._listening = False
        self._x_value = 0
        self._y_value = 0
        self._selective_repeater = SelectiveRepeaterReceiver(self._lossy_layer, self._window)

    # Clean up any state
    def close(self):
        self._listening = False
        self._lossy_layer.destroy()
        self._x_value = 0
        self._y_value = 0
        #self._lossy_layer = LossyLayer(self, SERVER_IP, SERVER_PORT, CLIENT_IP, CLIENT_PORT)
