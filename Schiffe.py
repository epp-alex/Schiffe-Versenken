import sys
import socket
import threading
import json
import random
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QGridLayout, QMessageBox, QLineEdit, QComboBox, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QSettings
from PyQt5.QtGui import QFont

GRID_SIZE = 10
SHIP_SIZES = [4, 3, 2, 2, 1, 1, 1]  # 1x4, 1x3, 2x2, 3x1

# Kennung für die gespeicherten Einstellungen (z.B. gewählte Sprache).
# QSettings legt die Datei je nach Betriebssystem automatisch am richtigen
# Ort ab:
#   Windows: %APPDATA%\SchiffeVersenkenApp\SchiffeVersenken.ini
#   Linux:   ~/.config/SchiffeVersenkenApp/SchiffeVersenken.ini
#   macOS:   ~/Library/Preferences/SchiffeVersenkenApp/SchiffeVersenken.ini
SETTINGS_ORG = "SchiffeVersenkenApp"
SETTINGS_APP = "SchiffeVersenken"

# ====================================================================== #
#  ÜBERSETZUNGEN                                                          #
#                                                                          #
#  Um eine neue Sprache hinzuzufügen: einfach einen neuen Eintrag mit     #
#  demselben Schlüsselsatz wie "de"/"en" ergänzen (z. B. "fr": {...})     #
#  und den Sprachnamen unten in LANGUAGE_NAMES eintragen. Alle Stellen    #
#  im Code, die Text anzeigen, holen sich diesen über self._t(key, ...)   #
#  und passen sich automatisch an.                                       #
# ====================================================================== #
LANGUAGE_NAMES = {
    "de": "Deutsch",
    "en": "English",
    "fr": "Français",
    "ru": "Русский",
    "uk": "Українська",
    "pl": "Polski",
    "nl": "Nederlands",
    "el": "Ελληνικά",
    "tr": "Türkçe",
    "es": "Español",
    "it": "Italiano",
    "pt": "Português",
    "cs": "Čeština",
    "hu": "Magyar",
    "ro": "Română",
    "sv": "Svenska",
    "da": "Dansk",
    "no": "Norsk",
    "fi": "Suomi",
    "bg": "Български",
    "hr": "Hrvatski",
    "sr": "Српски",
    "sk": "Slovenčina",
    "lt": "Lietuvių",
    "lv": "Latviešu",
    "et": "Eesti",
}

