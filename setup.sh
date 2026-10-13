#!/usr/bin/env bash
# ==============================================================================
# J.A.R.V.I.S. AI OS — Universal Setup & Orchestration Installer (Native Host)
# Optimiert für CachyOS / Arch Linux & Linux Desktop Integration
# Blueprint by Matthias Haase (Graba92)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
VENV_DIR="$BACKEND_DIR/.venv"

PERM_INSTALL_DIR="$HOME/.local/share/webjarvis"
DESKTOP_DIR="$HOME/.local/share/applications"
ICONS_DIR="$HOME/.local/share/icons/hicolor"
BIN_DIR="$HOME/.local/bin"

# ── Farben für lesbare Terminal-Ausgabe ───────────────────────────────────────
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
RESET='\033[0m'

banner() {
    echo -e "${CYAN}"
    cat << "BANNER_ART"
      ___   _____  ______      __ _____ _____       ____   _____ 
     / / \ |  __ \|  ____/\   / /|_   _/ ____|     / __ \ / ____|
    / / _ \| |__) | |__ /  \ / /   | || (___      | |  | | (___  
   / / ___ \  _  /|  __/ /\ \ /    | | \___ \     | |  | |\___ \ 
  / / /   \ \ | \ \| | / ____ \   _| |_ ____) | _  | |__| |____) |
 /_/_/   \_\_|  \_\_|/_/    \_\ |_____|_____/ (_)  \____/|_____/ 
BANNER_ART
    echo -e "${BOLD}${CYAN}   J.A.R.V.I.S. AI OS — Setup & Deployment Manager${RESET}"
    echo -e "${MAGENTA}   Native CachyOS / Arch Linux Host Installation${RESET}"
    echo -e "${BLUE}──────────────────────────────────────────────────────────────────────────────${RESET}"
}

# ── Erkennungs-Funktionen ───────────────────────────────────────────────────
has_native_install() {
    if [ -f "$VENV_DIR/bin/python3" ] && [ -d "$FRONTEND_DIR/node_modules" ]; then
        return 0
    fi
    return 1
}

print_status() {
    echo -e "${BOLD}${CYAN}[*] Prüfe bestehende Installationen auf deinem System...${RESET}"
    if has_native_install; then
        echo -e "  • ${GREEN}✓ Native Host-Installation:${RESET}  Erkannt (Python venv & Node-Module vorhanden)"
    else
        echo -e "  • ${YELLOW}○ Native Host-Installation:${RESET}  Nicht vollständig installiert"
    fi
    echo -e "${BLUE}──────────────────────────────────────────────────────────────────────────────${RESET}\n"
}

