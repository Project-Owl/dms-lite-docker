FROM python:slim-buster

RUN apt update && apt upgrade && apt install -y gcc libmariadb-dev libmariadb3

COPY serial_sqlwriter.py /

RUN pip3 install pyserial mariadb

ENTRYPOINT [ "python3", "serial_sqlwriter.py" ]
