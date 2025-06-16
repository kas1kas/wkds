1 install (with raspberry pi imager) **Rasberry Pi OS Lite 32 (bit)**
- enable ssh
- set hostname
- set wifi
2 sudo raspi-config
- interface options - enable I2C
3 install packages
- sudo apt install git python3-pip
- sudo pip3 install flask-restx rpi-ws281x python-tsl2591 --break-system-packages
4 install wordclock software
- git clone https://github.com/kas1kas/ds.git
- cp ds/alias.txt .bash_aliases
- crontab ds/crontab.txt
5 install WiFi-connect
- git clone https://github.com/kas1kas/wifi-connect.git
- cd wifi-connect/scripts
- sudo ./rpi_headless_wifi_install.sh
6 reboot

on your phone
click wifi
look for RPI-woordklok
select
ignore messages about Internet may not be available
connect
your phone is now connected to the wordclock
start a web browser (chrome, edge or whatever you use)
type 192.168.42.1:8080

a page opens and shows your network
if not, click on the down arrow and select the dot behind your network
type your password
click connect

the clock is now connected to the internet!!
the correct time will appear in a litle while


