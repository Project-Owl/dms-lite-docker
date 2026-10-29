# Development and testing

The Express application is constructed by `createApp({db, ...options})`; importing
it starts no listener or database connection. `bin/www` validates configuration,
creates the MariaDB pool, initializes the existing schema, and starts one server.
The web process alone creates tables. Writers wait for schema availability and
reconnect independently of Compose startup ordering.
Startup validates column types/capacities and mandatory insert columns, without
altering existing data. Python adapters set five-second connection, read, and write
timeouts; a failed operation reaches bounded retries instead of blocking forever.

Use Node.js 24 or newer for the development tests. Install locked dependencies:

```sh
cd dms-lite
npm ci
npm run build:css
npm test
npx playwright install chromium
npx playwright test
```

The browser suite runs a deterministic fixture server on `127.0.0.1:3107`, checks
desktop/narrow screens in a non-UTC timezone, and writes artifacts under the
ignored `.scratch/modernization/browser-results/` directory. Stop other processes
using 3107 before running it. It needs no MariaDB or PapaDuck. The HTTP tests bind
ephemeral loopback ports and use test substitutes only at the database boundary.

Python unit tests need no native MariaDB extension or connected hardware. Install
pyserial for the additional Linux pseudo-terminal transport test:

```sh
# From the repository root
python3 -m venv .venv
. .venv/bin/activate
python -m pip install pyserial==3.5
python -m unittest discover -s tests -v
```

The pseudo-terminal test exercises actual pyserial framing and split reads; it
does not establish physical USB permissions or PapaDuck command acknowledgement.
The ingestion images install their own component requirements.

## Docker integration smoke test

Requires a working Docker daemon and Docker Compose 2.24.4 or newer (`!override`
is used to replace bind mounts and ports). Run from the repository root:

```sh
python3 tests/smoke.py
```

The script first validates its resolved configuration. It uses a uniquely named
Compose project, a test-only named MariaDB volume replacing `./data-mariadb`, and an
assigned loopback web port. It seeds the original schema, checks row preservation,
publishes malformed and valid packets, exercises Express analytics, and checks
recovery across broker/database restarts. It also checks an empty database.
Finally it removes only that test project's containers and volume. Operator
credentials/storage are not used. Allow time for first image downloads/builds.

`tests/compose.smoke.yml` is a test override, not a deployment configuration.
Its dummy credentials come from the test script. To build the serial image
without physical hardware:

```sh
docker build -t dms-lite-smoke-serialwriter serial-sql-writer
```

For a physical serial check, configure `SERIAL_HOST_DEVICE`, start the normal
Serial Compose pair, send representative PapaDuck packets, and verify command
bytes/device behavior against the actual firmware. Record hardware, firmware
version, host architecture, and packet formats when reporting a problem.

## Data and API conventions

Keep raw payloads as text. Analytics converts finite decimal strings only and
returns UTC ISO timestamps. Query parameters are validated before reaching SQL;
all device/topic values are bound parameters. Query/insert failures must reach
HTTP error handling rather than return an empty success result.

The same-origin endpoints are `/api/topics`, `/api/ducks`, `/api/readings`,
`/api/alerts`, and `/api/ducks/:duckId/latest`. Chart and alert scans inspect at
most 1000 recent matching messages. There is no separate Flask API.

Use escaped EJS or text nodes for device-derived values. Browser assets are local;
map requests happen only after an explicit user action. Settings use the
`dmsLite.preferences` versioned browser-storage object and migrate valid legacy
chart/alert values without modifying unrelated keys.

## Runtime and migration checks

Build all three images before the runtime probes:

```sh
docker build -t dms-lite-smoke-web dms-lite
docker build -t dms-lite-smoke-wifiwriter wifi-sql-writer
docker build -t dms-lite-smoke-serialwriter serial-sql-writer
python3 tests/image_smoke.py
DMS_IMAGE_TESTS=1 python3 -m unittest discover -s tests -p test_container_serial.py -v
python3 tests/migration_smoke.py
```

The device test owns a temporary pseudo-terminal and verifies permission denial
without the required group, then actual non-root reads/writes with it. It binds
the same PTY inode because Docker's separate devpts namespace cannot reopen a
recreated PTY device node. Physical USB/firmware validation remains separate.
The migration rehearsal creates all storage and credentials in a generated `/tmp`
tree, verifies byte/ownership preservation of the original, restores Unicode,
NULLs and duplicate commands, and tests refusal, failed export, retained partial import, SIGINT/SIGTERM cleanup
and pre-write rollback.

The workflow tests natively on `ubuntu-24.04` (amd64) and `ubuntu-24.04-arm`
(arm64), using [GitHub's runner labels](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).
Creating the workflow does not establish a successful arm64 run; check its results.
No workflow publishes images. Production npm audit covers npm dependencies only;
there is no equivalent claim about complete OS/Python vulnerability scanning.

## Frontend styles

Edit `dms-lite/styles/app.css` and the EJS partials under `views/partials/`.
The interface is dark-only and uses system fonts. Tailwind 4.3.3 scans explicit
EJS and browser-script sources and writes the ignored
`public/stylesheets/app.css`. Run `npm run build:css` after changing templates or
styles, or `npm run build:css:watch` while developing. `npm start` builds styles
before starting the development server; the browser fixture also builds them.
The Express stylesheet URL includes its content digest, calculated at startup.
Restart the server after rebuilding styles when checking a deployment asset URL.

The web Dockerfile compiles styles in a separate stage with dev dependencies.
The final non-root image installs production packages only and copies the built
CSS. There is no Tailwind CDN or runtime compiler. The native architecture CI
matrix also builds styles before testing. Bootstrap/TableFilter are replaced by
local Tailwind styles and a small loaded-message search/topic filter.

The overview combines independent read-only snapshots. Failed counts display an
unknown marker and retry path; an empty first-run screen requires confirmed empty
messages and devices. Duck status derives from packet timestamps, never a claimed
radio or broker connection. Message search filters the loaded snapshot rather than
the entire database. The `/data` API/page and serial command endpoints retain their
existing paths. All dates are UTC and untrusted packet text stays escaped.
