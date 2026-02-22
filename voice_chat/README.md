# Voice Chat Simulation

This module provides a simulated voice chat system with server channels, similar to Discord.

## Features

- **Server Channels**: Clients can join specific channels.
- **Voice Broadcasting**: "Voice" data sent by one client is broadcast to all other clients in the same channel.
- **Simulated Audio**: Due to the lack of audio hardware and libraries (PortAudio) in this environment, voice is simulated using text messages. In a real deployment, the text payload would be replaced by PCM or Opus audio data.

## Usage

### Starting the Server

Run the server on a machine (or in a terminal):

```bash
python3 voice_chat/server.py [port]
```

Default port is 5000.

### Starting a Client

Run the client in a separate terminal:

```bash
python3 voice_chat/client.py [host] [port]
```

Default host is 127.0.0.1, default port is 5000.

### Client Commands

Once connected, you can use the following commands:

- `join <channel_id>`: Join a specific channel (e.g., `join general`).
- `leave`: Leave the current channel.
- `say <text>`: Simulate speaking. The text will be sent to all other users in the channel.
- `quit`: Exit the client.

## Implementation Details

- **Protocol**: TCP-based custom protocol.
- **Message Format**: `COMMAND <payload>\n`
- **Commands**: `JOIN`, `LEAVE`, `AUDIO`, `JOINED`.

## Note on Audio

To upgrade this to real audio, one would need to:
1. Install `pyaudio`.
2. Replace `input()` in client with `pyaudio.Stream.read()`.
3. Replace `print()` in client with `pyaudio.Stream.write()`.
4. Ideally, use UDP for audio data to reduce latency, while keeping TCP for control messages.
