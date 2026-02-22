import socket
import threading
import sys

class VoiceClient:
    def __init__(self, host='127.0.0.1', port=5000, on_message=None):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.current_channel = None
        self.on_message = on_message
        self.receive_thread = None

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"Connected to {self.host}:{self.port}")

            # Start receiving thread
            self.receive_thread = threading.Thread(target=self.receive_loop)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False

    def receive_loop(self):
        buffer = ""
        while self.connected:
            try:
                data = self.socket.recv(4096)
                if not data:
                    print("\nDisconnected from server.")
                    self.connected = False
                    break

                buffer += data.decode('utf-8')
                while '\n' in buffer:
                    message, buffer = buffer.split('\n', 1)
                    if message.strip():
                        self.process_message(message.strip())
            except OSError:
                break
            except Exception as e:
                if self.connected:
                    print(f"\nError receiving: {e}")
                self.connected = False
                break

    def process_message(self, message):
        parts = message.split(' ', 1)
        command = parts[0]

        if command == 'JOINED':
            if len(parts) > 1:
                self.current_channel = parts[1]
                if self.on_message:
                    self.on_message("JOINED", self.current_channel)
                else:
                    print(f"\n[System] Joined channel: {self.current_channel}")
                    print("> ", end="", flush=True)
        elif command == 'AUDIO':
            if len(parts) > 1:
                content = parts[1]
                if self.on_message:
                    self.on_message("AUDIO", content)
                else:
                    print(f"\n[Channel {self.current_channel}] Voice: {content}")
                    print("> ", end="", flush=True)
        else:
            if not self.on_message:
                print(f"\n[Unknown] {message}")
                print("> ", end="", flush=True)

    def join_channel(self, channel_id):
        if self.connected:
            # Sanitize input
            channel_id = channel_id.replace('\n', '').replace('\r', '').strip()
            self.socket.sendall(f"JOIN {channel_id}\n".encode('utf-8'))
        else:
            print("Not connected.")

    def leave_channel(self):
        if self.connected:
            self.socket.sendall("LEAVE\n".encode('utf-8'))
            self.current_channel = None
            if not self.on_message:
                print("\n[System] Left channel")
        else:
            print("Not connected.")

    def send_audio(self, text):
        if self.connected and self.current_channel:
            # Sanitize input to prevent protocol injection
            text = text.replace('\n', ' ').replace('\r', '')
            self.socket.sendall(f"AUDIO {text}\n".encode('utf-8'))
        elif not self.connected:
            print("Not connected.")
        elif not self.current_channel:
            print("Join a channel first.")

    def close(self):
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass

if __name__ == "__main__":
    host = '127.0.0.1'
    port = 5000

    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])

    client = VoiceClient(host, port)
    if not client.connect():
        sys.exit(1)

    print("Commands: join <channel>, leave, say <text>, quit")

    try:
        while True:
            cmd = input("> ")
            if not cmd: continue

            parts = cmd.split(' ', 1)
            command = parts[0].lower()

            if command == 'join':
                if len(parts) > 1:
                    client.join_channel(parts[1])
                else:
                    print("Usage: join <channel_id>")
            elif command == 'leave':
                client.leave_channel()
            elif command == 'say':
                if len(parts) > 1:
                    client.send_audio(parts[1])
                else:
                    print("Usage: say <text>")
            elif command == 'quit':
                break
            else:
                print("Unknown command")

    except KeyboardInterrupt:
        pass
    finally:
        client.close()
