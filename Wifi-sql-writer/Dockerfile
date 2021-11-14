##This file is where you setup the container config for the DMSPY DB Writer
FROM python:buster

#Copies files from the host into the container
COPY Wifi_sqlwriter.py /

#Installs Paho-Mqtt in the docker enviroment
RUN pip3 install paho-mqtt mariadb

#Tells Docker to run the python code and where it is located
ENTRYPOINT [ "python3", "Wifi_sqlwriter.py" ]
