FROM python:3.10-slim-bullseye
#COPY . /db-dms-lite
WORKDIR /db-dms-lite
COPY . . 
RUN apt update && apt upgrade -y && apt install -y gcc libmariadb-dev libmariadb3
RUN pip install -r requirements.txt
RUN pip install mariadb==1.0.11
RUN pip install python-dotenv
ENTRYPOINT ["python", "app.py"]


