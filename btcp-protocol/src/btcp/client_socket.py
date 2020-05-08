import random
import time
import sys
from btcp.btcp_socket import BTCPSocket
from btcp.lossy_layer import LossyLayer
from btcp.btcp_segment import *
from btcp.selective_repeat import *


# bTCP client socket
# A client application makes use of the services provided by bTCP by calling connect, send, disconnect, and close
class BTCPClientSocket(BTCPSocket):
    def __init__(self, window, timeout):
        super().__init__(window, timeout)
        self._lossy_layer = LossyLayer(self, CLIENT_IP, CLIENT_PORT, SERVER_IP, SERVER_PORT)

        # Boolean variable that determines whether the server has a connection to the cient
        self._connected_to_server = False

        # Global variables that keep track of the sequence and the acknowledgement number that are send during
        # the three-way handshake
        self._x_value = 0
        self._y_value = 0

        # Variable that keeps track of the window size on the server side
        self._window_size_server = 0

        # Selective repeater
        self._selective_repeater = SelectiveRepeaterSender(self._lossy_layer, self._window, self._timeout)

    # Called by the lossy layer from another thread whenever a segment arrives. 
    def lossy_layer_input(self, rec_data):
        (header, packet) = rec_data
        seg_info = unpack_segment(header)
        (seq_number, ack_number, (ack, syn, fin), window, data_length, checksum, data) = seg_info
        if not syn and ack and not fin:
            if self._selective_repeater is not None:
                self._selective_repeater.ReceiveAckPacket(seg_info)
            else:
                print("Selective repeat protocol not initiated, but still receiving ACK")
        if syn and ack and not fin:
            self.acknowledge_server(seg_info)
        if not syn and ack and fin:
            # Terminate connection between client and server
            self._connected_to_server = False
            print("disconnected to server")

    # Perform a three-way handshake to establish a connection
    def connect(self):
        # Variable that keeps track of the moment when the first step of the three-way handshake was initiated.
        # Used to determine whether a connection timeout has occurred.
        connect_start = time.time()

        # Variable that keeps track of the number of attempts to connect to the server.
        # Used to determine whether the max number of connection attempts was exceeded.
        connect_attempts = 1

        self.synchonize_server()
        print("connecting...")

        while not self._connected_to_server:
            if ((time.time() - connect_start) * 1000) >= self._timeout:
                # Connection Timeout
                if connect_attempts >= MAX_NUMBER_OF_CONNECTION_TRIES:
                    # Max number of connection tries was exceeded
                    print("Connection attempts failed: Max number of connection tries ({}) exceeded.".format(MAX_NUMBER_OF_CONNECTION_TRIES))
                    break
                else:
                    #Try to connect again
                    print("Connection attempt failed: Connection timeout, retrying...")
                    connect_attempts += 1
                    connect_start = time.time()
                    self.synchonize_server()


    # Step 3 of the three-way handshake to establish connection
    def synchonize_server(self):
        # Step 1 of three way handshake
        self._x_value = random.randint(0, MAX_VALUE_16_BIT_INTEGER + 1)
        ack_syn_fin = flags_to_binary(False, True, False)
        segment = Segment(self._x_value, 0, ack_syn_fin, 0, 0, 0, None)
        data = segment.create_segment()
        self._lossy_layer.send_segment(data)

    # Step 3 of the three-way handshake to establish connection
    def acknowledge_server(self, seg_info):
        # Step 3 of three way handshake
        (seq_number, ack_number, (ack, syn, fin), window, data_length, checksum, data) = seg_info
        if ack_number != self._x_value+1:
            print("acknowledgement number incorrect:", ack_number, self._x_value+1)
        else:
            self._y_value = seq_number
            self._window_size_server = window
            ack_syn_fin = flags_to_binary(True, False, False)
            segment = Segment(self._x_value+1, self._y_value+1, ack_syn_fin, 0, 0, 0, None)
            data = segment.create_segment()
            self._lossy_layer.send_segment(data)
            print("connected to server.")
            self._connected_to_server = True


    # Send data originating from the application in a reliable way to the server
    def send(self, data):
        self._selective_repeater.StartSending(data)

    # Perform a handshake to terminate a connection
    def disconnect(self):
        # Variable that keeps track of the moment when the first step of the termination handshake was initiated.
        # Used to determine whether a termination timeout has occurred.
        terminate_start = time.time()

        # Variable that keeps track of the number of attempts to terminate the connection to the server.
        # Used to determine whether the max number of termination attempts was exceeded.
        terminate_attempts = 1

        self.finish_server()
        print("disconnecting...")

        while self._connected_to_server:
            if ((time.time() - terminate_start) * 1000) >= self._timeout:
                # Connection Timeout
                if terminate_attempts >= MAX_NUMBER_OF_TERMINATION_TRIES:
                    # Max number of connection tries was exceeded
                    print("Termination attempts failed: Max number of termination tries ({}) exceeded.".format(
                        MAX_NUMBER_OF_TERMINATION_TRIES))
                    self._connected_to_server = False
                    break
                else:
                    # Try to connect again
                    print("Termination attempt failed: Termination timeout, retrying...")
                    terminate_attempts += 1
                    terminate_start = time.time()
                    self.finish_server()

    # First step of termination handshake
    def finish_server(self):
        ack_syn_fin = flags_to_binary(False, False, True)
        segment = Segment(0, 0, ack_syn_fin, 0, 0, 0, None)
        data = segment.create_segment()
        self._lossy_layer.send_segment(data)

    def clean(self):
        self._connected_to_server = False
        self._x_value = 0
        self._y_value = 0
        self._window_size_server = 0
        self._selective_repeater = SelectiveRepeaterSender(self._lossy_layer, self._window, self._timeout)

    # Clean up any state
    def close(self):
        self._lossy_layer.destroy()
        self._connected_to_server = False
        self._x_value = 0
        self._y_value = 0
        self._window_size_server = 0
        #self._lossy_layer = LossyLayer(self, SERVER_IP, SERVER_PORT, CLIENT_IP, CLIENT_PORT)
