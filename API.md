# API Documentation

## Health Check API

The Bank Statement Distribution System exposes a health check HTTP endpoint for monitoring system status.

### Endpoint

```
GET /health
```

### Response Format

#### Healthy Response

**Status Code:** `200 OK`

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000000Z",
  "last_execution": "2024-01-01T00:00:00.000000Z",
  "connectivity": {
    "google_drive": "connected",
    "email_server": "connected",
    "database": "connected"
  },
  "deliveries": {
    "pending": 0,
    "failed_last_24h": 0
  }
}
```

#### Unhealthy Response

**Status Code:** `503 Service Unavailable`

```json
{
  "status": "unhealthy",
  "timestamp": "2024-01-15T10:30:00.000000Z",
  "last_execution": "2024-01-01T00:00:00.000000Z",
  "connectivity": {
    "google_drive": "error",
    "email_server": "connected",
    "database": "connected"
  },
  "deliveries": {
    "pending": 5,
    "failed_last_24h": 3
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Overall system status: `"healthy"` or `"unhealthy"` |
| `timestamp` | string | Current timestamp in ISO 8601 format |
| `last_execution` | string | Timestamp of last successful execution (ISO 8601) |
| `connectivity.google_drive` | string | Google Drive API status: `"connected"`, `"disconnected"`, or `"error"` |
| `connectivity.email_server` | string | Email server status: `"connected"`, `"disconnected"`, or `"error"` |
| `connectivity.database` | string | Database status: `"connected"`, `"disconnected"`, or `"error"` |
| `deliveries.pending` | integer | Number of pending deliveries |
| `deliveries.failed_last_24h` | integer | Number of failed deliveries in last 24 hours |

### Health Status Logic

The system is considered **unhealthy** if:
- Any connectivity check returns `"disconnected"` or `"error"`
- There are failed deliveries in the last 24 hours

The system is considered **healthy** if:
- All connectivity checks return `"connected"`
- There are no failed deliveries in the last 24 hours

### Example Usage

#### cURL

```bash
curl http://localhost:8080/health
```

#### Python

```python
import requests

response = requests.get('http://localhost:8080/health')
health_data = response.json()

if health_data['status'] == 'healthy':
    print("System is healthy")
else:
    print("System is unhealthy")
    print(f"Issues: {health_data}")
```

#### Monitoring Script

```bash
#!/bin/bash
# health-check.sh

HEALTH_URL="http://localhost:8080/health"
ALERT_EMAIL="admin@company.com"

response=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $response -ne 200 ]; then
    echo "Health check failed with status code: $response" | \
        mail -s "Bank Statement System Alert" $ALERT_EMAIL
fi
```

## Command Line Interface

The system provides a comprehensive CLI for management and operations.

### Commands

#### Initialize Database

```bash
python main.py init
```

Initializes the database schema and creates all required tables.

#### Validate Configuration

```bash
python main.py validate-config
```

Validates system configuration including:
- Environment variables
- Configuration file
- Credentials
- Bank group folders
- Email settings

#### Run Distribution

```bash
# Run for all entities
python main.py run

# Run for specific entity
python main.py run --entity SMI

# Run for specific date
python main.py run --date 2024-01-01

# Run with both filters
python main.py run --entity SMI --date 2024-01-01
```

Executes the complete distribution workflow.

**Options:**
- `--entity`: Filter by entity name
- `--date`: Filter by date (ISO 8601 format: YYYY-MM-DD)

#### Test Connections

```bash
python main.py test-connections
```

Tests connectivity to:
- Database
- Google Drive API
- Email server

#### Show Health Status

```bash
python main.py health
```

Displays current system health status.

### Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | Error or failure |

## Python API

### Orchestrator

Main orchestrator for workflow execution.

```python
from src.orchestrator import Orchestrator

# Create orchestrator
orchestrator = Orchestrator()

# Execute workflow
summary = orchestrator.execute(
    entity_filter="SMI",  # Optional
    date_filter="2024-01-01"  # Optional
)

# Access summary
print(f"Files processed: {summary['files_processed']}")
print(f"Emails sent: {summary['emails_sent']}")
```

### Statement Scanner

Discover bank statements in Google Drive.

```python
from src.statement_scanner import StatementScanner

# Create scanner
scanner = StatementScanner()

# Discover statements
files = scanner.discover_statements()

for file in files:
    print(f"Found: {file.file_path}")
    print(f"Entity: {file.entity_name}")
    print(f"Size: {file.file_size} bytes")
```

### Entity Grouper

Group statements by entity.

```python
from src.entity_grouper import EntityGrouper

# Create grouper
grouper = EntityGrouper()

# Group files
entity_groups = grouper.group_by_entity(files)

for entity, entity_files in entity_groups.items():
    print(f"Entity: {entity}")
    print(f"Files: {len(entity_files)}")
```

### Package Manager

Create and manage ZIP packages.

```python
from src.package_manager import PackageManager

# Create package manager
packager = PackageManager()

# Create packages
packages = packager.create_packages(entity_groups)

for entity, entity_packages in packages.items():
    print(f"Entity: {entity}")
    print(f"Packages: {len(entity_packages)}")
    for package in entity_packages:
        print(f"  - {package.get_filename()}: {package.size} bytes")
```

### Email Distributor

Distribute packages via email.

```python
from src.email_distributor import EmailDistributor

# Create distributor
distributor = EmailDistributor()

# Distribute packages
successful, failed = distributor.distribute_packages(packages)

print(f"Successful: {successful}")
print(f"Failed: {failed}")
```

### Audit Logger

Query and manage audit logs.

```python
from src.audit_logger import AuditLogger
from datetime import datetime, timedelta

# Create audit logger
audit = AuditLogger()

# Query logs
start_date = datetime.now() - timedelta(days=30)
end_date = datetime.now()

logs = audit.query_logs(
    start_date=start_date,
    end_date=end_date,
    entity_name="SMI",
    limit=100
)

for log in logs:
    print(f"{log['timestamp']}: {log['operation_type']} - {log['outcome']}")
```

### Database Access

Direct database access for custom queries.

```python
from src.database import db
from src.models import StatementFile, Financier

# Query statement files
with db.get_session() as session:
    files = session.query(StatementFile).filter(
        StatementFile.entity_name == "SMI"
    ).all()
    
    for file in files:
        print(f"{file.file_path}: {file.status.value}")

# Query financiers
with db.get_session() as session:
    financiers = session.query(Financier).filter(
        Financier.active_status == "active"
    ).all()
    
    for financier in financiers:
        print(f"{financier.name}: {financier.email_address}")
```

## Integration Examples

### Monitoring Integration

#### Prometheus

```python
# prometheus_exporter.py
from prometheus_client import start_http_server, Gauge
from src.health_check import HealthCheckService
import time

# Create metrics
health_status = Gauge('bank_statements_health_status', 'System health status (1=healthy, 0=unhealthy)')
pending_deliveries = Gauge('bank_statements_pending_deliveries', 'Number of pending deliveries')
failed_deliveries = Gauge('bank_statements_failed_deliveries', 'Number of failed deliveries in last 24h')

def collect_metrics():
    health_service = HealthCheckService()
    health_data = health_service.get_health_status()
    
    # Update metrics
    health_status.set(1 if health_data['status'] == 'healthy' else 0)
    pending_deliveries.set(health_data['deliveries']['pending'])
    failed_deliveries.set(health_data['deliveries']['failed_last_24h'])

if __name__ == '__main__':
    start_http_server(9090)
    while True:
        collect_metrics()
        time.sleep(60)
```

#### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Bank Statement Distribution",
    "panels": [
      {
        "title": "System Health",
        "targets": [
          {
            "expr": "bank_statements_health_status"
          }
        ]
      },
      {
        "title": "Pending Deliveries",
        "targets": [
          {
            "expr": "bank_statements_pending_deliveries"
          }
        ]
      }
    ]
  }
}
```

### Webhook Integration

```python
# webhook_notifier.py
import requests
from src.orchestrator import Orchestrator

