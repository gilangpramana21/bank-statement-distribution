# Project Structure

Complete overview of the Bank Statement Distribution System project structure.

## Directory Tree

```
bank-statement-distribution/
├── docs/                            # Documentation and specifications
│   └── specs/
│       └── bank-statement-distribution/
│           ├── requirements.md     # System requirements
│           └── design.md          # Technical design
│
├── src/                           # Source code
│   ├── __init__.py               # Package initialization
│   ├── config.py                 # Configuration management
│   ├── models.py                 # Database models
│   ├── database.py               # Database connection
│   ├── security.py               # Credential encryption
│   ├── logger.py                 # Logging configuration
│   ├── statement_scanner.py      # Google Drive scanner
│   ├── entity_grouper.py         # Entity grouping logic
│   ├── package_manager.py        # ZIP packaging
│   ├── email_distributor.py      # Email distribution
│   ├── audit_logger.py           # Audit logging
│   ├── health_check.py           # Health monitoring
│   ├── orchestrator.py           # Main orchestrator
│   ├── cli.py                    # Command-line interface
│   └── scheduler.py              # Scheduled execution
│
├── tests/                        # Test suite
│   ├── __init__.py
│   └── test_entity_grouper.py   # Entity grouper tests
│
├── scripts/                      # Utility scripts
│   ├── setup.sh                 # Setup script
│   ├── deploy.sh                # Deployment script
│   └── generate_key.py          # Encryption key generator
│
├── credentials/                  # Credentials (gitignored)
│   └── google_drive_credentials.json
│
├── logs/                        # Log files (gitignored)
│   └── bank_statements.log
│
├── main.py                      # Main entry point
├── config.yaml                  # System configuration
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── .gitignore                   # Git ignore rules
│
├── Dockerfile                   # Docker image
├── docker-compose.yml           # Docker Compose config
│
├── README.md                    # Main documentation
├── QUICKSTART.md               # Quick start guide
├── DEPLOYMENT.md               # Deployment guide
├── API.md                      # API documentation
└── PROJECT_STRUCTURE.md        # This file
```

## Core Components

### 1. Configuration Layer

**Files:**
- `src/config.py` - Configuration management
- `config.yaml` - System configuration
- `.env` - Environment variables

**Purpose:**
- Load and validate configuration
- Manage environment-specific settings
- Provide configuration access to all components

### 2. Data Layer

**Files:**
- `src/models.py` - SQLAlchemy models
- `src/database.py` - Database connection and session management

**Models:**
- `Financier` - Financier information
- `EntityMapping` - Financier-entity mappings
- `StatementFile` - Statement file tracking
- `DeliveryStatus` - Delivery status tracking
- `AuditLog` - Audit trail
- `ProcessingState` - Processing state for fault tolerance
- `SystemHealth` - System health status
- `ExecutionSummary` - Execution summaries

### 3. Security Layer

**Files:**
- `src/security.py` - Credential encryption and management

**Features:**
- AES-256 encryption for credentials
- Credential masking in logs
- Secure credential rotation

### 4. Business Logic Layer

**Files:**
- `src/statement_scanner.py` - Google Drive integration
- `src/entity_grouper.py` - Entity-based grouping
- `src/package_manager.py` - ZIP packaging and splitting
- `src/email_distributor.py` - Email distribution

**Workflow:**
1. Scanner discovers files in Google Drive
2. Grouper reorganizes by entity
3. Packager creates ZIP archives
4. Distributor sends via email

### 5. Orchestration Layer

**Files:**
- `src/orchestrator.py` - Main workflow coordinator

**Responsibilities:**
- Coordinate all components
- Manage workflow execution
- Handle errors and retries
- Generate execution summaries

### 6. Monitoring Layer

**Files:**
- `src/audit_logger.py` - Comprehensive audit logging
- `src/health_check.py` - Health monitoring service
- `src/logger.py` - Structured logging

**Features:**
- Complete audit trail
- Health check HTTP endpoint
- Structured JSON logging
- Log rotation

### 7. Interface Layer

**Files:**
- `src/cli.py` - Command-line interface
- `src/scheduler.py` - Scheduled execution
- `main.py` - Main entry point

**Interfaces:**
- CLI for manual execution
- Scheduler for automated execution
- Health check API for monitoring

## Data Flow

```
┌─────────────────┐
│  Google Drive   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Statement       │
│ Scanner         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Entity          │
│ Grouper         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Package         │
│ Manager         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Email           │
│ Distributor     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Financiers     │
└─────────────────┘
```

## Configuration Files

### config.yaml

Main system configuration:
- Google Drive settings
- Email/SMTP settings
- Database configuration
- Processing parameters
- Retry settings
- Rate limits
- Scheduler settings
- Logging configuration

### .env

Environment-specific secrets:
- Encryption key
- Database credentials
- Email credentials
- Admin email addresses

### requirements.txt

Python dependencies:
- Google API client
- SQLAlchemy (database ORM)
- Cryptography (encryption)
- APScheduler (scheduling)
- Flask (health check API)
- Structlog (structured logging)
- Tenacity (retry logic)

## Database Schema

### Tables

