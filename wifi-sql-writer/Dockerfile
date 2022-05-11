##This file is where you setup the container config for the DMSPY DB Writer
FROM python:slim-buster

RUN apt update && apt upgrade -y && apt install -y gcc libmariadb-dev libmariadb3

#Copies files from the host into the container
COPY wifi_sqlwriter.py /

#Installs Paho-Mqtt in the docker enviroment
RUN pip3 install paho-mqtt mariadb

#Tells Docker to run the python code and where it is located
ENTRYPOINT [ "python3", "wifi_sqlwriter.py" ]
