# cloudwatch-log-forwarder

Daemon that ships application logs to CloudWatch Logs on a configurable
interval. Supports log group creation, retention policy enforcement, and
structured JSON log parsing. Designed to run as a sidecar alongside
long-running services.

## Usage

```bash
python forwarder.py --log-dir /var/log/app --group /prod/app --interval 60
```

## Configuration

AWS credentials are in `aws_config.py`. The daemon appends a flush cycle
entry to `forwarder.log` on every run for uptime tracking.

## Requirements

- Python 3.9+
- boto3
