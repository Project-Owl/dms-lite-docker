# Migrating a legacy installation

This version replaces LinuxServer MariaDB 10.5 with official MariaDB 11.4.
Legacy `data/` contains a `/config` layout; it cannot be mounted directly at the
new `/var/lib/mysql`. New installations use `data-mariadb/` and need no migration.

The helper requires Python 3.10+, a local Unix-socket Docker daemon, Compose,
and enough free disk for a complete legacy copy, SQL export and restored database.
It supports the stock `clusterData`/`clusterCommands` tables and application
account. Custom tables, accounts, grants, triggers, routines or events require
the manual route below. Keep your existing MYSQL settings in `.env`.

1. Stop the old deployment cleanly using its original Compose files. Stop all
   writers and other processes accessing its storage. Save the original code,
   configuration and image references for rollback. Make an independent backup.
2. Run from the updated checkout:

   ```sh
   python3 scripts/migrate_database.py --source ./data --destination ./data-mariadb --env-file .env --backup-root ./backups --timeout-seconds 600
   ```

3. Require a successful exit and a `verified` summary. Keep the backup workspace.
   Set `DATABASE_DATA_DIR=./data-mariadb` (or your chosen destination), then start
   the new Compose pair as described in the README. Check existing messages,
   commands, device activity and ingestion before accepting the deployment.

The helper refuses overlapping paths, symlink aliases, nonempty destinations,
invalid legacy layouts and running containers mounting the affected directories.
Keep other processes stopped throughout migration; the checks cannot prevent an
external process starting after preflight. It mounts the original read-only only
to copy it. It boots the pinned legacy image against that copy, checks credentials
and supported objects/grants, and exports only the application database. It never
imports the old `mysql` system database. The official image creates fresh system
accounts and the configured application account.

The import session retains legacy defaults for the character sets in use, so a
new server default does not silently change text comparison rules.
Verification compares schema metadata plus sorted, encoded row hashes and counts
for both tables, preserving duplicate rows, NULL/empty distinctions and UTC dates.
The successful destination is shut down cleanly before the helper exits. No web
application or writer is started by migration. The timeout applies to each Docker
operation, rather than the complete migration; increase it for a large database.

Each attempt creates a private `backups/migration-*` workspace (0700) with a cold
copy, SQL export, verification rows and summary (files created by the helper are
0600). These contain real application data and account material in the cold copy;
protect them as database backups. Passwords are passed through process environment,
never command arguments or summaries. Docker administrators can inspect container
environments. Keep `.env`, backups and data directories out of Git.

On failure or Ctrl-C the original, export/copy and partial destination are retained;
only this attempt's labeled temporary containers are removed. The summary records
the last `phase`, a bounded `failure.kind` (operation failure, interruption,
unexpected error or cleanup failure), and `cleanup.status`. Raw exceptions, SQL
and passwords are never copied into these diagnostics. `cleanup.status=failed`
means removal could not be confirmed; inspect the attempt’s labelled containers
before retrying. Preflight refusals before workspace creation produce only a
terminal error. Inspect the summary
and resolve the problem before retrying with a distinct empty destination. An
abrupt host shutdown or SIGKILL can leave temporary containers: inspect ownership
labels before stopping/removing any resource. Do not delete a partial destination
until you have decided it is disposable.

## Rollback

Before resuming writes, stop the new stack and restart the saved old version with
its original configuration and untouched `data/`. The rehearsal verifies this path.
After new ingestion or command dispatch begins, the old copy is stale. Reconcile
new rows and command state before rollback; replaying queued commands can repeat
physical actions. The helper does not merge divergent databases or promise exactly
once command delivery.

## Customized databases

Use a database administrator's logical migration procedure on an offline copy.
Inventory databases, tables, engines, character sets, accounts, grants, definers,
triggers, routines and events. Export application objects/data with the matching
legacy client; create fresh target system tables with the official image; recreate
reviewed accounts/grants and handle definers explicitly. Restore only selected
application schemas, compare schema/row contents and verify the application's
queries and writes before cutover. Preserve the original and a rollback plan.
Never restore the legacy `mysql` schema wholesale or point 11.4 at the old datadir.
