import socket
import threading
import sys

class VoiceServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.channels = {} # {channel_id: [client_socket]}
        self.client_channels = {} # {client_socket: channel_id}
        self.clients = []
        self.running = False
        self.lock = threading.Lock()

    def start(self):
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            print(f"Voice Server started on {self.host}:{self.port}")
            print("Waiting for connections...")

            while self.running:
                try:
                    client_socket, addr = self.server_socket.accept()
                    print(f"New connection from {addr}")
                    with self.lock:
                        self.clients.append(client_socket)

                    client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                    client_thread.daemon = True
                    client_thread.start()
                except OSError:
                    if self.running:
                        print("Server socket error.")
                    break
                except Exception as e:
                    print(f"Error accepting connection: {e}")

        except Exception as e:
            print(f"Failed to start server: {e}")
        finally:
            self.stop()

    def stop(self):
        self.running = False
        try:
            self.server_socket.close()
        except:
            pass

        # Close all client connections
        with self.lock:
            for client in self.clients:
                try:
                    client.close()
                except:
                    pass
            self.clients.clear()
            self.channels.clear()
            self.client_channels.clear()

        print("Server stopped.")

    def handle_client(self, client_socket):
        buffer = ""
        try:
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break

                buffer += data.decode('utf-8')

                while '\n' in buffer:
                    message, buffer = buffer.split('\n', 1)
                    if message.strip():
                        self.process_message(client_socket, message.strip())

        except ConnectionResetError:
            pass
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            self.remove_client(client_socket)
            try:
                client_socket.close()
            except:
                pass

    def process_message(self, client_socket, message):
        parts = message.split(' ', 1)
        command = parts[0]

        if command == 'JOIN':
            if len(parts) > 1:
                channel_id = parts[1]
                self.join_channel(client_socket, channel_id)
        elif command == 'LEAVE':
            self.leave_channel(client_socket)
        elif command == 'AUDIO':
            if len(parts) > 1:
                audio_data = parts[1]
                self.broadcast_audio(client_socket, audio_data)
        else:
            print(f"Unknown command: {command}")

    def join_channel(self, client_socket, channel_id):
        self.leave_channel(client_socket) # Leave current channel first

        with self.lock:
            if channel_id not in self.channels:
                self.channels[channel_id] = []

            self.channels[channel_id].append(client_socket)
            self.client_channels[client_socket] = channel_id
            print(f"Client joined channel {channel_id}")

        # Notify client (outside lock to avoid blocking)
        try:
            client_socket.sendall(f"JOINED {channel_id}\n".encode('utf-8'))
        except:
            pass

    def leave_channel(self, client_socket):
        with self.lock:
            if client_socket in self.client_channels:
                channel_id = self.client_channels[client_socket]
                if channel_id in self.channels:
                    if client_socket in self.channels[channel_id]:
                        self.channels[channel_id].remove(client_socket)
                    if not self.channels[channel_id]:
                        del self.channels[channel_id]
                del self.client_channels[client_socket]
                print(f"Client left channel {channel_id}")

    def broadcast_audio(self, sender_socket, audio_data):
        recipients = []
        with self.lock:
            if sender_socket in self.client_channels:
                channel_id = self.client_channels[sender_socket]
                if channel_id in self.channels:
                    # Create a copy of the list to iterate safely
                    recipients = [c for c in self.channels[channel_id] if c != sender_socket]

        if recipients:
            message = f"AUDIO {audio_data}\n".encode('utf-8')
            for client in recipients:
                try:
                    client.sendall(message)
                except:
                    # Connection might be dead, let handle_client clean it up
                    pass

    def remove_client(self, client_socket):
        self.leave_channel(client_socket)
        with self.lock:
            if client_socket in self.clients:
                self.clients.remove(client_socket)
        print("Client disconnected")

if __name__ == "__main__":
    port = 5000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    server = VoiceServer(port=port)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
