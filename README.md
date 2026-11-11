# DMS Lite

[![License](https://img.shields.io/github/license/project-owl/dms-lite-docker?style=flat-square)](LICENSE)
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/project-owl/dms-lite-docker?logo=github&style=flat-square)

DMS Lite is an open source, local tool for collecting and viewing data from
[ClusterDuck Protocol](https://github.com/ClusterDuck-Protocol/ClusterDuck-Protocol)
firmware without a cloud subscription. Connect a PapaDuck over MQTT or USB serial,
then use the browser interface to inspect messages, device activity, charts, and
browser alert thresholds. Core pages and assets work without internet access;
optional Google Maps/OpenStreetMap views require connectivity.

## How it works

A PapaDuck receives messages from your ClusterDuck network and forwards them to
DMS Lite using one of two ingestion modes:

- **USB serial:** connect the PapaDuck to the Docker host over USB. The serial
  writer reads newline-delimited JSON and stores the messages in MariaDB.
- **WiFi / MQTT:** the PapaDuck publishes JSON to the local MQTT broker. The WiFi
  writer subscribes to the broker and stores the messages in the same database.

Both modes use the same browser interface to display stored messages, Ducks, and
numeric readings. Open the interface on the Docker host or another device on its
local network.

Use PapaDuck firmware that supports your chosen ingestion mode and the packet
format below. The [USB serial example](https://github.com/ClusterDuck-Protocol/QuackPacks/tree/main/Custom-Papa/PapiDuck-DMS-Lite-Serial-Example)
and [WiFi example](https://github.com/ClusterDuck-Protocol/QuackPacks/tree/main/Custom-Papa/PapiDuck-DMS-Lite-WiFi-Example)
are firmware references; check their board settings and CDP version before use.

The stack contains an Express/EJS web application, MariaDB, and a Python ingestion
adapter. WiFi mode also starts a Mosquitto broker. Express serves all page and
analytics requests on port 3000.

**Offline use:** download/build the container images and dependencies before
deployment, or transfer them from a connected machine. Once installed, core pages,
styles, scripts, and icons are served locally; fonts use the browser's installed
font stack. Internet access is needed for the optional online map views.

## Requirements

- Docker running 64-bit Linux containers on amd64 or arm64.
- Docker Engine with Docker Compose 2.24.4 or newer.
- A PapaDuck running the compatible MQTT or serial DMS Lite firmware.
- For USB serial: a native Linux host with access to the serial device, such as a
  64-bit Raspberry Pi. Set the device path and permissions as described below.
  USB passthrough on macOS/Windows depends on the container runtime and requires
  separate host configuration; the native Linux instructions do not establish
  support for every desktop runtime.

### Packet format

Ingestion expects newline-delimited UTF-8 JSON over serial, or JSON MQTT messages,
with these fields. The default serial rate is 115200 baud:

```json
{"DeviceID":"DUCK001","topic":"sensor/temp","MessageID":"MSG001","Payload":"-2.5","path":"A,B","hops":2,"duckType":1}
```

Identifiers/topics are nonempty strings, payload/path are strings, and hops/type
are integers from 0 to 2147483647. Additional fields are accepted. Malformed
messages are logged and skipped; subsequent messages continue to be processed.

## Start

**Existing installations:** stop before starting this version. The database now
uses official MariaDB 11.4 and a separate `data-mariadb/` directory. Follow the
[database migration guide](docs/database-migration.md) to preserve legacy `data/`.
There is no automatic import. Retain your existing credentials.

For a fresh installation, clone the modernization branch and create your local
configuration. These instructions describe `modern-update`, which is separate
from the legacy default `main` while modernization is under review:

```sh
git clone --branch modern-update https://github.com/Project-Owl/dms-lite-docker.git
cd dms-lite-docker
cp .env.example .env
```

Set `MYSQL_ROOT_PASSWORD` and `MYSQL_PASSWORD` in `.env`. Choose your database/user
names before the first start. Keep `MYSQL_HOST=mariadb` for the bundled database.

**For USB serial on Linux:** set `SERIAL_HOST_DEVICE` in `.env` to the PapaDuck's
device path. Set `SERIAL_GID` to the numeric group owning that device; for example,
run `stat -c %g /dev/ttyUSB0` for a device at `/dev/ttyUSB0`. The non-root writer
needs both the device mapping and permission to access it.

Choose one ingestion mode. When switching modes, stop the previous Compose pair
first using the commands under [Operations](#operations).

```sh
# WiFi / MQTT
docker compose -f docker-compose-base.yml -f docker-compose-wifi.yml up -d --build

# USB serial — configure SERIAL_HOST_DEVICE and SERIAL_GID first
docker compose -f docker-compose-base.yml -f docker-compose-serial.yml up -d --build
```

For an offline host with all required images already available under their
configured image references, replace `--build` with `--no-build --pull never`.

Open `http://localhost:3000`, or `http://<docker-host-address>:3000` from another
device on the same LAN. If port 3000 is already in use, set `WEB_PORT` in `.env`
before starting, and use that port in the browser URL. No separate analytics
service or browser API address is needed. First startup waits for MariaDB and
creates missing tables without replacing existing rows.
If existing columns have incompatible types, capacities, or required insert
constraints, startup stops and identifies the table/column. It does not alter the
existing schema automatically.

In WiFi mode, configure the PapaDuck to publish to the Docker host's LAN address
on port 1883. The broker permits anonymous access by default, and the web UI has
no login; run this configuration on a trusted local network. To confine the web
port to the host, set `WEB_BIND_ADDRESS=127.0.0.1`.

## Configuration

| Setting | Default | Purpose |
| --- | --- | --- |
| `MYSQL_ROOT_PASSWORD`, `MYSQL_PASSWORD` | Required | Database initialization credentials |
| `MYSQL_DATABASE`, `MYSQL_USER` | `dms-lite` in example | Database and application account |
| `MYSQL_HOST` | `mariadb` | Database hostname |
| `WEB_PORT`, `WEB_BIND_ADDRESS` | `3000`, `0.0.0.0` | Host web port and interface |
| `SERIAL_HOST_DEVICE` | `/dev/ttyUSB0` | Linux host device mapped into the serial container |
| `DATABASE_DATA_DIR` | `./data-mariadb` | Official MariaDB storage; never point this at legacy `data/` |
| `SERIAL_GID` | `20` | Supplementary host serial-device group; use `stat -c %g /dev/ttyUSB0` |
| `SERIAL_BAUD` | `115200` | Serial baud rate |
| `MQTT_HOST`, `MQTT_PORT` | `mosquitto`, `1883` | Broker used by the WiFi writer |
| `MQTT_HOST_PORT`, `MQTT_BIND_ADDRESS` | `1883`, `0.0.0.0` | Bundled broker host port and interface |
| `MQTT_TOPIC` | `#` | Subscription filter; quote it as `'#'` in `.env` |
| `MAX_PACKET_BYTES` | `65536` | Packet/frame size limit; maximum configurable value 1048576 |
| `DEVICE_STALE_SECONDS` | `300` | Last-seen freshness window |

Serial mode enables the **WiFi ON / WiFi OFF** command controls automatically.
These require firmware that implements the requests; selecting serial mode does
not verify firmware support. A command is **queued** after its database insert
succeeds, then dispatched by the serial adapter. WiFi mode does not implement an
MQTT command protocol and hides/rejects those controls.
The UI confirms queueing only; a serial write does not confirm device receipt or
a WiFi state change.
A database failure after serial transmission can cause a repeated command.

## Using the interface

- **Overview:** a snapshot of loaded messages, known topics, Duck freshness, and numeric readings. Refresh explicitly to update it.
- **Messages** (`/data`): latest 100 raw messages, numeric charts, browser alert results, and a
  selected device's latest reading. Select a chart topic on the page.
- **Ducks:** each device's latest packet and last-seen freshness. This is inferred
  from message timestamps, not a live radio connection indicator.
- **Settings:** choose chart style/topics, sample limit, monitored device, alert
  bounds, and detailed message columns. Chart/alert preferences are saved in this
  browser; there is no background notification service.

The interface uses a dark layout throughout, with no theme selector. Core styles
are built locally with Tailwind and served by Express. The built-in **Setup guide**
is available without internet access.

Charts and alerts inspect at most the latest 1000 messages matching a topic.
Charts and threshold checks accept payload strings containing a single finite
decimal number, such as `"-2.5"`. Nonnumeric text and structured JSON payloads,
including health messages, remain visible in the message table but are not parsed
into numeric series. Alerts use values strictly below the minimum or above the
maximum. All displayed/API timestamps use UTC. Equal timestamps have no guaranteed
ordering in the existing schema.
Charts retain separate samples that share a timestamp; multiple series use gaps
where a matching timestamp/occurrence has no value.

Writers retry transient failures with bounded delays. They do not provide a
durable offline spool: messages can be lost during a database outage. Check logs
for packets that could not be stored.

## Operations

Use the same Compose file pair for status, logs, or shutdown:

```sh
docker compose -f docker-compose-base.yml -f docker-compose-wifi.yml ps
docker compose -f docker-compose-base.yml -f docker-compose-wifi.yml logs --tail=100 web wifiwriter
docker compose -f docker-compose-base.yml -f docker-compose-wifi.yml down
```

For serial deployments, substitute `docker-compose-serial.yml` and `serialwriter`.
MariaDB persists under `data-mariadb/`; back it up before any database/image migration.
The database port is internal to the Compose network. `/health/live` checks the
web process and `/health/ready` checks its database/table access.

Images are pinned to multi-platform digests: Node 24, Python 3.14, official
MariaDB 11.4, and Mosquitto 2.1. Application containers run without root.
For serial access, set `SERIAL_GID` to the numeric group owning your host device;
the container needs both the device mapping and that supplementary group.

## Development

See [development and testing](docs/development.md) and
[contributing](CONTRIBUTING.md). This project is licensed under the
[Apache License 2.0](LICENSE).
