"""Read-only preflight checks for local legacy database paths."""
from dataclasses import dataclass
from pathlib import Path

class MigrationError(Exception):
    """Safe operator-facing error; never includes credentials or SQL contents."""

@dataclass(frozen=True)
class MigrationPaths:
    source: Path
    destination: Path
    backup_root: Path

def overlaps(left, right):
    return left == right or left in right.parents or right in left.parents

def checked_path(value):
    path=Path(value).absolute()
    if any(part.is_symlink() for part in (path,*path.parents)):
        raise MigrationError('Symlink paths are not supported; use independent real directories')
    path=path.resolve()
    if path == Path(path.anchor):
        raise MigrationError('A filesystem root cannot be a migration path')
    if any(char in str(path) for char in ('\n','\r','\0')):
        raise MigrationError('Migration paths cannot contain control characters')
    return path

def plan_paths(source, destination, backup_root):
    source,destination,backup_root=map(checked_path,(source,destination,backup_root))
    if any(overlaps(a,b) for a,b in ((source,destination),(source,backup_root),(destination,backup_root))):
        raise MigrationError('Source, destination and backup directories must not overlap')
    checked_path(source/'databases/mysql')
    try:
        if not source.is_dir() or not (source/'databases/mysql').is_dir():
            raise MigrationError('Source is not the legacy LinuxServer data directory (databases/mysql missing)')
        if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
            raise MigrationError('Destination must be absent or empty; existing data is never overwritten')
        if backup_root.exists() and not backup_root.is_dir():
            raise MigrationError('Backup root must be a directory')
        if not (source.stat().st_mode & 0o444):
            raise MigrationError('Source is not readable')
    except OSError:
        raise MigrationError('Cannot read migration paths; check directory permissions') from None
    return MigrationPaths(source,destination,backup_root)

def assert_stopped(paths, runner):
    for mount in runner.running_mounts():
        existing=Path(mount).resolve()
        if any(overlaps(existing,path) for path in (paths.source,paths.destination,paths.backup_root)):
            raise MigrationError('A running container mounts a migration path; stop the old deployment first')
