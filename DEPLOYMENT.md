# Deployment Guide

This guide provides detailed instructions for deploying the Bank Statement Distribution System in a production environment.

## Prerequisites

- Linux server (Ubuntu 20.04+ recommended)
- Docker and Docker Compose installed
- PostgreSQL 12+ (or use Docker container)
- Google Drive API service account credentials
- SMTP email server access
- Minimum 2GB RAM, 10GB disk space

## Deployment Options

### Option 1: Docker Deployment (Recommended)

1. **Prepare the server**

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install docker-compose -y
```

2. **Clone the repository**

```bash
git clone <repository-url>
cd bank-statement-distribution
```

3. **Configure environment**

```bash
# Copy environment template
cp .env.example .env

# Generate encryption key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Edit .env with your values
nano .env
```

4. **Add credentials**

```bash
# Create credentials directory
mkdir -p credentials

# Copy Google Drive service account credentials
cp /path/to/your/credentials.json credentials/google_drive_credentials.json
```

5. **Configure system**

```bash
# Edit config.yaml
nano config.yaml

# Update:
# - Bank group folders
# - SMTP settings
# - Rate limits
# - Scheduler settings
```

6. **Deploy**

```bash
# Make deploy script executable
chmod +x scripts/deploy.sh

# Run deployment
./scripts/deploy.sh
```

7. **Verify deployment**

```bash
# Check services
docker-compose ps

# Check logs
docker-compose logs -f

# Test health endpoint
curl http://localhost:8080/health
```

### Option 2: Manual Deployment

1. **Install Python and dependencies**

```bash
# Install Python 3.8+
sudo apt-get install python3 python3-pip python3-venv -y

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

2. **Install PostgreSQL**

```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib -y

# Create database
sudo -u postgres psql
CREATE DATABASE bank_statements;
CREATE USER your_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE bank_statements TO your_user;
\q
```

3. **Configure and run**

```bash
# Setup environment
cp .env.example .env
nano .env

# Initialize database
python main.py init

# Validate configuration
python main.py validate-config

# Test connections
python main.py test-connections
```

4. **Set up systemd service**

Create `/etc/systemd/system/bank-statements.service`:

```ini
[Unit]
Description=Bank Statement Distribution System
After=network.target postgresql.service

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/bank-statement-distribution
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python -m src.scheduler
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable bank-statements
sudo systemctl start bank-statements
sudo systemctl status bank-statements
```

## Security Hardening

### 1. Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 8080/tcp  # Health check (optional, can be internal only)
sudo ufw enable
```

### 2. Credential Management

- Store credentials in encrypted format
- Use environment variables for sensitive data
- Rotate credentials regularly
- Use separate service accounts with minimal permissions

### 3. Database Security

```bash
# Configure PostgreSQL for local connections only
sudo nano /etc/postgresql/*/main/pg_hba.conf

# Add:
# local   all   all   md5
# host    all   all   127.0.0.1/32   md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### 4. SSL/TLS

- Use TLS for SMTP connections
- Use SSL for database connections (if remote)
- Use HTTPS for health check endpoint (with reverse proxy)

## Monitoring

### 1. Health Check Monitoring

Set up monitoring to check the health endpoint:

```bash
# Example with cron
*/5 * * * * curl -f http://localhost:8080/health || echo "Health check failed" | mail -s "Alert" admin@company.com
```

### 2. Log Monitoring

```bash
# View logs
tail -f logs/bank_statements.log

# Set up log rotation
sudo nano /etc/logrotate.d/bank-statements
```

Add:

```
/path/to/bank-statement-distribution/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 your_user your_group
    sharedscripts
    postrotate
        systemctl reload bank-statements > /dev/null 2>&1 || true
    endscript
}
```

### 3. Database Monitoring

```bash
# Monitor database size
psql -U your_user -d bank_statements -c "SELECT pg_size_pretty(pg_database_size('bank_statements'));"

# Monitor table sizes
psql -U your_user -d bank_statements -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

## Backup and Recovery

### 1. Database Backup

```bash
# Create backup script
cat > /usr/local/bin/backup-bank-statements.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/bank-statements"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
pg_dump -U your_user bank_statements | gzip > $BACKUP_DIR/backup_$DATE.sql.gz
# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
EOF

chmod +x /usr/local/bin/backup-bank-statements.sh

# Add to cron (daily at 2 AM)
echo "0 2 * * * /usr/local/bin/backup-bank-statements.sh" | crontab -
```

### 2. Configuration Backup

```bash
# Backup configuration files
tar -czf config-backup-$(date +%Y%m%d).tar.gz config.yaml .env credentials/
```

### 3. Recovery

```bash
# Restore database
gunzip -c backup_20240115_020000.sql.gz | psql -U your_user bank_statements

# Restore configuration
tar -xzf config-backup-20240115.tar.gz
```

## Scaling

### Horizontal Scaling

For high-volume processing:

1. **Separate components**:
   - Run scanner on one server
   - Run distributor on another server
   - Use shared database

2. **Load balancing**:
   - Use multiple distributor instances
   - Implement job queue (e.g., Celery with Redis)

3. **Database optimization**:
   - Add indexes for frequently queried columns
   - Partition large tables by date
   - Use read replicas for reporting

### Vertical Scaling

- Increase server resources (CPU, RAM)
- Optimize batch sizes in config.yaml
- Adjust rate limits based on API quotas

## Troubleshooting

### Common Issues

1. **Google Drive API quota exceeded**
   - Reduce rate limit in config.yaml
   - Increase cooldown period
   - Request quota increase from Google

2. **Email sending failures**
   - Check SMTP credentials
   - Verify firewall allows outbound SMTP
   - Check email server rate limits

3. **Database connection issues**
   - Verify PostgreSQL is running
   - Check connection settings
   - Verify credentials

4. **Out of disk space**
   - Clean up old logs
   - Clean up temporary files
   - Archive old audit logs

### Debug Mode

Enable debug logging:

```yaml
# config.yaml
logging:
  level: "DEBUG"
```

## Maintenance

### Regular Tasks

1. **Weekly**:
   - Review logs for errors
   - Check disk space
   - Verify backups

2. **Monthly**:
   - Review audit logs
   - Clean up old data
   - Update dependencies

3. **Quarterly**:
   - Rotate credentials
   - Review and update configuration
   - Performance optimization

### Updates

```bash
# Pull latest code
git pull

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart service
sudo systemctl restart bank-statements
```

## Support

For issues or questions:
- Check logs: `logs/bank_statements.log`
- Review audit logs in database
- Contact: support@yourcompany.com
