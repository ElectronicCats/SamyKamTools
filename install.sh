#!/usr/bin/env bash

#curl https://raw.githubusercontent.com/ElectronicsCats/SamyKamTools/install.sh | sudo sh

#Beta Install Script

#SamyKam - A set of pentesting tools to test Mag-Stripe readers and tokenization processes
#Code and hardware integration by Salvador Mendoza (https://salmg.net)
#PCB design and advisory by Andres Sabas
#Team work with @electronicats (https://twitter.com/electronicats)
#Named the tool in honor of Samy Kamkar(http://samy.pl)
#For his hard work and community support

cat << "EOF"
   .d8888.  .d8b.  .88b  d88. db    db   db   dD  .d8b.  .88b  d88.
   88'  YP d8' `8b 88'YbdP`88 `8b  d8'   88 ,8P' d8' `8b 88'YbdP`88
   `8bo.   88ooo88 88  88  88  `8bd8'    88,8P   88ooo88 88  88  88
     `Y8b. 88~~~88 88  88  88    88      88`8b   88~~~88 88  88  88
   db   8D 88   88 88  88  88    88      88 `88. 88   88 88  88  88
   `8888Y' YP   YP YP  YP  YP    YP      YP   YD YP   YP YP  YP  YP


              d888888b  .d88b.   .d88b.  db      .d8888.
              `~~88~~' .8P  Y8. .8P  Y8. 88      88'  YP
                 88    88    88 88    88 88      `8bo.
                 88    88    88 88    88 88        `Y8b.
                 88    `8b  d8' `8b  d8' 88booo. db   8D
                 YP     `Y88P'   `Y88P'  Y88888P `8888Y'
                    by ElectronicCats and Salvador Mendoza
EOF
sleep 2

apt-get update  # To get the latest package lists
#apt-get upgrade -y
apt-get install python-dev python-setuptools swig python-bluez gcc-avr binutils-avr avr-libc-y #Prerequisites for WiringPi-Python

cd
#gdata-2
curl -L https://pypi.python.org/packages/a8/70/bd554151443fe9e89d9a934a7891aaffc63b9cb5c7d608972919a002c03c/gdata-2.0.18.tar.gz#md5=13b6e6dd8f9e3e9a8e005e05a8329408 | tar xzf -
cd gdata-2.0.18
python setup.py install

#WiringPi
#git clone git://git.drogon.net/wiringPi
#cd wiringPi
#./build

cd

#WiringPi-Python
git clone --recursive https://github.com/ElectronicsCats/WiringPi-Python
cd WiringPi-Python
./build.sh
python setup.py install

cd
#SPIDEV
git clone https://github.com/doceme/py-spidev
cd py-spidev
python setup.py install

cd
#Adafruit_SSD1306
git clone https://github.com/adafruit/Adafruit_Python_SSD1306
cd Adafruit_Python_SSD1306
sudo python setup.py install

#py-gaugette
git clone https://github.com/guyc/py-gaugette
cd py-gaugette
sudo python setup.py install

#SamyKamTools
git clone https://github.com/ElectronicsCats/SamyKamTools
cd SamyKamTools
sudo python SamyKamTools.py
