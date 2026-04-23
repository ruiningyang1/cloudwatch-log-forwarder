"""
daemon.py — Log synchronization daemon.
Periodically ships local log files to S3 and prunes files older than
RETENTION_DAYS. Writes a heartbeat line to run_log.txt on each cycle.
"""

import os
import time
import boto3
import logging
import argparse
from datetime import datetime, timedelta
from aws_config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
from aws_config import S3_LOG_BUCKET, LOG_PREFIX, RETENTION_DAYS
from utils import collect_log_files, upload_file, prune_old_files

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

RUN_LOG = os.path.join(os.path.dirname(__file__), "run_log.txt")


def get_s3_client():
    session = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )
    return session.client("s3")


def sync_cycle(log_dir: str, dry_run: bool = False) -> int:
    """
    Run one sync cycle: collect, upload, prune.
    Returns the number of files shipped.
    """
    s3 = get_s3_client()
    files = collect_log_files(log_dir)
    shipped = 0

    for path in files:
        key = f"{LOG_PREFIX}/{os.path.basename(path)}"
        if not dry_run:
            upload_file(s3, path, S3_LOG_BUCKET, key)
        logger.debug(f"Shipped: {path} → s3://{S3_LOG_BUCKET}/{key}")
        shipped += 1

    cutoff = datetime.utcnow() - timedelta(days=RETENTION_DAYS)
    pruned = prune_old_files(log_dir, cutoff, dry_run=dry_run)
    logger.info(f"Cycle complete: {shipped} uploaded, {pruned} pruned")
    return shipped


def append_heartbeat(count: int) -> None:
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with open(RUN_LOG, "a") as f:
        f.write(f"[{ts} UTC] Heartbeat #{count}: daemon alive, {count} cycles completed\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Log sync daemon")
    parser.add_argument("--log-dir", default="/var/log/app", help="Directory to sync")
    parser.add_argument("--interval", type=int, default=60, help="Sync interval in seconds")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    logger.info(f"Daemon starting. Syncing {args.log_dir} every {args.interval}s")
    cycle_count = 0
    while True:
        cycle_count += 1
        try:
            sync_cycle(args.log_dir, dry_run=args.dry_run)
            append_heartbeat(cycle_count)
        except Exception as exc:
            logger.error(f"Cycle {cycle_count} failed: {exc}")
        time.sleep(args.interval)
