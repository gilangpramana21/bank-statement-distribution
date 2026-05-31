# Quick Start Guide

Get the Bank Statement Distribution System up and running in 10 minutes.

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- Google Drive API service account credentials
- SMTP email server access

## Step 1: Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd bank-statement-distribution

# Run setup script
chmod +x scripts/setup.sh
./scripts/setup.sh
```

## Step 2: Generate Encryption Key

```bash
# Generate encryption key
python3 scripts/generate_key.py

# Copy the generated key to your .env file
```

## Step 3: Configure Environment

Edit `.env` file:

```bash
# Required settings
ENCRYPTION_KEY=your-generated-key-here
DB_USER=postgres
DB_PASSWORD=your-db-password
EMAIL_USER=your-email@company.com
EMAIL_PASSWORD=your-email-password
ADMIN_EMAILS=admin@company.com
```

## Step 4: Add Google Drive Credentials

```bash
# Create credentials directory
mkdir -p credentials

# Copy your Google Drive service account JSON file
cp /path/to/your/service-account.json credentials/google_drive_credentials.json
```

## Step 5: Configure System

Edit `config.yaml`:

```yaml
google_drive:
  bank_groups:
    - "Organic Bank Statements"
    - "SAPTA Bank Statements"
    - "IPM Bank Statements"

email:
  smtp_host: "smtp.gmail.com"
  smtp_port: 587
  sender_address: "statements@yourcompany.com"

database:
  host: "localhost"
  port: 5432
  database: "bank_statements"
```

## Step 6: Initialize Database

```bash
# Activate virtual environment
source venv/bin/activate

# Initialize database
python main.py init
```

## Step 7: Add Financiers

Connect to your database and add financiers:

```sql
-- Add financiers
INSERT INTO financiers (name, email_address, active_status) VALUES
('Financier A', 'financier.a@example.com', 'active'),
('Financier B', 'financier.b@example.com', 'active');

-- Add entity mappings
INSERT INTO entity_mappings (financier_id, entity_name, authorized_date) VALUES
(1, 'SMI', '2024-01-01'),
(1, 'PBS', '2024-01-01'),
(2, 'NSG', '2024-01-01');
```

Or use Python:

```python
from src.database import db
from src.models import Financier, EntityMapping, ActiveStatus
from datetime import datetime

with db.get_session() as session:
    # Add financier
    financier = Financier(
        name="Financier A",
        email_address="financier.a@example.com",
        active_status=ActiveStatus.ACTIVE
    )
    session.add(financier)
    session.flush()
    
    # Add entity mapping
    mapping = EntityMapping(
        financier_id=financier.financier_id,
        entity_name="SMI",
        authorized_date=datetime.now()
    )
    session.add(mapping)
```

## Step 8: Test Connections

```bash
# Test all connections
python main.py test-connections
```

Expected output:
```
Testing database connection... ✓ OK
Testing Google Drive API... ✓ OK
Testing email server... ✓ OK
```

## Step 9: Run First Distribution

```bash
# Run distribution workflow
python main.py run
```

## Step 10: Check Results

```bash
# Check system health
python main.py health

# View logs
tail -f logs/bank_statements.log
```

## Common Issues

### Issue: Google Drive Authentication Failed

**Solution:**
1. Verify credentials file exists: `credentials/google_drive_credentials.json`
2. Check service account has access to folders
3. Verify folder names in `config.yaml` match Google Drive

### Issue: Email Sending Failed

**Solution:**
1. Check SMTP credentials in `.env`
2. Verify SMTP host and port in `config.yaml`
3. For Gmail, enable "Less secure app access" or use App Password

### Issue: Database Connection Failed

**Solution:**
1. Verify PostgreSQL is running: `sudo systemctl status postgresql`
2. Check database credentials in `.env`
3. Verify database exists: `psql -U postgres -l`

## Next Steps

### Enable Scheduled Execution

```bash
# Start scheduler (runs monthly on 1st at 00:00 UTC)
python -m src.scheduler
```

### Set Up Monitoring

```bash
# Start health check server
python -m src.health_check

# Access health endpoint
curl http://localhost:8080/health
```

### Deploy to Production

See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment guide.

## Docker Quick Start

If you prefer Docker:

```bash
# Copy environment file
cp .env.example .env

# Edit .env with your values
nano .env

# Add credentials
mkdir -p credentials
cp /path/to/credentials.json credentials/google_drive_credentials.json

# Deploy with Docker
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

## Useful Commands

```bash
# Run for specific entity
python main.py run --entity SMI

# Run for specific date
python main.py run --date 2024-01-01

# Validate configuration
python main.py validate-config

# View logs
tail -f logs/bank_statements.log

# Check health
curl http://localhost:8080/health
```

## Getting Help

- **Documentation**: See [README.md](README.md)
- **API Reference**: See [API.md](API.md)
- **Deployment Guide**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **Support**: support@yourcompany.com

## What's Next?

1. **Customize Configuration**: Adjust rate limits, batch sizes, and timeouts in `config.yaml`
2. **Add More Financiers**: Add financiers and entity mappings to the database
3. **Set Up Monitoring**: Integrate with your monitoring system
4. **Schedule Backups**: Set up automated database backups
5. **Review Logs**: Regularly review audit logs for issues

## Tips

- Start with a small test run using `--entity` filter
- Monitor the first few executions closely
- Review audit logs after each execution
- Set up alerts for failed deliveries
- Keep credentials secure and rotate regularly

---

**Congratulations!** Your Bank Statement Distribution System is now running. 🎉
