FROM python:slim

RUN apt update && apt upgrade && apt install -y gcc libmariadb3 libmariadb-dev

COPY serial_sqlwriter.py /

RUN pip3 install pyserial mariadb

ENTRYPOINT [ "python3", "serial_sqlwriter.py" ]
