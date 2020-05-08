import sys
import time
from btcp.btcp_segment import *


# Method that converts data to an array with parts of the data
def DivideDataInArray(data):
    # array that packets will be put into
    data_array = []
    # data that still has to be put in the array
    file = open(data, 'rb')
    current_data = file.read()
    file.close()

    while len(current_data) > 0:
        # take first PAYLOAD_SIZE of bytes and put in in the array
        packet = current_data[:PAYLOAD_SIZE]
        data_array.append(packet)

        current_data = current_data[PAYLOAD_SIZE:]

    return data_array


class SelectiveRepeaterSender:
    def __init__(self, lossy_layer, window_size, packet_timeout):
        self._lossy_layer = lossy_layer
        self._data_array = []

        # array that keeps track of the times when a packet was sent
        self._timeout_array = []

        # boolean array that determines for each packet whether it was sent
        self._sent_array = []

        # boolean array that determines for each packet whether an ack was received for it
        self._ack_array = []

        # lower bound of window
        self._send_base = 0
        # sequence number of next packet to be sent
        self._send_next = 0

        # window size of client side
        self._window_size = window_size

        # when the sender doesn't receive an ACK from the receiver side within this packet_timeout a new
        # packet is sent.
        self._packet_timeout = packet_timeout

    # Sender side of selective repeat protocol
    def StartSending(self, data):
        # Create data array
        self._data_array = DivideDataInArray(data)

        for x in range(len(self._data_array)):
            self._timeout_array.append(0)

        for x in range(len(self._data_array)):
            self._sent_array.append(False)

        for x in range(len(self._data_array)):
            self._ack_array.append(False)

        # Start sender loop
        while self._send_base < len(self._data_array):
            # send package to receiver only if it is within the window
            if (self._send_next - self._send_base) < self._window_size:
                if self._send_next < len(self._data_array):
                    self.SendSenderPacket(self._send_next)
                    self._send_next += 1
            # check if timeout on one of the packets that has NOT received an ACK yet has occurred
            for x in range(len(self._sent_array)):
                if self._sent_array[x] and not self._ack_array[x]:
                    if ((time.time() - self._timeout_array[x]) * 1000) > self._packet_timeout:
                        # a timeout has occurred and the packet is send again
                        print("packet timeout occurred")
                        self.SendSenderPacket(x)


    # Method that is called when a package with the ack flag (and only the ack flag) is received
    def ReceiveAckPacket(self, seg_info):
        (seq_number, ack_number, (ack, syn, fin), window, data_length, checksum, data) = seg_info
        # Now that the ack has been received we set the boolean that keeps track whether an ack is being sent to false
        self._ack_array[ack_number] = True

        # Now we update the _send_base variable because a new ack was received
        index = 0
        for x in self._ack_array:
            if not x:
                break
            index += 1
        self._send_base = index
        #print(self._send_base, ack_number)

    # Method that sends a packet from the sender to receiver
    def SendSenderPacket(self, seq_number):
        #print("sending", seq_number)
        data_to_send = self._data_array[seq_number]
        segment = Segment(seq_number, 0, 0, 0, len(data_to_send), calculate_checksum(data_to_send), data_to_send)
        data = segment.create_segment()
        self._lossy_layer.send_segment(data)

        # keep track of time that packet was send to determine when a timeout occurs
        self._timeout_array[seq_number] = time.time()

        # state that packet was sent
        self._sent_array[seq_number] = True


class SelectiveRepeaterReceiver:
    def __init__(self, lossy_layer, window_size):
        self._window_size = window_size
        self._lossy_layer = lossy_layer

        self._delivering = False

        # lower bound of window
        self._rec_base = 0

        # array that keeps track of the packets that were received
        self._rec_array = []
        for x in range(MAX_PACKET_SIZE):
            self._rec_array.append(False)

        # data that should be delivered to application layer
        self._data_to_deliver = bytes()

        # data buffer that keeps a hold of unordered segments
        self._buffer = []
        for x in range(MAX_PACKET_SIZE):
            self._buffer.append(bytes())

    # Deliver data to application layer
    def DeliverData(self):
        # don't do anything if data is currently being delivered (to _data_to_deliver) (mutual exclusion)
        if not self._delivering:
            # empty the data_to_deliver bytes and return the data
            data = self._data_to_deliver
            self._data_to_deliver = bytes()
            return data
        else:
            return bytes()

    def PutInDataToDeliver(self, data):
        self._delivering = True
        self._data_to_deliver += data
        self._delivering = False

    # method that tests whether a package has not been received yet. i.e. handling duplicate packats
    def NotYetReceived(self, index):
        return self._rec_array[index] == False

    # Method that is called when a packet (without any flag) is received
    def ReceivePacket(self, seg_info):
        (seq_number, ack_number, (ack, syn, fin), window, data_length, checksum, data) = seg_info

        # now we verify the checksum and check whether the packet can be received
        if checksum == calculate_checksum(data) and (seq_number - self._rec_base) < self._window_size:
            # We ONLY do something with the data if we haven't yet received the packet.
            # i.e. when we receive the packet for the first time
            if self.NotYetReceived(seq_number):
                # Mark that the packet with sequence number has been received
                self._rec_array[seq_number] = True

                # Send ACK back to the sender
                self.SendACK(seq_number)

                # Now we update the _rec_base variable because a new packet was received
                index = 0
                for x in self._rec_array:
                    if not x:
                        break
                    index += 1
                self._rec_base = index

                # temporarily store data in buffer
                unpadded_data = data[:data_length]
                self._buffer[seq_number] = unpadded_data

                # Collect all the data that is ordered so that it can be delivered to the application layer
                # Note that when data is not ordered it remains in the buffer
                data = bytes()
                for x in range(index):
                    data += self._buffer[x]
                    self._buffer[x] = bytes()

                self.PutInDataToDeliver(data)
            else:
                # otherwise we only resent the ACK
                self.SendACK(seq_number)
        else:
            print("error detected: ignoring packet", self.NotYetReceived(seq_number), (seq_number - self._rec_base) < self._window_size)

    # Method that sends a ACK to the sender
    def SendACK(self, seq_number):
        ack_syn_fin = flags_to_binary(True, False, False)
        segment = Segment(0, seq_number, ack_syn_fin, 0, 0, 0, None)
        data = segment.create_segment()
        self._lossy_layer.send_segment(data)
