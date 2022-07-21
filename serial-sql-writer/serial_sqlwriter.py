
from time import gmtime, strftime
import mariadb
import serial
import json
import logging
import os

ser = serial.Serial('/dev/ttyUSB0',115200)

def writeToDb(theTime, duckId, topic, messageId, payload, path, hops, duckType):
    try:
        conn = mariadb.connect(
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            host=os.egetenv('MYSQL_HOST'),
            database=os.getenv('MYSQL_DATABASE'),
			port=3306
        )
        c = conn.cursor()
        print ("Writing to db...")
        logging.warning("Writing New Message")
        c.execute("INSERT INTO clusterData VALUES (?,?,?,?,?,?,?,?)", (theTime, duckId, topic, messageId, payload, path, hops, duckType))
        conn.commit()
        conn.close()
    except mariadb.Error as e:
        print(e)

try:
    db = mariadb.connect(
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        host=os.getenv('MYSQL_HOST'),
        database=os.getenv('MYSQL_DATABASE')
		port=3306
    )
    db.cursor().execute("CREATE TABLE IF NOT EXISTS clusterData (timestamp DATETIME, duck_id TEXT, topic TEXT, message_id TEXT, payload TEXT, path TEXT, hops INT, duck_type INT)")
    db.commit()
    db.close()
except mariadb.Error as e:
    print(e)

while True:
    theTime = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    payload = ser.readline()
    prstrip = payload.rstrip().decode('utf8')
    if len(prstrip) >0:
      print(prstrip)
      try:
        p = json.loads(prstrip)
        writeToDb(theTime, p["DeviceID"], p["topic"], p["MessageID"], p["Payload"], p["path"],p["hops"],p["duckType"])
      except:
         print(prstrip)
         print("Invalid Packet")