LANG = {
    "de": {
        "app_title": "Multiplayer Schiffe Versenken Pro (2-4 Spieler)",
        "lbl_language": "Sprache:",
        "lbl_role": "Rolle:",
        "role_host": "Host (Spieler 1)",
        "role_client": "Client (Beitreten)",
        "lbl_players": "Anzahl Spieler:",
        "players_n": "{n} Spieler",
        "lbl_ip": "IP:",
        "btn_find_ip": "📍 IP finden",
        "tooltip_find_ip": "Ermittelt automatisch deine lokale Netzwerk-IP",
        "lbl_port": "Port:",
        "btn_connect": "Lobby Starten / Beitreten",
        "status_welcome": "Willkommen! Bitte erstelle eine Lobby oder tritt einer bei.",
        "btn_rotate_h": "Schiff Drehen: Horizontal [R]",
        "btn_rotate_v": "Schiff Drehen: Vertikal [R]",
        "btn_auto_place": "🎲 Auto-Platzieren",
        "btn_play_again": "🔄 Nochmal spielen",
        "lbl_my_fleet": "<b>DEINE FLOTTE (Eigenes Feld)</b>",
        "lbl_radar": "<b>ANGRIFFS-RADAR (Schießen)</b>",
        "lbl_target_player": "Ziel-Spieler:",

        "status_ip_found": "IP automatisch gefunden: {ip}",
        "dlg_ip_title": "IP-Erkennung",
        "dlg_ip_fail": "Konnte lokale IP nicht ermitteln: {err}",

        "status_place_ship": "Platziere Schiff der Länge {size}",
        "status_all_placed_wait": "Alle Schiffe platziert! Warte auf andere Spieler...",
        "dlg_invalid_title": "Ungültig",
        "dlg_invalid_ship": "Schiff passt hier nicht hin oder überlappt!",
        "status_auto_placed": "Alle Schiffe automatisch platziert (mit Abstand)! Bereitschaft gesendet.",

        "dlg_wait_title": "Warten",
        "dlg_wait_placement": "Die Platzierungsphase läuft noch!",
        "dlg_not_turn_title": "Nicht dran!",
        "dlg_not_turn_msg": "Du bist aktuell nicht an der Reihe!",
        "dlg_error_title": "Fehler",
        "dlg_no_target": "Kein gültiges Ziel gefunden!",
        "dlg_already_shot_title": "Bereits beschossen",
        "dlg_already_shot_msg": "Auf dieses Feld hast du schon geschossen!",

        "status_lobby_open": "Lobby eröffnet! Warte auf {n} weitere Spieler...",
        "dlg_conn_fail_msg": "Verbindung fehlgeschlagen:\n{err}",

        "status_connected": "Verbunden als Spieler {pid}! Platziere deine Schiffe.",
        "status_hit": "💥 GETROFFEN! Dein Schiff wurde getroffen.",
        "status_miss": "🌊 FEHLSCHUSS! Wasser.",
        "status_player_eliminated": "☠️ Spieler {pid} ist ausgeschieden! Sein Feld wurde aufgedeckt.",
        "status_radar_handover": "📡 Schusswissen des ausgeschiedenen Spielers übernommen.",
        "status_hit_on": "💥 TREFFER! Spieler {target} wurde getroffen.",
        "status_miss_on": "🌊 FEHLSCHUSS gegen Spieler {target}.",
        "status_player_left": "🔌 Spieler {pid} hat die Verbindung verloren und scheidet aus.",
        "status_host_lost": "🔌 Verbindung zum Host verloren. Das Spiel kann nicht fortgesetzt werden.",
        "status_you_won": "🏆 DU HAST GEWONNEN!",
        "status_player_won": "🏆 Spieler {winner} hat gewonnen.",
        "status_new_game": "🔄 Neues Spiel! Platziere Schiff der Länge {size}",

        "player_label": "Spieler {pid}",
        "eliminated_suffix": "  (ausgeschieden)",
        "status_eliminated_self": "☠️ Du bist ausgeschieden.",
        "status_your_turn": "👉 DU BIST DRAN! Wähle ein Feld und schieße!",
        "status_waiting_turn": "⏳ Spieler {pid} ist an der Reihe...",
    },
    "en": {
        "app_title": "Multiplayer Battleship Pro (2-4 Players)",
        "lbl_language": "Language:",
        "lbl_role": "Role:",
        "role_host": "Host (Player 1)",
        "role_client": "Client (Join)",
        "lbl_players": "Number of players:",
        "players_n": "{n} Players",
        "lbl_ip": "IP:",
        "btn_find_ip": "📍 Find IP",
        "tooltip_find_ip": "Automatically detects your local network IP",
        "lbl_port": "Port:",
        "btn_connect": "Start / Join Lobby",
        "status_welcome": "Welcome! Please create a lobby or join one.",
        "btn_rotate_h": "Rotate Ship: Horizontal [R]",
        "btn_rotate_v": "Rotate Ship: Vertical [R]",
        "btn_auto_place": "🎲 Auto-Place",
        "btn_play_again": "🔄 Play again",
        "lbl_my_fleet": "<b>YOUR FLEET (Own Board)</b>",
        "lbl_radar": "<b>ATTACK RADAR (Shoot)</b>",
        "lbl_target_player": "Target player:",

        "status_ip_found": "IP automatically found: {ip}",
        "dlg_ip_title": "IP Detection",
        "dlg_ip_fail": "Could not determine local IP: {err}",

        "status_place_ship": "Place ship of length {size}",
        "status_all_placed_wait": "All ships placed! Waiting for other players...",
        "dlg_invalid_title": "Invalid",
        "dlg_invalid_ship": "Ship doesn't fit here or overlaps another ship!",
        "status_auto_placed": "All ships placed automatically (with spacing)! Ready signal sent.",

        "dlg_wait_title": "Please wait",
        "dlg_wait_placement": "The placement phase is still in progress!",
        "dlg_not_turn_title": "Not your turn!",
        "dlg_not_turn_msg": "It's currently not your turn!",
        "dlg_error_title": "Error",
        "dlg_no_target": "No valid target found!",
        "dlg_already_shot_title": "Already shot here",
        "dlg_already_shot_msg": "You've already shot at this cell!",

        "status_lobby_open": "Lobby opened! Waiting for {n} more player(s)...",
        "dlg_conn_fail_msg": "Connection failed:\n{err}",

        "status_connected": "Connected as player {pid}! Place your ships.",
        "status_hit": "💥 HIT! Your ship was hit.",
        "status_miss": "🌊 MISS! Water.",
        "status_player_eliminated": "☠️ Player {pid} has been eliminated! Their board is revealed.",
        "status_radar_handover": "📡 Took over shot knowledge from the eliminated player.",
        "status_hit_on": "💥 HIT! Player {target} was hit.",
        "status_miss_on": "🌊 MISS against player {target}.",
        "status_player_left": "🔌 Player {pid} lost connection and has been eliminated.",
        "status_host_lost": "🔌 Lost connection to host. The game cannot continue.",
        "status_you_won": "🏆 YOU WON!",
        "status_player_won": "🏆 Player {winner} has won.",
        "status_new_game": "🔄 New game! Place ship of length {size}",

        "player_label": "Player {pid}",
        "eliminated_suffix": "  (eliminated)",
        "status_eliminated_self": "☠️ You have been eliminated.",
        "status_your_turn": "👉 YOUR TURN! Choose a cell and fire!",
        "status_waiting_turn": "⏳ Player {pid}'s turn...",
    },
    "fr": {
        "app_title": "Bataille Navale Pro Multijoueur (2-4 joueurs)",
        "lbl_language": "Langue :",
        "lbl_role": "Rôle :",
        "role_host": "Hôte (Joueur 1)",
        "role_client": "Client (Rejoindre)",
        "lbl_players": "Nombre de joueurs :",
        "players_n": "{n} joueurs",
        "lbl_ip": "IP :",
        "btn_find_ip": "📍 Trouver l'IP",
        "tooltip_find_ip": "Détecte automatiquement votre IP de réseau local",
        "lbl_port": "Port :",
        "btn_connect": "Créer / Rejoindre le salon",
        "status_welcome": "Bienvenue ! Veuillez créer un salon ou en rejoindre un.",
        "btn_rotate_h": "Pivoter le navire : Horizontal [R]",
        "btn_rotate_v": "Pivoter le navire : Vertical [R]",
        "btn_auto_place": "🎲 Placement automatique",
        "btn_play_again": "🔄 Rejouer",
        "lbl_my_fleet": "<b>VOTRE FLOTTE (Grille propre)</b>",
        "lbl_radar": "<b>RADAR D'ATTAQUE (Tirer)</b>",
        "lbl_target_player": "Joueur cible :",

        "status_ip_found": "IP trouvée automatiquement : {ip}",
        "dlg_ip_title": "Détection d'IP",
        "dlg_ip_fail": "Impossible de déterminer l'IP locale : {err}",

        "status_place_ship": "Placez le navire de taille {size}",
        "status_all_placed_wait": "Tous les navires sont placés ! En attente des autres joueurs...",
        "dlg_invalid_title": "Invalide",
        "dlg_invalid_ship": "Le navire ne rentre pas ici ou se chevauche !",
        "status_auto_placed": "Tous les navires sont placés automatiquement (avec espacement) ! Signal de prêt envoyé.",

        "dlg_wait_title": "Attendre",
        "dlg_wait_placement": "La phase de placement est toujours en cours !",
        "dlg_not_turn_title": "Pas votre tour !",
        "dlg_not_turn_msg": "Ce n'est pas votre tour actuellement !",
        "dlg_error_title": "Erreur",
        "dlg_no_target": "Aucune cible valide trouvée !",
        "dlg_already_shot_title": "Déjà ciblé",
        "dlg_already_shot_msg": "Vous avez déjà tiré sur cette case !",

        "status_lobby_open": "Salon créé ! En attente de {n} joueur(s) supplémentaire(s)...",
        "dlg_conn_fail_msg": "Échec de la connexion :\n{err}",

        "status_connected": "Connecté en tant que Joueur {pid} ! Placez vos navires.",
        "status_hit": "💥 TOUCHÉ ! Votre navire a été touché.",
        "status_miss": "🌊 MANQUÉ ! À l'eau.",
        "status_player_eliminated": "☠️ Le joueur {pid} est éliminé ! Sa grille a été révélée.",
        "status_radar_handover": "📡 Données de tir du joueur éliminé récupérées.",
        "status_hit_on": "💥 TOUCHÉ ! Le joueur {target} a été touché.",
        "status_miss_on": "🌊 MANQUÉ contre le joueur {target}.",
        "status_player_left": "🔌 Le joueur {pid} a perdu la connexion et est éliminé.",
        "status_host_lost": "🔌 Connexion à l'hôte perdue. La partie ne peut pas continuer.",
        "status_you_won": "🏆 VOUS AVEZ GAGNÉ !",
        "status_player_won": "🏆 Le joueur {winner} a gagné.",
        "status_new_game": "🔄 Nouvelle partie ! Placez le navire de taille {size}",

        "player_label": "Joueur {pid}",
        "eliminated_suffix": "  (éliminé)",
        "status_eliminated_self": "☠️ Vous êtes éliminé.",
        "status_your_turn": "👉 C'EST VOTRE TOUR ! Choisissez une case et tirez !",
        "status_waiting_turn": "⏳ C'est au tour du joueur {pid}...",
    },

"ru": {
        "app_title": "Мультиплеер Морской бой Pro (2-4 игрока)",
        "lbl_language": "Язык:",
        "lbl_role": "Роль:",
        "role_host": "Хост (Игрок 1)",
        "role_client": "Клиент (Войти)",
        "lbl_players": "Количество игроков:",
        "players_n": "{n} игроков",
        "lbl_ip": "IP:",
        "btn_find_ip": "📍 Найти IP",
        "tooltip_find_ip": "Автоматически определяет ваш локальный IP-адрес",
        "lbl_port": "Порт:",
        "btn_connect": "Создать / Войти в лобби",
        "status_welcome": "Добро пожаловать! Пожалуйста, создайте лобби или подключитесь к существующему.",
        "btn_rotate_h": "Повернуть корабль: Горизонтально [R]",
        "btn_rotate_v": "Повернуть корабль: Вертикально [R]",
        "btn_auto_place": "🎲 Авто-расстановка",
        "btn_play_again": "🔄 Играть снова",
        "lbl_my_fleet": "<b>ВАШ ФЛОТ (Свое поле)</b>",
        "lbl_radar": "<b>РАДАР АТАКИ (Стрельба)</b>",
        "lbl_target_player": "Цель:",

        "status_ip_found": "IP автоматически найден: {ip}",
        "dlg_ip_title": "Определение IP",
        "dlg_ip_fail": "Не удалось определить локальный IP: {err}",

        "status_place_ship": "Разместите корабль длиной {size}",
        "status_all_placed_wait": "Все корабли размещены! Ожидание других игроков...",
        "dlg_invalid_title": "Недействительно",
        "dlg_invalid_ship": "Корабль не помещается здесь или перекрывает другой!",
        "status_auto_placed": "Все корабли автоматически размещены (с соблюдением дистанции)! Сигнал готовности отправлен.",

        "dlg_wait_title": "Ожидание",
        "dlg_wait_placement": "Фаза расстановки еще продолжается!",
        "dlg_not_turn_title": "Не ваш ход!",
        "dlg_not_turn_msg": "Сейчас не ваш ход!",
        "dlg_error_title": "Ошибка",
        "dlg_no_target": "Не найдено валидной цели!",
        "dlg_already_shot_title": "Уже обстреляно",
        "dlg_already_shot_msg": "Вы уже стреляли по этой клетке!",

        "status_lobby_open": "Лобби создано! Ожидание еще {n} игроков...",
        "dlg_conn_fail_msg": "Ошибка подключения:\n{err}",

        "status_connected": "Подключено как Игрок {pid}! Расставьте свои корабли.",
        "status_hit": "💥 ПОПАДАНИЕ! Ваш корабль подбит.",
        "status_miss": "🌊 МИМО! Вода.",
        "status_player_eliminated": "☠️ Игрок {pid} выбыл! Его поле раскрыто.",
        "status_radar_handover": "📡 Данные о выстрелах выбывшего игрока получены.",
        "status_hit_on": "💥 ПОПАДАНИЕ! Игрок {target} подбит.",
        "status_miss_on": "🌊 МИМО по игроку {target}.",
        "status_player_left": "🔌 Игрок {pid} потерял соединение и выбыл.",
        "status_host_lost": "🔌 Соединение с хостом потеряно. Игра не может быть продолжена.",
        "status_you_won": "🏆 ВЫ ПОБЕДИЛИ!",
        "status_player_won": "🏆 Игрок {winner} победил.",
        "status_new_game": "🔄 Новая игра! Разместите корабль длиной {size}",

        "player_label": "Игрок {pid}",
        "eliminated_suffix": "  (выбыл)",
        "status_eliminated_self": "☠️ Вы выбыли.",
        "status_your_turn": "👉 ВАШ ХОД! Выберите клетку и стреляйте!",
        "status_waiting_turn": "⏳ Ходит игрок {pid}...",
    },
    "uk": {
        "app_title": "Мультиплеєр Морський бій Pro (2-4 гравці)",
        "lbl_language": "Мова:",
        "lbl_role": "Роль:",
        "role_host": "Хост (Гравець 1)",
        "role_client": "Клієнт (Приєднатися)",
        "lbl_players": "Кількість гравців:",
        "players_n": "{n} гравців",
        "lbl_ip": "IP:",
        "btn_find_ip": "📍 Знайти IP",
        "tooltip_find_ip": "Автоматично визначає вашу локальну IP-адресу",
        "lbl_port": "Порт:",
        "btn_connect": "Створити / Приєднатися до лобі",
        "status_welcome": "Ласкаво просимо! Будь ласка, створіть лобі або приєднайтеся до існуючого.",
        "btn_rotate_h": "Повернути корабель: Горизонтально [R]",
        "btn_rotate_v": "Повернути корабель: Вертикально [R]",
        "btn_auto_place": "🎲 Авто-розстановка",
        "btn_play_again": "🔄 Грати знову",
        "lbl_my_fleet": "<b>ВАШ ФЛОТ (Власне поле)</b>",
        "lbl_radar": "<b>РАДАР АТАКИ (Стрільба)</b>",
        "lbl_target_player": "Ціль:",

        "status_ip_found": "IP автоматично знайдено: {ip}",
        "dlg_ip_title": "Визначення IP",
        "dlg_ip_fail": "Не вдалося визначити локальний IP: {err}",

        "status_place_ship": "Розмістіть корабель довжиною {size}",
        "status_all_placed_wait": "Усі кораблі розміщено! Очікування інших гравців...",
        "dlg_invalid_title": "Недійсно",
        "dlg_invalid_ship": "Корабель не вміщується тут або перекриває інший!",
        "status_auto_placed": "Усі кораблі автоматично розміщено (з дотриманням відстані)! Сигнал готовності відправлено.",

        "dlg_wait_title": "Очікування",
        "dlg_wait_placement": "Фаза розстановки ще триває!",
        "dlg_not_turn_title": "Не ваш хід!",
        "dlg_not_turn_msg": "Зараз не ваш хід!",
        "dlg_error_title": "Помилка",
        "dlg_no_target": "Не знайдено дійсної цілі!",
        "dlg_already_shot_title": "Вже обстріляно",
        "dlg_already_shot_msg": "Ви вже стріляли по цій клітинці!",

        "status_lobby_open": "Лобі створено! Очікування ще {n} гравців...",
        "dlg_conn_fail_msg": "Помилка підключення:\n{err}",

        "status_connected": "Підключено як Гравець {pid}! Розставте свої кораблі.",
        "status_hit": "💥 ВЛУЧАННЯ! Ваш корабель підбито.",
        "status_miss": "🌊 МИМО! Вода.",
        "status_player_eliminated": "☠️ Гравець {pid} вибув! Його поле відкрито.",
        "status_radar_handover": "📡 Дані про постріли гравця, який вибув, отримано.",
        "status_hit_on": "💥 ВЛУЧАННЯ! Гравця {target} підбито.",
        "status_miss_on": "🌊 МИМО по гравцю {target}.",
        "status_player_left": "🔌 Гравець {pid} втратив з'єднання та вибув.",
        "status_host_lost": "🔌 З'єднання з хостом втрачено. Гра не може бути продовжена.",
        "status_you_won": "🏆 ВИ ПЕРЕМОГЛИ!",
        "status_player_won": "🏆 Гравець {winner} переміг.",
        "status_new_game": "🔄 Нова гра! Розмістіть корабель довжиною {size}",

        "player_label": "Гравець {pid}",
        "eliminated_suffix": "  (вибув)",
        "status_eliminated_self": "☠️ Ви вибули.",
        "status_your_turn": "👉 ВАШ ХІД! Оберіть клітинку та стріляйте!",
        "status_waiting_turn": "⏳ Ходить гравець {pid}...",
    },

"pl": {
        "app_title": "Wieloosobowa Gra w Statki Pro (2-4 graczy)",
        "lbl_language": "Język:",
        "lbl_role": "Rola:",
        "role_host": "Host (Gracz 1)",
        "role_client": "Klient (Dołącz)",
        "lbl_players": "Liczba graczy:",
        "players_n": "{n} graczy",
        "lbl_ip": "IP:",
        "btn_find_ip": "📍 Znajdź IP",
        "tooltip_find_ip": "Automatycznie wykrywa Twój lokalny adres IP",
        "lbl_port": "Port:",
        "btn_connect": "Stwórz / Dołącz do lobby",
        "status_welcome": "Witamy! Utwórz lobby lub dołącz do istniejącego.",
        "btn_rotate_h": "Obróć statek: Poziomo [R]",
        "btn_rotate_v": "Obróć statek: Pionowo [R]",
        "btn_auto_place": "🎲 Automatyczne rozmieszczenie",
        "btn_play_again": "🔄 Zagraj ponownie",
        "lbl_my_fleet": "<b>TWOJA FLOTA (Własna plansza)</b>",
        "lbl_radar": "<b>RADAR ATAKU (Strzelanie)</b>",
        "lbl_target_player": "Gracz docelowy:",

        "status_ip_found": "Automatycznie znaleziono IP: {ip}",
        "dlg_ip_title": "Wykrywanie IP",
        "dlg_ip_fail": "Nie udało się ustalić lokalnego IP: {err}",

        "status_place_ship": "Umieść statek o długości {size}",
        "status_all_placed_wait": "Wszystkie statki umieszczone! Oczekiwanie na innych graczy...",
        "dlg_invalid_title": "Nieprawidłowe",
        "dlg_invalid_ship": "Statek tu nie pasuje lub nachodzi na inny!",
        "status_auto_placed": "Wszystkie statki automatycznie rozmieszczone (z zachowaniem odstępu)! Sygnał gotowości wysłany.",

        "dlg_wait_title": "Czekaj",
        "dlg_wait_placement": "Faza rozmieszczania wciąż trwa!",
        "dlg_not_turn_title": "Nie Twoja kolej!",
        "dlg_not_turn_msg": "Obecnie nie jest Twoja kolej!",
        "dlg_error_title": "Błąd",
        "dlg_no_target": "Nie znaleziono prawidłowego celu!",
        "dlg_already_shot_title": "Już ostrzelane",
        "dlg_already_shot_msg": "Już strzelałeś w to pole!",

        "status_lobby_open": "Lobby otwarte! Oczekiwanie na jeszcze {n} graczy...",
        "dlg_conn_fail_msg": "Połączenie nie powiodło się:\n{err}",

        "status_connected": "Połączono jako Gracz {pid}! Rozmieść swoje statki.",
        "status_hit": "💥 TRAFIONY! Twój statek został trafiony.",
        "status_miss": "🌊 PUDŁO! Woda.",
        "status_player_eliminated": "☠️ Gracz {pid} został wyeliminowany! Jego plansza została odsłonięta.",
        "status_radar_handover": "📡 Przejęto dane o strzałach wyeliminowanego gracza.",
        "status_hit_on": "💥 TRAFIENIE! Gracz {target} został trafiony.",
        "status_miss_on": "🌊 PUDŁO w gracza {target}.",
        "status_player_left": "🔌 Gracz {pid} stracił połączenie i został wyeliminowany.",
        "status_host_lost": "🔌 Utracono połączenie z hostem. Gra nie może być kontynuowana.",
        "status_you_won": "🏆 WYGRAŁEŚ!",
        "status_player_won": "🏆 Gracz {winner} wygrał.",
        "status_new_game": "🔄 Nowa gra! Umieść statek o długości {size}",

        "player_label": "Gracz {pid}",
        "eliminated_suffix": "  (wyeliminowany)",
        "status_eliminated_self": "☠️ Zostałeś wyeliminowany.",
        "status_your_turn": "👉 TWOJA KOLEJ! Wybierz pole i strzelaj!",
        "status_waiting_turn": "⏳ Kolej gracza {pid}...",
    },
    "nl": {
        "app_title": "Multiplayer Zeeslag Pro (2-4 spelers)",
        "lbl_language": "Taal:",
        "lbl_role": "Rol:",
        "role_host": "Host (Speler 1)",
        "role_client": "Client (Deelnemen)",
        "lbl_players": "Aantal spelers:",
        "players_n": "{n} spelers",
        "lbl_ip": "IP:",
        "btn_find_ip": "📍 IP zoeken",
        "tooltip_find_ip": "Detecteert automatisch je lokale netwerk-IP",
        "lbl_port": "Poort:",
        "btn_connect": "Lobby starten / Deelnemen",
        "status_welcome": "Welkom! Maak een lobby aan of neem deel aan een bestaande.",
        "btn_rotate_h": "Schip draaien: Horizontaal [R]",
        "btn_rotate_v": "Schip draaien: Verticaal [R]",
        "btn_auto_place": "🎲 Automatisch plaatsen",
        "btn_play_again": "🔄 Opnieuw spelen",
        "lbl_my_fleet": "<b>JOUW VLOOT (Eigen bord)</b>",
        "lbl_radar": "<b>AANVALSRADAR (Schieten)</b>",
        "lbl_target_player": "Doelspeler:",

        "status_ip_found": "IP automatisch gevonden: {ip}",
        "dlg_ip_title": "IP-detectie",
        "dlg_ip_fail": "Kon lokaal IP niet bepalen: {err}",

        "status_place_ship": "Plaats schip van lengte {size}",
        "status_all_placed_wait": "Alle schepen geplaatst! Wachten op andere spelers...",
        "dlg_invalid_title": "Ongeldig",
        "dlg_invalid_ship": "Schip past hier niet of overlapt!",
        "status_auto_placed": "Alle schepen automatisch geplaatst (met afstand)! Gereed-signaal verzonden.",

        "dlg_wait_title": "Wachten",
        "dlg_wait_placement": "De plaatsingsfase is nog bezig!",
        "dlg_not_turn_title": "Niet jouw beurt!",
        "dlg_not_turn_msg": "Het is momenteel niet jouw beurt!",
        "dlg_error_title": "Fout",
        "dlg_no_target": "Geen geldig doel gevonden!",
        "dlg_already_shot_title": "Al beschoten",
        "dlg_already_shot_msg": "Je hebt al op dit vakje geschoten!",

        "status_lobby_open": "Lobby geopend! Wachten op nog {n} speler(s)...",
        "dlg_conn_fail_msg": "Verbinding mislukt:\n{err}",

        "status_connected": "Verbonden als Speler {pid}! Plaats je schepen.",
        "status_hit": "💥 GERAAKT! Je schip is geraakt.",
        "status_miss": "🌊 MIS! Water.",
        "status_player_eliminated": "☠️ Speler {pid} is uitgeschakeld! Zijn bord is onthuld.",
        "status_radar_handover": "📡 Schotgegevens van uitgeschakelde speler overgenomen.",
        "status_hit_on": "💥 RAAK! Speler {target} is geraakt.",
        "status_miss_on": "🌊 MIS tegen speler {target}.",
        "status_player_left": "🔌 Speler {pid} heeft de verbinding verloren en is uitgeschakeld.",
        "status_host_lost": "🔌 Verbinding met host verloren. Het spel kan niet worden voortgezet.",
        "status_you_won": "🏆 JE HEBT GEWONNEN!",
        "status_player_won": "🏆 Speler {winner} heeft gewonnen.",
        "status_new_game": "🔄 Nieuw spel! Plaats schip van lengte {size}",

        "player_label": "Speler {pid}",
        "eliminated_suffix": "  (uitgeschakeld)",
        "status_eliminated_self": "☠️ Je bent uitgeschakeld.",
        "status_your_turn": "👉 JOUW BEURT! Kies een vakje en schiet!",
        "status_waiting_turn": "⏳ Speler {pid} is aan de beurt...",
    },
"el": {
        "app_title": "Πολλαπλών Παικτών Ναυμαχία Pro (2-4 παίκτες)",
        "lbl_language": "Γλώσσα:",
        "lbl_role": "Ρόλος:",
        "role_host": "Host (Παίκτης 1)",
        "role_client": "Client (Σύνδεση)",
        "lbl_players": "Αριθμός παικτών:",
        "players_n": "{n} παίκτες",
        "lbl_ip": "IP:",
        "btn_find_ip": "📍 Εύρεση IP",
        "tooltip_find_ip": "Εντοπίζει αυτόματα την τοπική IP δικτύου σας",
        "lbl_port": "Θύρα:",
        "btn_connect": "Δημιουργία / Σύνδεση σε Lobby",
        "status_welcome": "Καλώς ήρθατε! Παρακαλώ δημιουργήστε ένα lobby ή συνδεθείτε σε ένα υπάρχον.",
        "btn_rotate_h": "Περιστροφή πλοίου: Οριζόντια [R]",
        "btn_rotate_v": "Περιστροφή πλοίου: Κατακόρυφα [R]",
        "btn_auto_place": "🎲 Αυτόματη τοποθέτηση",
        "btn_play_again": "🔄 Παίξτε ξανά",
        "lbl_my_fleet": "<b>Ο ΣΤΟΛΟΣ ΣΑΣ (Δικός σας πίνακας)</b>",
        "lbl_radar": "<b>ΡΑΝΤΑΡ ΕΠΙΘΕΣΗΣ (Βολές)</b>",
        "lbl_target_player": "Παίκτης-Στόχος:",

        "status_ip_found": "IP βρέθηκε αυτόματα: {ip}",
        "dlg_ip_title": "Εντοπισμός IP",
        "dlg_ip_fail": "Αδυναμία εντοπισμού τοπικής IP: {err}",

        "status_place_ship": "Τοποθετήστε πλοίο μεγέθους {size}",
        "status_all_placed_wait": "Όλα τα πλοία τοποθετήθηκαν! Αναμονή για τους άλλους παίκτες...",
        "dlg_invalid_title": "Μη έγκυρο",
        "dlg_invalid_ship": "Το πλοίο δεν χωράει εδώ ή επικαλύπτεται!",
        "status_auto_placed": "Όλα τα πλοία τοποθετήθηκαν αυτόματα (με αποστάσεις)! Το σήμα ετοιμότητας στάλθηκε.",

        "dlg_wait_title": "Αναμονή",
        "dlg_wait_placement": "Η φάση τοποθέτησης είναι ακόμη σε εξέλιξη!",
        "dlg_not_turn_title": "Δεν είναι η σειρά σας!",
        "dlg_not_turn_msg": "Δεν είναι η σειρά σας αυτή τη στιγμή!",
        "dlg_error_title": "Σφάλμα",
        "dlg_no_target": "Δεν βρέθηκε έγκυρος στόχος!",
        "dlg_already_shot_title": "Ήδη στοχευμένο",
        "dlg_already_shot_msg": "Έχετε ήδη πυροβολήσει σε αυτό το τετράγωνο!",

        "status_lobby_open": "Το lobby άνοιξε! Αναμονή για ακόμη {n} παίκτη(ες)...",
        "dlg_conn_fail_msg": "Η σύνδεση απέτυχε:\n{err}",

        "status_connected": "Συνδεθήκατε ως Παίκτης {pid}! Τοποθετήστε τα πλοία σας.",
        "status_hit": "💥 ΒΡΗΚΕ ΣΤΟΧΟ! Το πλοίο σας χτυπήθηκε.",
        "status_miss": "🌊 ΑΣΤΟΧΙΑ! Νερό.",
        "status_player_eliminated": "☠️ Ο Παίκτης {pid} αποκλείστηκε! Ο πίνακάς του αποκαλύφθηκε.",
        "status_radar_handover": "📡 Λήφθηκαν τα δεδομένα βολών του αποκλεισμένου παίκτη.",
        "status_hit_on": "💥 ΕΠΙΤΥΧΙΑ! Ο Παίκτης {target} χτυπήθηκε.",
        "status_miss_on": "🌊 ΑΣΤΟΧΙΑ εναντίον του Παίκτη {target}.",
        "status_player_left": "🔌 Ο Παίκτης {pid} έχασε τη σύνδεση και αποκλείστηκε.",
        "status_host_lost": "🔌 Χάθηκε η σύνδεση με τον Host. Το παιχνίδι δεν μπορεί να συνεχιστεί.",
        "status_you_won": "🏆 ΝΙΚΗΣΑΤΕ!",
        "status_player_won": "🏆 Ο Παίκτης {winner} νίκησε.",
        "status_new_game": "🔄 Νέο παιχνίδι! Τοποθετήστε πλοίο μεγέθους {size}",

        "player_label": "Παίκτης {pid}",
        "eliminated_suffix": "  (αποκλείστηκε)",
        "status_eliminated_self": "☠️ Αποκλειστήκατε.",
        "status_your_turn": "👉 ΕΙΝΑΙ Η ΣΕΙΡΑ ΣΑΣ! Επιλέξτε τετράγωνο και πυροβολήστε!",
        "status_waiting_turn": "⏳ Αναμονή για τη σειρά του Παίκτη {pid}...",
    },
    "tr": {
        "app_title": "Çok Oyunculu Amiral Baktı Pro (2-4 Oyuncu)",
        "lbl_language": "Dil:",
        "lbl_role": "Rol:",
        "role_host": "Host (Oyuncu 1)",
        "role_client": "Client (Katıl)",
        "lbl_players": "Oyuncu Sayısı:",
        "players_n": "{n} Oyuncu",
        "lbl_ip": "IP:",
        "btn_find_ip": "📍 IP Bul",
        "tooltip_find_ip": "Yerel ağ IP adresinizi otomatik olarak tespit eder",
        "lbl_port": "Port:",
        "btn_connect": "Lobi Oluştur / Katıl",
        "status_welcome": "Hoş geldiniz! Lütfen bir lobi oluşturun veya mevcut bir lobiye katılın.",
        "btn_rotate_h": "Gemiyi Döndür: Yatay [R]",
        "btn_rotate_v": "Gemiyi Döndür: Dikey [R]",
        "btn_auto_place": "🎲 Otomatik Yerleştir",
        "btn_play_again": "🔄 Tekrar Oyna",
        "lbl_my_fleet": "<b>SİZİN FİLONUZ (Kendi Alanınız)</b>",
        "lbl_radar": "<b>SALDIRI RADARI (Ateş Et)</b>",
        "lbl_target_player": "Hedef Oyuncu:",

        "status_ip_found": "IP otomatik olarak bulundu: {ip}",
        "dlg_ip_title": "IP Tespiti",
        "dlg_ip_fail": "Yerel IP tespit edilemedi: {err}",

        "status_place_ship": "{size} uzunluğundaki gemiyi yerleştirin",
        "status_all_placed_wait": "Tüm gemiler yerleştirildi! Diğer oyuncular bekleniyor...",
        "dlg_invalid_title": "Geçersiz",
        "dlg_invalid_ship": "Gemi buraya sığmıyor veya üst üste biniyor!",
        "status_auto_placed": "Tüm gemiler otomatik olarak (boşluklu) yerleştirildi! Hazır sinyali gönderildi.",

        "dlg_wait_title": "Bekleyin",
        "dlg_wait_placement": "Yerleştirme aşaması devam ediyor!",
        "dlg_not_turn_title": "Sıra Sizde Değil!",
        "dlg_not_turn_msg": "Şu anda sıra sizde değil!",
        "dlg_error_title": "Hata",
        "dlg_no_target": "Geçerli bir hedef bulunamadı!",
        "dlg_already_shot_title": "Zaten Ateş Edildi",
        "dlg_already_shot_msg": "Bu kareye zaten ateş ettiniz!",

        "status_lobby_open": "Lobi açıldı! {n} oyuncu daha bekleniyor...",
        "dlg_conn_fail_msg": "Bağlantı başarısız:\n{err}",

        "status_connected": "Oyuncu {pid} olarak bağlandınız! Gemilerinizi yerleştirin.",
        "status_hit": "💥 VURULDU! Geminiz hasar aldı.",
        "status_miss": "🌊 ISKA! Boş su.",
        "status_player_eliminated": "☠️ Oyuncu {pid} elendi! Alanı açığa çıkarıldı.",
        "status_radar_handover": "📡 Elenen oyuncunun atış verileri devralındı.",
        "status_hit_on": "💥 İSABET! Oyuncu {target} vuruldu.",
        "status_miss_on": "🌊 ISKA (Oyuncu {target}).",
        "status_player_left": "🔌 Oyuncu {pid} bağlantısını kaybetti ve elendi.",
        "status_host_lost": "🔌 Sunucu ile bağlantı kesildi. Oyun devam ettirilemez.",
        "status_you_won": "🏆 KAZANDINIZ!",
        "status_player_won": "🏆 Oyuncu {winner} kazandı.",
        "status_new_game": "🔄 Yeni Oyun! {size} uzunluğundaki gemiyi yerleştirin",

        "player_label": "Oyuncu {pid}",
        "eliminated_suffix": "  (elendi)",
        "status_eliminated_self": "☠️ Elendiniz.",
        "status_your_turn": "👉 SIRA SİZDE! Bir kare seçin ve ateş edin!",
        "status_waiting_turn": "⏳ Oyuncu {pid} sırasını oynuyor...",
    },
"es": {
        "app_title": "Batalla Naval Pro Multijugador (2-4 jugadores)",
        "lbl_language": "Idioma:",
        "lbl_role": "Rol:",
        "role_host": "Anfitrión (Jugador 1)",
        "role_client": "Cliente (Unirse)",
        "lbl_players": "Número de jugadores:",
        "players_n": "{n} jugadores",
        "lbl_ip": "IP:",
        "btn_find_ip": "📍 Buscar IP",
        "tooltip_find_ip": "Detecta automáticamente tu IP de red local",
        "lbl_port": "Puerto:",
        "btn_connect": "Crear / Unirse a la sala",
        "status_welcome": "¡Bienvenido! Por favor, crea una sala o únete a una existente.",
        "btn_rotate_h": "Rotar barco: Horizontal [R]",
        "btn_rotate_v": "Rotar barco: Vertical [R]",
        "btn_auto_place": "🎲 Colocación automática",
        "btn_play_again": "🔄 Jugar de nuevo",
        "lbl_my_fleet": "<b>TU FLOTA (Tablero propio)</b>",
        "lbl_radar": "<b>RADAR DE ATAQUE (Disparar)</b>",
        "lbl_target_player": "Jugador objetivo:",

        "status_ip_found": "IP encontrada automáticamente: {ip}",
        "dlg_ip_title": "Detección de IP",
        "dlg_ip_fail": "No se pudo determinar la IP local: {err}",

        "status_place_ship": "Coloca el barco de tamaño {size}",
        "status_all_placed_wait": "¡Todos los barcos colocados! Esperando a los demás jugadores...",
        "dlg_invalid_title": "No válido",
        "dlg_invalid_ship": "¡El barco no cabe aquí o se superpone!",
        "status_auto_placed": "¡Todos los barcos colocados automáticamente (con distancia)! Señal de listo enviada.",

        "dlg_wait_title": "Espere",
        "dlg_wait_placement": "¡La fase de colocación aún está activa!",
        "dlg_not_turn_title": "¡No es tu turno!",
        "dlg_not_turn_msg": "¡Actualmente no es tu turno!",
        "dlg_error_title": "Error",
        "dlg_no_target": "¡No se encontró ningún objetivo válido!",
        "dlg_already_shot_title": "Ya disparado",
        "dlg_already_shot_msg": "¡Ya has disparado en esta casilla!",

        "status_lobby_open": "¡Sala creada! Esperando a {n} jugador(es) más...",
        "dlg_conn_fail_msg": "Conexión fallida:\n{err}",

        "status_connected": "¡Conectado como Jugador {pid}! Coloca tus barcos.",
        "status_hit": "💥 ¡TOCADO! Tu barco ha sido alcanzado.",
        "status_miss": "🌊 ¡AGUA! Disparo fallido.",
        "status_player_eliminated": "☠️ ¡El Jugador {pid} ha sido eliminado! Se ha revelado su tablero.",
        "status_radar_handover": "📡 Datos de disparos del jugador eliminado transferidos.",
        "status_hit_on": "💥 ¡TOCADO! El Jugador {target} ha sido alcanzado.",
        "status_miss_on": "🌊 ¡AGUA contra el Jugador {target}!",
        "status_player_left": "🔌 El Jugador {pid} ha perdido la conexión y queda eliminado.",
        "status_host_lost": "🔌 Conexión con el anfitrión perdida. El juego no puede continuar.",
        "status_you_won": "🏆 ¡HAS GANADO!",
        "status_player_won": "🏆 El Jugador {winner} ha ganado.",
        "status_new_game": "🔄 ¡Nueva partida! Coloca el barco de tamaño {size}",

        "player_label": "Jugador {pid}",
        "eliminated_suffix": "  (eliminado)",
        "status_eliminated_self": "☠️ Has sido eliminado.",
        "status_your_turn": "👉 ¡ES TU TURNO! ¡Elige una casilla y dispara!",
        "status_waiting_turn": "⏳ Esperando el turno del Jugador {pid}...",
    },
    "it": {
        "app_title": "Battaglia Navale Pro Multiplayer (2-4 giocatori)",
        "lbl_language": "Lingua:",
        "lbl_role": "Ruolo:",
        "role_host": "Host (Giocatore 1)",
        "role_client": "Client (Entra)",
        "lbl_players": "Numero di giocatori:",
        "players_n": "{n} giocatori",
        "lbl_ip": "IP:",
        "btn_find_ip": "📍 Trova IP",
        "tooltip_find_ip": "Rileva automaticamente il tuo IP di rete locale",
        "lbl_port": "Porta:",
        "btn_connect": "Crea / Entra nella stanza",
        "status_welcome": "Benvenuto! Crea una stanza o entra in una esistente.",
        "btn_rotate_h": "Ruota nave: Orizzontale [R]",
        "btn_rotate_v": "Ruota nave: Verticale [R]",
        "btn_auto_place": "🎲 Posizionamento automatico",
        "btn_play_again": "🔄 Gioca ancora",
        "lbl_my_fleet": "<b>LA TUA FLOTTA (Griglia propria)</b>",
        "lbl_radar": "<b>RADAR D'ATTACCO (Spara)</b>",
        "lbl_target_player": "Giocatore bersaglio:",

        "status_ip_found": "IP trovato automaticamente: {ip}",
        "dlg_ip_title": "Rilevamento IP",
        "dlg_ip_fail": "Impossibile determinare l'IP locale: {err}",

        "status_place_ship": "Posiziona la nave di lunghezza {size}",
        "status_all_placed_wait": "Tutte le navi posizionate! In attesa degli altri giocatori...",
        "dlg_invalid_title": "Non valido",
        "dlg_invalid_ship": "La nave non entra qui o si sovrappone!",
        "status_auto_placed": "Tutte le navi posizionate automaticamente (con distanziamento)! Segnale di pronto inviato.",

        "dlg_wait_title": "Attendi",
        "dlg_wait_placement": "La fase di posizionamento è ancora in corso!",
        "dlg_not_turn_title": "Non è il tuo turno!",
        "dlg_not_turn_msg": "Al momento non è il tuo turno!",
        "dlg_error_title": "Errore",
        "dlg_no_target": "Nessun bersaglio valido trovato!",
        "dlg_already_shot_title": "Già colpito",
        "dlg_already_shot_msg": "Hai già sparato su questa casella!",

        "status_lobby_open": "Stanza creata! In attesa di altri {n} giocatore/i...",
        "dlg_conn_fail_msg": "Connessione fallita:\n{err}",

        "status_connected": "Connesso come Giocatore {pid}! Posiziona le tue navi.",
        "status_hit": "💥 COLPITO! La tua nave è stata colpita.",
        "status_miss": "🌊 ACQUA! Colpo a vuoto.",
        "status_player_eliminated": "☠️ Il Giocatore {pid} è stato eliminato! La sua griglia è stata rivelata.",
        "status_radar_handover": "📡 Dati sui colpi del giocatore eliminato acquisiti.",
        "status_hit_on": "💥 COLPITO! Il Giocatore {target} è stato colpito.",
        "status_miss_on": "🌊 ACQUA contro il Giocatore {target}.",
        "status_player_left": "🔌 Il Giocatore {pid} ha perso la connessione ed è stato eliminato.",
        "status_host_lost": "🔌 Connessione all'host perduta. La partita non può continuare.",
        "status_you_won": "🏆 HAI VINTO!",
        "status_player_won": "🏆 Il Giocatore {winner} ha vinto.",
        "status_new_game": "🔄 Nuova partita! Posiziona la nave di lunghezza {size}",

        "player_label": "Giocatore {pid}",
        "eliminated_suffix": "  (eliminato)",
        "status_eliminated_self": "☠️ Sei stato eliminato.",
        "status_your_turn": "👉 È IL TUO TURNO! Scegli una casella e spara!",
        "status_waiting_turn": "⏳ È il turno del Giocatore {pid}...",
    },
"pt": {
        "app_title": "Batalha Naval Pro Multijogador (2-4 jogadores)",
        "lbl_language": "Idioma:",
        "lbl_role": "Função:",
        "role_host": "Anfitrião (Jogador 1)",
        "role_client": "Cliente (Entrar)",
        "lbl_players": "Número de jogadores:",
        "players_n": "{n} jogadores",
        "lbl_ip": "IP:",
        "btn_find_ip": "📍 Encontrar IP",
        "tooltip_find_ip": "Detecta automaticamente o seu IP de rede local",
        "lbl_port": "Porta:",
        "btn_connect": "Criar / Entrar na sala",
        "status_welcome": "Bem-vindo! Por favor, crie uma sala ou entre em uma existente.",
        "btn_rotate_h": "Girar navio: Horizontal [R]",
        "btn_rotate_v": "Girar navio: Vertical [R]",
        "btn_auto_place": "🎲 Posicionamento automático",
        "btn_play_again": "🔄 Jogar novamente",
        "lbl_my_fleet": "<b>A SUA FROTA (Grelha própria)</b>",
        "lbl_radar": "<b>RADAR DE ATAQUE (Disparar)</b>",
        "lbl_target_player": "Jogador alvo:",

        "status_ip_found": "IP encontrado automaticamente: {ip}",
        "dlg_ip_title": "Deteção de IP",
        "dlg_ip_fail": "Não foi possível determinar o IP local: {err}",

        "status_place_ship": "Posicione o navio de tamanho {size}",
        "status_all_placed_wait": "Todos os navios posicionados! A aguardar outros jogadores...",
        "dlg_invalid_title": "Inválido",
        "dlg_invalid_ship": "O navio não cabe aqui ou sobrepõe-se!",
        "status_auto_placed": "Todos os navios posicionados automaticamente (com espaçamento)! Sinal de pronto enviado.",

        "dlg_wait_title": "Aguarde",
        "dlg_wait_placement": "A fase de posicionamento ainda está ativa!",
        "dlg_not_turn_title": "Não é a sua vez!",
        "dlg_not_turn_msg": "Atualmente não é a sua vez!",
        "dlg_error_title": "Erro",
        "dlg_no_target": "Nenhum alvo válido encontrado!",
        "dlg_already_shot_title": "Já disparado",
        "dlg_already_shot_msg": "Já disparou nesta coordenada!",

        "status_lobby_open": "Sala aberta! A aguardar mais {n} jogador(es)...",
        "dlg_conn_fail_msg": "Falha na conexão:\n{err}",

        "status_connected": "Conectado como Jogador {pid}! Posicione os seus navios.",
        "status_hit": "💥 ATINGIDO! O seu navio foi atingido.",
        "status_miss": "🌊 ÁGUA! Disparo falhado.",
        "status_player_eliminated": "☠️ O Jogador {pid} foi eliminado! A sua grelha foi revelada.",
        "status_radar_handover": "📡 Dados de disparos do jogador eliminado transferidos.",
        "status_hit_on": "💥 ATINGIDO! O Jogador {target} foi atingido.",
        "status_miss_on": "🌊 ÁGUA contra o Jogador {target}.",
        "status_player_left": "🔌 O Jogador {pid} perdeu a conexão e foi eliminado.",
        "status_host_lost": "🔌 Conexão ao anfitrião perdida. O jogo não pode continuar.",
        "status_you_won": "🏆 VOCÊ GANHOU!",
        "status_player_won": "🏆 O Jogador {winner} ganhou.",
        "status_new_game": "🔄 Novo jogo! Posicione o navio de tamanho {size}",

        "player_label": "Jogador {pid}",
        "eliminated_suffix": "  (eliminado)",
        "status_eliminated_self": "☠️ Você foi eliminado.",
        "status_your_turn": "👉 É A SUA VEZ! Escolha uma casa e dispare!",
        "status_waiting_turn": "⏳ É a vez do Jogador {pid}...",
    },
    "cs": {
        "app_title": "Multiplayer Lodičky Pro (2-4 hráči)",
        "lbl_language": "Jazyk:",
        "lbl_role": "Role:",
        "role_host": "Hostitel (Hráč 1)",
        "role_client": "Klient (Připojit se)",
        "lbl_players": "Počet hráčů:",
        "players_n": "{n} hráči",
        "lbl_ip": "IP:",
        "btn_find_ip": "📍 Najít IP",
        "tooltip_find_ip": "Automaticky zjistí vaši lokální IP adresu",
        "lbl_port": "Port:",
        "btn_connect": "Vytvořit / Připojit se do lobby",
        "status_welcome": "Vítejte! Vytvořte lobby nebo se připojte k existujícímu.",
        "btn_rotate_h": "Otočit loď: Horizontálně [R]",
        "btn_rotate_v": "Otočit loď: Vertikálně [R]",
        "btn_auto_place": "🎲 Automatické rozmístění",
        "btn_play_again": "🔄 Hrát znovu",
        "lbl_my_fleet": "<b>VAŠE FLOTILA (Vlastní pole)</b>",
        "lbl_radar": "<b>ÚTOČNÝ RADAR (Střelba)</b>",
        "lbl_target_player": "Cílový hráč:",

        "status_ip_found": "IP automaticky nalezena: {ip}",
        "dlg_ip_title": "Detekce IP",
        "dlg_ip_fail": "Nedařilo se zjistit lokální IP: {err}",

        "status_place_ship": "Umístěte loď o délce {size}",
        "status_all_placed_wait": "Všechny lodě rozmístěny! Čekání na ostatní hráče...",
        "dlg_invalid_title": "Neplatné",
        "dlg_invalid_ship": "Loď se sem nevejde nebo se překrývá!",
        "status_auto_placed": "Všechny lodě automaticky rozmístěny (s rozestupy)! Signál připravenosti odeslán.",

        "dlg_wait_title": "Čekejte",
        "dlg_wait_placement": "Fáze rozmísťování stále probíhá!",
        "dlg_not_turn_title": "Nejste na řadě!",
        "dlg_not_turn_msg": "Právě nejste na řadě!",
        "dlg_error_title": "Chyba",
        "dlg_no_target": "Nenalezen žádný platný cíl!",
        "dlg_already_shot_title": "Již vystřeleno",
        "dlg_already_shot_msg": "Na toto pole jste již stříleli!",

        "status_lobby_open": "Lobby otevřeno! Čekání na další {n} hráče...",
        "dlg_conn_fail_msg": "Připojení selhalo:\n{err}",

        "status_connected": "Připojeno jako Hráč {pid}! Rozmístěte své lodě.",
        "status_hit": "💥 ZÁSAH! Vaše loď byla zasažena.",
        "status_miss": "🌊 VODA! Vedle.",
        "status_player_eliminated": "☠️ Hráč {pid} byl vyřazen! Jeho pole bylo odhaleno.",
        "status_radar_handover": "📡 Data střelby vyřazeného hráče byla převzata.",
        "status_hit_on": "💥 ZÁSAH! Hráč {target} byl zasažen.",
        "status_miss_on": "🌊 VODA proti hráči {target}.",
        "status_player_left": "🔌 Hráč {pid} ztratil spojení a byl vyřazen.",
        "status_host_lost": "🔌 Spojení s hostitelem bylo ztraceno. Hra nemůže pokračovat.",
        "status_you_won": "🏆 VYHRÁL JSI!",
        "status_player_won": "🏆 Hráč {winner} vyhrál.",
        "status_new_game": "🔄 Nová hra! Umístěte loď o délce {size}",

        "player_label": "Hráč {pid}",
        "eliminated_suffix": "  (vyřazen)",
        "status_eliminated_self": "☠️ Byl jste vyřazen.",
        "status_your_turn": "👉 JSI NA ŘADĚ! Vyber pole a vystřel!",
        "status_waiting_turn": "⏳ Na řadě je Hráč {pid}...",
    },
    "hu": {
        "app_title": "Többjátékos Torpedó Pro (2-4 játékos)",
        "lbl_language": "Nyelv:",
        "lbl_role": "Szerep:",
        "role_host": "Gazda (1. játékos)",
        "role_client": "Kliens (Csatlakozás)",
        "lbl_players": "Játékosok száma:",
        "players_n": "{n} játékos",
        "lbl_ip": "IP:",
        "btn_find_ip": "📍 IP keresése",
        "tooltip_find_ip": "Automatikusan felismeri a helyi hálózati IP-címet",
        "lbl_port": "Port:",
        "btn_connect": "Lobby létrehozása / Csatlakozás",
        "status_welcome": "Üdvözöljük! Hozzon létre egy lobby-t vagy csatlakozzon egy meglévőhöz.",
        "btn_rotate_h": "Hajó forgatása: Vízszintes [R]",
        "btn_rotate_v": "Hajó forgatása: Függőleges [R]",
        "btn_auto_place": "🎲 Automatikus elhelyezés",
        "btn_play_again": "🔄 Újrajáték",
        "lbl_my_fleet": "<b>AZ ÖN FLOTTÁJA (Saját tábla)</b>",
        "lbl_radar": "<b>TÁMADÁSI RADAR (Lövés)</b>",
        "lbl_target_player": "Célpont játékos:",

        "status_ip_found": "IP automatikusan megtalálva: {ip}",
        "dlg_ip_title": "IP-észlelés",
        "dlg_ip_fail": "Nem sikerült meghatározni a helyi IP-címet: {err}",

        "status_place_ship": "Helyezze el a(z) {size} hosszúságú hajót",
        "status_all_placed_wait": "Minden hajó elhelyezve! Várakozás a többi játékosra...",
        "dlg_invalid_title": "Érvénytelen",
        "dlg_invalid_ship": "A hajó nem fér el itt, vagy átfedésben van!",
        "status_auto_placed": "Minden hajó automatikusan elhelyezve (távolságtartással)! Kész jelzés elküldve.",

        "dlg_wait_title": "Várakozás",
        "dlg_wait_placement": "A hajóelhelyezési fázis még tart!",
        "dlg_not_turn_title": "Nem te jössz!",
        "dlg_not_turn_msg": "Jelenleg nem te vagy soron!",
        "dlg_error_title": "Hiba",
        "dlg_no_target": "Nem található érvényes célpont!",
        "dlg_already_shot_title": "Már meglőve",
        "dlg_already_shot_msg": "Erre a mezőre már lőttél!",

        "status_lobby_open": "Lobby megnyitva! Várakozás további {n} játékosra...",
        "dlg_conn_fail_msg": "A csatlakozás sikertelen:\n{err}",

        "status_connected": "Csatlakozva mint {pid}. játékos! Helyezze el a hajóit.",
        "status_hit": "💥 TALÁLAT! A hajódat eltalálták.",
        "status_miss": "🌊 MELLÉ! Víz.",
        "status_player_eliminated": "☠️ A(z) {pid}. játékos kiesett! A táblája felfedve.",
        "status_radar_handover": "📡 A kiesett játékos lövési adatai átvéve.",
        "status_hit_on": "💥 TALÁLAT! A(z) {target}. játékost eltalálták.",
        "status_miss_on": "🌊 MELLÉ a(z) {target}. játékos ellen.",
        "status_player_left": "🔌 A(z) {pid}. játékos elvesztette a kapcsolatot és kiesett.",
        "status_host_lost": "🔌 A kapcsolat megszakadt a gazdával. A játék nem folytatható.",
        "status_you_won": "🏆 NYERTÉL!",
        "status_player_won": "🏆 A(z) {winner}. játékos nyert.",
        "status_new_game": "🔄 Új játék! Helyezze el a(z) {size} hosszúságú hajót",

        "player_label": "{pid}. játékos",
        "eliminated_suffix": "  (kiesett)",
        "status_eliminated_self": "☠️ Kiesztél.",
        "status_your_turn": "👉 TE JÖSSZ! Válassz egy mezőt és lőj!",
        "status_waiting_turn": "⏳ A(z) {pid}. játékos van soron...",
    },
    "ro": {
        "app_title": "Bătălia Navală Pro Multiplayer (2-4 jucători)",
        "lbl_language": "Limbă:",
        "lbl_role": "Rol:",
        "role_host": "Gazdă (Jucător 1)",
        "role_client": "Client (Conectare)",
        "lbl_players": "Număr de jucători:",
        "players_n": "{n} jucători",
        "lbl_ip": "IP:",
        "btn_find_ip": "📍 Găsește IP",
        "tooltip_find_ip": "Detectează automat adresa IP din rețeaua locală",
        "lbl_port": "Port:",
        "btn_connect": "Creează / Conectează-te la lobby",
        "status_welcome": "Bine ai venit! Creează un lobby sau conectează-te la unul existent.",
        "btn_rotate_h": "Rotește nava: Orizontal [R]",
        "btn_rotate_v": "Rotește nava: Vertical [R]",
        "btn_auto_place": "🎲 Plasare automată",
        "btn_play_again": "🔄 Joacă din nou",
        "lbl_my_fleet": "<b>FLOTA TA (Grila proprie)</b>",
        "lbl_radar": "<b>RADAR DE ATAC (Tragere)</b>",
        "lbl_target_player": "Jucător țintă:",

        "status_ip_found": "IP găsit automat: {ip}",
        "dlg_ip_title": "Detectare IP",
        "dlg_ip_fail": "Nu s-a putut determina IP-ul local: {err}",

        "status_place_ship": "Plasează nava de dimensiune {size}",
        "status_all_placed_wait": "Toate navele au fost plasate! Se așteaptă ceilalți jucători...",
        "dlg_invalid_title": "Invalid",
        "dlg_invalid_ship": "Nava nu se potrivește aici sau se suprapune!",
        "status_auto_placed": "Toate navele au fost plasate automat (cu distanțare)! Semnal de pregătire trimis.",

        "dlg_wait_title": "Așteaptă",
        "dlg_wait_placement": "Faza de plasare este încă activă!",
        "dlg_not_turn_title": "Nu este rândul tău!",
        "dlg_not_turn_msg": "Momentan nu este rândul tău!",
        "dlg_error_title": "Eroare",
        "dlg_no_target": "Nu s-a găsit nicio țintă validă!",
        "dlg_already_shot_title": "Deja țintit",
        "dlg_already_shot_msg": "Ai tras deja în această căsuță!",

        "status_lobby_open": "Lobby creat! Se așteaptă încă {n} jucător(i)...",
        "dlg_conn_fail_msg": "Conexiune eșuată:\n{err}",

        "status_connected": "Conectat ca Jucătorul {pid}! Plasează-ți navele.",
        "status_hit": "💥 LOVIT! Nava ta a fost lovită.",
        "status_miss": "🌊 RATAT! Apă.",
        "status_player_eliminated": "☠️ Jucătorul {pid} a fost eliminat! Grila sa a fost dezvăluită.",
        "status_radar_handover": "📡 Datele de tragere ale jucătorului eliminat au fost preluate.",
        "status_hit_on": "💥 LOVIT! Jucătorul {target} a fost lovit.",
        "status_miss_on": "🌊 RATAT împotriva Jucătorului {target}.",
        "status_player_left": "🔌 Jucătorul {pid} a pierdut conexiunea și este eliminat.",
        "status_host_lost": "🔌 Conexiunea cu gazda a fost pierdută. Jocul nu poate continua.",
        "status_you_won": "🏆 AI CÂȘTIGAT!",
        "status_player_won": "🏆 Jucătorul {winner} a câștigat.",
        "status_new_game": "🔄 Joc nou! Plasează nava de dimensiune {size}",

        "player_label": "Jucătorul {pid}",
        "eliminated_suffix": "  (eliminat)",
        "status_eliminated_self": "☠️ Ai fost eliminat.",
        "status_your_turn": "👉 ESTE RÂNDUL TĂU! Alege o căsuță și trage!",
        "status_waiting_turn": "⏳ Este rândul Jucătorului {pid}...",
    },
    "sv": {
        "app_title": "Multiplayer Sänka Skepp Pro (2-4 spelare)",
        "lbl_language": "Språk:",
        "lbl_role": "Roll:",
        "role_host": "Värd (Spelare 1)",
        "role_client": "Klient (Gå med)",
        "lbl_players": "Antal spelare:",
        "players_n": "{n} spelare",
        "lbl_ip": "IP:",
        "btn_find_ip": "📍 Hitta IP",
        "tooltip_find_ip": "Identifierar automatiskt din lokala nätverks-IP",
        "lbl_port": "Port:",
        "btn_connect": "Skapa / Gå med i lobby",
        "status_welcome": "Välkommen! Skapa en lobby eller gå med i en befintlig.",
        "btn_rotate_h": "Rotera skepp: Horisontellt [R]",
        "btn_rotate_v": "Rotera skepp: Vertikalt [R]",
        "btn_auto_place": "🎲 Automatisk placering",
        "btn_play_again": "🔄 Spela igen",
        "lbl_my_fleet": "<b>DIN FLOTTA (Eget rutnät)</b>",
        "lbl_radar": "<b>ATTACKRADAR (Skjut)</b>",
        "lbl_target_player": "Målspelare:",

        "status_ip_found": "IP hittades automatiskt: {ip}",
        "dlg_ip_title": "IP-identifiering",
        "dlg_ip_fail": "Kunde inte identifiera lokal IP: {err}",

        "status_place_ship": "Placera skepp med storlek {size}",
        "status_all_placed_wait": "Alla skepp placerade! Väntar på andra spelare...",
        "dlg_invalid_title": "Ogiltigt",
        "dlg_invalid_ship": "Skeppet passar inte här eller överlappar!",
        "status_auto_placed": "Alla skepp placerade automatiskt (med avstånd)! Redo-signal skickad.",

        "dlg_wait_title": "Vänta",
        "dlg_wait_placement": "Placeringsfasen pågår fortfarande!",
        "dlg_not_turn_title": "Inte din tur!",
        "dlg_not_turn_msg": "Det är inte din tur just nu!",
        "dlg_error_title": "Fel",
        "dlg_no_target": "Inget giltigt mål hittades!",
        "dlg_already_shot_title": "Redan beskjuten",
        "dlg_already_shot_msg": "Du har redan skjutit på den här rutan!",

        "status_lobby_open": "Lobby skapad! Väntar på ytterligare {n} spelare...",
        "dlg_conn_fail_msg": "Anslutningen misslyckades:\n{err}",

        "status_connected": "Ansluten som Spelare {pid}! Placera dina skepp.",
        "status_hit": "💥 TRÄFF! Ditt skepp blev träffat.",
        "status_miss": "🌊 MISS! Vatten.",
        "status_player_eliminated": "☠️ Spelare {pid} är utslagen! Hans rutnät har avslöjats.",
        "status_radar_handover": "📡 Skottdata från den utslagna spelaren har övertagits.",
        "status_hit_on": "💥 TRÄFF! Spelare {target} blev träffad.",
        "status_miss_on": "🌊 MISS mot Spelare {target}.",
        "status_player_left": "🔌 Spelare {pid} tappade anslutningen och är utslagen.",
        "status_host_lost": "🔌 Anslutningen till värden förlorades. Spelet kan inte fortsätta.",
        "status_you_won": "🏆 DU VANN!",
        "status_player_won": "🏆 Spelare {winner} vann.",
        "status_new_game": "🔄 Nytt spel! Placera skepp med storlek {size}",

        "player_label": "Spelare {pid}",
        "eliminated_suffix": "  (utslagen)",
        "status_eliminated_self": "☠️ Du är utslagen.",
        "status_your_turn": "👉 DET ÄR DIN TUR! Välj en ruta och skjut!",
        "status_waiting_turn": "⏳ Det är Spelare {pid}s tur...",
    },

"da": {
        "app_title": "Multiplayer Sænke Slagskibe Pro (2-4 spillere)",
        "lbl_language": "Sprog:",
        "lbl_role": "Rolle:",
        "role_host": "Vært (Spiller 1)",
        "role_client": "Klient (Deltag)",
        "lbl_players": "Antal spillere:",
        "players_n": "{n} spillere",
        "lbl_ip": "IP:",
        "btn_find_ip": "📍 Find IP",
        "tooltip_find_ip": "Finder automatisk din lokale netværks-IP",
        "lbl_port": "Port:",
        "btn_connect": "Opret / Deltag i lobby",
        "status_welcome": "Velkommen! Opret en lobby eller deltag i en eksisterende.",
        "btn_rotate_h": "Roter skib: Vandret [R]",
        "btn_rotate_v": "Roter skib: Lodret [R]",
        "btn_auto_place": "🎲 Automatisk placering",
        "btn_play_again": "🔄 Spil igen",
        "lbl_my_fleet": "<b>DIN FLÅDE (Eget bræt)</b>",
        "lbl_radar": "<b>ANGREBSRADAR (Skyd)</b>",
        "lbl_target_player": "Målspiller:",

        "status_ip_found": "IP fundet automatisk: {ip}",
        "dlg_ip_title": "IP-registrering",
        "dlg_ip_fail": "Kunne ikke bestemme lokal IP: {err}",

        "status_place_ship": "Placer skib af størrelse {size}",
        "status_all_placed_wait": "Alle skibe placeret! Venter på andre spillere...",
        "dlg_invalid_title": "Ugyldig",
        "dlg_invalid_ship": "Skibet passer ikke her eller overlapper!",
        "status_auto_placed": "Alle skibe automatisk placeret (med afstand)! Klar-signal sendt.",

        "dlg_wait_title": "Vent",
        "dlg_wait_placement": "Placeringsfasen er stadig i gang!",
        "dlg_not_turn_title": "Ikke din tur!",
        "dlg_not_turn_msg": "Det er i øjeblikket ikke din tur!",
        "dlg_error_title": "Fejl",
        "dlg_no_target": "Intet gyldigt mål fundet!",
        "dlg_already_shot_title": "Allerede beskudt",
        "dlg_already_shot_msg": "Du har allerede skudt på dette felt!",

        "status_lobby_open": "Lobby åben! Venter på yderligere {n} spiller(e)...",
        "dlg_conn_fail_msg": "Forbindelse mislykkedes:\n{err}",

        "status_connected": "Tilsluttet som Spiller {pid}! Placer dine skibe.",
        "status_hit": "💥 RAMT! Dit skib er blevet ramt.",
        "status_miss": "🌊 FORBI! Vand.",
        "status_player_eliminated": "☠️ Spiller {pid} er elimineret! Vedkommendes bræt er afsløret.",
        "status_radar_handover": "📡 Skuddata fra elimineret spiller overtaget.",
        "status_hit_on": "💥 RAMT! Spiller {target} blev ramt.",
        "status_miss_on": "🌊 FORBI mod Spiller {target}.",
        "status_player_left": "🔌 Spiller {pid} mistede forbindelsen og blev elimineret.",
        "status_host_lost": "🔌 Forbindelse til værten mistet. Spillet kan ikke fortsætte.",
        "status_you_won": "🏆 DU VANDT!",
        "status_player_won": "🏆 Spiller {winner} vandt.",
        "status_new_game": "🔄 Nyt spil! Placer skib af størrelse {size}",

        "player_label": "Spiller {pid}",
        "eliminated_suffix": "  (elimineret)",
        "status_eliminated_self": "☠️ Du er elimineret.",
        "status_your_turn": "👉 DET ER DIN TUR! Vælg et felt og skyd!",
        "status_waiting_turn": "⏳ Venter på Spiller {pid}s tur...",
    },
    "no": {
        "app_title": "Flerspiller Senke Skip Pro (2-4 spillere)",
        "lbl_language": "Språk:",
        "lbl_role": "Rolle:",
        "role_host": "Vert (Spiller 1)",
        "role_client": "Klient (Bli med)",
        "lbl_players": "Antall spillere:",
        "players_n": "{n} spillere",
        "lbl_ip": "IP:",
        "btn_find_ip": "📍 Finn IP",
        "tooltip_find_ip": "Oppdager automatisk din lokale nettverks-IP",
        "lbl_port": "Port:",
        "btn_connect": "Opprett / Bli med i lobby",
        "status_welcome": "Velkommen! Opprett en lobby eller bli med i en eksisterende.",
        "btn_rotate_h": "Roter skip: Horisontalt [R]",
        "btn_rotate_v": "Roter skip: Vertikalt [R]",
        "btn_auto_place": "🎲 Automatisk plassering",
        "btn_play_again": "🔄 Spill igjen",
        "lbl_my_fleet": "<b>DIN FLÅTE (Eget brett)</b>",
        "lbl_radar": "<b>ANGREPSRADAR (Skyt)</b>",
        "lbl_target_player": "Målspiller:",

        "status_ip_found": "IP automatisk funnet: {ip}",
        "dlg_ip_title": "IP-oppdaging",
        "dlg_ip_fail": "Kunne ikke bestemme lokal IP: {err}",

        "status_place_ship": "Plasser skip med størrelse {size}",
        "status_all_placed_wait": "Alle skip plassert! Venter på andre spillere...",
        "dlg_invalid_title": "Ugyldig",
        "dlg_invalid_ship": "Skipet passer ikke her eller overlapper!",
        "status_auto_placed": "Alle skip automatisk plassert (med avstand)! Klar-signal sendt.",

        "dlg_wait_title": "Vent",
        "dlg_wait_placement": "Plasseringsfasen pågår fortsatt!",
        "dlg_not_turn_title": "Ikke din tur!",
        "dlg_not_turn_msg": "Det er for øyeblikket ikke din tur!",
        "dlg_error_title": "Feil",
        "dlg_no_target": "Ingen gyldig mål funnet!",
        "dlg_already_shot_title": "Allerede skutt på",
        "dlg_already_shot_msg": "Du har allerede skutt på denne ruten!",

        "status_lobby_open": "Lobby åpnet! Venter på {n} spiller(e) til...",
        "dlg_conn_fail_msg": "Tilkobling mislyktes:\n{err}",

        "status_connected": "Tilkoblet som Spiller {pid}! Plasser skipene dine.",
        "status_hit": "💥 TREFF! Skipet ditt ble treft.",
        "status_miss": "🌊 BOM! Vann.",
        "status_player_eliminated": "☠️ Spiller {pid} er eliminert! Brettet ble avslørt.",
        "status_radar_handover": "📡 Skudddata fra eliminert spiller overtat.",
        "status_hit_on": "💥 TREFF! Spiller {target} ble treft.",
        "status_miss_on": "🌊 BOM mot Spiller {target}.",
        "status_player_left": "🔌 Spiller {pid} mistet tilkoblingen og er eliminert.",
        "status_host_lost": "🔌 Tilkobling til verten mistet. Spillet kan ikke fortsette.",
        "status_you_won": "🏆 DU VANT!",
        "status_player_won": "🏆 Spiller {winner} vant.",
        "status_new_game": "🔄 Nytt spill! Plasser skip med størrelse {size}",

        "player_label": "Spiller {pid}",
        "eliminated_suffix": "  (eliminert)",
        "status_eliminated_self": "☠️ Du er eliminert.",
        "status_your_turn": "👉 DET ER DIN TUR! Velg en rute og skyt!",
        "status_waiting_turn": "⏳ Venter på Spiller {pid} sin tur...",
    },
    "fi": {
        "app_title": "Moninpeli Laivanupotus Pro (2-4 pelaajaa)",
        "lbl_language": "Kieli:",
        "lbl_role": "Rooli:",
        "role_host": "Isäntä (Pelaaja 1)",
        "role_client": "Asiakas (Liity)",
        "lbl_players": "Pelaajamäärä:",
        "players_n": "{n} pelaajaa",
        "lbl_ip": "IP:",
        "btn_find_ip": "📍 Etsi IP",
        "tooltip_find_ip": "Tunnistaa paikallisen IP-osoitteesi automaattisesti",
        "lbl_port": "Portti:",
        "btn_connect": "Luo / Liity aulaan",
        "status_welcome": "Tervetuloa! Luo aula tai liity olemassa olevaan.",
        "btn_rotate_h": "Käännä laivaa: Vaakatasossa [R]",
        "btn_rotate_v": "Käännä laivaa: Pystytasossa [R]",
        "btn_auto_place": "🎲 Automaattinen sijoittelu",
        "btn_play_again": "🔄 Pelaa uudelleen",
        "lbl_my_fleet": "<b>OMAT LAIVAT (Oma ruudukko)</b>",
        "lbl_radar": "<b>HYÖKKÄYSRADAR (Ammunta)</b>",
        "lbl_target_player": "Kohdepelaaja:",

        "status_ip_found": "IP löytyi automaattisesti: {ip}",
        "dlg_ip_title": "IP-tunnistus",
        "dlg_ip_fail": "Paikallista IP-osoitetta ei saatu määritettyä: {err}",

        "status_place_ship": "Sijoita laiva, jonka koko on {size}",
        "status_all_placed_wait": "Kaikki laivat sijoitettu! Odotetaan muita pelaajia...",
        "dlg_invalid_title": "Virheellinen",
        "dlg_invalid_ship": "Laiva ei mahdu tähän tai menee päällekkäin!",
        "status_auto_placed": "Kaikki laivat sijoitettu automaattisesti! Valmis-signaali lähetetty.",

        "dlg_wait_title": "Odota",
        "dlg_wait_placement": "Sijoitteluvaihe on edelleen käynnissä!",
        "dlg_not_turn_title": "Ei sinun vuorosi!",
        "dlg_not_turn_msg": "Ei ole tällä hetkellä sinun vuorosi!",
        "dlg_error_title": "Virhe",
        "dlg_no_target": "Voimassa olevaa kohdetta ei löytynyt!",
        "dlg_already_shot_title": "Jo ammuttu",
        "dlg_already_shot_msg": "Olet jo ampunut tähän ruutuun!",

        "status_lobby_open": "Aula avattu! Odotetaan vielä {n} pelaajaa...",
        "dlg_conn_fail_msg": "Yhdistäminen epäonnistui:\n{err}",

        "status_connected": "Yhdistetty Pelaajana {pid}! Sijoita laivasi.",
        "status_hit": "💥 OSUMA! Laivaasi osuttiin.",
        "status_miss": "🌊 OHILUOTI! Vettä.",
        "status_player_eliminated": "☠️ Pelaaja {pid} on pudotettu! Hänen ruudukkonsa paljastettiin.",
        "status_radar_handover": "📡 Pudotetun pelaajan ammuntatiedot saatu.",
        "status_hit_on": "💥 OSUMA! Pelaajaan {target} osuttiin.",
        "status_miss_on": "🌊 OHI pelaajasta {target}.",
        "status_player_left": "🔌 Pelaaja {pid} menetti yhteyden ja putosi.",
        "status_host_lost": "🔌 Yhteys isäntään menetettiin. Peliä ei voi jatkaa.",
        "status_you_won": "🏆 VOITIT!",
        "status_player_won": "🏆 Pelaaja {winner} voitti.",
        "status_new_game": "🔄 Uusi peli! Sijoita laiva, jonka koko on {size}",

        "player_label": "Pelaaja {pid}",
        "eliminated_suffix": "  (pudotettu)",
        "status_eliminated_self": "☠️ Sinut on pudotettu.",
        "status_your_turn": "👉 SINUN VUOROSI! Valitse ruutu ja ammu!",
        "status_waiting_turn": "⏳ Odotetaan Pelaajan {pid} vuoroa...",
    },
    "bg": {
        "app_title": "Мултиплейър Морски бой Pro (2-4 играчи)",
        "lbl_language": "Език:",
        "lbl_role": "Роля:",
        "role_host": "Хост (Играч 1)",
        "role_client": "Клиент (Присъединяване)",
        "lbl_players": "Брой играчи:",
        "players_n": "{n} играчи",
        "lbl_ip": "IP:",
        "btn_find_ip": "📍 Намери IP",
        "tooltip_find_ip": "Автоматично открива вашия локален IP адрес",
        "lbl_port": "Порт:",
        "btn_connect": "Създай / Присъедини се към лоби",
        "status_welcome": "Добре дошли! Моля, създайте лоби или се присъединете към съществуващо.",
        "btn_rotate_h": "Завърти кораба: Хоризонтално [R]",
        "btn_rotate_v": "Завърти кораба: Вертикално [R]",
        "btn_auto_place": "🎲 Автоматично разполагане",
        "btn_play_again": "🔄 Играй отново",
        "lbl_my_fleet": "<b>ВАШИЯТ ФЛОТ (Собствено поле)</b>",
        "lbl_radar": "<b>АТАКУВАЩ РАДАР (Стрелба)</b>",
        "lbl_target_player": "Целеви играч:",

        "status_ip_found": "IP автоматично намерено: {ip}",
        "dlg_ip_title": "Откриване на IP",
        "dlg_ip_fail": "Не можа да се определи локалният IP адрес: {err}",

        "status_place_ship": "Поставете кораб с размер {size}",
        "status_all_placed_wait": "Всички кораби са поставени! Изчакване на останалите играчи...",
        "dlg_invalid_title": "Невалидно",
        "dlg_invalid_ship": "Корабът не се събира тук или се застъпва!",
        "status_auto_placed": "Всички кораби са поставени автоматично (с разстояние)! Изпратен е сигнал за готовност.",

        "dlg_wait_title": "Изчакайте",
        "dlg_wait_placement": "Фазата на разполагане все още е активна!",
        "dlg_not_turn_title": "Не сте на ход!",
        "dlg_not_turn_msg": "В момента не сте на ход!",
        "dlg_error_title": "Грешка",
        "dlg_no_target": "Не е намерена валидна цел!",
        "dlg_already_shot_title": "Вече е стреляно",
        "dlg_already_shot_msg": "Вече сте стреляли в това квадратче!",

        "status_lobby_open": "Лобито е отворено! Изчакване на още {n} играч(а)...",
        "dlg_conn_fail_msg": "Връзката се провали:\n{err}",

        "status_connected": "Свързан като Играч {pid}! Разположете корабите си.",
        "status_hit": "💥 ПОПАДЕНИЕ! Вашият кораб беше ударен.",
        "status_miss": "🌊 ПРОПУСК! Вода.",
        "status_player_eliminated": "☠️ Играч {pid} е елиминиран! Полето му беше разкрито.",
        "status_radar_handover": "📡 Данните за изстрелите на елиминирания играч са получени.",
        "status_hit_on": "💥 ПОПАДЕНИЕ! Играч {target} беше ударен.",
        "status_miss_on": "🌊 ПРОПУСК срещу Играч {target}.",
        "status_player_left": "🔌 Играч {pid} загуби връзка и беше елиминиран.",
        "status_host_lost": "🔌 Връзката с хоста е изгубена. Играта не може да продължи.",
        "status_you_won": "🏆 ВИЕ ПОБЕДИХТЕ!",
        "status_player_won": "🏆 Играч {winner} спечели.",
        "status_new_game": "🔄 Нова игра! Поставете кораб с размер {size}",

        "player_label": "Играч {pid}",
        "eliminated_suffix": "  (елиминиран)",
        "status_eliminated_self": "☠️ Вие бяхте елиминиран.",
        "status_your_turn": "👉 ВИЕ СТЕ НА ХОД! Изберете квадратче и стреляйте!",
        "status_waiting_turn": "⏳ Изчакване хода на Играч {pid}...",
    },
    "hr": {
        "app_title": "Mrežne Podmornice Pro (2-4 igrača)",
        "lbl_language": "Jezik:",
        "lbl_role": "Uloga:",
        "role_host": "Domaćin (Igrač 1)",
        "role_client": "Klijent (Pridruži se)",
        "lbl_players": "Broj igrača:",
        "players_n": "{n} igrača",
        "lbl_ip": "IP:",
        "btn_find_ip": "📍 Pronađi IP",
        "tooltip_find_ip": "Automatski otkriva vašu lokalnu IP adresu",
        "lbl_port": "Port:",
        "btn_connect": "Stvori / Pridruži se predvorju",
        "status_welcome": "Dobrodošli! Stvorite predvorje ili se pridružite postojećem.",
        "btn_rotate_h": "Zakreni brod: Vodoravno [R]",
        "btn_rotate_v": "Zakreni brod: Okomito [R]",
        "btn_auto_place": "🎲 Automatsko postavljanje",
        "btn_play_again": "🔄 Igraj ponovno",
        "lbl_my_fleet": "<b>VAŠA FLOTA (Vlastita ploča)</b>",
        "lbl_radar": "<b>NADAPNI RADAR (Pucanje)</b>",
        "lbl_target_player": "Ciljani igrač:",

        "status_ip_found": "IP automatski pronađen: {ip}",
        "dlg_ip_title": "Otkrivanje IP-a",
        "dlg_ip_fail": "Nije moguće odrediti lokalni IP: {err}",

        "status_place_ship": "Postavite brod veličine {size}",
        "status_all_placed_wait": "Svi brodovi postavljeni! Čekanje ostalih igrača...",
        "dlg_invalid_title": "Nevaljano",
        "dlg_invalid_ship": "Brod ne stane ovdje ili se preklapa!",
        "status_auto_placed": "Svi brodovi automatski postavljeni (s razmakom)! Signal spremnosti poslan.",

        "dlg_wait_title": "Čekajte",
        "dlg_wait_placement": "Faza postavljanja još traje!",
        "dlg_not_turn_title": "Niste na potezu!",
        "dlg_not_turn_msg": "Trenutačno niste na potezu!",
        "dlg_error_title": "Pogreška",
        "dlg_no_target": "Nije pronađen valjan cilj!",
        "dlg_already_shot_title": "Već gađano",
        "dlg_already_shot_msg": "Već ste pucali u ovo polje!",

        "status_lobby_open": "Predvorje otvoreno! Čekanje još {n} igrača...",
        "dlg_conn_fail_msg": "Povezivanje nije uspjelo:\n{err}",

        "status_connected": "Povezani kao Igrač {pid}! Postavite svoje brodove.",
        "status_hit": "💥 POGODAK! Vaš brod je pogođen.",
        "status_miss": "🌊 PROMAŠAJ! Voda.",
        "status_player_eliminated": "☠️ Igrač {pid} je eliminiran! Njegova ploča je otkrivena.",
        "status_radar_handover": "📡 Podaci o pucanju eliminiranog igrača preuzeti.",
        "status_hit_on": "💥 POGODAK! Igrač {target} je pogođen.",
        "status_miss_on": "🌊 PROMAŠAJ protiv Igrača {target}.",
        "status_player_left": "🔌 Igrač {pid} je izgubio vezu i eliminiran je.",
        "status_host_lost": "🔌 Veza s domaćinom je izgubljena. Igra se ne može nastaviti.",
        "status_you_won": "🏆 POBIJEDILI STE!",
        "status_player_won": "🏆 Igrač {winner} je pobijedio.",
        "status_new_game": "🔄 Nova igra! Postavite brod veličine {size}",

        "player_label": "Igrač {pid}",
        "eliminated_suffix": "  (eliminiran)",
        "status_eliminated_self": "☠️ Eliminirani ste.",
        "status_your_turn": "👉 VI STE NA POTEZU! Odaberite polje i pucajte!",
        "status_waiting_turn": "⏳ Čekanje na potez Igrača {pid}...",
    },
    "sr": {
        "app_title": "Мултиплејер Потопање бродова Pro (2-4 играча)",
        "lbl_language": "Језик:",
        "lbl_role": "Улога:",
        "role_host": "Домаћин (Играч 1)",
        "role_client": "Клијент (Придружи се)",
        "lbl_players": "Број играча:",
        "players_n": "{n} играча",
        "lbl_ip": "IP:",
        "btn_find_ip": "📍 Пронађи IP",
        "tooltip_find_ip": "Аутоматски открива вашу локалну IP адресу",
        "lbl_port": "Порт:",
        "btn_connect": "Креирај / Придружи се лобију",
        "status_welcome": "Добродошли! Креирајте лоби или се придружите постојећем.",
        "btn_rotate_h": "Заротирај брод: Хоризонтално [R]",
        "btn_rotate_v": "Заротирај брод: Вертикално [R]",
        "btn_auto_place": "🎲 Аутоматско постављање",
        "btn_play_again": "🔄 Играј поново",
        "lbl_my_fleet": "<b>ВАША ФЛОТА (Сопствена табла)</b>",
        "lbl_radar": "<b>РАДАР НАПАДА (Гађање)</b>",
        "lbl_target_player": "Циљани играч:",

        "status_ip_found": "IP аутоматски пронађен: {ip}",
        "dlg_ip_title": "Откривање IP-а",
        "dlg_ip_fail": "Није могуће одредити локални IP: {err}",

        "status_place_ship": "Поставите брод величине {size}",
        "status_all_placed_wait": "Сви бродови постављени! Чекање осталих играча...",
        "dlg_invalid_title": "Неважеће",
        "dlg_invalid_ship": "Брод не стаје овде или се преклапа!",
        "status_auto_placed": "Сви бродови су аутоматски постављени (са размаком)! Сигнал спремности послат.",

        "dlg_wait_title": "Чекајте",
        "dlg_wait_placement": "Фаза постављања је и даље активна!",
        "dlg_not_turn_title": "Нисте на потезу!",
        "dlg_not_turn_msg": "Тренутно нисте на потезу!",
        "dlg_error_title": "Грешка",
        "dlg_no_target": "Није пронађен важећи циљ!",
        "dlg_already_shot_title": "Већ гађано",
        "dlg_already_shot_msg": "Већ сте пуцали у ово поље!",

        "status_lobby_open": "Лоби је отворен! Чекање још {n} играча...",
        "dlg_conn_fail_msg": "Повезивање није успело:\n{err}",

        "status_connected": "Повезани као Играч {pid}! Поставите своје бродове.",
        "status_hit": "💥 ПОГОДАК! Ваш брод је погођен.",
        "status_miss": "🌊 ПРОМАШАЈ! Вода.",
        "status_player_eliminated": "☠️ Играч {pid} је елиминисан! Његова табла је откривена.",
        "status_radar_handover": "📡 Подаци о пуцању елиминисаног играча преузети.",
        "status_hit_on": "💥 ПОГОДАК! Играч {target} је погођен.",
        "status_miss_on": "🌊 ПРОМАШАЈ против Играча {target}.",
        "status_player_left": "🔌 Играч {pid} је изгубио везу и елиминисан је.",
        "status_host_lost": "🔌 Веза са домаћином је изгубљена. Игра не може да се настави.",
        "status_you_won": "🏆 ПОБЕДИЛИ СТЕ!",
        "status_player_won": "🏆 Играч {winner} је победио.",
        "status_new_game": "🔄 Нова игра! Поставите брод величине {size}",

        "player_label": "Играч {pid}",
        "eliminated_suffix": "  (елиминисан)",
        "status_eliminated_self": "☠️ Елиминисани сте.",
        "status_your_turn": "👉 ВИ СТЕ НА ПОТЕЗУ! Изаберите поље и пуцајте!",
        "status_waiting_turn": "⏳ Чекање на потез Играча {pid}...",
    },
    "sk": {
        "app_title": "Multiplayer Loďky Pro (2-4 hráči)",
        "lbl_language": "Jazyk:",
        "lbl_role": "Rola:",
        "role_host": "Hostiteľ (Hráč 1)",
        "role_client": "Klient (Pripojiť sa)",
        "lbl_players": "Počet hráčov:",
        "players_n": "{n} hráči",
        "lbl_ip": "IP:",
        "btn_find_ip": "📍 Nájsť IP",
        "tooltip_find_ip": "Automaticky zistí vašu lokálnu IP adresu",
        "lbl_port": "Port:",
        "btn_connect": "Vytvoriť / Pripojiť sa do lobby",
        "status_welcome": "Vitajte! Vytvorte lobby alebo sa pripojte k existujúcemu.",
        "btn_rotate_h": "Otočiť loď: Horizontálne [R]",
        "btn_rotate_v": "Otočiť loď: Vertikálne [R]",
        "btn_auto_place": "🎲 Automatické rozmiestnenie",
        "btn_play_again": "🔄 Hrať znova",
        "lbl_my_fleet": "<b>VAŠA FLOTILA (Vlastné pole)</b>",
        "lbl_radar": "<b>ÚTOČNÝ RADAR (Streľba)</b>",
        "lbl_target_player": "Cieľový hráč:",

        "status_ip_found": "IP automaticky nájdená: {ip}",
        "dlg_ip_title": "Detekcia IP",
        "dlg_ip_fail": "Nepadarilo sa zistiť lokálnu IP: {err}",

        "status_place_ship": "Umiestnite loď s dĺžkou {size}",
        "status_all_placed_wait": "Všetky lode rozmiestnené! Čakanie na ostatných hráčov...",
        "dlg_invalid_title": "Neplatné",
        "dlg_invalid_ship": "Loď sa sem nezmestí alebo sa prekrýva!",
        "status_auto_placed": "Všetky lode automaticky rozmiestnené (s rozostupmi)! Signál pripravenosti odoslaný.",

        "dlg_wait_title": "Čakajte",
        "dlg_wait_placement": "Fáza rozmiestňovania stále prebieha!",
        "dlg_not_turn_title": "Nie ste na rade!",
        "dlg_not_turn_msg": "Momentálne nie ste na rade!",
        "dlg_error_title": "Chyba",
        "dlg_no_target": "Nenašiel sa žiadny platný cieľ!",
        "dlg_already_shot_title": "Už vystrelené",
        "dlg_already_shot_msg": "Na toto pole ste už strieľali!",

        "status_lobby_open": "Lobby otvorené! Čakanie na ďalších {n} hráčov...",
        "dlg_conn_fail_msg": "Pripojenie zlyhalo:\n{err}",

        "status_connected": "Pripojený ako Hráč {pid}! Rozmiestnite svoje lode.",
        "status_hit": "💥 ZÁSAH! Vaša loď bola zasiahnutá.",
        "status_miss": "🌊 VODA! Vedľa.",
        "status_player_eliminated": "☠️ Hráč {pid} bol vyradený! Jeho pole bolo odhalené.",
        "status_radar_handover": "📡 Údaje streľby vyradeného hráča boli prevzaté.",
        "status_hit_on": "💥 ZÁSAH! Hráč {target} bol zasiahnutý.",
        "status_miss_on": "🌊 VODA proti hráčovi {target}.",
        "status_player_left": "🔌 Hráč {pid} stratil spojenie a bol vyradený.",
        "status_host_lost": "🔌 Spojenie s hostiteľom sa stratilo. Hra nemôže pokračovať.",
        "status_you_won": "🏆 VYHRAL SI!",
        "status_player_won": "🏆 Hráč {winner} vyhral.",
        "status_new_game": "🔄 Nová hra! Umiestnite loď s dĺžkou {size}",

        "player_label": "Hráč {pid}",
        "eliminated_suffix": "  (vyradený)",
        "status_eliminated_self": "☠️ Boli ste vyradený.",
        "status_your_turn": "👉 SI NA RADE! Vyber pole a vystrel!",
        "status_waiting_turn": "⏳ Čakanie na ťah Hráča {pid}...",
    },
    "lt": {
        "app_title": "Daugėlio žaidėjų Laivų mūšis Pro (2-4 žaidėjai)",
        "lbl_language": "Kalba:",
        "lbl_role": "Rolė:",
        "role_host": "Šeimininkas (1 žaidėjas)",
        "role_client": "Klientas (Prisijungti)",
        "lbl_players": "Žaidėjų skaičius:",
        "players_n": "{n} žaidėjai",
        "lbl_ip": "IP:",
        "btn_find_ip": "📍 Rasti IP",
        "tooltip_find_ip": "Automatiškai nustato jūsų vietinio tinklo IP",
        "lbl_port": "Prievadas:",
        "btn_connect": "Sukurti / Prisijungti prie kambario",
        "status_welcome": "Sveiki! Sukurkite kambarį arba prisijunkite prie esamo.",
        "btn_rotate_h": "Pasukti laivą: Horizontaliai [R]",
        "btn_rotate_v": "Pasukti laivą: Vertikaliai [R]",
        "btn_auto_place": "🎲 Automatinis išdėstymas",
        "btn_play_again": "🔄 Žaisti dar kartą",
        "lbl_my_fleet": "<b>JŪSŲ LAIVYNAS (Sava lenta)</b>",
        "lbl_radar": "<b>ATAKOS RADARAS (Šaudymas)</b>",
        "lbl_target_player": "Tikslinis žaidėjas:",

        "status_ip_found": "IP automatiškai rastas: {ip}",
        "dlg_ip_title": "IP nustatymas",
        "dlg_ip_fail": "Nepavyko nustatyti vietinio IP: {err}",

        "status_place_ship": "Padėkite laivą, kurio dydis {size}",
        "status_all_placed_wait": "Visi laivai išdėstyti! Laukiama kitų žaidėjų...",
        "dlg_invalid_title": "Netinkama",
        "dlg_invalid_ship": "Laivas čia netelpa arba susikerta!",
        "status_auto_placed": "Visi laivai automatiškai išdėstyti (su tarpais)! Pasirengimo signalas išsiųstas.",

        "dlg_wait_title": "Laukite",
        "dlg_wait_placement": "Išdėstymo etapas dar vyksta!",
        "dlg_not_turn_title": "Ne jūsų ėjimas!",
        "dlg_not_turn_msg": "Šiuo metu ne jūsų ėjimas!",
        "dlg_error_title": "Klaida",
        "dlg_no_target": "Nerastas tinkamas tikslas!",
        "dlg_already_shot_title": "Jau šauta",
        "dlg_already_shot_msg": "Jūs jau šovėte į šį langelį!",

        "status_lobby_open": "Kambarys atidarytas! Laukiama dar {n} žaidėjo(-ų)...",
        "dlg_conn_fail_msg": "Prisijungti nepavyko:\n{err}",

        "status_connected": "Prisijungta kaip {pid} žaidėjas! Išdėstykite savo laivus.",
        "status_hit": "💥 PATAISYTA! Jūsų laivas kliudytas.",
        "status_miss": "🌊 PRO ŠALĮ! Vanduo.",
        "status_player_eliminated": "☠️ Žaidėjas {pid} pašalintas! Jo lenta atskleista.",
        "status_radar_handover": "📡 Pašalinto žaidėjo šūvių duomenys perimti.",
        "status_hit_on": "💥 PATAISYTA! Žaidėjas {target} kliudytas.",
        "status_miss_on": "🌊 PRO ŠALĮ prieš žaidėją {target}.",
        "status_player_left": "🔌 Žaidėjas {pid} prarado ryšį ir buvo pašalintas.",
        "status_host_lost": "🔌 Ryšys su šeimininku prarastas. Žaidimas negali būti tęsiamas.",
        "status_you_won": "🏆 JŪS LAIMĖJOTE!",
        "status_player_won": "🏆 Žaidėjas {winner} laimėjo.",
        "status_new_game": "🔄 Naujas žaidimas! Padėkite laivą, kurio dydis {size}",

        "player_label": "Žaidėjas {pid}",
        "eliminated_suffix": "  (pašalintas)",
        "status_eliminated_self": "☠️ Jūs buvote pašalintas.",
        "status_your_turn": "👉 JŪSŲ ĖJIMAS! Pasirinkite langelį ir šaukite!",
        "status_waiting_turn": "⏳ Laukiama žaidėjo {pid} ėjimo...",
    },
    "lv": {
        "app_title": "Daudzspēlētāju Kuģu kauja Pro (2-4 spēlētāji)",
        "lbl_language": "Valoda:",
        "lbl_role": "Loma:",
        "role_host": "Mājinieks (1. spēlētājs)",
        "role_client": "Klients (Pievienoties)",
        "lbl_players": "Spēlētāju skaits:",
        "players_n": "{n} spēlētāji",
        "lbl_ip": "IP:",
        "btn_find_ip": "📍 Atrast IP",
        "tooltip_find_ip": "Automātiski nosaka jūsu lokālā tīkla IP",
        "lbl_port": "Ports:",
        "btn_connect": "Izveidot / Pievienoties telpai",
        "status_welcome": "Laipni lūdzam! Lūdzu, izveidojiet telpu vai pievienojieties esošajai.",
        "btn_rotate_h": "Pagriezt kuģi: Horizontāli [R]",
        "btn_rotate_v": "Pagriezt kuģi: Vertikāli [R]",
        "btn_auto_place": "🎲 Automātiskā izvietošana",
        "btn_play_again": "🔄 Spēlēt vēlreiz",
        "lbl_my_fleet": "<b>JŪSU FLOTE (Sava tērauds)</b>",
        "lbl_radar": "<b>UZBRUKUMA RADARS (Šaušana)</b>",
        "lbl_target_player": "Mērķa spēlētājs:",

        "status_ip_found": "IP automātiski atrasts: {ip}",
        "dlg_ip_title": "IP noteikšana",
        "dlg_ip_fail": "Neizdevās noteikt lokālo IP: {err}",

        "status_place_ship": "Novietojiet kuģi ar izmēru {size}",
        "status_all_placed_wait": "Visi kuģi novietoti! Gaida citus spēlētājus...",
        "dlg_invalid_title": "Nederīgs",
        "dlg_invalid_ship": "Kuģis šeit neiederas vai pārklājas!",
        "status_auto_placed": "Visi kuģi automātiski novietoti (ar atstarpi)! Gatavības signāls nosūtīts.",

        "dlg_wait_title": "Gaidiet",
        "dlg_wait_placement": "Izvietošanas fāze joprojām ir aktīva!",
        "dlg_not_turn_title": "Nav jūsu gājiens!",
        "dlg_not_turn_msg": "Šobrīd nav jūsu gājiens!",
        "dlg_error_title": "Kļūda",
        "dlg_no_target": "Nav atrasts derīgs mērķis!",
        "dlg_already_shot_title": "Jau apšaudīts",
        "dlg_already_shot_msg": "Jūs jau esat šāvis šajā šūnā!",

        "status_lobby_open": "Telpa atvērta! Gaida vēl {n} spēlētāju(s)...",
        "dlg_conn_fail_msg": "Savienojums neizdevās:\n{err}",

        "status_connected": "Pievienojies kā {pid}. spēlētājs! Izvietojiet savus kuģus.",
        "status_hit": "💥 TRĀPĪTS! Jūsu kuģim trāpīts.",
        "status_miss": "🌊 GARĀM! Ūdens.",
        "status_player_eliminated": "☠️ Spēlētājs {pid} ir eliminēts! Viņa laukums tika atklāts.",
        "status_radar_handover": "📡 Eliminētā spēlētāja šāvienu dati pārņemti.",
        "status_hit_on": "💥 TRĀPĪTS! Spēlētājam {target} trāpīts.",
        "status_miss_on": "🌊 GARĀM pret spēlētāju {target}.",
        "status_player_left": "🔌 Spēlētājs {pid} zaudēja savienojumu un tika eliminēts.",
        "status_host_lost": "🔌 Savienojums ar mājinieku zaudēts. Spēli nevar turpināt.",
        "status_you_won": "🏆 JŪS UZVARĒJĀT!",
        "status_player_won": "🏆 Spēlētājs {winner} uzvarēja.",
        "status_new_game": "🔄 Jauna spēle! Novietojiet kuģi ar izmēru {size}",

        "player_label": "Spēlētājs {pid}",
        "eliminated_suffix": "  (eliminēts)",
        "status_eliminated_self": "☠️ Jūs tikāt eliminēts.",
        "status_your_turn": "👉 JŪSU GĀJIENS! Izvēlieties šūnu un šaujiet!",
        "status_waiting_turn": "⏳ Gaida {pid}. spēlētāja gājienu...",
    },
    "et": {
        "app_title": "Mitmemängija Laevade pommitamine Pro (2-4 mängijat)",
        "lbl_language": "Keel:",
        "lbl_role": "Roll:",
        "role_host": "Looja (Mängija 1)",
        "role_client": "Kliendiprogramm (Liitu)",
        "lbl_players": "Mängijate arv:",
        "players_n": "{n} mängijat",
        "lbl_ip": "IP:",
        "btn_find_ip": "📍 Leia IP",
        "tooltip_find_ip": "Tuvastab automaatselt teie kohaliku võrgu IP",
        "lbl_port": "Port:",
        "btn_connect": "Loo / Liitu ruumiga",
        "status_welcome": "Tere tulemast! Palun loo ruum või liitu olemasolevaga.",
        "btn_rotate_h": "Pööra laeva: Horisontaalselt [R]",
        "btn_rotate_v": "Pööra laeva: Vertikaalselt [R]",
        "btn_auto_place": "🎲 Automaatne paigutus",
        "btn_play_again": "🔄 Mängi uuesti",
        "lbl_my_fleet": "<b>TEIE LAEVASTIK (Oma laud)</b>",
        "lbl_radar": "<b>RÜNNAKARADAR (Laskmine)</b>",
        "lbl_target_player": "Sihtmängija:",

        "status_ip_found": "IP automaatselt leitud: {ip}",
        "dlg_ip_title": "IP tuvastamine",
        "dlg_ip_fail": "Kohalikku IP-d ei õnnestunud tuvastada: {err}",

        "status_place_ship": "Paiguta laev suurusega {size}",
        "status_all_placed_wait": "Kõik laevad paigutatud! Oodatakse teisi mängijaid...",
        "dlg_invalid_title": "Kehtetu",
        "dlg_invalid_ship": "Laev ei mahu siia või kattub teisega!",
        "status_auto_placed": "Kõik laevad automaatselt paigutatud (vahedega)! Valmisolekusignaal saadetud.",

        "dlg_wait_title": "Oota",
        "dlg_wait_placement": "Paigutusfaas on veel pooleli!",
        "dlg_not_turn_title": "Pole sinu käik!",
        "dlg_not_turn_msg": "Hetkel pole sinu käik!",
        "dlg_error_title": "Viga",
        "dlg_no_target": "Kehtivat sihtmärki ei leitud!",
        "dlg_already_shot_title": "Juba tulistatud",
        "dlg_already_shot_msg": "Oled sellesse ruutu juba tulistanud!",

        "status_lobby_open": "Ruum avatud! Oodatakse veel {n} mängijat...",
        "dlg_conn_fail_msg": "Ühendus ebaõnnestus:\n{err}",

        "status_connected": "Ühendatud kui Mängija {pid}! Paiguta oma laevad.",
        "status_hit": "💥 PIHTIS! Sinu laev sai pihta.",
        "status_miss": "🌊 MÖÖDA! Vesi.",
        "status_player_eliminated": "☠️ Mängija {pid} on välja langenud! Tema laud avaldati.",
        "status_radar_handover": "📡 Väljalangenud mängija laskeandmed üle võetud.",
        "status_hit_on": "💥 PIHTIS! Mängija {target} sai pihta.",
        "status_miss_on": "🌊 MÖÖDA mängija {target} vastu.",
        "status_player_left": "🔌 Mängija {pid} kaotas ühenduse ja langes välja.",
        "status_host_lost": "🔌 Ühendus loojaga kaotatud. Mäng ei saa jätkuda.",
        "status_you_won": "🏆 SINA VÕITSID!",
        "status_player_won": "🏆 Mängija {winner} võitis.",
        "status_new_game": "🔄 Uus mäng! Paiguta laev suurusega {size}",

        "player_label": "Mängija {pid}",
        "eliminated_suffix": "  (välja langenud)",
        "status_eliminated_self": "☠️ Oled välja langenud.",
        "status_your_turn": "👉 SINU KÄIK! Vali ruut ja tulista!",
        "status_waiting_turn": "⏳ Oodatakse mängija {pid} käiku...",
    },

}


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

        # Einstellungen (Sprache etc.) betriebssystemgerecht laden - siehe
        # SETTINGS_ORG/SETTINGS_APP oben für die jeweiligen Speicherorte.
        self.settings = QSettings(QSettings.IniFormat, QSettings.UserScope, SETTINGS_ORG, SETTINGS_APP)
        saved_lang = self.settings.value("language", "de")
        self.lang = saved_lang if saved_lang in LANG else "de"  # Fallback, falls z.B. eine alte/unbekannte Sprache gespeichert war

        self.setWindowTitle(self._t("app_title"))
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

    def _t(self, key, **kwargs):
        """Übersetzungshelfer: holt den Text in der aktuell eingestellten
        Sprache und füllt evtl. Platzhalter (z.B. {pid}, {size}) ein."""
        text = LANG.get(self.lang, LANG["de"]).get(key, key)
        if kwargs:
            return text.format(**kwargs)
        return text

    def auto_detect_ip(self):
        """Ermittelt die echte lokale Netzwerk-IP des PCs."""
        try:
            # Trick: Erstelle einen Dummy-Socket, um die primäre Route ins Netzwerk zu finden
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            self.txt_ip.setText(local_ip)
            self.lbl_status.setText(self._t("status_ip_found", ip=local_ip))
        except Exception as e:
            # Fallback auf Loopback, falls kein Netzwerk aktiv ist
            self.txt_ip.setText("127.0.0.1")
            QMessageBox.warning(self, self._t("dlg_ip_title"), self._t("dlg_ip_fail", err=e))

    def on_language_change(self, index):
        codes = list(LANGUAGE_NAMES.keys())
        if 0 <= index < len(codes):
            self.lang = codes[index]
            self.settings.setValue("language", self.lang)
            self.retranslate_ui()

    def retranslate_ui(self):
        """Aktualisiert alle aktuell sichtbaren, statischen Texte auf die
        neu gewählte Sprache, ohne die App neu starten zu müssen."""
        self.setWindowTitle(self._t("app_title"))

        self.lbl_role_text.setText(self._t("lbl_role"))
        was_host_index = self.role_combo.currentIndex()
        self.role_combo.blockSignals(True)
        self.role_combo.clear()
        self.role_combo.addItems([self._t("role_host"), self._t("role_client")])
        self.role_combo.setCurrentIndex(was_host_index if was_host_index >= 0 else 0)
        self.role_combo.blockSignals(False)

        self.lbl_players.setText(self._t("lbl_players"))
        was_num_index = self.combo_num_players.currentIndex()
        self.combo_num_players.blockSignals(True)
        self.combo_num_players.clear()
        self.combo_num_players.addItems([self._t("players_n", n=n) for n in (2, 3, 4)])
        self.combo_num_players.setCurrentIndex(was_num_index if was_num_index >= 0 else 0)
        self.combo_num_players.blockSignals(False)

        self.lbl_ip_text.setText(self._t("lbl_ip"))
        self.btn_get_ip.setText(self._t("btn_find_ip"))
        self.btn_get_ip.setToolTip(self._t("tooltip_find_ip"))
        self.lbl_port_text.setText(self._t("lbl_port"))
        self.btn_connect.setText(self._t("btn_connect"))

        self.btn_rotate.setText(
            self._t("btn_rotate_v") if self.placement_orientation == 'V' else self._t("btn_rotate_h")
        )
        self.btn_auto_place.setText(self._t("btn_auto_place"))
        self.btn_play_again.setText(self._t("btn_play_again"))

        self.lbl_my_fleet.setText(self._t("lbl_my_fleet"))
        self.lbl_radar.setText(self._t("lbl_radar"))
        self.lbl_target_player.setText(self._t("lbl_target_player"))

        # Ziel-Spieler-Dropdown neu befüllen (enthält übersetzte Labels)
        if self.combo_target_player.count() > 0:
            self.setup_target_dropdown()

        # Status-Zeile: nach Möglichkeit anhand des aktuellen Spielzustands
        # neu erzeugen, statt den (evtl. veralteten) Text stehen zu lassen.
        if not self.placement_phase and self.active_players:
            self.update_turn_status()
        else:
            self.lbl_status.setText(self._t("status_welcome"))

    def init_ui(self):
        main_widget = QWidget()
        self.main_layout = QVBoxLayout()

        # ----------------- TOP BAR: LOBBY & VERBINDUNG -----------------
        self.top_frame = QFrame()
        top_layout = QHBoxLayout()

        self.lbl_language_text = QLabel(self._t("lbl_language"))
        self.combo_language = QComboBox()
        self.combo_language.addItems(list(LANGUAGE_NAMES.values()))
        self.combo_language.setCurrentIndex(list(LANGUAGE_NAMES.keys()).index(self.lang))
        self.combo_language.currentIndexChanged.connect(self.on_language_change)

        self.lbl_role_text = QLabel(self._t("lbl_role"))
        self.role_combo = QComboBox()
        self.role_combo.addItems([self._t("role_host"), self._t("role_client")])
        self.role_combo.currentIndexChanged.connect(self.on_role_change)

        self.lbl_players = QLabel(self._t("lbl_players"))
        self.combo_num_players = QComboBox()
        self.combo_num_players.addItems([self._t("players_n", n=n) for n in (2, 3, 4)])

        self.txt_ip = QLineEdit("192.168.178.3")
        self.txt_port = QLineEdit("5555")
        self.txt_ip.setFixedWidth(110)
        self.txt_port.setFixedWidth(50)

        # NEU: Button zum automatischen Ermitteln der echten IP
        self.btn_get_ip = QPushButton(self._t("btn_find_ip"))
        self.btn_get_ip.clicked.connect(self.auto_detect_ip)
        self.btn_get_ip.setToolTip(self._t("tooltip_find_ip"))

        self.btn_connect = QPushButton(self._t("btn_connect"))
        self.btn_connect.clicked.connect(self.start_network)

        self.lbl_ip_text = QLabel(self._t("lbl_ip"))
        self.lbl_port_text = QLabel(self._t("lbl_port"))

        top_layout.addWidget(self.lbl_language_text)
        top_layout.addWidget(self.combo_language)
        top_layout.addWidget(self.lbl_role_text)
        top_layout.addWidget(self.role_combo)
        top_layout.addWidget(self.lbl_players)
        top_layout.addWidget(self.combo_num_players)
        top_layout.addWidget(self.lbl_ip_text)
        top_layout.addWidget(self.txt_ip)
        top_layout.addWidget(self.btn_get_ip)  # Der neue Button
        top_layout.addWidget(self.lbl_port_text)
        top_layout.addWidget(self.txt_port)
        top_layout.addWidget(self.btn_connect)
        top_layout.addStretch()

        self.top_frame.setLayout(top_layout)
        self.main_layout.addWidget(self.top_frame)

        # ----------------- STATUS & STEUERUNG -----------------
        status_layout = QHBoxLayout()
        self.lbl_status = QLabel(self._t("status_welcome"))
        self.lbl_status.setFont(QFont("Arial", 11, QFont.Bold))
        status_layout.addWidget(self.lbl_status)
        
        self.btn_rotate = QPushButton(self._t("btn_rotate_h"))
        self.btn_rotate.clicked.connect(self.toggle_orientation)
        self.btn_auto_place = QPushButton(self._t("btn_auto_place"))
        self.btn_auto_place.clicked.connect(self.auto_place_ships)

        self.btn_play_again = QPushButton(self._t("btn_play_again"))
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
        self.lbl_my_fleet = QLabel(self._t("lbl_my_fleet"))
        left_box.addWidget(self.lbl_my_fleet)
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
        self.lbl_radar = QLabel(self._t("lbl_radar"))
        radar_header.addWidget(self.lbl_radar)
        self.lbl_target_player = QLabel(self._t("lbl_target_player"))
        radar_header.addWidget(self.lbl_target_player)
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
            self.btn_rotate.setText(self._t("btn_rotate_v"))
        else:
            self.placement_orientation = 'H'
            self.btn_rotate.setText(self._t("btn_rotate_h"))

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
                self.lbl_status.setText(self._t("status_place_ship", size=SHIP_SIZES[self.placement_index]))
            else:
                self.lbl_status.setText(self._t("status_all_placed_wait"))
                self.btn_auto_place.setEnabled(False)
                self.btn_rotate.setEnabled(False)
                self.send_network_data({"type": "READY", "player": self.player_id})
        else:
            QMessageBox.warning(self, self._t("dlg_invalid_title"), self._t("dlg_invalid_ship"))

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
        self.lbl_status.setText(self._t("status_auto_placed"))
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
            QMessageBox.warning(self, self._t("dlg_wait_title"), self._t("dlg_wait_placement"))
            return

        # Ausgeschiedene Spieler dürfen nicht mehr schießen.
        if self.player_id not in self.active_players:
            return

        # STRENGE PRÜFUNG: Ist der Spieler wirklich an der Reihe?
        if self.current_turn != self.player_id:
            QMessageBox.warning(self, self._t("dlg_not_turn_title"), self._t("dlg_not_turn_msg"))
            return

        # Das automatische Ziel basierend auf der festen Reihenfolge ermitteln
        target_id = self.get_next_target_for(self.player_id)
        if not target_id:
            QMessageBox.warning(self, self._t("dlg_error_title"), self._t("dlg_no_target"))
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
            QMessageBox.warning(self, self._t("dlg_already_shot_title"), self._t("dlg_already_shot_msg"))
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
            self.lbl_status.setText(self._t("status_lobby_open", n=self.num_players - 1))
            self.top_frame.setEnabled(False)
        else:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                self.client_socket.connect((ip, port))
                self.recv_buffers[self.client_socket] = ""
                threading.Thread(target=self.listen_to_server, daemon=True).start()
                self.top_frame.setEnabled(False)
            except Exception as e:
                QMessageBox.critical(self, self._t("dlg_error_title"), self._t("dlg_conn_fail_msg", err=str(e)))

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
            self.lbl_status.setText(self._t("status_connected", pid=self.player_id))
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
            self.lbl_status.setText(self._t("status_hit") if hit else self._t("status_miss"))

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
            self.lbl_status.setText(self._t("status_player_eliminated", pid=pid))

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
                self.lbl_status.setText(self._t("status_radar_handover"))

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
                self._t("status_hit_on", target=target) if hit else self._t("status_miss_on", target=target)
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
            self.lbl_status.setText(self._t("status_player_left", pid=pid))

        elif mtype == "_HOST_CONNECTION_LOST":
            self.current_turn = -1
            self.combo_target_player.setEnabled(False)
            self.lbl_status.setText(self._t("status_host_lost"))

        elif mtype == "GAME_OVER":
            winner = int(msg["winner"])

            if "active_players" in msg:
                self.active_players = [int(x) for x in msg["active_players"]]

            self.current_turn = -1
            self.combo_target_player.setEnabled(False)
            self.btn_play_again.setVisible(True)

            self.lbl_status.setText(
                self._t("status_you_won")
                if winner == self.player_id
                else self._t("status_player_won", winner=winner)
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

        self.btn_rotate.setText(self._t("btn_rotate_h"))
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

        self.lbl_status.setText(self._t("status_new_game", size=SHIP_SIZES[0]))

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
            label = self._t("player_label", pid=pid)
            if pid not in self.active_players:
                label += self._t("eliminated_suffix")
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
            self.lbl_status.setText(self._t("status_eliminated_self"))
            self.lbl_status.setStyleSheet(
                "color: #757575; font-weight: bold; font-size: 14px;"
            )
        elif self.current_turn == self.player_id:
            self.lbl_status.setText(self._t("status_your_turn"))
            self.lbl_status.setStyleSheet(
                "color: #2e7d32; font-weight: bold; font-size: 14px;"
            )
        else:
            self.lbl_status.setText(self._t("status_waiting_turn", pid=self.current_turn))
            self.lbl_status.setStyleSheet(
                "color: #c62828; font-weight: bold; font-size: 14px;"
            )

    def closeEvent(self, event):
        """Schließt beim Beenden des Fensters alle aktiven Sockets sauber.

        Wichtig v.a. unter macOS: Wird ein Socket nicht explizit mit
        shutdown()/close() beendet, bleibt der Port dort oft länger im
        Zustand TIME_WAIT hängen als unter Windows/Linux - ein erneuter
        Start (z.B. erneut als Host auf demselben Port) kann dann
        fehlschlagen, bis das Betriebssystem den Port von selbst freigibt.
        """
        sockets_to_close = []

        if self.client_socket is not None:
            sockets_to_close.append(self.client_socket)

        sockets_to_close.extend(self.client_connections.values())

        for sock in sockets_to_close:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass  # Verbindung war evtl. schon getrennt - kein Problem
            try:
                sock.close()
            except OSError:
                pass

        if self.server_socket is not None:
            try:
                self.server_socket.close()
            except OSError:
                pass

        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # macOS-Fix: Der native "Aqua"-Style ignoriert bei normalen QPushButtons
    # häufig Stylesheet-Vorgaben wie background-color (z.B. für Treffer/
    # Wasser-Markierungen auf dem Spielfeld). Fusion ist plattformunabhängig
    # und respektiert Stylesheets zuverlässig auf allen drei Betriebssystemen.
    app.setStyle("Fusion")
    win = SchiffeVersenkenApp()
    win.show()
    sys.exit(app.exec_())
