--- SYSTEM ANALYSIS REPORT ---
So 11. Okt 02:32:59 CEST 2026

--- CPU TOP 10 ---
    PID    PPID CMD                         %CPU %MEM
   1158     611 /usr/bin/plasmashell --no-r 45.4 16.4
1012065  882922 /opt/brave-bin/brave --type 18.3  1.6
 882950  882919 /opt/brave-bin/brave --type  7.2  0.6
 884061  882922 /opt/brave-bin/brave --type  6.6  3.1
   1027    1023 /usr/bin/kwin_wayland --way  4.7  1.0
 883506  882922 /opt/brave-bin/brave --type  2.3  2.2
 882909     611 /opt/brave-bin/brave         1.4  0.8
 952926  882922 /opt/brave-bin/brave --type  1.3  1.3
1020702 1020691 /home/graba/.local/share/we  1.2  0.2
1101490  882922 /opt/brave-bin/brave --type  1.0  0.3

--- RAM TOP 10 ---
    PID    PPID CMD                         %CPU %MEM
   1158     611 /usr/bin/plasmashell --no-r 45.4 16.4
 884061  882922 /opt/brave-bin/brave --type  6.6  3.1
 883506  882922 /opt/brave-bin/brave --type  2.3  2.2
1012065  882922 /opt/brave-bin/brave --type 18.3  1.6
 952926  882922 /opt/brave-bin/brave --type  1.3  1.3
   1027    1023 /usr/bin/kwin_wayland --way  4.7  1.0
 882909     611 /opt/brave-bin/brave         1.4  0.8
 882950  882919 /opt/brave-bin/brave --type  7.2  0.6
 952780  882922 /opt/brave-bin/brave --type  0.3  0.6
 883000  882922 /opt/brave-bin/brave --type  0.3  0.5

--- GPU STATUS (intel_gpu_top equivalent) ---
GPU state unavailable

--- DISK SPACE ---
Dateisystem    Größe Benutzt Verf. Verw% Eingehängt auf
/dev/sdb2       462G    446G   13G   98% /
devtmpfs        7,6G       0  7,6G    0% /dev
tmpfs           7,8G     84K  7,8G    1% /dev/shm
efivarfs        128K    126K     0  100% /sys/firmware/efi/efivars
tmpfs           3,2G    2,0M  3,2G    1% /run
none            1,0M       0  1,0M    0% /run/credentials/systemd-journald.service
none            1,0M       0  1,0M    0% /run/credentials/systemd-resolved.service
/dev/sdb2       462G    446G   13G   98% /home
/dev/sdb2       462G    446G   13G   98% /srv
tmpfs           7,8G     92M  7,7G    2% /tmp
/dev/sdb2       462G    446G   13G   98% /root
/dev/sdb2       462G    446G   13G   98% /var/tmp
/dev/sdb1       4,1G    1,3G  2,9G   31% /boot
/dev/sdb2       462G    446G   13G   98% /var/log
/dev/sdb2       462G    446G   13G   98% /var/cache
tmpfs           1,6G    168K  1,6G    1% /run/user/1000
none            1,0M    4,0K 1020K    1% /run/credentials/libvirtd.service
none            1,0M       0  1,0M    0% /run/credentials/getty@tty4.service
/dev/loop0      2,5G    2,5G     0  100% /var/lib/waydroid/rootfs
/dev/loop1      536M    536M     0  100% /var/lib/waydroid/rootfs/vendor

--- ANALYSIS & POTENTIAL CAUSES ---
Check CPU TOP 10 for processes causing high load. Previous spike was due to kioworker.
Check RAM TOP 10. High browsers/Plasmashell usage can impact performance.
--- INSTANT SYSTEM SNAPSHOT ---
CPU Load: 85.2% | RAM Used: 47.2% | SSD Used: 97.2% | GPU Load: 22%
Potential Issue: SSD Root is nearly full (97.2% belegt), this can significantly degrade system performance and cause stutters.
