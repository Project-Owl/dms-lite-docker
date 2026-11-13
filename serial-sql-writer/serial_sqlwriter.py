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

def read_frames(port, stop, max_bytes=65536):
    buffer = bytearray()
    discarding = False
    while not stop.is_set():
        chunk = port.read_until(b"\n", max_bytes + 1)
        for byte in chunk:
            if byte == 10:
                if buffer and not discarding:
                    yield bytes(buffer).rstrip(b"\r")
                buffer.clear()
                discarding = False
            elif not discarding:
                buffer.append(byte)
                if len(buffer) > max_bytes:
                    buffer.clear()
                    discarding = True
                    LOG.warning("Discarding oversized serial frame")

def dispatch_one(connect, serial_port):
    conn = cursor = None
    try:
        conn = connect()
        cursor = conn.cursor()
        cursor.execute("START TRANSACTION")
        cursor.execute("SELECT timestamp, topic, payload FROM clusterCommands ORDER BY timestamp ASC LIMIT 1 FOR UPDATE")
        row = cursor.fetchone()
        if row is None:
            conn.rollback()
            return False
        timestamp, topic, payload = row
        raw = json.dumps({"topic": topic, "payload": payload}).encode("utf-8")
        if serial_port.write(raw) != len(raw):
            raise OSError("Partial serial command write")
        cursor.execute("DELETE FROM clusterCommands WHERE timestamp=? AND topic=? AND payload=? LIMIT 1", (timestamp, topic, payload))
        conn.commit()
        return True
    except Exception as error:
        LOG.warning("Command dispatch failed (%s); command retained", type(error).__name__)
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                LOG.warning("Command rollback failed")
        return False
    finally:
        close_resources(cursor, conn)

def run_serial(serial_factory, connect, stop, *, device="/dev/ttyUSB0", baud=115200, max_bytes=65536, dispatch=None):
    while not stop.is_set():
        if not wait_for_schema(connect, stop):
            break
        port = None
        command_stop = threading.Event()
        command_thread = None
        try:
            port = serial_factory(device, baud, timeout=1, write_timeout=2)
            if dispatch:
                def commands(current_port=port, current_stop=command_stop):
                    while not stop.is_set() and not current_stop.is_set():
                        dispatch(connect, current_port)
                        current_stop.wait(1)
                command_thread = threading.Thread(target=commands, daemon=True)
                command_thread.start()
            for raw in read_frames(port, stop, max_bytes):
                try:
                    packet = decode_packet(raw, max_bytes)
                except ValueError as error:
                    LOG.warning("Rejected serial packet: %s", error)
                    continue
                store_packet(packet, connect, datetime.now(timezone.utc))
        except OSError as error:
            LOG.warning("Serial connection failed (%s); reconnecting", type(error).__name__)
        finally:
            command_stop.set()
            if command_thread:
                command_thread.join(timeout=8)
            close_resources(port)
        stop.wait(1)

def main():
    import mariadb
    import serial
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    maximum = settings()
    baud = int(os.getenv("SERIAL_BAUD", "115200"))
    if baud < 1:
        raise ValueError("SERIAL_BAUD must be positive")
    run_serial(serial.Serial, lambda: connect_database(mariadb), stop_event(),
               device=os.getenv("SERIAL_DEVICE", "/dev/ttyUSB0"), baud=baud, max_bytes=maximum,
               dispatch=dispatch_one)

if __name__ == "__main__":
    main()
