# vidaa-control

[![PyPI](https://img.shields.io/pypi/v/vidaa-control)](https://pypi.org/project/vidaa-control/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Python library for controlling Hisense/Vidaa Smart TVs. Communicates directly with the TV's built-in MQTT-over-TLS broker — no cloud, no external broker needed.

Used by the [ha-vidaa-tv](https://github.com/tombabolewski/ha-vidaa-tv) Home Assistant integration.

## Features

- **Direct SSL connection** to the TV's built-in broker (port 36669)
- **Auto-discovery** via SSDP and UDP broadcast
- **PIN pairing** — authenticate via TV screen, tokens persisted automatically
- **Protocol detection** — supports modern, middle, and legacy Vidaa firmware
- **48 remote keys** — power, navigation, playback, numbers, colors, etc.
- **Volume control** — get/set/mute with state tracking
- **Input source switching** — HDMI, TV, AV, Component
- **App launching** — Netflix, YouTube, Prime Video, Disney+, and more
- **Wake-on-LAN** — power on from standby
- **Sync and async clients** — `VidaaTV` and `AsyncVidaaTV`
- **CLI tool** — `vidaa` command for interactive control

## Installation

```bash
pip install vidaa-control
```

## Quick Start

### CLI

```bash
# Discover TVs on the network
vidaa discover

# Pair with a TV (shows PIN on TV screen)
vidaa pair 192.168.1.225

# Send commands
vidaa key home
vidaa volume 25
vidaa launch netflix
vidaa source hdmi1
```

### Python (sync)

```python
from vidaa import VidaaTV

tv = VidaaTV(
    host="192.168.1.225",
    mac_address="AA:BB:CC:DD:EE:FF",
    use_dynamic_auth=True,
)

if tv.connect():
    tv.power_on()
    tv.set_volume(25)
    tv.launch_app("netflix")
    tv.disconnect()
```

### Python (async)

```python
from vidaa import AsyncVidaaTV
from vidaa.config import TokenStorage

tv = AsyncVidaaTV(
    host="192.168.1.225",
    mac_address="AA:BB:CC:DD:EE:FF",
    use_dynamic_auth=True,
    enable_persistence=True,
    storage=TokenStorage("tokens.json"),
)

if await tv.async_connect():
    state = await tv.async_get_state()
    volume = await tv.async_get_volume()
    await tv.async_launch_app("youtube")
    await tv.async_disconnect()
```

## Remote Keys

48 keys available via `send_key()` / `async_send_key()`:

| Category | Keys |
|----------|------|
| Power | `KEY_POWER` |
| Navigation | `KEY_UP`, `KEY_DOWN`, `KEY_LEFT`, `KEY_RIGHT`, `KEY_OK`, `KEY_BACK`, `KEY_MENU`, `KEY_HOME`, `KEY_EXIT` |
| Volume | `KEY_VOLUME_UP`, `KEY_VOLUME_DOWN`, `KEY_MUTE` |
| Channel | `KEY_CHANNEL_UP`, `KEY_CHANNEL_DOWN` |
| Playback | `KEY_PLAY`, `KEY_PAUSE`, `KEY_STOP`, `KEY_FAST_FORWARD`, `KEY_REWIND` |
| Numbers | `KEY_0` through `KEY_9` |
| Colors | `KEY_RED`, `KEY_GREEN`, `KEY_YELLOW`, `KEY_BLUE` |
| Extras | `KEY_INFO`, `KEY_SUBTITLE` |

## Protocol

Communication uses MQTT over TLS on port 36669. The library bundles the required client certificates. Authentication is handled automatically:

1. **Discovery** — SSDP or UDP broadcast finds TVs
2. **Protocol detection** — HTTP probe determines firmware generation
3. **Pairing** — TV displays PIN, client authenticates
4. **Token persistence** — auth tokens stored for reconnection

See [docs/PROTOCOL.md](docs/PROTOCOL.md) for the full protocol analysis.

## License

MIT
