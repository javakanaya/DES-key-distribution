import socket
import time
import threading


def handle_client(client_socket, address, client_id, clients):
    print(f"Accepted connection from {address} with ID {client_id}")
    # Send a welcome message to the client
    client_socket.send(str({
        'data': f"Welcome to the server! Your ID is {client_id}",
        'client_id': client_id
    }).encode('utf-8'))

    time.sleep(0.5)

    # recieve the new client public key
    public_key = eval(client_socket.recv(
        1024).decode('utf-8'))['public_key']

    # Send the new public key to all old clients
    for _, client_item_socket in clients.items():
        if client_item_socket != client_socket:
            client_item_socket.send(str({
                'client_id': client_id,
                'public_key': public_key,
                'data': f"New Client ID: {client_id} Public Key"
            }).encode('utf-8'))

    time.sleep(0.5)

    # Send the public keys to the new client
    client_socket.send(str({
        'public_keys': public_keys,
        'data': "Public Keys Dictionary"
    }).encode('utf-8'))

    # update server public keys dictionary
    public_keys[client_id] = public_key

    try:
        while True:
            # Receive data from the client
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break

            data = eval(data)

            # Print the received data
            print(
                f"Received data from {address} (ID {client_id}): {data}")

            # Parse the received data
            try:
                if data['data'] == 'L':
                    # Handle request for the list of connected clients
                    send_client_list(client_id)
                else:
                    # Assume the client sends data in the format "target_ids:message"
                    target_ids = [int(data['target_id'])]

                    # Forward the message to the specified target clients
                    forward_message(client_id, target_ids, data['data'], data['step'], data['length'])
            except ValueError as e:
                print(f"Invalid format received from client {client_id}: {e}")

    except Exception as e:
        print(f"Error handling client {client_id}: {e}")

    finally:
        # Remove the client from the dictionary when the connection is closed
        del clients[client_id]

        # Close the connection with the client
        print(f"Connection with {address} (ID {client_id}) closed")
        client_socket.close()


def forward_message(sender_id, target_ids, message, step, length):
    # Forward the message to the specified target clients
    for target_id in target_ids:
        try:
            target_socket = clients.get(target_id)
            if target_socket and target_id != sender_id:
                target_socket.send(str({
                    'step': step,
                    'sender_id': sender_id,
                    'data': message,
                    'length': length
                }).encode('utf-8'))
        except Exception as e:
            print(f"Error forwarding message to client {target_id}: {e}")


def send_client_list(client_id):
    # Send the list of connected clients to the requesting client
    client_socket = clients[client_id]
    connected_clients = ", ".join(map(str, clients.keys()))
    client_socket.send(str({
        'data': f"Connected clients: {connected_clients}"
    }).encode('utf-8'))


if __name__ == "__main__":
    # Dictionary to store connected clients and their sockets
    clients = {}
    public_keys = {}
    # Set up the server socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 12345))
    server.listen(5)

    print("Server listening on port 12345...")

    try:
        while True:
            # Accept a new client connection
            client_socket, addr = server.accept()

            # Assign a unique ID to the client
            client_id = len(clients) + 1

            # Add the client to the dictionary
            clients[client_id] = client_socket

            # Start a new thread to handle the client
            client_handler = threading.Thread(
                target=handle_client, args=(client_socket, addr, client_id, clients))
            client_handler.start()

    except KeyboardInterrupt:
        print("Server shutting down.")

    finally:
        # Close all client connections
        for client_socket in clients.values():
            client_socket.close()
