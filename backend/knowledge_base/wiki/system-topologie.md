# System-Topologie & Hardware-Kontext

## 1. Hauptsystem (CachyOS Host)
- **Hostname:** `graba-pc-w`
- **Betriebssystem:** CachyOS Linux (Arch-basiert, Kernel 6.18 LTS x86_64).
- **Hardware:** Asus Z87-PRO Mainboard, Intel Core i5-4670K (4 Kerne @ 3.40GHz), 16 GB DDR3 RAM, NVIDIA GeForce GTX 970.
- **Speicher-Architektur:** HDD-basierter Hauptspeicher; erfordert sparsamen Disk-I/O und atomare Schreibverfahren ([[sentinel-architektur]]).

## 2. Satellitensysteme & Piloten
- **Thorsten Pilot Hub (Legacy Notebook):**
  - OS: Debian 13 (Trixie) mit Trinity Desktop Environment (TDE R14.1.5).
  - Hardware: HP/Compaq mit AMD Athlon X2 DualCore QL-66, 1.7 GB RAM.
  - Zweck: Niedrigst-Ressourcen-Deployment für das Q4OS-Hub (`/home/graba/Schreibtisch/ASGRAD/graba-help-tool/q4os_hub/`).
- **Zweit- und Reservesysteme:**
  - Lenovo G780 (Intel Core i7-3630QM).
  - Windows 10 Dual-Boot Reserve.
  - Xbox Series S.

## 3. Sicherheits-Architektur
- Bubblewrap Sandboxing für ungesicherte Python-Aktionen.
- Physisches Hardware Confirmation Gate für risikobehaftete Systemänderungen.

## 4. Verknüpfungen
- [[system-architecture-map]]
- [[audio-stack-zustaendigkeiten]]
- [[sentinel-architektur]]