# ── 1. Paketmanager & Systempakete prüfen (Native) ───────────────────────────
install_system_deps() {
    echo -e "${CYAN}[*] Prüfe System-Paketmanager & Basis-Werkzeuge...${RESET}"
    if command -v pacman >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${RESET} CachyOS / Arch Linux erkannt."
        PACKAGES=(nodejs npm python python-pip python-pyqt6 pipewire pipewire-pulse brightnessctl networkmanager bubblewrap libnotify)
        MISSING=()
        for pkg in "${PACKAGES[@]}"; do
            if ! pacman -Qi "$pkg" >/dev/null 2>&1 && ! command -v "$pkg" >/dev/null 2>&1; then
                MISSING+=("$pkg")
            fi
        done
        if [ ${#MISSING[@]} -gt 0 ]; then
            echo -e "  ${YELLOW}!${RESET} Fehlende Pakete: ${MISSING[*]}"
            echo -e "  ${CYAN}Installiere via 'sudo pacman -S --needed' (Passwortabfrage)...${RESET}"
            sudo pacman -S --needed --noconfirm "${MISSING[@]}" || true
        else
            echo -e "  ${GREEN}✓${RESET} Alle Basis-Systempakete sind vorhanden."
        fi
    elif command -v apt-get >/dev/null 2>&1; then
        echo -e "  ${YELLOW}!${RESET} Debian/Ubuntu erkannt."
        sudo apt-get update && sudo apt-get install -y nodejs npm python3-venv python3-pip python3-pyqt6 pipewire bubblewrap libnotify-bin || true
    fi
}

# ── 2. Konfigurationsdateien vorbereiten ──────────────────────────────────────
setup_configs() {
    echo -e "\n${CYAN}[*] Initialisiere Konfigurationsdateien...${RESET}"
    mkdir -p "$BACKEND_DIR/config" "$SCRIPT_DIR/data/lancedb" "$SCRIPT_DIR/data/logs"

    if [ ! -f "$SCRIPT_DIR/.env" ] && [ -f "$SCRIPT_DIR/.env.example" ]; then
        cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
        echo -e "  ${GREEN}✓${RESET} .env aus Vorlage erstellt."
    fi

    if [ ! -f "$BACKEND_DIR/config/api_keys.json" ] && [ -f "$BACKEND_DIR/config/api_keys.example.json" ]; then
        cp "$BACKEND_DIR/config/api_keys.example.json" "$BACKEND_DIR/config/api_keys.json"
        echo -e "  ${GREEN}✓${RESET} backend/config/api_keys.json initialisiert."
    fi

    if [ ! -f "$BACKEND_DIR/config/contacts.json" ] && [ -f "$BACKEND_DIR/config/contacts.example.json" ]; then
        cp "$BACKEND_DIR/config/contacts.example.json" "$BACKEND_DIR/config/contacts.json"
        echo -e "  ${GREEN}✓${RESET} backend/config/contacts.json initialisiert."
    fi

    if [ ! -f "$BACKEND_DIR/config/sandbox_config.json" ]; then
        mkdir -p "$BACKEND_DIR/sandbox_workspace"
        cat << 'EOF' > "$BACKEND_DIR/config/sandbox_config.json"
{
  "allowed_paths": [
    "./sandbox_workspace"
  ]
}
EOF
        echo -e "  ${GREEN}✓${RESET} backend/config/sandbox_config.json initialisiert (./sandbox_workspace)."
    fi
}

# ── 3. Python Virtual Environment (Native) ───────────────────────────────────
setup_python_env() {
    local force_reinstall="${1:-false}"
    echo -e "\n${CYAN}[*] Richte Python Virtual Environment ein ($VENV_DIR)...${RESET}"
    if [ "$force_reinstall" = "true" ] && [ -d "$VENV_DIR" ]; then
        echo -e "  ${YELLOW}!${RESET} Lösche bestehende Virtual Environment für saubere Neuinstallation..."
        rm -rf "$VENV_DIR"
    fi

    if [ ! -f "$VENV_DIR/bin/python3" ]; then
        python3 -m venv "$VENV_DIR"
        echo -e "  ${GREEN}✓${RESET} Virtual Environment erfolgreich angelegt."
    fi

    echo -e "  ${CYAN}• Installiere / aktualisiere Python-Abhängigkeiten via pip...${RESET}"
    "$VENV_DIR/bin/pip" install --upgrade pip >/dev/null
    "$VENV_DIR/bin/pip" install -r "$BACKEND_DIR/requirements.txt"
    echo -e "  ${GREEN}✓${RESET} Python-Abhängigkeiten erfolgreich installiert."
}

# ── 4. Frontend Node-Pakete (Native) ─────────────────────────────────────────
setup_node_deps() {
    local force_reinstall="${1:-false}"
    echo -e "\n${CYAN}[*] Richte Frontend Node-Pakete ein (Next.js 15 / Three.js)...${RESET}"
    if [ "$force_reinstall" = "true" ] && [ -d "$FRONTEND_DIR/node_modules" ]; then
        rm -rf "$FRONTEND_DIR/node_modules" "$FRONTEND_DIR/package-lock.json"
    fi

    if [ -d "$FRONTEND_DIR" ]; then
        (cd "$FRONTEND_DIR" && npm install --no-fund --no-audit --loglevel=error > /dev/null)
        echo -e "  ${GREEN}✓${RESET} Frontend-Abhängigkeiten bereit."
    fi
}

# ── 5. Berechtigungen vergeben ───────────────────────────────────────────────
make_executables() {
    echo -e "\n${CYAN}[*] Setze Ausführungsrechte auf Starter- & Kontrollskripte...${RESET}"
    chmod +x "$SCRIPT_DIR"/*.sh "$SCRIPT_DIR"/*.py 2>/dev/null || true
    echo -e "  ${GREEN}✓${RESET} Berechtigungen gesetzt."
}

# ── 6. Permanente OS-Installation & Synchronisation ──────────────────────────
sync_to_permanent_os_install() {
    if [ "$SCRIPT_DIR" != "$PERM_INSTALL_DIR" ]; then
        echo -e "\n${BOLD}${CYAN}[*] Installiere WebJarvis als feste OS-Anwendung ($PERM_INSTALL_DIR)...${RESET}"
        mkdir -p "$PERM_INSTALL_DIR"
        if command -v rsync >/dev/null 2>&1; then
            rsync -a \
                --exclude='frontend/.next' \
                --exclude='data/logs' \
                "$SCRIPT_DIR/" "$PERM_INSTALL_DIR/"
        else
            cp -r "$SCRIPT_DIR/"* "$PERM_INSTALL_DIR/" 2>/dev/null || true
            cp -r "$SCRIPT_DIR/".* "$PERM_INSTALL_DIR/" 2>/dev/null || true
        fi
        chmod +x "$PERM_INSTALL_DIR"/*.sh "$PERM_INSTALL_DIR"/*.py 2>/dev/null || true
        echo -e "  ${GREEN}✓${RESET} WebJarvis OS-Dateistruktur synchronisiert."
    fi
}

# ── 7. Desktop Integration: App-Manager & Startleiste (KDE Plasma) ───────────
install_desktop_integration() {
    echo -e "\n${BOLD}${CYAN}[*] Registriere App-Manager & Startleisten-Einträge (KDE Plasma / CachyOS)...${RESET}"
    mkdir -p "$DESKTOP_DIR" "$ICONS_DIR/scalable/apps" "$ICONS_DIR/256x256/apps" "$BIN_DIR"

    # Synchronisiere ins feste OS-Verzeichnis
    if [ "$SCRIPT_DIR" != "$PERM_INSTALL_DIR" ]; then
        sync_to_permanent_os_install
    fi

    local target_dir="$PERM_INSTALL_DIR"
    if [ ! -f "$target_dir/manager.sh" ]; then
        target_dir="$SCRIPT_DIR"
    fi

    # Icons in System-Themes kopieren
    if [ -f "$target_dir/assets/jarvis-manager.svg" ]; then
        cp "$target_dir/assets/jarvis-manager.svg" "$ICONS_DIR/scalable/apps/webjarvis-manager.svg"
    fi
    if [ -f "$target_dir/assets/jarvis-manager.png" ]; then
        cp "$target_dir/assets/jarvis-manager.png" "$ICONS_DIR/256x256/apps/webjarvis-manager.png"
    fi

    # 1. Desktop Entry: Jarvis Manager (Wartungsfenster mit Status, Start/Stop, Autostart & GitHub Updates)
    # WICHTIG: Startet IMMER manager.sh (Wartungsfenster), NIEMALS direkt das ganze Jarvis-System!
    cat << EOF > "$DESKTOP_DIR/jarvis-manager.desktop"
[Desktop Entry]
Name=Jarvis Manager
GenericName=AI OS Maintenance & Control Center
Comment=J.A.R.V.I.S. AI OS Wartungs- und Kontrollzentrum
Exec=$target_dir/manager.sh
Icon=$target_dir/assets/jarvis-manager.png
Terminal=false
Type=Application
Categories=Utility;System;Settings;Development;
Keywords=Jarvis;AI;Assistant;Manager;CachyOS;WebJarvis;Control;
StartupNotify=true
EOF
    chmod +x "$DESKTOP_DIR/jarvis-manager.desktop"

    # 2. Desktop Entry: WebJarvis AI OS (Zeigt ebenfalls auf manager.sh zur Vermeidung von Fehlstarts!)
    cat << EOF > "$DESKTOP_DIR/webjarvis.desktop"
[Desktop Entry]
Name=WebJarvis AI OS
GenericName=AI Operating System
Comment=J.A.R.V.I.S. AI OS Kontrollzentrum
Exec=$target_dir/manager.sh
Icon=$target_dir/assets/jarvis-manager.png
Terminal=false
Type=Application
Categories=Utility;Development;
StartupNotify=true
EOF
    chmod +x "$DESKTOP_DIR/webjarvis.desktop"

    # CLI Shortcuts in ~/.local/bin
    ln -sf "$target_dir/manager.sh" "$BIN_DIR/jarvis-manager"
    ln -sf "$target_dir/manager.sh" "$BIN_DIR/jarvis"
    ln -sf "$target_dir/manager.sh" "$BIN_DIR/webjarvis"
    ln -sf "$target_dir/stop.sh" "$BIN_DIR/jarvis-stop"

    # KDE Plasma / XDG Desktop Database aktualisieren
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
    fi
    if command -v kbuildsycoca6 >/dev/null 2>&1; then
        kbuildsycoca6 2>/dev/null || true
    fi

    echo -e "  ${GREEN}✓${RESET} 'Jarvis Manager' im Startmenü registriert (öffnet das Wartungsfenster manager.py)."
    echo -e "  ${GREEN}✓${RESET} CLI-Befehl ${BOLD}jarvis-manager${RESET} bereitgestellt."
    echo -e "  ${CYAN}• Ziel-Skript:${RESET} ${BOLD}$target_dir/manager.sh${RESET}"
}

# ── Installations-Ablauf: Nativ ──────────────────────────────────────────────
install_native() {
    echo -e "\n${BOLD}${CYAN}=== [Starte Native Host-Installation] ===${RESET}\n"
    local reinstall="false"
    if has_native_install; then
        echo -e "${YELLOW}[!] Eine native Installation wurde bereits erkannt.${RESET}"
        echo -e "  1) Aktualisieren (Pakete & Abhängigkeiten updaten - Schnell & Erhaltend)"
        echo -e "  2) Sauber Neuinstallieren (venv und node_modules verwerfen & frisch bauen)"
        echo -ne "${BOLD}Wähle eine Option [1-2] (Standard: 1): ${RESET}"
        read -r N_CHOICE
        if [ "$N_CHOICE" = "2" ]; then
            reinstall="true"
        fi
    fi

    install_system_deps
    setup_configs
    setup_python_env "$reinstall"
    setup_node_deps "$reinstall"
    make_executables
    install_desktop_integration

    echo -e "\n${BOLD}${GREEN}==============================================================================${RESET}"
    echo -e "${BOLD}${GREEN}✓ Native Installation erfolgreich abgeschlossen!${RESET}"
    echo -e "Das Wartungsfenster ist im KDE Startmenü als ${BOLD}'Jarvis Manager'${RESET} einsatzbereit."
    echo -e "Dort kannst du Jarvis starten/stoppen, den Status prüfen und Autostart verwalten."
    echo -e "(Jarvis wurde planmäßig nicht automatisch gestartet)."
    echo -e "${BOLD}${GREEN}==============================================================================${RESET}\n"
}

# ── Installations-Ablauf: Update ─────────────────────────────────────────────
perform_update() {
    echo -e "\n${BOLD}${CYAN}=== [WebJarvis Aktualisierung / Update] ===${RESET}\n"
    
    if ! has_native_install; then
        echo -e "${YELLOW}[!] Keine bestehende Installation gefunden. Führe Neuinstallation aus.${RESET}"
        install_native
        return
    fi

    setup_configs
    make_executables

    echo -e "\n${CYAN}[*] Aktualisiere Native Host-Installation...${RESET}"
    setup_python_env "false"
    setup_node_deps "false"
    echo -e "${GREEN}✓ Native Host-Installation auf dem neuesten Stand.${RESET}"

    install_desktop_integration

    echo -e "\n${BOLD}${GREEN}==============================================================================${RESET}"
    echo -e "${BOLD}${GREEN}✓ Aktualisierung erfolgreich durchgeführt!${RESET}"
    echo -e "Das Wartungsfenster ist im Startmenü als ${BOLD}'Jarvis Manager'${RESET} aktualisiert."
    echo -e "(Jarvis wurde planmäßig nicht automatisch gestartet)."
    echo -e "${BOLD}${GREEN}==============================================================================${RESET}\n"
}

# ── Argumenten-Prüfung ───────────────────────────────────────────────────────
case "${1:-}" in
    -n|--native)
        banner
        install_native
        exit 0
        ;;
    -u|--update)
        banner
        perform_update
        exit 0
        ;;
    -d|--desktop)
        banner
        install_desktop_integration
        exit 0
        ;;
    -h|--help)
        banner
        echo "Verwendung: ./setup.sh [OPTION]"
        echo "Optionen:"
        echo "  -n, --native    Startet native Installation auf dem Host"
        echo "  -u, --update    Aktualisiert bestehende Installation (venv & npm)"
        echo "  -d, --desktop   Erneuert nur die Desktop-Integration / Startmenü"
        echo "  -h, --help      Zeigt diese Hilfe an"
        exit 0
        ;;
esac

# ── Interaktives Hauptmenü ───────────────────────────────────────────────────
banner
print_status

echo -e "${BOLD}${CYAN}Wähle die gewünschte Aktion:${RESET}\n"
echo -e "${BOLD}${CYAN}   1)${RESET} ${BOLD}Native Host Installation${RESET} (venv, Next.js & Startmenü-Eintrag einrichten)"
echo -e "${BOLD}${CYAN}   2)${RESET} ${BOLD}Aktualisieren / Update${RESET} (Bestehende Installation & Module updaten)"
echo -e "${BOLD}${CYAN}   3)${RESET} ${BOLD}Desktop-Integration erneuern${RESET} (Startmenü-Eintrag 'Jarvis Manager' neu schreiben)"
echo -e "${BOLD}${CYAN}   4)${RESET} Beenden"
echo -e "${BLUE}──────────────────────────────────────────────────────────────────────────────${RESET}"
echo -ne "${BOLD}Wähle eine Option [1-4]: ${RESET}"
read -r CHOICE

case "$CHOICE" in
    1) install_native ;;
    2) perform_update ;;
    3) install_desktop_integration ;;
    4|q|Q) echo -e "\n${CYAN}Setup beendet.${RESET}"; exit 0 ;;
    *) echo -e "\n${RED}Ungültige Eingabe.${RESET}"; exit 1 ;;
esac
