FROM python:slim-bullseye

RUN apt update && apt upgrade -y && apt install -y gcc libmariadb-dev libmariadb3
# Copies files from the host into the container
COPY handling-db.py /

# Installs libraries for API from requirements.txt
RUN pip3 install -r requirements.txt 

# Tells Docker to run the python code and where it is located
ENTRYPOINT [ "python3", "handling-db.py" ]
