FROM python@sha256:091095620858dbb9c33def8b77170bd8e1d3373c7591f931e75018f6fdb23da4

RUN apt update && apt upgrade -y && apt install -y gcc libmariadb-dev libmariadb3

COPY serial_sqlwriter.py /

RUN pip3 install pyserial mariadb

ENTRYPOINT [ "python3", "serial_sqlwriter.py" ]
