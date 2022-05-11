FROM python:slim-bullseye

RUN apt update && apt upgrade -y && apt install -y gcc libmariadb-dev libmariadb3

# Copies files from the host into the container
COPY serial_sqlwriter.py /

# Installs serial and mariadb libraries for python
RUN pip3 install pyserial mariadb

# Tells Docker to run the python code and where it is located
ENTRYPOINT [ "python3", "serial_sqlwriter.py" ]
