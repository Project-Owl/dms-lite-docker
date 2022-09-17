FROM python:slim-bullseye

RUN apt update && apt upgrade -y && apt install -y gcc libmariadb-dev libmariadb3

# Copies files from the host into the container
COPY wifi_sqlwriter.py /

# Installs paho-MQTT and mariadb libraries for python
RUN pip3 install paho-mqtt mariadb==1.0.11

# Tells Docker to run the python code and where it is located
ENTRYPOINT [ "python3", "wifi_sqlwriter.py" ]
