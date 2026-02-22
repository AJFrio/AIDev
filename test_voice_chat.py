import threading
import time
import unittest
import socket
from voice_chat.server import VoiceServer
from voice_chat.client import VoiceClient

class TestVoiceChat(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start server in a separate thread
        cls.server_port = 5001  # Use a different port for testing
        cls.server = VoiceServer(port=cls.server_port)
        cls.server_thread = threading.Thread(target=cls.server.start)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        time.sleep(1)  # Wait for server to start

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()
        # cls.server_thread.join(timeout=2) # Can't join daemon thread easily if it's blocking on accept

    def test_voice_communication(self):
        received_messages_client1 = []
        received_messages_client2 = []

        def on_message_client1(type, content):
            received_messages_client1.append((type, content))

        def on_message_client2(type, content):
            received_messages_client2.append((type, content))

        # Start two clients
        client1 = VoiceClient(port=self.server_port, on_message=on_message_client1)
        client2 = VoiceClient(port=self.server_port, on_message=on_message_client2)

        self.assertTrue(client1.connect(), "Client 1 failed to connect")
        self.assertTrue(client2.connect(), "Client 2 failed to connect")

        # Join same channel
        channel = "test_channel"
        client1.join_channel(channel)
        time.sleep(0.5)
        client2.join_channel(channel)
        time.sleep(0.5)

        # Verify JOINED messages (locally processed)
        # Wait for callback
        time.sleep(0.5)
        # Note: server sends JOINED confirmation back to the client that joined

        # Since on_message is called when server sends back JOINED
        # Verify client 1 got JOINED
        self.assertTrue(any(m[0] == "JOINED" and m[1] == channel for m in received_messages_client1))
        # Verify client 2 got JOINED
        self.assertTrue(any(m[0] == "JOINED" and m[1] == channel for m in received_messages_client2))

        # Send audio from client 1
        message = "Hello World"
        client1.send_audio(message)
        time.sleep(0.5)

        # Verify client 2 received it
        self.assertTrue(any(m[0] == "AUDIO" and m[1] == message for m in received_messages_client2),
                        f"Client 2 did not receive audio: {received_messages_client2}")

        # Verify client 1 did NOT receive it (echo cancellation / not broadcast to self)
        self.assertFalse(any(m[0] == "AUDIO" and m[1] == message for m in received_messages_client1),
                         "Client 1 received its own audio")

        # Client 2 leaves channel and joins another
        client2.join_channel("other_channel")
        time.sleep(0.5)

        # Send audio from client 1 again
        message2 = "Are you there?"
        client1.send_audio(message2)
        time.sleep(0.5)

        # Verify client 2 did NOT receive it
        self.assertFalse(any(m[0] == "AUDIO" and m[1] == message2 for m in received_messages_client2),
                         "Client 2 received audio from wrong channel")

        client1.close()
        client2.close()

if __name__ == "__main__":
    unittest.main()
