#This script takes the incoming messages and writes them to the DB  & MQTT
from time import gmtime, strftime
import paho.mqtt.client as mqtt
import mariadb
import json
import logging
import os

status_topic = "#"
logging.warning("Write to DB is Running")

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    print(client)

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(status_topic)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    theTime = strftime("%Y-%m-%d %H:%M:%S", gmtime())

    result = (theTime + "\t" + str(msg.payload))
    print(msg.topic + ":\t" + result)
    # if (msg.topic == status_topic):
    p = json.loads(msg.payload)
    print (json.dumps(p))
    print("New message received")
    logging.warning("New message received")
    print(["topic"])
    writeToDb(theTime, p["DeviceID"], p["topic"], p["MessageID"], p["Payload"], p["path"], p["hops"], p["duckType"])
    return

def writeToDb(theTime, duckId, topic, messageId, payload, path, hops, duckType):
    conn = mariadb.connect(
		user=os.getenv('MYSQL_USER'),
		password=os.getenv('MYSQL_PASSWORD'),
		host="mariadb",
		database=os.getenv('MYSQL_DATABASE')
	)
    c = conn.cursor()
    print ("Writing to db...")
    try:
        c.execute("INSERT INTO clusterData VALUES (?,?,?,?,?,?,?,?)", (theTime, duckId, topic, messageId, payload, path, hops, duckType))
        conn.close()
    except mariadb.Error as e:
        print("Not Correct Packet")
        print(e)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("mqtt_broker", 1883, 60)


try:
    db = mariadb.connect(
		user=os.getenv('MYSQL_USER'),
		password=os.getenv('MYSQL_PASSWORD'),
		host="mariadb",
		database=os.getenv('MYSQL_DATABASE')
	)
    db.cursor().execute("CREATE TABLE IF NOT EXISTS clusterData (timestamp datetime, duck_id TEXT, topic TEXT, message_id TEXT, payload TEXT, path TEXT, hops INT, duck_type INT)")
    db.close()
except mariadb.Error as e:
    print(e)


# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
