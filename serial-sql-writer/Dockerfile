FROM python:buster

COPY serial_sqlwriter.py /

RUN pip3 install pyserial mariadb

ENTRYPOINT [ "python3", "serial_sqlwriter.py" ]
