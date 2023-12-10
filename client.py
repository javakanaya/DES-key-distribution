import socket
import threading
from encryption.rsa import setkeys

global state


def receive_messages(client_socket):
    global state, target_id
    try:
        while True:
            # Receive messages from the server
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break

            data = eval(data)

            if 'sender_id' in data:
                state = 'chat'
                target_id = data['sender_id']
                print(
                    "\nAnother client is sending messages, Refresh client ('R') to reply")

            # Print the received message
            print(f"\nReceived from server: {data['data']}")

    except Exception as e:
        print(f"\nError receiving messages: {e}")


if __name__ == "__main__":
    state = "listen"
    target_id = None
    # Set up the client socket
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("127.0.0.1", 12345))

    public_key, private_key, n = setkeys()

    # Receive the welcome message from the server
    welcome_msg = client.recv(1024)
    print(f"Server says: {eval(welcome_msg.decode('utf-8'))['data']}")

    # Start a thread to receive messages from the server
    receive_thread = threading.Thread(target=receive_messages, args=(client,))
    receive_thread.start()

    try:
        while True:
            if state == 'listen':
                if target_id is None:
                    # Prompt the user for the initial target client ID
                    target_id_str = input(
                        "Enter target client ID ('L' to show the list of connected clients, 'Ctrl + C' to quit, 'R' to refresh): ")
                    if target_id_str.lower() == 'q':
                        break

                    if target_id_str.lower() == 'l':
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

                # Prompt the user for the message
                message = input(
                    f"Enter the message to {target_id} ('b' to stop chatting): ")

                if message.lower() == 'b':
                    # Choose a new target client
                    state = 'listen'
                    target_id = None
                else:
                    # Send the input to the server in the format "target_id:message"
                    client.send(str({
                        "target_id": target_id,
                        "data": message})
                        .encode('utf-8'))

            elif state == 'chat':
                # Directly enter the message in chat mode
                message = input(
                    f"Enter the message to {target_id} ('b' to stop chatting): ")

                if message.lower() == 'b':
                    # Return to listening mode
                    state = 'listen'
                    target_id = None
                else:
                    # Send the input to the server in the format "target_id:message"
                    client.send(str({
                        "target_id": target_id,
                        "data": message})
                        .encode('utf-8'))

    except KeyboardInterrupt:
        pass  # Handle Ctrl+C to exit the loop

    finally:
        # Close the client connection
        client.close()
