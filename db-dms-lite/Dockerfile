FROM python:3.10-slim-bullseye

WORKDIR /db-dms-lite
COPY . .

RUN apt update && apt upgrade -y && apt install -y gcc libmariadb-dev libmariadb3
RUN pip3 install -r requirements.txt
RUN pip3 install mariadb==1.0.11 python-dotenv

ENTRYPOINT ["python3", "app.py"]