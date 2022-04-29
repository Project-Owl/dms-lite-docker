##This file is where you setup the container config for the DMSPY DB Writer
FROM python@sha256:091095620858dbb9c33def8b77170bd8e1d3373c7591f931e75018f6fdb23da4

RUN apt update && apt upgrade -y && apt install -y gcc libmariadb-dev libmariadb3

#Copies files from the host into the container
COPY Wifi_sqlwriter.py /

#Installs Paho-Mqtt in the docker enviroment
RUN pip3 install paho-mqtt mariadb

#Tells Docker to run the python code and where it is located
ENTRYPOINT [ "python3", "Wifi_sqlwriter.py" ]
