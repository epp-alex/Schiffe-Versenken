import sys
import socket
import threading
import json
import random
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QGridLayout, QMessageBox, QLineEdit, QComboBox, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QFont

GRID_SIZE = 10
SHIP_SIZES = [4, 3, 2, 2, 1, 1, 1]  # 1x4, 1x3, 2x2, 3x1

class NetworkSignals(QObject):
    data_received = pyqtSignal(dict)
    connected = pyqtSignal()
    disconnected = pyqtSignal()

class SchiffeVersenkenApp(QMainWindow):
    # Einheitlicher Stil für unbeschossene Felder (siehe Kommentar bei der
    # Button-Erstellung weiter unten - wichtig für den macOS-Größenbug).
    EMPTY_CELL_STYLE = "background-color: #ffffff; border: 1px solid #90a4ae;"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multiplayer Schiffe Versenken Pro (2-4 Spieler)")
        self.resize(1100, 650)

        # Netzwerkeinstellungen
        self.signals = NetworkSignals()
        self.signals.data_received.connect(self.handle_network_data)
        
        self.is_host = False
        self.player_id = 0  # 1 bis 4
        self.current_turn = 1
        self.num_players = 2
        self.active_players = [] # Liste der Spieler, die noch Schiffe haben

        self.server_socket = None
        self.client_socket = None
        self.client_connections = {} # Für Host: {player_id: socket}
        self.recv_buffers = {}
        self.send_lock = threading.Lock()

        # Spielfeld Daten (0 = Leer, 1 = Schiff, 2 = Wasser-Fehlschlag, 3 = Treffer)
        self.my_grid = [[0]*GRID_SIZE for _ in range(GRID_SIZE)]
        self.enemy_grids = {} # {player_id: [[0]*10 for _ in range(10)]}

        # Schiff-Platzierung Status
        self.placement_index = 0
        self.placement_orientation = 'H' # 'H' = Horizontal, 'V' = Vertikal
        self.placement_phase = True
        self.players_ready = set()

        self.init_ui()

    def auto_detect_ip(self):
        """Ermittelt die echte lokale Netzwerk-IP des PCs."""
        try:
            # Trick: Erstelle einen Dummy-Socket, um die primäre Route ins Netzwerk zu finden
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            self.txt_ip.setText(local_ip)
            self.lbl_status.setText(f"IP automatisch gefunden: {local_ip}")
        except Exception as e:
            # Fallback auf Loopback, falls kein Netzwerk aktiv ist
            self.txt_ip.setText("127.0.0.1")
            QMessageBox.warning(self, "IP-Erkennung", f"Konnte lokale IP nicht ermitteln: {e}")

    def init_ui(self):
        main_widget = QWidget()
        self.main_layout = QVBoxLayout()

        # ----------------- TOP BAR: LOBBY & VERBINDUNG -----------------
        self.top_frame = QFrame()
        top_layout = QHBoxLayout()

        self.role_combo = QComboBox()
        self.role_combo.addItems(["Host (Spieler 1)", "Client (Beitreten)"])
        self.role_combo.currentIndexChanged.connect(self.on_role_change)

        self.lbl_players = QLabel("Anzahl Spieler:")
        self.combo_num_players = QComboBox()
        self.combo_num_players.addItems(["2 Spieler", "3 Spieler", "4 Spieler"])

        self.txt_ip = QLineEdit("192.168.178.3")
        self.txt_port = QLineEdit("5555")
        self.txt_ip.setFixedWidth(110)
        self.txt_port.setFixedWidth(50)

        # NEU: Button zum automatischen Ermitteln der echten IP
        self.btn_get_ip = QPushButton("📍 IP finden")
        self.btn_get_ip.clicked.connect(self.auto_detect_ip)
        self.btn_get_ip.setToolTip("Ermittelt automatisch deine lokale Netzwerk-IP")

        self.btn_connect = QPushButton("Lobby Starten / Beitreten")
        self.btn_connect.clicked.connect(self.start_network)

        top_layout.addWidget(QLabel("Rolle:"))
        top_layout.addWidget(self.role_combo)
        top_layout.addWidget(self.lbl_players)
        top_layout.addWidget(self.combo_num_players)
        top_layout.addWidget(QLabel("IP:"))
        top_layout.addWidget(self.txt_ip)
        top_layout.addWidget(self.btn_get_ip)  # Der neue Button
        top_layout.addWidget(QLabel("Port:"))
        top_layout.addWidget(self.txt_port)
        top_layout.addWidget(self.btn_connect)
        top_layout.addStretch()

        self.top_frame.setLayout(top_layout)
        self.main_layout.addWidget(self.top_frame)

        # ----------------- STATUS & STEUERUNG -----------------
        status_layout = QHBoxLayout()
        self.lbl_status = QLabel("Willkommen! Bitte erstelle eine Lobby oder tritt einer bei.")
        self.lbl_status.setFont(QFont("Arial", 11, QFont.Bold))
        status_layout.addWidget(self.lbl_status)
        
        self.btn_rotate = QPushButton("Schiff Drehen: Horizontal [R]")
        self.btn_rotate.clicked.connect(self.toggle_orientation)
        self.btn_auto_place = QPushButton("🎲 Auto-Platzieren")
        self.btn_auto_place.clicked.connect(self.auto_place_ships)

        self.btn_play_again = QPushButton("🔄 Nochmal spielen")
        self.btn_play_again.clicked.connect(self.request_restart)
        self.btn_play_again.setVisible(False)  # erst sichtbar, wenn das Spiel zu Ende ist

        status_layout.addWidget(self.btn_rotate)
        status_layout.addWidget(self.btn_auto_place)
        status_layout.addWidget(self.btn_play_again)
        self.main_layout.addLayout(status_layout)

        # ----------------- SPIELFFELDER -----------------
        fields_layout = QHBoxLayout()

        # Linkes Feld: Eigene Flotte
        left_box = QVBoxLayout()
        left_box.addWidget(QLabel("<b>DEINE FLOTTE (Eigenes Feld)</b>"))
        self.grid_my = QGridLayout()
        self.grid_my.setSpacing(2)
        self.my_buttons = [[None]*GRID_SIZE for _ in range(GRID_SIZE)]
        
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                btn = QPushButton("")
                # Feste Zellgröße: verhindert, dass X/Fonts/Hit-Markierungen
                # unter macOS die Quadrate vergrößern.
                cell_size = 38 if sys.platform == "darwin" else 35
                btn.setFixedSize(cell_size, cell_size)
                btn.setMinimumSize(cell_size, cell_size)
                btn.setMaximumSize(cell_size, cell_size)
                btn.setSizePolicy(
                    __import__("PyQt5.QtWidgets", fromlist=["QSizePolicy"]).QSizePolicy.Fixed,
                    __import__("PyQt5.QtWidgets", fromlist=["QSizePolicy"]).QSizePolicy.Fixed
                )
                # WICHTIG (macOS-Fix): Auch leere Felder brauchen von Anfang an
                # ein eigenes Stylesheet. Sonst nutzt macOS für unbeschossene
                # Felder den nativen Aqua-Button-Stil (eigene Innenabstände),
                # waehrend beschossene Felder (die ein Stylesheet bekommen)
                # exakt die per setFixedSize() vorgegebene Pixelgroesse nutzen -
                # das fuehrt zu sichtbar unterschiedlich grossen/verzerrten
                # Zellen im selben Gitter. Unter Windows/Linux gibt es diesen
                # nativ-vs-gestylt-Unterschied nicht.
                btn.setStyleSheet(self.EMPTY_CELL_STYLE)
                btn.clicked.connect(lambda ch, row=r, col=c: self.on_my_cell_click(row, col))
                self.grid_my.addWidget(btn, r, c)
                self.my_buttons[r][c] = btn

        left_box.addLayout(self.grid_my)
        fields_layout.addLayout(left_box)

        fields_layout.addSpacing(30)

        # Rechtes Feld: Angriffs-Radar
        right_box = QVBoxLayout()
        radar_header = QHBoxLayout()
        radar_header.addWidget(QLabel("<b>ANGRIFFS-RADAR (Schießen)</b>"))
        radar_header.addWidget(QLabel("Ziel-Spieler:"))
        self.combo_target_player = QComboBox()
        radar_header.addWidget(self.combo_target_player)
        right_box.addLayout(radar_header)

        self.grid_radar = QGridLayout()
        self.grid_radar.setSpacing(2)
        self.radar_buttons = [[None]*GRID_SIZE for _ in range(GRID_SIZE)]

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                btn = QPushButton("")
                cell_size = 38 if sys.platform == "darwin" else 35
                btn.setFixedSize(cell_size, cell_size)
                btn.setMinimumSize(cell_size, cell_size)
                btn.setMaximumSize(cell_size, cell_size)
                btn.setSizePolicy(
                    __import__("PyQt5.QtWidgets", fromlist=["QSizePolicy"]).QSizePolicy.Fixed,
                    __import__("PyQt5.QtWidgets", fromlist=["QSizePolicy"]).QSizePolicy.Fixed
                )
                btn.setStyleSheet(self.EMPTY_CELL_STYLE)  # macOS-Fix, siehe oben
                btn.clicked.connect(lambda ch, row=r, col=c: self.on_radar_cell_click(row, col))
                self.grid_radar.addWidget(btn, r, c)
                self.radar_buttons[r][c] = btn

        right_box.addLayout(self.grid_radar)
        fields_layout.addLayout(right_box)

        self.main_layout.addLayout(fields_layout)
        main_widget.setLayout(self.main_layout)
        self.setCentralWidget(main_widget)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_R:
            self.toggle_orientation()

    def on_role_change(self, index):
        is_host = (index == 0)
        self.lbl_players.setVisible(is_host)
        self.combo_num_players.setVisible(is_host)

    def toggle_orientation(self):
        if self.placement_orientation == 'H':
            self.placement_orientation = 'V'
            self.btn_rotate.setText("Schiff Drehen: Vertikal [R]")
        else:
            self.placement_orientation = 'H'
            self.btn_rotate.setText("Schiff Drehen: Horizontal [R]")

    # ----------------- SCHIFFS-PLATZIERUNG -----------------
    def can_place_ship(self, grid, r, c, size, orientation):
        # 1. Prüfen ob das Schiff überhaupt ins Spielfeld passt
        if orientation == 'H':
            if c + size > GRID_SIZE: return False
        else:
            if r + size > GRID_SIZE: return False

        # 2. Prüfen ob das Feld und der umliegende Sicherheitsabstand frei sind
        for i in range(size):
            curr_r = r + (i if orientation == 'V' else 0)
            curr_c = c + (i if orientation == 'H' else 0)

            # Prüfe das Feld selbst und alle 8 umliegenden Nachbarn
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    check_r = curr_r + dr
                    check_c = curr_c + dc
                    if 0 <= check_r < GRID_SIZE and 0 <= check_c < GRID_SIZE:
                        if grid[check_r][check_c] != 0:
                            return False # Schiff berührt ein anderes Schiff oder ist zu nah dran!
        return True

    def place_ship(self, grid, r, c, size, orientation):
        if orientation == 'H':
            for i in range(size): grid[r][c+i] = 1
        else:
            for i in range(size): grid[r+i][c] = 1

    def on_my_cell_click(self, r, c):
        if not self.placement_phase:
            return

        if self.placement_index >= len(SHIP_SIZES):
            return

        size = SHIP_SIZES[self.placement_index]
        if self.can_place_ship(self.my_grid, r, c, size, self.placement_orientation):
            self.place_ship(self.my_grid, r, c, size, self.placement_orientation)
            self.placement_index += 1
            self.update_my_grid_ui()

            if self.placement_index < len(SHIP_SIZES):
                self.lbl_status.setText(f"Platziere Schiff der Länge {SHIP_SIZES[self.placement_index]}")
            else:
                self.lbl_status.setText("Alle Schiffe platziert! Warte auf andere Spieler...")
                self.btn_auto_place.setEnabled(False)
                self.btn_rotate.setEnabled(False)
                self.send_network_data({"type": "READY", "player": self.player_id})
        else:
            QMessageBox.warning(self, "Ungültig", "Schiff passt hier nicht hin oder überlappt!")

    def auto_place_ships(self):
        self.my_grid = [[0]*GRID_SIZE for _ in range(GRID_SIZE)]
        
        for size in SHIP_SIZES:
            placed = False
            attempts = 0
            while not placed and attempts < 1000: # Verhindert Endlosschleife
                r = random.randint(0, GRID_SIZE-1)
                c = random.randint(0, GRID_SIZE-1)
                ori = random.choice(['H', 'V'])
                if self.can_place_ship(self.my_grid, r, c, size, ori):
                    self.place_ship(self.my_grid, r, c, size, ori)
                    placed = True
                attempts += 1
            
            if not attempts < 1000:
                # Falls das Feld zu voll wird, Neustart des Versuchs
                return self.auto_place_ships()
        
        self.placement_index = len(SHIP_SIZES)
        self.update_my_grid_ui()
        self.lbl_status.setText("Alle Schiffe automatisch platziert (mit Abstand)! Bereitschaft gesendet.")
        self.btn_auto_place.setEnabled(False)
        self.btn_rotate.setEnabled(False)
        self.send_network_data({"type": "READY", "player": self.player_id})

    def update_my_grid_ui(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                val = self.my_grid[r][c]
                btn = self.my_buttons[r][c]
                if val == 0:
                    btn.setStyleSheet(self.EMPTY_CELL_STYLE)  # macOS-Fix, siehe oben
                    btn.setText("")
                elif val == 1:
                    btn.setStyleSheet("background-color: #5c6bc0; color: white;") # Schiff (Blau)
                elif val == 2:
                    btn.setStyleSheet("background-color: #9e9e9e; color: black; font-weight: bold;")
                    btn.setText("X") # Wasser
                elif val == 3:
                    btn.setStyleSheet("background-color: #e53935; color: white; font-weight: bold;")
                    btn.setText("X") # Treffer

    # ----------------- SCHIESSEN & RADAR -----------------
    def on_radar_cell_click(self, r, c):
        if self.placement_phase:
            QMessageBox.warning(self, "Warten", "Die Platzierungsphase läuft noch!")
            return

        # Ausgeschiedene Spieler dürfen nicht mehr schießen.
        if self.player_id not in self.active_players:
            return

        # STRENGE PRÜFUNG: Ist der Spieler wirklich an der Reihe?
        if self.current_turn != self.player_id:
            QMessageBox.warning(self, "Nicht dran!", "Du bist aktuell nicht an der Reihe!")
            return

        # Das automatische Ziel basierend auf der festen Reihenfolge ermitteln
        target_id = self.get_next_target_for(self.player_id)
        if not target_id:
            QMessageBox.warning(self, "Fehler", "Kein gültiges Ziel gefunden!")
            return

        # Da man jetzt auch das Feld anderer (z.B. bereits aufgedeckter,
        # eliminierter) Spieler zum Ansehen auswaehlen kann, muss hier
        # geprueft werden, ob man auch WIRKLICH gerade das Pflichtziel
        # anschaut - sonst wuerde ein Klick auf ein nur angeschautes Feld
        # versehentlich einen Schuss auf das (unsichtbare) echte Ziel abgeben.
        viewed_id = self.combo_target_player.currentData()
        if viewed_id is None or int(viewed_id) != target_id:
            # Nach dem Ausscheiden eines Spielers kann dessen aufgedecktes
            # Feld noch im Radar sichtbar sein. Dieses Feld ist aber kein
            # gültiges Ziel mehr. Beim nächsten Schuss automatisch auf das
            # nächste aktive Ziel umschalten, damit der Spieler nicht auf
            # einem "toten" Feld hängen bleibt.
            idx = self.combo_target_player.findData(target_id)
            if idx >= 0:
                self.combo_target_player.setCurrentIndex(idx)
                self.update_radar_ui()
            return

        # Sicherstellen, dass das Grid für dieses Ziel existiert
        if target_id not in self.enemy_grids:
            self.enemy_grids[target_id] = [[0]*GRID_SIZE for _ in range(GRID_SIZE)]

        # Prüfen, ob Zelle bereits beschossen wurde
        target_grid = self.enemy_grids[target_id]
        if target_grid[r][c] != 0:
            QMessageBox.warning(self, "Bereits beschossen", "Auf dieses Feld hast du schon geschossen!")
            return

        # Schuss an den Host / die Mitspieler senden
        self.send_network_data({
            "type": "SHOOT",
            "from": self.player_id,
            "target": target_id,
            "row": r,
            "col": c
        })

    def update_radar_ui(self):
        target_id = self.combo_target_player.currentData()
        if target_id is None:
            return
        target_id = int(target_id)
        
        # Sicherheitsprüfung: Falls das Grid noch nicht existiert, erstellen
        if target_id not in self.enemy_grids:
            self.enemy_grids[target_id] = [[0]*GRID_SIZE for _ in range(GRID_SIZE)]

        grid = self.enemy_grids[target_id]

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                val = grid[r][c]
                btn = self.radar_buttons[r][c]
                if val == 0:
                    btn.setStyleSheet(self.EMPTY_CELL_STYLE)  # macOS-Fix, siehe oben (statt "")
                    btn.setText("")
                elif val == 2:
                    btn.setStyleSheet(
                        "background-color: #e0e0e0; color: black; "
                        "font-weight: bold;"
                    )
                    btn.setText("X")  # Fehlschuss
                elif val == 3:
                    btn.setStyleSheet(
                        "background-color: #e53935; color: white; "
                        "font-weight: bold; border: 2px solid #b71c1c;"
                    )
                    btn.setText("X")  # Treffer

    # ----------------- NETZWERK & RUNDEN LOGIK -----------------

    def start_network(self):
        ip = self.txt_ip.text().strip()
        port = int(self.txt_port.text())
        self.is_host = (self.role_combo.currentIndex() == 0)

        if self.is_host:
            self.num_players = int(self.combo_num_players.currentText().split(" ")[0])
            self.player_id = 1
            self.active_players = list(range(1, self.num_players + 1))
            self.players_ready = {1}
            self.current_turn = 1

            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((ip, port))
            self.server_socket.listen(self.num_players - 1)

            threading.Thread(target=self.accept_clients, daemon=True).start()
            self.lbl_status.setText(
                f"Lobby eröffnet! Warte auf {self.num_players - 1} weitere Spieler..."
            )
            self.top_frame.setEnabled(False)
        else:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                self.client_socket.connect((ip, port))
                self.recv_buffers[self.client_socket] = ""
                threading.Thread(target=self.listen_to_server, daemon=True).start()
                self.top_frame.setEnabled(False)
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Verbindung fehlgeschlagen:\n{str(e)}")

    def accept_clients(self):
        next_id = 2
        while next_id <= self.num_players:
            try:
                conn, addr = self.server_socket.accept()
                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.client_connections[next_id] = conn
                self.recv_buffers[conn] = ""
                print(f"Spieler {next_id} verbunden: {addr}")

                self.send_to_player(next_id, {
                    "type": "INIT",
                    "your_id": next_id,
                    "num_players": self.num_players
                })

                threading.Thread(
                    target=self.listen_to_client,
                    args=(conn, next_id),
                    daemon=True
                ).start()
                next_id += 1
            except Exception as e:
                print(f"Fehler beim Annehmen eines Clients: {e}")
                break

    def _process_received_data(self, data, source):
        buffer = self.recv_buffers.get(source, "") + data
        messages = buffer.split("\n")
        self.recv_buffers[source] = messages.pop()

        for line in messages:
            line = line.strip()
            if not line:
                continue
            try:
                self.signals.data_received.emit(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"Ungültige Netzwerk-Nachricht: {e} | {line!r}")

    def listen_to_client(self, conn, p_id):
        while True:
            try:
                data = conn.recv(4096)
                if not data:
                    break
                self._process_received_data(data.decode("utf-8"), conn)
            except Exception as e:
                print(f"Verbindung zu Spieler {p_id} beendet: {e}")
                break
        self.recv_buffers.pop(conn, None)
        self.client_connections.pop(p_id, None)
        # WICHTIG: Diese Methode laeuft in einem Hintergrund-Thread, darf also
        # NIE direkt GUI-Zustand aendern. Stattdessen ganz normal ueber den
        # Signal-Mechanismus an handle_network_data() melden (das laeuft
        # zuverlaessig im Hauptthread, wie jede andere Netzwerknachricht auch).
        self.signals.data_received.emit({"type": "_PLAYER_DISCONNECTED", "player": p_id})

    def listen_to_server(self):
        while True:
            try:
                data = self.client_socket.recv(4096)
                if not data:
                    break
                self._process_received_data(data.decode("utf-8"), self.client_socket)
            except Exception as e:
                print(f"Verbindung zum Host beendet: {e}")
                break
        self.recv_buffers.pop(self.client_socket, None)
        self.signals.data_received.emit({"type": "_HOST_CONNECTION_LOST"})

    def _send_raw(self, conn, msg_dict):
        raw = (json.dumps(msg_dict, separators=(",", ":")) + "\n").encode("utf-8")
        try:
            with self.send_lock:
                conn.sendall(raw)
            return True
        except Exception as e:
            print(f"Netzwerk senden fehlgeschlagen: {e}")
            return False

    def send_to_player(self, player_id, msg_dict):
        if self.is_host and player_id == self.player_id:
            self.signals.data_received.emit(msg_dict)
            return True
        if not self.is_host:
            return False
        conn = self.client_connections.get(player_id)
        if conn is None:
            print(f"Kein Netzwerkkanal für Spieler {player_id}")
            return False
        return self._send_raw(conn, msg_dict)

    def send_network_data(self, msg_dict):
        if self.is_host:
            self.signals.data_received.emit(msg_dict)
            for pid in list(self.client_connections):
                self.send_to_player(pid, msg_dict)
        else:
            self._send_raw(self.client_socket, msg_dict)

    def broadcast(self, msg_dict):
        self.signals.data_received.emit(msg_dict)
        for pid in list(self.client_connections):
            self.send_to_player(pid, msg_dict)

    # ----------------- SPIEL-NACHRICHTEN -----------------

    def handle_network_data(self, msg):
        mtype = msg.get("type")

        if mtype == "INIT":
            self.player_id = int(msg["your_id"])
            self.num_players = int(msg["num_players"])
            self.active_players = list(range(1, self.num_players + 1))
            self.current_turn = 1
            self.lbl_status.setText(
                f"Verbunden als Spieler {self.player_id}! Platziere deine Schiffe."
            )
            self.setup_target_dropdown()

        elif mtype == "READY":
            if not self.is_host:
                return
            p = int(msg.get("player", 0))
            if p in self.active_players:
                self.players_ready.add(p)

            print(f"READY: {sorted(self.players_ready)} / {len(self.active_players)}")

            # Gegen die noch AKTIVEN Spieler pruefen, nicht gegen die urspruengliche
            # Gesamtzahl - sonst wartet das Spiel ewig auf ein READY von jemandem,
            # der waehrend der Platzierungsphase bereits die Verbindung verloren hat.
            if self.active_players and len(self.players_ready) == len(self.active_players):
                print("ALLE BEREIT -> START_GAME")
                self.broadcast({"type": "START_GAME", "first_turn": self.active_players[0]})

        elif mtype == "START_GAME":
            self.placement_phase = False
            self.current_turn = int(msg.get("first_turn", 1))
            self.enemy_grids.clear()

            for pid in self.active_players:
                if pid != self.player_id:
                    self.enemy_grids[pid] = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]

            self.setup_target_dropdown()
            self.update_turn_status()
            self.update_radar_ui()

        elif mtype == "SHOOT":
            # Alleen de host beslist of een schot geldig is.
            if not self.is_host:
                return

            shooter = int(msg["from"])
            target = int(msg["target"])
            r = int(msg["row"])
            c = int(msg["col"])

            if shooter != self.current_turn:
                print(f"Schuss ignoriert: {shooter} ist nicht dran, sondern {self.current_turn}.")
                return

            if shooter not in self.active_players:
                return

            expected_target = self.get_next_target_for(shooter)
            if target != expected_target:
                print(f"Falsches Ziel: {shooter} darf nur auf {expected_target} schießen.")
                return

            if not (0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE):
                return

            # Host schickt den Schuss an den Zielspieler.
            self.send_to_player(target, {
                "type": "CHECK_SHOT",
                "shooter": shooter,
                "target": target,
                "row": r,
                "col": c
            })

        elif mtype == "CHECK_SHOT":
            if self.player_id != int(msg["target"]):
                return

            r = int(msg["row"])
            c = int(msg["col"])
            hit = (self.my_grid[r][c] == 1)

            # Zielspieler markiert sein eigenes Feld sofort.
            self.my_grid[r][c] = 3 if hit else 2
            self.update_my_grid_ui()

            has_ships = any(1 in row for row in self.my_grid)

            # WICHTIG: Erst die eigene Statusmeldung setzen, DANN senden.
            # Grund: send_network_data() loest beim Host synchron/verschachtelt
            # die Kette SHOT_RESULT -> TURN_CHANGE -> update_turn_status() aus
            # (kein echter Netzwerk-Umweg noetig, wenn man an sich selbst sendet).
            # Stand die GETROFFEN-Meldung hier VOR dem send-Aufruf, wurde die
            # "Du bist dran"-Meldung aus dieser verschachtelten Kette sofort
            # wieder ueberschrieben, bevor der Host sie je zu sehen bekam.
            self.lbl_status.setText(
                "💥 GETROFFEN! Dein Schiff wurde getroffen."
                if hit else
                "🌊 FEHLSCHUSS! Wasser."
            )

            self.send_network_data({
                "type": "SHOT_RESULT",
                "shooter": int(msg["shooter"]),
                "target": self.player_id,
                "row": r,
                "col": c,
                "hit": hit,
                "eliminated": not has_ships,
                # Wenn ich ausscheide, gebe ich auch mein bisheriges
                # Angriffs-Radar weiter. Damit der naechste Spieler nicht
                # wieder mit einem komplett leeren Radar anfangen muss.
                "handover_grids": (
                    {
                        str(pid): grid
                        for pid, grid in self.enemy_grids.items()
                        if pid != self.player_id
                    }
                    if not has_ships else None
                ),
                # Mein komplettes Feld wird beim Ausscheiden ebenfalls
                # aufgedeckt.
                "full_grid": self.my_grid if not has_ships else None
            })

        elif mtype == "SHOT_RESULT":
            # Nur der Host verarbeitet das Ergebnis und bestimmt den nächsten Spieler.
            if not self.is_host:
                return

            shooter = int(msg["shooter"])
            target = int(msg["target"])
            r = int(msg["row"])
            c = int(msg["col"])
            hit = bool(msg["hit"])
            eliminated = bool(msg["eliminated"])

            if eliminated and target in self.active_players:
                self.active_players.remove(target)
                print(
                    f"Spieler {target} ist ausgeschieden. "
                    f"Aktive Spieler: {self.active_players}"
                )

                full_grid = msg.get("full_grid")
                handover_grids = msg.get("handover_grids") or {}

                if full_grid is not None:
                    # Das komplette Feld des Ausgeschiedenen aufdecken.
                    self.broadcast({
                        "type": "PLAYER_ELIMINATED",
                        "player": target,
                        "full_grid": full_grid
                    })

                # Die Schuss-Erkenntnisse des ausgeschiedenen Spielers
                # bleiben im Spiel erhalten. Jeder verbleibende Spieler
                # bekommt sie; beim Zielwechsel wird dadurch kein neues
                # leeres Radar erzwungen.
                if handover_grids:
                    self.broadcast({
                        "type": "RADAR_HANDOVER",
                        "from_player": target,
                        "grids": handover_grids,
                        "active_players": self.active_players
                    })

            # Ergebnis nur an den Schützen.
            self.send_to_player(shooter, {
                "type": "RESULT",
                "shooter": shooter,
                "target": target,
                "row": r,
                "col": c,
                "hit": hit,
                "eliminated": eliminated
            })

            # WICHTIG: Alle Rechner müssen dieselbe aktive Spielerliste haben.
            if len(self.active_players) == 1:
                self.broadcast({
                    "type": "GAME_OVER",
                    "winner": self.active_players[0],
                    "active_players": self.active_players
                })
                return

            # Exakte Reihenfolge unter den NOCH AKTIVEN Spielern:
            # 1 -> 2 -> 3 -> 1, und wenn jemand raus ist z.B. 1 -> 3 -> 1.
            if shooter in self.active_players:
                idx = self.active_players.index(shooter)
            else:
                idx = 0

            next_turn = self.active_players[(idx + 1) % len(self.active_players)]
            self.current_turn = next_turn

            self.broadcast({
                "type": "TURN_CHANGE",
                "next_turn": next_turn,
                "active_players": self.active_players
            })

        elif mtype == "PLAYER_ELIMINATED":
            pid = int(msg["player"])
            full_grid = msg.get("full_grid")
            if full_grid is not None and pid != self.player_id:
                # Komplettes Feld des Ausgeschiedenen uebernehmen (ersetzt
                # den bisherigen, moeglicherweise leeren/unvollstaendigen
                # Stand) - jede Zelle mit Schiff (1) wird als bereits
                # getroffen (3) angezeigt, Wasser bleibt Wasser/unbekannt (0),
                # damit man sofort weiterschiessen kann, ohne bereits
                # versenkte Schiffe erneut anvisieren zu muessen.
                revealed = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
                for rr in range(GRID_SIZE):
                    for cc in range(GRID_SIZE):
                        revealed[rr][cc] = 3 if full_grid[rr][cc] in (1, 3) else full_grid[rr][cc]
                self.enemy_grids[pid] = revealed
                # Liste neu aufbauen, DAMIT der aufgedeckte Spieler ueberhaupt
                # als waehlbarer Eintrag auftaucht (vorher wurden nur die
                # Daten aktualisiert, aber der Dropdown-Eintrag selbst kam
                # nie dazu - das war der eigentliche Grund, warum das Feld
                # erst viel spaeter/zufaellig sichtbar wurde).
                self.setup_target_dropdown()
            self.lbl_status.setText(f"☠️ Spieler {pid} ist ausgeschieden! Sein Feld wurde aufgedeckt.")

        elif mtype == "RADAR_HANDOVER":
            # Das Angriffs-Wissen des ausgeschiedenen Spielers uebernehmen.
            # Es wird mit unserem eigenen Wissen zusammengefuehrt:
            # Treffer/Fehlschuesse, die wir schon kennen, bleiben erhalten.
            grids = msg.get("grids") or {}

            for target_key, incoming in grids.items():
                try:
                    target_id = int(target_key)
                except (TypeError, ValueError):
                    continue

                if target_id == self.player_id:
                    continue

                if target_id not in self.active_players:
                    continue

                if target_id not in self.enemy_grids:
                    self.enemy_grids[target_id] = [
                        [0] * GRID_SIZE for _ in range(GRID_SIZE)
                    ]

                current = self.enemy_grids[target_id]

                for rr in range(min(GRID_SIZE, len(incoming))):
                    for cc in range(min(GRID_SIZE, len(incoming[rr]))):
                        # 3 = Treffer und 2 = Fehlschuss sind echte
                        # Erkenntnisse. Niemals ein bekanntes Feld loeschen.
                        if incoming[rr][cc] in (2, 3):
                            current[rr][cc] = incoming[rr][cc]

            self.setup_target_dropdown()
            self.update_radar_ui()

            if self.player_id in self.active_players:
                self.lbl_status.setText(
                    "📡 Schusswissen des ausgeschiedenen Spielers übernommen."
                )

        elif mtype == "RESULT":
            shooter = int(msg["shooter"])
            if shooter != self.player_id:
                return

            target = int(msg["target"])
            r = int(msg["row"])
            c = int(msg["col"])
            hit = bool(msg["hit"])

            if target not in self.enemy_grids:
                self.enemy_grids[target] = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]

            # Im Angriffs-Radar wird ein Treffer deutlich ROT angezeigt.
            self.enemy_grids[target][r][c] = 3 if hit else 2
            self.update_radar_ui()

            self.lbl_status.setText(
                f"💥 TREFFER! Spieler {target} wurde getroffen."
                if hit else
                f"🌊 FEHLSCHUSS gegen Spieler {target}."
            )

        elif mtype == "TURN_CHANGE":
            self.current_turn = int(msg["next_turn"])

            if "active_players" in msg:
                self.active_players = [int(x) for x in msg["active_players"]]

            # Wenn ich ausgeschieden bin, darf ich nicht mehr schießen.
            #if self.player_id not in self.active_players:
                #self.current_turn = -1

            self.setup_target_dropdown()
            self.update_turn_status()
            self.update_radar_ui()

            # Nach einem ausgeschiedenen Host oder anderen Spieler wird das
            # Radar sofort auf das nächste aktive Ziel gesetzt.
            if self.player_id in self.active_players and self.current_turn == self.player_id:
                target_id = self.get_next_target_for(self.player_id)
                if target_id is not None:
                    idx = self.combo_target_player.findData(target_id)
                    if idx >= 0:
                        self.combo_target_player.setCurrentIndex(idx)
                        self.update_radar_ui()

        elif mtype == "_PLAYER_DISCONNECTED":
            # Nur der Host trifft Entscheidungen ueber den Spielzustand.
            if not self.is_host:
                return
            pid = int(msg["player"])
            if pid not in self.active_players:
                return  # war schon vorher raus (z.B. schon eliminiert)

            was_their_turn = (self.current_turn == pid)
            self.active_players.remove(pid)
            self.players_ready.discard(pid)
            print(
                f"Spieler {pid} hat die Verbindung verloren. "
                f"Aktive Spieler: {self.active_players}"
            )

            if self.placement_phase:
                # Spiel hat noch nicht begonnen (Lobby/Schiffe-Platzieren):
                # nur austragen und pruefen, ob die Verbleibenden jetzt
                # vollzaehlig bereit sind - kein Zug/Sieg-Handling noetig,
                # das ergibt vor Spielbeginn keinen Sinn.
                self.broadcast({
                    "type": "PLAYER_LEFT",
                    "player": pid,
                    "active_players": self.active_players
                })
                if self.active_players and len(self.players_ready) == len(self.active_players):
                    print("ALLE VERBLEIBENDEN BEREIT -> START_GAME")
                    self.broadcast({"type": "START_GAME", "first_turn": self.active_players[0]})
                return

            # Ab hier: laeuft bereits ein aktives Spiel.
            self.broadcast({
                "type": "PLAYER_LEFT",
                "player": pid,
                "active_players": self.active_players
            })

            if len(self.active_players) <= 1:
                if self.active_players:
                    self.broadcast({
                        "type": "GAME_OVER",
                        "winner": self.active_players[0],
                        "active_players": self.active_players
                    })
                return

            if was_their_turn:
                # Gleiche Logik wie bei einer regulaeren Elimination: naechster
                # Spieler in der Reihenfolge der noch aktiven Spieler.
                next_turn = self.active_players[0]
                self.current_turn = next_turn
                self.broadcast({
                    "type": "TURN_CHANGE",
                    "next_turn": next_turn,
                    "active_players": self.active_players
                })

        elif mtype == "PLAYER_LEFT":
            pid = int(msg["player"])
            if "active_players" in msg:
                self.active_players = [int(x) for x in msg["active_players"]]
            self.lbl_status.setText(f"🔌 Spieler {pid} hat die Verbindung verloren und scheidet aus.")

        elif mtype == "_HOST_CONNECTION_LOST":
            self.current_turn = -1
            self.combo_target_player.setEnabled(False)
            self.lbl_status.setText(
                "🔌 Verbindung zum Host verloren. Das Spiel kann nicht fortgesetzt werden."
            )

        elif mtype == "GAME_OVER":
            winner = int(msg["winner"])

            if "active_players" in msg:
                self.active_players = [int(x) for x in msg["active_players"]]

            self.current_turn = -1
            self.combo_target_player.setEnabled(False)
            self.btn_play_again.setVisible(True)

            self.lbl_status.setText(
                "🏆 DU HAST GEWONNEN!"
                if winner == self.player_id
                else f"🏆 Spieler {winner} hat gewonnen."
            )

        elif mtype == "REQUEST_RESTART":
            # Jeder Spieler darf ein neues Spiel anstossen - der Host
            # bestaetigt und verteilt den Reset an alle (inkl. sich selbst).
            if not self.is_host:
                return
            self.players_ready = set()
            self.broadcast({"type": "RESTART"})

        elif mtype == "RESTART":
            self.reset_for_new_game()

    def advance_turn(self):
        # Nur als Kompatibilität für alten Code.
        if not self.is_host or not self.active_players:
            return
        idx = self.active_players.index(self.current_turn)
        next_turn = self.active_players[(idx + 1) % len(self.active_players)]
        self.current_turn = next_turn
        self.broadcast({"type": "TURN_CHANGE", "next_turn": next_turn})

    def request_restart(self):
        self.btn_play_again.setVisible(False)
        self.send_network_data({"type": "REQUEST_RESTART", "player": self.player_id})

    def reset_for_new_game(self):
        """Setzt die komplette Partie zurueck auf die Schiffsplatzierungs-
        Phase, ohne dass die App neu gestartet werden muss. Wird bei ALLEN
        Spielern (inkl. Host, ueber den normalen broadcast()-Weg) aufgerufen."""
        self.placement_phase = True
        self.placement_index = 0
        self.placement_orientation = 'H'
        self.my_grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.enemy_grids = {}
        self.active_players = list(range(1, self.num_players + 1))
        self.current_turn = 1

        self.btn_rotate.setText("Schiff Drehen: Horizontal [R]")
        self.btn_rotate.setEnabled(True)
        self.btn_auto_place.setEnabled(True)
        self.btn_play_again.setVisible(False)

        self.update_my_grid_ui()
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                btn = self.radar_buttons[r][c]
                btn.setStyleSheet(self.EMPTY_CELL_STYLE)
                btn.setText("")

        self.combo_target_player.clear()
        self.combo_target_player.setEnabled(False)

        self.lbl_status.setText(
            f"🔄 Neues Spiel! Platziere Schiff der Länge {SHIP_SIZES[0]}"
        )

    def setup_target_dropdown(self):
        try:
            self.combo_target_player.currentIndexChanged.disconnect(self.update_radar_ui)
        except TypeError:
            pass

        self.combo_target_player.clear()
        target_id = self.get_next_target_for(self.player_id)

        # Alle Spieler anzeigen, ueber die wir ueberhaupt Daten haben - also
        # sowohl noch aktive Gegner als auch bereits eliminierte, deren Feld
        # per PLAYER_ELIMINATED aufgedeckt wurde. Vorher stand hier nur das
        # eine aktuelle Pflichtziel - dadurch verschwand ein gerade
        # eliminierter Spieler sofort wieder aus der Liste, bevor man sein
        # aufgedecktes Feld ueberhaupt zu sehen bekam.
        known_ids = sorted(set(self.enemy_grids.keys()) | ({target_id} if target_id else set()))
        for pid in known_ids:
            label = f"Spieler {pid}"
            if pid not in self.active_players:
                label += "  (ausgeschieden)"
            self.combo_target_player.addItem(label, userData=pid)

            # Ausgeschiedene Spieler bleiben zum Anschauen im Dropdown,
            # können aber nicht mehr als Schussziel ausgewählt werden.
            item_index = self.combo_target_player.count() - 1
            if pid not in self.active_players:
                self.combo_target_player.model().item(item_index).setEnabled(False)

        # Auf das aktuelle Pflichtziel voreinstellen (haeufigster Fall: man
        # will direkt darauf schiessen), die Liste bleibt aber bedienbar,
        # damit man sich zwischendurch auch andere/aufgedeckte Felder
        # anschauen kann.
        if target_id is not None:
            idx = self.combo_target_player.findData(target_id)
            if idx >= 0:
                self.combo_target_player.setCurrentIndex(idx)
        self.combo_target_player.setEnabled(self.combo_target_player.count() > 0)

        self.combo_target_player.currentIndexChanged.connect(self.update_radar_ui)
        self.update_radar_ui()

    def get_next_target_for(self, shooter_id):
        if shooter_id not in self.active_players or len(self.active_players) <= 1:
            return None
        idx = self.active_players.index(shooter_id)
        return self.active_players[(idx + 1) % len(self.active_players)]

    def update_turn_status(self):
        if self.player_id not in self.active_players:
            self.lbl_status.setText("☠️ Du bist ausgeschieden.")
            self.lbl_status.setStyleSheet(
                "color: #757575; font-weight: bold; font-size: 14px;"
            )
        elif self.current_turn == self.player_id:
            self.lbl_status.setText("👉 DU BIST DRAN! Wähle ein Feld und schieße!")
            self.lbl_status.setStyleSheet(
                "color: #2e7d32; font-weight: bold; font-size: 14px;"
            )
        else:
            self.lbl_status.setText(
                f"⏳ Spieler {self.current_turn} ist an der Reihe..."
            )
            self.lbl_status.setStyleSheet(
                "color: #c62828; font-weight: bold; font-size: 14px;"
            )

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = SchiffeVersenkenApp()
    win.show()
    sys.exit(app.exec_())