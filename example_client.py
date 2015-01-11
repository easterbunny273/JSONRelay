__author__ = 'easterbunny'

import socket
import sys
import signal
import json
import time

assert len(sys.argv) == 3
identity = sys.argv[1]
receiving_identity = sys.argv[2]

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def parse_header_message_block(data):

    # we expect a message in the format "<LENGTH OF MESSAGE, starting after space><SPACE>MESSAGE", e.g.: "2 ab"

    pos_of_space = data.index(b' ')
    length_of_message = int(data[:pos_of_space])
    message_first_part = data[pos_of_space+1:]

    current_message_block = message_first_part
    if len(message_first_part) <= length_of_message:
        remaining_bytes_left_for_current_block = length_of_message - len(message_first_part)
    else:
        decode_message_block(message_first_part[:length_of_message])
        data = data[pos_of_space+1+length_of_message:]
        return parse_header_message_block(data)
    return current_message_block, remaining_bytes_left_for_current_block

def decode_message_block(current_block):
    #try:
    received_list_of_messages = json.loads(bytes.decode(current_block, 'UTF-8'))
    print ("Decoded block of " + str(len(received_list_of_messages)) + " messages")
    #except BaseException as e:
    #    print ("Error while decoding :" + bytes.decode(current_message_block, 'UTF-8'))

def signal_handler(signal, frame):
        print('You pressed Ctrl+C, exiting...')
        client_socket.close()
        sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

client_socket.connect(('localhost', 8891))

while True:
    data = client_socket.recv(512)
    if data == b'INIT':
        init_dict = {"identity": identity}
        client_socket.send(bytes(json.dumps(init_dict), 'UTF-8'))

        data = client_socket.recv(512)
        if data == b'OK':
            # everything okay so far
            client_socket.setblocking(False)

            current_message_block = b""
            remaining_bytes_left_for_current_block = 0
            while True:

                try:
                    data = client_socket.recv(4096 if remaining_bytes_left_for_current_block is 0 or remaining_bytes_left_for_current_block > 4096 else remaining_bytes_left_for_current_block)
                    if data:
                        if not remaining_bytes_left_for_current_block:

                            current_message_block, remaining_bytes_left_for_current_block = parse_header_message_block(data)
                        else:
                            length_of_received_data = len(data)
                            assert length_of_received_data <= remaining_bytes_left_for_current_block

                            current_message_block += data
                            remaining_bytes_left_for_current_block -= length_of_received_data

                        if remaining_bytes_left_for_current_block is 0:
                            decode_message_block(current_message_block)



                except BlockingIOError as e:
                    pass
                except socket.error as e:
                    break

                # here we can send something
                #test_message_dict = { "sender": identity, "receiver": receiving_identity, "metadata": {"time-sent": time.ctime()}, "userdata": {"message": "hallo " + receiving_identity}}
                #client_socket.send(bytes(json.dumps(test_message_dict), 'UTF-8'))
                #time.sleep(0.1)


        else:
            print("INIT Handshake failed, got \"" + str(data) + "\" instead of \"OK\"")
            client_socket.close()
            sys.exit(1)
    else:
        print("INIT Handshake failed, got \"" + str(data) + "\" instead of \"INIT\"")
        client_socket.close()
        sys.exit(1)