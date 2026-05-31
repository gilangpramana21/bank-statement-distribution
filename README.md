# Bank Statement Distribution System

A production-ready automated workflow system for distributing bank statements from Google Drive to financiers via email attachments.

## Features

- **Automated Discovery**: Automatically scans Google Drive folders for new bank statements
- **Entity-Based Grouping**: Reorganizes statements from bank-based hierarchy to entity-based grouping
- **Smart Packaging**: Compresses statements into ZIP archives with automatic splitting for large files
- **Secure Distribution**: Sends statements as direct email attachments with authorization checks
- **Fault Tolerance**: Implements retry logic, error recovery, and idempotent processing
- **Comprehensive Auditing**: Maintains detailed audit logs of all operations
- **Health Monitoring**: Provides health check endpoint for system monitoring
- **Scheduled Execution**: Supports both scheduled (monthly) and manual execution

## Architecture

The system consists of the following components:

- **Statement Scanner**: Discovers bank statements in Google Drive
- **Entity Grouper**: Reorganizes files by entity
- **Package Manager**: Creates and splits ZIP archives
- **Email Distributor**: Sends packages via email with authorization
- **Audit Logger**: Maintains comprehensive audit logs
- **Health Check Service**: Monitors system health
- **Orchestrator**: Coordinates all components

## Requirements

- Python 3.8+
- PostgreSQL 12+
- Google Drive API credentials
- SMTP email server access

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd bank-statement-distribution
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your actual values
```

4. Configure the system:
```bash
# Edit config.yaml with your settings
```

5. Set up Google Drive credentials:
```bash
# Place your Google Drive service account credentials in:
# credentials/google_drive_credentials.json
```

6. Initialize the database:
```bash
python main.py init
```

7. Validate configuration:
```bash
python main.py validate-config
```

## Usage

### Manual Execution

Run the distribution workflow manually:

```bash
# Run for all entities
python main.py run

# Run for specific entity
python main.py run --entity SMI

# Run for specific date range
python main.py run --date 2024-01-01
```

### Scheduled Execution

Start the scheduler for automated monthly execution:

```bash
python -m src.scheduler
```

The scheduler will run on the first day of each month at 00:00 UTC (configurable in `config.yaml`).

### Health Check

Check system health status:

```bash
python main.py health
```

Or access the health check endpoint:

```bash
curl http://localhost:8080/health
```

### Test Connections

Test all system connections:

```bash
python main.py test-connections
```

## Configuration

### Environment Variables (.env)

```bash
# Encryption key for credentials
ENCRYPTION_KEY=your-encryption-key

# Database credentials
DB_USER=postgres
DB_PASSWORD=your-db-password

# Email credentials
EMAIL_USER=your-email@company.com
EMAIL_PASSWORD=your-email-password

# Admin emails (comma-separated)
ADMIN_EMAILS=admin1@company.com,admin2@company.com

# Environment
ENVIRONMENT=production
```

### System Configuration (config.yaml)

Key configuration options:

- **Google Drive**: Bank group folders, rate limits, max depth
- **Email**: SMTP settings, rate limits, attachment size limits
- **Database**: Connection settings
- **Processing**: Batch sizes, timeouts, retry settings
- **Scheduler**: Cron expression, timezone

See `config.yaml` for full configuration options.

## Database Schema

The system uses the following main tables:

- **financiers**: Stores financier information
- **entity_mappings**: Maps financiers to authorized entities
- **statement_files**: Tracks discovered statement files
- **delivery_status**: Tracks delivery status for each file-financier pair
- **audit_logs**: Comprehensive audit trail
- **execution_summaries**: Execution summary reports
- **system_health**: System health status

## Security

- **Credential Encryption**: All credentials encrypted with AES-256
- **TLS/SSL**: Email sent via TLS-encrypted SMTP
- **Access Control**: Authorization checks for all deliveries
- **Audit Logging**: Complete audit trail of all operations
- **Credential Masking**: Credentials masked in logs and error messages

## Monitoring

### Health Check Endpoint

The system exposes a health check endpoint at `/health` (default port 8080):

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "last_execution": "2024-01-01T00:00:00Z",
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

### Audit Logs

Query audit logs via the database or API:

```python
from src.audit_logger import AuditLogger

audit = AuditLogger()
logs = audit.query_logs(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31),
    entity_name="SMI"
)
```

## Error Handling

The system implements comprehensive error handling:

- **Transient Errors**: Automatic retry with exponential backoff
- **Permanent Errors**: Logged and skipped
- **Partial Failures**: Continue processing remaining items
- **State Persistence**: Resume from last successful operation after restart

## Performance

- **Rate Limiting**: Respects Google Drive API and email server limits
- **Batch Processing**: Processes files in configurable batches
- **Timeout Management**: Configurable timeouts with warnings
- **Resource Cleanup**: Automatic cleanup of temporary files

## Troubleshooting

### Common Issues

1. **Google Drive Authentication Failed**
   - Check credentials file exists and is valid
   - Verify service account has access to folders

2. **Email Sending Failed**
   - Verify SMTP credentials
   - Check firewall/network settings
   - Verify TLS/SSL settings

3. **Database Connection Failed**
   - Check database is running
   - Verify connection settings
   - Check credentials

### Logs

Logs are stored in `logs/bank_statements.log` with rotation.

View logs:
```bash
tail -f logs/bank_statements.log
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Structure

```
src/
├── config.py           # Configuration management
├── models.py           # Database models
├── database.py         # Database connection
├── security.py         # Credential encryption
├── logger.py           # Logging setup
├── statement_scanner.py    # Google Drive scanner
├── entity_grouper.py       # Entity grouping logic
├── package_manager.py      # ZIP packaging
├── email_distributor.py    # Email distribution
├── audit_logger.py         # Audit logging
├── health_check.py         # Health monitoring
├── orchestrator.py         # Main orchestrator
├── cli.py                  # Command-line interface
└── scheduler.py            # Scheduled execution
```

## License

Copyright © 2024 Your Company. All rights reserved.

## Support

For support, please contact: support@yourcompany.com
