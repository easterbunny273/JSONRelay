__author__ = 'easterbunny'

import socket
import sys
import threading
import time
import signal
import queue
import json
from _thread import *


HOST = ''  # Symbolic name meaning all available interfaces
PORT = 8891  # Arbitrary non-privileged port

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def signal_handler(signal, frame):
        print('You pressed Ctrl+C, exiting...')
        s.close()
        sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

print('Socket created')

# Bind socket to local host and port
try:
    s.bind((HOST, PORT))
except socket.error as msg:
    print('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
    sys.exit()

print('Socket bind complete')

# Start listening on socket
s.listen(10)
print('Socket now listening')

# Function for handling connections. This will be used to create threads
def clientthread(client_id, conn):
    client_identity = None
    # Sending message to connected client
    conn.send(b'INIT')
    try:
        data = conn.recv(1024)
        if data:
            try:
                init_message = json.loads(bytes.decode(data, 'UTF-8'))
                client_identity = init_message["identity"]
                if client_identity not in message_queues_for_identities:
                    message_queues_for_identities[client_identity] = queue.Queue()
            except BaseException as e:
                conn.send(b"ERROR_COULD_NOT_DECODE_INIT_JSON_BLOCK")
                conn.close()

            if conn:
                conn.send(b'OK')

    except socket.error as e:
        conn.close()

    if conn:
        #conn.send(bytes(welcome_message, 'UTF-8'))  #send only takes string
        conn.setblocking(False)

        # infinite loop so that function do not terminate and thread do not end.
        while True:

            # Receiving from client
            try:
                data = conn.recv(1024)

                if data:
                    full_message = json.loads(bytes.decode(data, 'UTF-8'))

                    if full_message["sender"] == client_identity:


                        add_message_to_queues(sender=full_message["sender"],
                                              receiver=full_message["receiver"],
                                              message=full_message)
                else:
                    break
            except BlockingIOError as e:
                pass
            except socket.error as e:
                break

            my_queue = message_queues_for_identities[client_identity]
            if not my_queue.empty():
                full_message_to_send = b"["
                messages_sent = 0
                while not my_queue.empty():
                    top_message = my_queue.get()
                    if messages_sent > 0:
                        full_message_to_send += b","
                    top_message["_server_metadata"]["time-sent"] = time.ctime()
                    full_message_to_send += str.encode(json.dumps(top_message), 'UTF-8')
                    messages_sent+=1
                full_message_to_send += b"]"

                length_of_full_message = len(full_message_to_send)
                full_message_including_meta_info = bytes(str(length_of_full_message), 'UTF-8') + b' ' + full_message_to_send
                conn.sendall(full_message_including_meta_info)

                print("Sent " + str(messages_sent) + " message(s) to " + client_identity)

        # came out of loop
        conn.close()


def add_message_to_queues(sender, receiver, message):
    # add server metadata
    message["_server_metadata"] = {"time-processed": time.ctime()}

    if receiver:
        if receiver not in message_queues_for_identities:
            message_queues_for_identities[receiver] = queue.Queue()
        message_queues_for_identities[receiver].put(message)
    else:
        for identity in message_queues_for_identities:
            if identity != sender:
                current_queue = message_queues_for_identities[identity]
                current_queue.put(message)

# now keep talking with the client
next_free_client_id = 0
created_threads = {}
message_queues_for_identities = {}

while 1:
    # wait to accept a connection - blocking call
    conn, addr = s.accept()
    print('Connected with ' + addr[0] + ':' + str(addr[1]))

    new_client_thread = threading.Thread(target=clientthread, args=(next_free_client_id, conn, ))
    created_threads[next_free_client_id] = new_client_thread
    next_free_client_id += 1

    new_client_thread.start()

s.close()