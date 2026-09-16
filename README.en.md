# 🚢 Multiplayer Battleship (2–4 Players)

*[Deutsche Version*](file:///C:/Users/Alex/Downloads/README.md)

A network-enabled "Battleship" game for 2 to 4 players over a local network (LAN), built with **Python** and **PyQt5**. One player hosts the game, the others join via IP/port – plain TCP socket networking, no external servers or accounts required.

Runs on **Windows**, **Linux**, and **macOS**.

## Features

- **2–4 players** in one game, playing in a fixed turn order

- **Host/client architecture** over TCP sockets on the local network

- **Manual or automatic ship placement** (`🎲 Auto-Place`), including a minimum spacing rule between ships

- Rotate ships with the **`R`** key or a button (horizontal/vertical)

- **Elimination mode**: whoever loses all their ships is out – last player standing wins

- Revealed cells of eliminated players remain viewable via the radar dropdown

- **Automatic IP detection** (`📍 Find IP`) for the host

- **Play again** without having to restart the app

- Robust connection handling: a disconnected player is automatically eliminated, the game continues for the rest

- UI fix for consistent cell sizes on macOS

## Download (pre-built binaries)

Ready-to-run programs are available for every release on the [Releases page](file:///C:/Users/releases) – no Python required:

| Platform | File |
| - | - |
| Windows | `Schiffe-Windows.exe` |
| macOS | `Schiffe-macOS.dmg` |
| Linux | `Schiffe-Linux` |


> **Note (Windows/macOS):** Since these builds aren't commercially signed, you may see a security warning on first launch ("Windows protected your PC" / "unidentified developer"). Just confirm via "More info → Run anyway" (Windows) or right-click → "Open" (macOS).

## Requirements (only needed to run from source)

- Python 3.8 or newer

- PyQt5

```
pip install PyQt5
```

## Running (from source)

```
python Schiffe.py
```

Each player starts the file separately (on their own machine, on the same network).

## How to play

### Host (Player 1)

1. Select the role **"Host (Player 1)"**

2. Choose the number of players (2–4)

3. Optionally click **"📍 Find IP"** to auto-fill your own local network IP

4. Set a port (default: `5555`)

5. Click **"Start / Join Lobby"** – the app now waits for the remaining players

6. **Share the displayed IP address with all other players** (e.g. via chat/voice) – it's needed in the next step

### Other players (Client)

1. Select the role **"Client (Join)"**

2. **Enter exactly the IP address shown on the host** (see step 6 above) – a typo or a wrong/outdated IP will prevent joining

3. Enter the same port as the host

4. Click **"Start / Join Lobby"**

> ⚠️ **The most common reason joining fails:** the IP entered on the client doesn't exactly match the IP the host obtained via "📍 Find IP". It's best to copy the IP directly from the host rather than typing it out, to avoid typos. If the host's IP changes in the meantime (e.g. after reconnecting to Wi-Fi), it needs to be re-detected and shared with the other players again.

Once everyone is connected, each player places their ships on their own board (left side). After placing, you wait for the remaining players – then the game starts automatically.

On the right-hand board (**attack radar**), clicking fires at the current opponent. The **"Target player"** dropdown also lets you view already-revealed cells of other players (including eliminated ones) – but shots always go to the mandatory target dictated by the turn order.

## Network notes

- All players must be on the **same local network** (Wi-Fi/LAN), or the host must forward the chosen port through their firewall/router for incoming connections if playing over the internet.

- Communication is **unencrypted**, plain JSON-over-TCP – intended for private, trusted networks, not for use over the open internet without additional safeguards.

- There's no authentication: anyone who knows the host's IP and port can join the lobby.

- The host's local IP address can change whenever the router restarts or Wi-Fi reconnects (typical for DHCP-assigned addresses). If joining suddenly stops working, check first whether the host's IP has changed.

## Known limitations

- No reconnecting after a dropped connection (a disconnected player is permanently eliminated from the running game)

- No encryption/authentication (see above – intended for trusted LANs only)

- Fixed ship sizes: `[4, 3, 2, 2, 1, 1, 1]` on a 10×10 board

## License

MIT License – see [LICENSE](file:///C:/Users/Alex/Downloads/LICENSE).

## Contributing

Pull requests and issues are welcome!

