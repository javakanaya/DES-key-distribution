import socket
import threading
import random
from encryption.des import text_to_binary, binary_to_text, generateKeys, encrypt, decrypt
from encryption.rsa import setkeys, encoder, decoder
import secrets
import string
import time

global state


def print_message_box(header, lines):
    max_line_length = max(len(line) for line in lines)
    border = "+" + "-" * (max_line_length + 2) + "+"

    header_row = f"| {header.center(max_line_length)} |"
    content_rows = [f"| {line.ljust(max_line_length)} |" for line in lines]

    rows = [border, header_row, border] + content_rows + [border]

    print("")
    for row in rows:
        print(row)


def generate_random_string(length=8):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(secrets.choice(characters) for _ in range(length))
    return random_string


def receive_messages(client_socket):
    global state, target_id, session_des_key, session_round_key
    try:
        while True:

            # Receive messages from the server
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break

            data = eval(data)
            if 'public_keys' in data:
                public_keys.update(data['public_keys'])

                # Example usage:
                header = f"Received"
                lines = [
                    f"{data['data']}",
                ]

                print_message_box(header, lines)


            elif 'public_key' in data:
                public_keys[data['client_id']] = data['public_key']

                header = f"Received"
                lines = [
                    f"{data['data']}",
                ]

                print_message_box(header, lines)

            elif 'step' in data:
                # print(data['data'])
                if data['step'] == 1:
                    print(
                        "\n>>> Another client is sending messages, Refresh client ('R') to reply <<<")
                    decrypted = eval(decoder(data['data'], private_key, n))
                    bring_back_to = data['sender_id']
                    recv_n_1_from_step_1 = decrypted['n_1']
                    recv_n_1 = recv_n_1_from_step_1

                    data_step_2 = {
                        'n_1': recv_n_1_from_step_1,
                        'n_2': n_2
                    }

                    selected_public_keys = public_keys[bring_back_to]

                    encrypted_step_2 = encoder(
                        str(data_step_2), selected_public_keys, n)

                    client_socket.send(str({
                        "step": 2,
                        "target_id": bring_back_to,
                        "data": encrypted_step_2,
                        'length': -1
                    })
                        .encode('utf-8'))

                elif data['step'] == 2:
                    decrypted = eval(decoder(data['data'], private_key, n))
                    bring_back_to = int(data['sender_id'])
                    recv_n_1_from_step_2 = decrypted['n_1']
                    recv_n_2_from_step_2 = decrypted['n_2']


                    if n_1 != recv_n_1_from_step_2:
                        raise ValueError("N1 did not match!")

                    if (n_1 == recv_n_1_from_step_2):
                        print("+--------------------------------+")
                        print("|          N1 matches            |")
                        print(
                            f"|          {n_1} == {recv_n_1_from_step_2}          |")
                        print("+--------------------------------+")

                    data_step_3 = {
                        'n_2': recv_n_2_from_step_2
                    }

                    selected_public_keys = public_keys[bring_back_to]

                    encrypted_step_3 = encoder(
                        str(data_step_3), selected_public_keys, n)

                    client_socket.send(str({
                        "step": 3,
                        "target_id": bring_back_to,
                        "data": encrypted_step_3,
                        'length': -1
                    })
                        .encode('utf-8'))

                elif data['step'] == 3:
                    decrypted = eval(decoder(data['data'], private_key, n))
                    bring_back_to = int(data['sender_id'])
                    recv_n_2_from_step_3 = decrypted['n_2']

                    if n_2 != recv_n_2_from_step_3:
                        raise ValueError("N2 did not match!")

                    if (n_2 == recv_n_2_from_step_3):
                        print("+--------------------------------+")
                        print("|          N2 matches            |")
                        print(
                            f"|          {n_2} == {recv_n_2_from_step_3}          |")
                        print("+--------------------------------+")

                    state = 'chat'

                    data_step_4 = {
                        'n_1': recv_n_1,
                        'k_s': generated_des_key
                    }

                    session_des_key = generated_des_key
                    bin_key = text_to_binary(session_des_key)[0]
                    session_round_key = generateKeys(bin_key)

                    selected_public_keys = public_keys[bring_back_to]

                    encrypted_step_4 = encoder(
                        str(data_step_4), selected_public_keys, n)

                    client_socket.send(str({
                        "step": 4,
                        "target_id": bring_back_to,
                        "data": encrypted_step_4,
                        'length': -1
                    })
                        .encode('utf-8'))

                elif data['step'] == 4:
                    target_id = int(data['sender_id'])
                    decrypted = eval(decoder(data['data'], private_key, n))
                    recv_n_1_from_step_4 = decrypted['n_1']

                    if n_1 != recv_n_1_from_step_4:
                        raise ValueError("N1 did not match!")

                    if (n_1 == recv_n_1_from_step_4):
                        print("+--------------------------------+")
                        print("|          N1 matches            |")
                        print(
                            f"|          {n_1} == {recv_n_1_from_step_4}          |")
                        print("+--------------------------------+")

                    session_des_key = decrypted['k_s']
                    bin_key = text_to_binary(session_des_key)[0]
                    session_round_key = generateKeys(bin_key)
                    print(">>> Session Acquired <<<")
                    print(" - DES key acquired")
                    print(f" - connected to client ID: {target_id}")

                elif data['step'] == 5:
                    target_id = int(data['sender_id'])
                    state = 'chat'
                    length = data['length']
                    encrypted_bin_message = data['data']
                    source = data['sender_id']

                    # Decrypt the message
                    decrypted_bin_message = ''
                    for i in range(0, len(encrypted_bin_message), 64):
                        chunk = encrypted_bin_message[i:i+64]
                        decrypted_chunk = decrypt(chunk, session_round_key)
                        decrypted_bin_message += decrypted_chunk

                    # Trim the message to its original length
                    decrypted_message = binary_to_text(decrypted_bin_message)

                    # Print the message in a box :)
                    header = f"Received from {source}:"
                    lines = [
                        f"Raw           : {binary_to_text(encrypted_bin_message)}",
                        f"Decrypted   : {decrypted_message[:length]}"
                    ]

                    print_message_box(header, lines)

            else:
                print(f"\nReceived from server: {data['data']}")
    except Exception as e:
        print(f"\nError receiving messages: {e}")


