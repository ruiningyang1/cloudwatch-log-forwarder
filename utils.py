"""
utils.py — Helpers for the log-sync-daemon.
"""

import os
import glob
import logging
from datetime import datetime
from typing import List

logger = logging.getLogger(__name__)


def collect_log_files(directory: str, pattern: str = "*.log") -> List[str]:
    """Return all log files in directory matching pattern."""
    if not os.path.isdir(directory):
        logger.warning(f"Log directory not found: {directory}")
        return []
    return sorted(glob.glob(os.path.join(directory, pattern)))


def upload_file(s3_client, local_path: str, bucket: str, key: str) -> None:
    """Upload a single file to S3."""
    s3_client.upload_file(local_path, bucket, key)
    logger.debug(f"Uploaded {local_path} → s3://{bucket}/{key}")


def prune_old_files(directory: str, cutoff: datetime, dry_run: bool = False) -> int:
    """Delete files older than cutoff. Returns count of pruned files."""
    pruned = 0
    for path in collect_log_files(directory):
        mtime = datetime.utcfromtimestamp(os.path.getmtime(path))
        if mtime < cutoff:
            if not dry_run:
                os.remove(path)
            logger.info(f"Pruned: {path} (mtime={mtime.isoformat()})")
            pruned += 1
    return pruned


def parse_log_timestamp(line: str) -> datetime | None:
    """Extract UTC timestamp from a heartbeat log line, or return None."""
    try:
        ts_str = line.split("]")[0].lstrip("[")
        return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S UTC")
    except (ValueError, IndexError):
        return None
