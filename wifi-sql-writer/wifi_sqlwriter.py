"""PapaDuck ingestion adapter. Importing this module performs no I/O."""
import json
import logging
import os
import signal
import threading
import time
from datetime import datetime, timezone

LOG = logging.getLogger(__name__)
FIELDS = ("DeviceID", "topic", "MessageID", "Payload", "path", "hops", "duckType")

def decode_packet(raw, max_bytes=65536):
    if len(raw) > max_bytes:
        raise ValueError("packet exceeds size limit")
    try:
        packet = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError("invalid UTF-8 or JSON") from error
    if not isinstance(packet, dict) or any(key not in packet for key in FIELDS):
        raise ValueError("packet object is missing required fields")
    for key in ("DeviceID", "topic", "MessageID", "Payload", "path"):
        if not isinstance(packet[key], str):
            raise ValueError("packet text field has an invalid type")
    if any(not packet[key].strip() for key in ("DeviceID", "topic", "MessageID")):
        raise ValueError("packet identifier or topic is empty")
    for key in ("hops", "duckType"):
        if type(packet[key]) is not int or not 0 <= packet[key] <= 2147483647:
            raise ValueError("packet integer field is out of range")
    return packet

def connect_database(driver, env=None):
    env = os.environ if env is None else env
    return driver.connect(user=env.get("MYSQL_USER"), password=env.get("MYSQL_PASSWORD"),
                          host=env.get("MYSQL_HOST"), database=env.get("MYSQL_DATABASE"),
                          port=3306, connect_timeout=5, read_timeout=5, write_timeout=5)

def close_resources(*resources):
    for resource in resources:
        if resource is not None:
            try:
                resource.close()
            except Exception:
                LOG.warning("Database resource cleanup failed")

def store_packet(packet, connect, received_at, *, max_attempts=3, sleep=time.sleep):
    timestamp = received_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    values = (timestamp,) + tuple(packet[key] for key in FIELDS)
    for attempt in range(max_attempts):
        conn = cursor = None
        try:
            conn = connect()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO clusterData (timestamp, duck_id, topic, message_id, payload, path, hops, duck_type) VALUES (?,?,?,?,?,?,?,?)", values)
            conn.commit()
            return True
        except Exception as error:
            # This boundary contains only driver operations; validation happens first.
            LOG.warning("Message storage failed (%s), attempt %d", type(error).__name__, attempt + 1)
        finally:
            close_resources(cursor, conn)
        if attempt + 1 < max_attempts:
            sleep(min(2 ** attempt, 5))
    LOG.error("Message not stored after bounded retries")
    return False

def wait_for_schema(connect, stop, sleep=time.sleep):
    delay = 1
    while not stop.is_set():
        conn = cursor = None
        try:
            conn = connect()
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp, duck_id, topic, message_id, payload, path, hops, duck_type FROM clusterData LIMIT 0")
            cursor.execute("SELECT timestamp, topic, payload FROM clusterCommands LIMIT 0")
            return True
        except Exception as error:
            LOG.warning("Waiting for database/schema (%s)", type(error).__name__)
        finally:
            close_resources(cursor, conn)
        if sleep is time.sleep:
            stop.wait(delay)
        else:
            sleep(delay)
        delay = min(delay * 2, 5)
    return False

def settings():
    for key in ("MYSQL_HOST", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE"):
        if not os.getenv(key):
            raise ValueError(key + " must be configured")
    maximum = int(os.getenv("MAX_PACKET_BYTES", "65536"))
    if maximum < 1 or maximum > 1048576:
        raise ValueError("MAX_PACKET_BYTES must be between 1 and 1048576")
    return maximum

def stop_event():
    stop = threading.Event()
    for name in (signal.SIGINT, signal.SIGTERM):
        signal.signal(name, lambda *_: stop.set())
    return stop

def make_callbacks(store, topic="#", max_bytes=65536):
    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            client.subscribe(topic)
        else:
            LOG.warning("MQTT connection was rejected")
    def on_message(client, userdata, message):
        try:
            packet = decode_packet(message.payload, max_bytes)
        except ValueError as error:
            LOG.warning("Rejected MQTT packet: %s", error)
            return
        try:
            store(packet)
        except Exception as error:
            LOG.error("MQTT storage callback failed (%s)", type(error).__name__)
    return on_connect, on_message

def main():
    import mariadb
    import paho.mqtt.client as mqtt
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    maximum = settings()
    stop = stop_event()
    connect = lambda: connect_database(mariadb)
    if not wait_for_schema(connect, stop):
        return
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect, client.on_message = make_callbacks(
        lambda packet: store_packet(packet, connect, datetime.now(timezone.utc)),
        os.getenv("MQTT_TOPIC", "#"), maximum)
    client.reconnect_delay_set(min_delay=1, max_delay=5)
    client.connect_async(os.getenv("MQTT_HOST", "mosquitto"), int(os.getenv("MQTT_PORT", "1883")), 60)
    client.loop_start()
    try:
        stop.wait()
    finally:
        client.disconnect()
        client.loop_stop()

if __name__ == "__main__":
    main()