if __name__ == "__main__":
    public_keys = {}
    state = "listen"
    target_id = None
    generated_des_key = generate_random_string()

    session_des_key = None
    session_round_key = None

    # Set up the client socket
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("127.0.0.1", 12345))

    public_key, private_key, n = setkeys()
    n_1 = random.randint(1000, 9999)
    n_2 = random.randint(1000, 9999)
    recv_n_1 = None

    print(f"Your private key is {private_key}")
    client.send(str({
        "public_key": public_key})
        .encode('utf-8'))

    # Receive the welcome message from the server
    welcome_msg = eval(client.recv(1024).decode('utf-8'))
    print(welcome_msg['data'])
    my_id = welcome_msg['client_id']

    # Start a thread to receive messages from the server
    receive_thread = threading.Thread(target=receive_messages, args=(client,))
    receive_thread.start()

    try:
        while True:
            time.sleep(0.1)
            if state == 'listen':
                print("a1")
                if target_id is None:
                    print("a1x")

                    # Prompt the user for the initial target client ID
                    while True:
                        target_id_str = input(
                            "Enter target client ID ('L' to show the list of connected clients, 'Ctrl + C' to quit, 'R' to refresh): ")

                        # Check if the input is a number or one of the specified letters
                        if target_id_str.isdigit():
                            target_id = int(target_id_str)

                            # Check if the selected client ID exists in public_keys
                            if target_id in public_keys:
                                break
                            else:
                                print(
                                    "You can't send messages to yourself, choose another client ID")
                        elif target_id_str.strip().upper() in ['L', 'Q', 'R']:
                            break
                        else:
                            print(
                                "Invalid input. Please enter a valid number or one of the specified letters.")

                    if target_id_str.lower() == 'q':
                        break

                    if target_id_str.lower() == 'l':
                        target_id = None
                        # Handle request to show the list of connected clients
                        client.send(str({
                            "data": 'L'})
                            .encode('utf-8'))
                        continue
                    elif target_id_str.lower() == 'r':
                        print("Refreshing client")
                        continue
                    else:
                        target_id = int(target_id_str)
                        state = 'chat'

                print("a1y")
                print("Getting session...")
                # Send the input to the server
                selected_public_keys = public_keys[int(target_id)]

                data_step_1 = {
                    'n_1': n_1,
                    'id_a': my_id
                }

                encrypted_step_1 = encoder(
                    str(data_step_1), selected_public_keys, n)

                client.send(str({
                    "step": 1,
                    "target_id": target_id,
                    "data": encrypted_step_1,
                    'length': -1
                })
                    .encode('utf-8'))
                continue

            elif state == 'chat':
                message = input(
                    f"Enter the message to {target_id} ('b' to stop chatting): ")

                if message.lower() == 'b':
                    # Choose a new target client
                    state = 'listen'
                    target_id = None
                else:

                    bin_message = text_to_binary(message)
                    encrypted_bin_message = ''
                    for chunk in bin_message:
                        encrypted_bin_message += encrypt(chunk,
                                                         session_round_key)

                    # Send the dictionary as a string to the server

                    client.send(str({
                        'step': 5,
                        'target_id': target_id,
                        'length': len(message),
                        'data': encrypted_bin_message
                    })
                        .encode('utf-8'))

    except KeyboardInterrupt:
        pass  # Handle Ctrl+C to exit the loop

    finally:
        # Close the client connection
        client.close()
