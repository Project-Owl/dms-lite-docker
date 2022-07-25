import time
from time import gmtime, strftime
import threading
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

def handleCommands():
	while True:
		try:
			conn = mariadb.connect(
			user=os.getenv('MYSQL_USER'),
			password=os.getenv('MYSQL_PASSWORD'),
			host="mariadb",
			database=os.getenv('MYSQL_DATABASE')
			)
			c = conn.cursor()
			c.execute("SELECT * FROM clusterCommands LIMIT 1")
			for (timestamp, topic, payload) in c:
			    print (f"Executing Command {topic} with {payload}")
			    command = {"topic": topic, "payload": payload}
			    ser.write(json.dumps(command).encode('utf-8'))
			    query = f"DELETE FROM clusterCommands WHERE timestamp='{timestamp}'"
			    c.execute(query)
			    conn.commit()
			    conn.close()
		except mariadb.Error as e:
			print(e)
		time.sleep(1)

try:
    db = mariadb.connect(
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        host=os.getenv('MYSQL_HOST'),
        database=os.getenv('MYSQL_DATABASE')
		port=3306
    )
    db.cursor().execute("CREATE TABLE IF NOT EXISTS clusterData (timestamp DATETIME, duck_id TEXT, topic TEXT, message_id TEXT, payload TEXT, path TEXT, hops INT, duck_type INT)")
    db.cursor().execute("CREATE TABLE IF NOT EXISTS clusterCommands (timestamp TEXT, topic TEXT, payload TEXT)")
    db.commit()
except mariadb.Error as e:
    print(e)


threading.Thread(target=handleCommands).start()
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