1. **financiers**
   - financier_id (PK)
   - name
   - email_address
   - active_status
   - created_at, updated_at

2. **entity_mappings**
   - mapping_id (PK)
   - financier_id (FK)
   - entity_name
   - authorized_date
   - created_at

3. **statement_files**
   - file_id (PK)
   - file_path (unique)
   - bank_name
   - entity_name
   - file_size
   - last_modified
   - checksum (SHA-256)
   - status
   - discovered_at, processed_at

4. **delivery_status**
   - delivery_id (PK)
   - file_id (FK)
   - financier_id (FK)
   - status
   - delivery_timestamp
   - retry_count
   - last_error
   - created_at, updated_at

5. **audit_logs**
   - log_id (PK)
   - timestamp
   - operation_type
   - outcome
   - component_name
   - entity_name
   - financier_email
   - file_path
   - attachment_names
   - attachment_sizes
   - checksum
   - error_type
   - error_message
   - context_info

6. **processing_state**
   - state_id (PK)
   - execution_id (UUID)
   - file_id (FK)
   - processing_status
   - target_financiers
   - created_at, updated_at

7. **system_health**
   - health_id (PK)
   - last_execution_timestamp
   - last_execution_status
   - gdrive_connectivity
   - email_connectivity
   - db_connectivity
   - pending_deliveries_count
   - failed_deliveries_count
   - updated_at

8. **execution_summaries**
   - summary_id (PK)
   - execution_id (UUID)
   - start_time, end_time
   - duration_seconds
   - files_discovered
   - files_processed
   - emails_sent
   - delivery_failures
   - failure_details
   - created_at

## Deployment Artifacts

### Docker

- `Dockerfile` - Container image definition
- `docker-compose.yml` - Multi-container orchestration

### Scripts

- `scripts/setup.sh` - Initial setup
- `scripts/deploy.sh` - Deployment automation
- `scripts/generate_key.py` - Encryption key generation

## Testing

### Test Structure

```
tests/
├── __init__.py
├── test_entity_grouper.py
├── test_package_manager.py (to be added)
├── test_email_distributor.py (to be added)
└── test_orchestrator.py (to be added)
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test
pytest tests/test_entity_grouper.py
```

## Logging

### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failures
- **CRITICAL**: Critical errors requiring immediate attention

### Log Format

Structured JSON logging:

```json
{
  "timestamp": "2024-01-15T10:30:00.000000Z",
  "level": "info",
  "logger": "src.orchestrator",
  "event": "execution_started",
  "execution_id": "uuid-here",
  "entity_filter": null,
  "date_filter": null
}
```

## Security Considerations

### Credentials

- All credentials encrypted with AES-256
- Encryption key stored separately
- Credentials never logged or exposed
- Support for credential rotation

### Access Control

- Financier-entity authorization checks
- Active status filtering
- Audit trail for all operations

### Network Security

- TLS/SSL for SMTP
- HTTPS for health check (with reverse proxy)
- Firewall rules for production

## Performance Optimization

### Rate Limiting

- Google Drive: 10 requests/second (configurable)
- Email: 10 emails/minute (configurable)
- Automatic pause when threshold reached

### Batch Processing

- Process files in batches of 100
- Split large entities into multiple batches
- Configurable batch sizes

### Resource Management

- Connection pooling for database
- Automatic cleanup of temporary files
- Log rotation to manage disk space

## Monitoring and Observability

### Health Check

- HTTP endpoint at `/health`
- Returns system status and metrics
- Checks all component connectivity

### Audit Logs

- Complete operation trail
- Queryable by date, entity, financier
- 24-month retention

### Execution Summaries

- Summary report after each execution
- Stored in database
- Sent to admin emails

## Extension Points

### Adding New Components

1. Create new module in `src/`
2. Implement component logic
3. Add to orchestrator workflow
4. Add tests in `tests/`
5. Update documentation

### Custom Workflows

Extend `Orchestrator` class:

```python
from src.orchestrator import Orchestrator

class CustomOrchestrator(Orchestrator):
    def execute(self, **kwargs):
        # Custom pre-processing
        result = super().execute(**kwargs)
        # Custom post-processing
        return result
```

### Integration Hooks

- Pre-execution hooks
- Post-execution hooks
- Custom notification handlers
- Custom audit log processors

## Maintenance

### Regular Tasks

- Review logs weekly
- Clean up old audit logs monthly
- Rotate credentials quarterly
- Update dependencies regularly

### Backup Strategy

- Database backups daily
- Configuration backups before changes
- Credential backups (encrypted)

## Support and Documentation

- **README.md** - Overview and features
- **QUICKSTART.md** - Getting started guide
- **DEPLOYMENT.md** - Production deployment
- **API.md** - API reference
- **PROJECT_STRUCTURE.md** - This document

## Version History

- **v1.0.0** - Initial release
  - Core workflow implementation
  - Google Drive integration
  - Email distribution
  - Audit logging
  - Health monitoring
  - Scheduled execution

## Future Enhancements

Potential improvements:
- Web-based admin dashboard
- Self-service financier portal
- Advanced reporting and analytics
- Multi-cloud storage support
- Enhanced notification system
- Machine learning for anomaly detection
