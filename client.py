#!/usr/bin/python
# Client program handwritten to suit our server
from socket import *
import datetime as dt
import time
import argparse


# Initializing parser for accepting command line arguements
parser = argparse.ArgumentParser(
    description="""UDP Heartbeat Client. Simulates sending and receiving packets to and from the server \
                   To close the client socket, press 'Ctrl + C'""")

# Assign server's IP address obtained from the command line
parser.add_argument(
    '--serverip', metavar='str', type=str, required=True,
    help="The server's IP address. A required value. Format: a.b.c.d, where a,b,c and d are within the range 0-255")

parser.add_argument(
    '--serverport', metavar='int', type=int, required=True,
    help="The server's port. A required value. Range: 1024 to 65535")

args = parser.parse_args()

if args.serverip == None:
    print 'IP address of server is missing. Use the flag -h to print help'
    clientSocket.close()
    exit()

elif args.serverport == None:
    print 'Port number of server is missing. Use the flag -h to print help'
    clientSocket.close()
    exit()

elif args.serverport < 1024 or args.serverport > 65535 or len(args.serverip) < 7 or len(args.serverip) > 15:
    print 'Invalid value for argument. Please execute with -h flag for help regarding the value ranges of arguments to be passed'
    clientSocket.close()
    exit()

# Create a UDP socket
clientSocket = socket(AF_INET, SOCK_DGRAM)
port = 12345
flag = True

while flag:
    try:
        # Bind server to port
        clientSocket.bind(('', port))
        print 'Client bound to port', port
        flag = False

    except IOError:
        print 'Cannot bind client to port',port,'. Trying with the next one...'
        port+=1

    except OverflowError:
        port = 1024

# A variable to hold the count of number of pings sent
scount = 0
# A variable to hold the count of number of pings received
rcount = 0
# Initialize the sequence number
seq = 1
while True:
    
    try:
        now = dt.datetime.now()

        # Set timeout for socket operations
        clientSocket.settimeout(1)

        # Create a message with first part as a sequence number and second part as the timestamp separated by a whitespace tab character
        # Modeled on collaborative effort with group X (Raje Neha's group)
        clientSocket.sendto(( str(seq) + '\t' + str(now) ), (args.serverip,args.serverport))
        print "PING",args.serverip,':',args.serverport,"at",now
        scount+=1
    
        # Receive the client packet along with the address it is coming from
        message, address = clientSocket.recvfrom(1024)

        print message
        rcount+=1

        # Increment the sequence number
        seq+=1

        time.sleep(3)
    
    except TypeError:
        print "Server sent an unexpected response"
        break

    except Exception as e:
        print e


    except KeyboardInterrupt:
        print '\nSafely shutting down the client'
        print "Statistics:"
        print "Packets Sent:",scount
        print "Packets Received",rcount
        print "Percentage Packet Loss",((1-(rcount/(scount*1.0)))*100),"%"
        break

clientSocket.close()