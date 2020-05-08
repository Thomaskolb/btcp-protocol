#!/usr/local/bin/python3

import argparse
from btcp.client_socket import BTCPClientSocket


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--window", help="Define bTCP window size", type=int, default=100)
    parser.add_argument("-t", "--timeout", help="Define bTCP timeout in milliseconds", type=int, default=100)
    parser.add_argument("-i", "--input", help="File to send", default="input.file")
    args = parser.parse_args()

    # Create a bTCP client socket with the given window size and timeout value
    s = BTCPClientSocket(args.window, args.timeout)
    # TODO Write your file transfer clientcode using your implementation of BTCPClientSocket's connect, send, and disconnect methods.

    print("Welcome to the Client Application v1.0 - (Created by Thomas Kolb)")

    while True:
        x = input("> ")
        inp = x.lower()
        if inp == "help":
            print("Possible commands are:")
            print("connect - establish a connection to a server")
            print("send [input] - send data to the connected server")
            print("disconnect - disconnect from the server")
            print("close - clean up any state and close application")
        elif inp == "connect":
            s.connect()
        elif inp[:4] == "send":
            if len(inp) <= 4:
                print("Usage: send [input]")
            else:
                arg_input = x[5:]
                s.send(arg_input)
                print("input sent!")
        elif inp == "disconnect":
            s.disconnect()
        elif inp == "close":
            s.close()
            print("closing application...")
            break
        else:
            print("Command not recognized: use command 'help' for help")


main()
