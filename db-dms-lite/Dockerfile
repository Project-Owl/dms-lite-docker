# FROM python:slim-bullseye

# RUN apt update && apt upgrade -y && apt install -y gcc libmariadb-dev libmariadb3

# COPY requirements.txt  requirements.txt 

# RUN pip3 install -r requirements.txt 

# COPY . .

# #export to run in :5000
# EXPOSE 5000

# # Tells Docker to run the python code and where it is located
# ENTRYPOINT [ "python3"]
# CMD ["handling-db.py" ]
FROM python:slim-bullseye
COPY . /db-dms-lite
WORKDIR /db-dms-lite
RUN apt update && apt upgrade -y && apt install -y gcc libmariadb-dev libmariadb3
RUN pip install -r requirements.txt
RUN pip install mariadb==1.0.11
RUN pip install python-dotenv
ENTRYPOINT ["python"]
CMD ["app.py"]



# # Copies files from the host into the container
# COPY handling-db.py /

# # Installs libraries for API from requirements.txt


# #export to run in :5000
# EXPOSE 5000

# # Tells Docker to run the python code and where it is located
# ENTRYPOINT [ "python3", "handling-db.py" ]
