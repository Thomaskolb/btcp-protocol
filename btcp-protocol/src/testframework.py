import subprocess
import unittest
import sys
import time

from btcp.client_socket import BTCPClientSocket
from btcp.server_socket import BTCPServerSocket

from btcp.btcp_segment import calculate_checksum

timeout = 100
winsize = 100
intf = "lo"
netem_add = "sudo tc qdisc add dev {} root netem".format(intf)
netem_change = "sudo tc qdisc change dev {} root netem {}".format(intf, "{}")
netem_del = "sudo tc qdisc del dev {} root netem".format(intf)

"""run command and retrieve output"""


def run_command_with_output(command, input=None, cwd=None, shell=True):
    import subprocess
    try:
        process = subprocess.Popen(command, cwd=cwd, shell=shell, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    except Exception as inst:
        print("problem running command : \n   ", str(command))

    [stdoutdata, stderrdata] = process.communicate(
        input)  # no pipes set for stdin/stdout/stdout streams so does effectively only just wait for process ends  (same as process.wait()

    if process.returncode:
        print(stderrdata)
        print("problem running command : \n   ", str(command), " ", process.returncode)

    return stdoutdata


"""run command with no output piping"""


def run_command(command, cwd=None, shell=True):
    import subprocess
    process = None
    try:
        process = subprocess.Popen(command, shell=shell, cwd=cwd)
        print(str(process))
    except Exception as inst:
        print("1. problem running command : \n   ", str(command), "\n problem : ", str(inst))

    process.communicate()  # wait for the process to end

    if process.returncode:
        print("2. problem running command : \n   ", str(command), " ", process.returncode)


class TestbTCPFramework(unittest.TestCase):
    """Test cases for bTCP"""

    def setUp(self):
        """Prepare for testing"""
        # default netem rule (does nothing)
        run_command(netem_add)

        # launch localhost server
        server_socket.accept()

    def tearDown(self):
        """Clean up after testing"""
        # clean the environment
        run_command(netem_del)

        # close server
        client_socket.disconnect()
        server_socket.clean()
        client_socket.clean()

    def test_ideal_network(self):
        """reliability over an ideal framework"""

        # setup environment (nothing to set)

        # launch localhost client connecting to server
        client_socket.connect()

        # client sends content to server
        client_socket.send(input_file)

        # because it takes a bit of time for the data to be send over, there needs to be a bit of a delay here
        time.sleep(0.3)

        # server receives content from client
        server_socket.recv(output_path.format("ideal"))

        # content received by server matches the content sent by client

        # calculate checksum of both input and output file and compare them
        f_in = open(input_file, 'rb')
        inp_bytes = f_in.read()
        f_in.close()

        f_out = open(output_file.format("ideal"), 'rb')
        outp_bytes = f_out.read()
        f_out.close()

        self.assertEqual(inp_bytes, outp_bytes, "The input and output file are NOT equal.")
        self.assertEqual(calculate_checksum(inp_bytes), calculate_checksum(outp_bytes),
                         "The checksum of the input and output file are NOT equal.")

    def test_flipping_network(self):
        """reliability over network with bit flips
        (which sometimes results in lower layer packet loss)"""

        # setup environment
        run_command(netem_change.format("corrupt 1%"))

        # launch localhost client connecting to server
        client_socket.connect()

        # client sends content to server
        client_socket.send(input_file)

        # because it takes a bit of time for the data to be send over, there needs to be a bit of a delay here
        time.sleep(0.3)

        # server receives content from client
        server_socket.recv(output_path.format("flip"))

        # content received by server matches the content sent by client

        # calculate checksum of both input and output file and compare them
        f_in = open(input_file, 'rb')
        inp_bytes = f_in.read()
        f_in.close()

        f_out = open(output_file.format("flip"), 'rb')
        outp_bytes = f_out.read()
        f_out.close()

        self.assertEqual(inp_bytes, outp_bytes, "The input and output file are NOT equal.")
        self.assertEqual(calculate_checksum(inp_bytes), calculate_checksum(outp_bytes),
                         "The checksum of the input and output file are NOT equal.")

    def test_duplicates_network(self):
        """reliability over network with duplicate packets"""

        # setup environment
        run_command(netem_change.format("duplicate 10%"))

        # launch localhost client connecting to server
        client_socket.connect()

        # client sends content to server
        client_socket.send(input_file)

        # because it takes a bit of time for the data to be send over, there needs to be a bit of a delay here
        time.sleep(0.3)

        # server receives content from client
        server_socket.recv(output_path.format("duplicate"))

        # content received by server matches the content sent by client

        # calculate checksum of both input and output file and compare them
        f_in = open(input_file, 'rb')
        inp_bytes = f_in.read()
        f_in.close()

        f_out = open(output_file.format("duplicate"), 'rb')
        outp_bytes = f_out.read()
        f_out.close()

        self.assertEqual(inp_bytes, outp_bytes, "The input and output file are NOT equal.")
        self.assertEqual(calculate_checksum(inp_bytes), calculate_checksum(outp_bytes),
                         "The checksum of the input and output file are NOT equal.")

    def test_lossy_network(self):
        """reliability over network with packet loss"""

        # setup environment
        run_command(netem_change.format("loss 10% 25%"))

        # launch localhost client connecting to server
        client_socket.connect()

        # client sends content to server
        client_socket.send(input_file)

        # because it takes a bit of time for the data to be send over, there needs to be a bit of a delay here
        time.sleep(0.3)

        # server receives content from client
        server_socket.recv(output_path.format("lossy_nw"))

        # content received by server matches the content sent by client

        # calculate checksum of both input and output file and compare them
        f_in = open(input_file, 'rb')
        inp_bytes = f_in.read()
        f_in.close()

        f_out = open(output_file.format("lossy_nw"), 'rb')
        outp_bytes = f_out.read()
        f_out.close()

        self.assertEqual(inp_bytes, outp_bytes, "The input and output file are NOT equal.")
        self.assertEqual(calculate_checksum(inp_bytes), calculate_checksum(outp_bytes),
                         "The checksum of the input and output file are NOT equal.")

    def test_reordering_network(self):
        """reliability over network with packet reordering"""

        # setup environment
        run_command(netem_change.format("delay 20ms reorder 25% 50%"))

        # launch localhost client connecting to server
        client_socket.connect()

        # client sends content to server
        client_socket.send(input_file)

        # because it takes a bit of time for the data to be send over, there needs to be a bit of a delay here
        time.sleep(0.3)

        # server receives content from client
        server_socket.recv(output_path.format("reorder"))

        # content received by server matches the content sent by client

        # calculate checksum of both input and output file and compare them
        f_in = open(input_file, 'rb')
        inp_bytes = f_in.read()
        f_in.close()

        f_out = open(output_file.format("reorder"), 'rb')
        outp_bytes = f_out.read()
        f_out.close()

        self.assertEqual(inp_bytes, outp_bytes, "The input and output file are NOT equal.")
        self.assertEqual(calculate_checksum(inp_bytes), calculate_checksum(outp_bytes),
                         "The checksum of the input and output file are NOT equal.")

    def test_delayed_network(self):
        """reliability over network with delay relative to the timeout value"""

        # setup environment
        run_command(netem_change.format("delay " + str(timeout) + "ms 20ms"))

        # launch localhost client connecting to server
        client_socket.connect()

        # client sends content to server
        client_socket.send(input_file)

        # because it takes a bit of time for the data to be send over, there needs to be a bit of a delay here
        time.sleep(0.3)

        # server receives content from client
        server_socket.recv(output_path.format("delay"))

        # content received by server matches the content sent by client

        # calculate checksum of both input and output file and compare them
        f_in = open(input_file, 'rb')
        inp_bytes = f_in.read()
        f_in.close()

        f_out = open(output_file.format("delay"), 'rb')
        outp_bytes = f_out.read()
        f_out.close()

        self.assertEqual(inp_bytes, outp_bytes, "The input and output file are NOT equal.")
        self.assertEqual(calculate_checksum(inp_bytes), calculate_checksum(outp_bytes),
                         "The checksum of the input and output file are NOT equal.")

    def test_allbad_network(self):
        """reliability over network with all of the above problems"""

        # setup environment
        run_command(netem_change.format("corrupt 1% duplicate 10% loss 10% 25% delay 20ms reorder 25% 50%"))

        # launch localhost client connecting to server
        client_socket.connect()

        # client sends content to server
        client_socket.send(input_file)

        # because it takes a bit of time for the data to be send over, there needs to be a bit of a delay here
        time.sleep(0.3)

        # server receives content from client
        server_socket.recv(output_path.format("all_bad"))

        # content received by server matches the content sent by client

        # calculate checksum of both input and output file and compare them
        f_in = open(input_file, 'rb')
        inp_bytes = f_in.read()
        f_in.close()

        f_out = open(output_file.format("all_bad"), 'rb')
        outp_bytes = f_out.read()
        f_out.close()

        self.assertEqual(inp_bytes, outp_bytes, "The input and output file are NOT equal.")
        self.assertEqual(calculate_checksum(inp_bytes), calculate_checksum(outp_bytes),
                         "The checksum of the input and output file are NOT equal.")


#    def test_command(self):
#        #command=['dir','.']
#        out = run_command_with_output("dir .")
#        print(out)


if __name__ == "__main__":
    # Parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(description="bTCP tests")
    parser.add_argument("-w", "--window", help="Define bTCP window size used", type=int, default=100)
    parser.add_argument("-t", "--timeout", help="Define the timeout value used (ms)", type=int, default=timeout)
    args, extra = parser.parse_known_args()
    timeout = args.timeout
    winsize = args.window
    output_path = "/home/uppaal/PycharmProjects/nwd-project/src/output/output_{}.file"
    input_file = "input.file"
    output_file = "output/output_{}.file"

    client_socket = BTCPClientSocket(winsize, timeout)
    server_socket = BTCPServerSocket(winsize, timeout)

    # Pass the extra arguments to unittest
    sys.argv[1:] = extra

    # Start test suite
    unittest.main()