class WebhookOrchestrator(Orchestrator):
    def __init__(self, webhook_url):
        super().__init__()
        self.webhook_url = webhook_url
    
    def _send_summary_report(self, summary):
        # Send to webhook
        requests.post(self.webhook_url, json=summary)
        
        # Call parent method
        super()._send_summary_report(summary)

# Usage
orchestrator = WebhookOrchestrator("https://your-webhook.com/notify")
summary = orchestrator.execute()
```

## Error Codes

| Code | Description | Action |
|------|-------------|--------|
| `AUTH_001` | Google Drive authentication failed | Check credentials file |
| `AUTH_002` | Email authentication failed | Check SMTP credentials |
| `AUTH_003` | Database authentication failed | Check database credentials |
| `CONN_001` | Google Drive connection failed | Check network/firewall |
| `CONN_002` | Email server connection failed | Check SMTP settings |
| `CONN_003` | Database connection failed | Check database is running |
| `PROC_001` | File processing failed | Check file format/permissions |
| `PROC_002` | Package creation failed | Check disk space |
| `PROC_003` | Email delivery failed | Check recipient address |
| `CONF_001` | Configuration validation failed | Check config.yaml |
| `CONF_002` | Missing required configuration | Check .env file |

## Rate Limits

| Service | Default Limit | Configurable |
|---------|--------------|--------------|
| Google Drive API | 10 requests/second | Yes (config.yaml) |
| Email Sending | 10 emails/minute | Yes (config.yaml) |
| Health Check | No limit | N/A |

## Support

For API support:
- Documentation: See README.md
- Issues: GitHub Issues
- Email: support@yourcompany.com
