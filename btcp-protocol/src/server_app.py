#!/usr/local/bin/python3

import argparse
from btcp.server_socket import BTCPServerSocket


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--window", help="Define bTCP window size", type=int, default=100)
    parser.add_argument("-t", "--timeout", help="Define bTCP timeout in milliseconds", type=int, default=100)
    parser.add_argument("-o", "--output", help="Where to store the file", default="output.file")
    args = parser.parse_args()

    # Create a bTCP server socket
    s = BTCPServerSocket(args.window, args.timeout)
    # TODO Write your file transfer server code here using your BTCPServerSocket's accept, and recv methods.
    #s.accept()

    #s.recv()

    # Clean up any state
    #s.close()

    print("Welcome to the Server Application v1.0 - (Created by Thomas Kolb)")

    while True:
        x = input("> ")
        inp = x.lower()
        if inp == "help":
            print("Possible commands are:")
            print("accept - start listening for a client")
            print("recv [output] - receives data and sends it to the output path")
            print("close - clean up any state and close application")
        elif inp == "accept":
            s.accept()
            print("listening for client...")
        elif inp[:4] == "recv":
            if len(inp) <= 4:
                print("Usage: recv [output]")
            else:
                output = x[5:]
                s.recv(output)
        elif inp == "close":
            print("closing application...")
            s.close()
            break
        else:
            print("Command not recognized: use command 'help' for help")



main()

