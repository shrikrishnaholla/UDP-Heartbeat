#!/usr/bin/python

import random
from socket import *
import datetime as dt
import argparse

# Create a UDP socket
serverSocket = socket(AF_INET, SOCK_DGRAM)

# Initializing parser for accepting command line arguements
parser = argparse.ArgumentParser(
    description="""UDP Heartbeat Server. Simulates packet loss and supports user defined value for the port number. \
                   To close the server, press 'Ctrl + C'""",
    usage="./Heartbeat.py [--port] N  [--packetloss] N [-h/--help]")

# Assign port number to socket
parser.add_argument(
    '--port', default=12000, type=int, metavar='int',
    help='The port where the server should run (integer > 1024 and < 65535) Default: 12000')

# Assign packetloss percentage
parser.add_argument(
    '--packetloss', default=40, type=int, metavar='int',
    help='Percentage of data loss experienced by the server (Simulated) Default: 40%')

try:
    args = parser.parse_args()
except ValueError:
    print "Usage: ./Heartbeat.py [--port] N  [--packetloss] N [-h/--help]"
    exit()

if args.port < 1024 or args.port > 65535:
    print 'Invalid port number. Value must be within the range 1024-65535'
    exit()

if args.packetloss < 0 or args.packetloss > 100:
    print 'Invalid value for packet loss percentage. Value must be in between 0 to 100'
    exit()
# Variable has to be initialized outside so as to be able to use everywhere in the program
server_start = dt.datetime.now()

if args.port == 12000:
    # I have taken a default value and it is my headache to make sure it works
    def portassign():
        """A function to make sure the server binds to a free port in case the user hasn't specified one on his own"""
        flag = True
        while flag:
            try:
                # Bind server to port
                serverSocket.bind(('', args.port))
                # Record the time at which the server started
                server_start = dt.datetime.now()
                print 'Serving on host at port', args.port,'with a packet loss simulation of',args.packetloss,'%'
                flag = False

            except IOError:
                print 'Unsuccessful in binding server to port',args.port,'. Trying with another one..'
                args.port += 1

            except OverflowError:
                port = 1024

    portassign()


else:
    try:
        # Bind server to port
        serverSocket.bind(('', args.port))
        # Record the time at which the server started
        server_start = dt.datetime.now()
        print 'Serving on host at port', args.port,'with a packet loss simulation of',args.packetloss,'%'

    except IOError:
        # The user has specified the port number. 
        # We should allow him to specify an alternative rather than take matters into our own hands
        print 'Cannot bind server to port',args.port,'. Try with another one'
        exit()

# Multiple clients may access the server
# So maintain a dictionary (table) with IP address of the client as key 
# and a list with fields as
# 1: the number of packets received as value
# 2: The lost packet count
# 3: Timestamp of last received heartbeat
iptable = dict()
# This is another dictionary that holds the number of packets lost between two successive replies
# for a particular address
packets_lost = dict()
while True:

    try:
        # If no client pings the server for a whole minute, we have to assume that all clients are closed
        serverSocket.settimeout(60)
        # Generate random number in the range of 0 to 100
        rand = random.randint(0, 100)

        # Receive the client packet along with the address it is coming from
        message, address = serverSocket.recvfrom(1024)
        # The client is sending us a message with sequence number and a timestamp separated by a whitespace tab character
        # We need to split it by the whitespace tab character to extract the timestamp
        message_list = message.split('\t')
        message = dt.datetime.strptime(message_list[1],"%Y-%m-%d %H:%M:%S.%f")
        
        try:
    
            # If the client is pinging the server for the first time, create a key for its address
            if not address in iptable:
                iptable[address] = [0,0,0]
                # iptable[address][0] --> No of packets received
                # iptable[address][1] --> Lost packet count
                # iptable[address][2] --> Timestamp of last heartbeat
                packets_lost[address] = 0

            # A new packet has been received, so the value has to be incremented
            iptable[address][0] += 1

            # Human readable console response
            print 'Received packet no',iptable[address][0],'from',address,'.',
            print 'The sequence number sent with the packet was',message_list[0]
            now = dt.datetime.now()
            
            # Delay between the time at which the client sent the packet and the time server received it
            response = now - message

            # Timestamp of most recent ping from the client
            iptable[address][2] = now

            # If rand is less is than the arguement packetloss, we consider the packet lost and do not respond  
            if rand < args.packetloss:
                print 'Simulating packet loss for',address[0], ':', address[1]
                # Increment the value of total packets lost for the address
                iptable[address][1]+=1
                # Increment the value of packets lost in between two successful replies
                # Needed to report to the client
                packets_lost[address] += 1
                continue

            
            # Otherwise, the server responds by replying with the time difference and a report of lost packets
            reply = "Packet delivery delay = "+str(response)+", Number of packets lost in between = "+ packets_lost[address]
            # Reset packets_lost's value. We are restarting the counter for that address
            packets_lost[address] = 0

            serverSocket.sendto(reply, address)
            print 'Sent response to',address,'with a delay of',response.total_seconds()

        # The client may send a packet with invalid data either mistakenly or with a mischievious attempt at breaking the server.
        # This except block replies with a response and makes sure that server doesn't break down
        except TypeError:
            print 'Client at',address,'sent an unrecognized packet. Replying with an appropriate response'
            response = 'The datatype supported by this server is string. Given data is'+str(type(message))
            serverSocket.sendto(response,address)

    # The server can be closed with a keyboard interrupt. But before exiting, the socket must be safely closed for security reasons
    # Optional feature addition is to print a report of all the clients who pinged and some additional information
    except KeyboardInterrupt:
        print '\nSafely closing down the server...'
        # It should exit with a status summary of no of packets received from each client in a tabular format
        def decor():
            """Decoration for Status Summary"""
            for i in range(0,70):
                print '-',
            print

        decor()
        print "Summary"
        decor()
        server_end = dt.datetime.now()
        print "Server started serving on port",args.port,"on",server_start,"and is exiting on",server_end
        print "Server ran for a duration of",( server_end - server_start )
        print "NOTE: The packetloss percentage is only for studying the simulation.",
        print "Real life UDP server wouldn't know and wouldn't care about packetloss"
        decor()
        print "Client\t\t\tNumber of Packets Received\tPacket loss percentage\tLast Heartbeat received at"
        decor()

        for key in iptable:
            percentage = ((int(iptable[key][1])) / (int(iptable[key][0]) * 1.0) * 100)
            print key,"\t",iptable[key][0],"\t\t\t\t",("%.2f" %percentage) ,"%\t\t\t", iptable[key][2]

        print ''
        decor()
        break;

    except Exception as e:
        
        if type(e) == timeout:
            print "NOTE: It's been a whole minute since the last client pinged the server.",
            print "If there are no more clients to test the server with, you can close the server with Ctrl+C key stroke"

        else:
            print e

# Safely close the socket
serverSocket.close()
