# 🏦 Bank Statement Distribution System

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg)]()

> **Automated workflow for distributing bank statements from Google Drive to financiers via email**

Replaces a manual 2-4 hour monthly process with a fully automated, secure, and auditable system.

---

## 🎯 Problem Solved

### Before (Manual Process - 2-4 hours)
- ❌ Download statements one by one from Google Drive
- ❌ Manually regroup files by entity (from bank-based folders)
- ❌ Manually compress and split files to stay within 25MB email limit
- ❌ Manually send multiple emails to each financier
- ❌ Repeat every month

### After (Automated - Single Command)
- ✅ **Automatic discovery** from Google Drive
- ✅ **Automatic regrouping** by entity across all banks
- ✅ **Automatic compression** and splitting at 25MB
- ✅ **Automatic email distribution** to authorized financiers
- ✅ **Scheduled monthly execution** or manual trigger

---

## ✨ Key Features

### Core Functionality
- 🔍 **Automatic Statement Discovery** - Scans Google Drive folders recursively
- 📊 **Entity-Based Grouping** - Regroups statements by entity (not bank)
- 📦 **Smart Packaging** - ZIP compression with automatic 25MB splitting
- 📧 **Email Distribution** - Direct attachments via SMTP with TLS
- 🔄 **Monthly Automation** - Scheduled execution on 1st of each month
- 🎯 **Single Trigger** - Manual execution with `python main.py run`

### Security & Compliance
- 🔐 **AES-256 Encryption** - Secure credential storage
- 📝 **Comprehensive Audit Logging** - 24-month retention
- ✅ **File Integrity Validation** - SHA-256 checksums
- 🔒 **Authorization Control** - Financier-entity mappings
- 🛡️ **Credential Rotation** - No code changes required

### Reliability & Performance
- ♻️ **Idempotent Processing** - No duplicate deliveries
- 🔁 **Automatic Retry Logic** - Exponential backoff for failures
- 🚦 **Rate Limiting** - API and email throttling
- 📊 **Batch Processing** - Handles up to 1000 files
- ⚡ **Connection Pooling** - Optimized database access

### Monitoring & Operations
- 🏥 **Health Check Endpoint** - HTTP monitoring at `/health`
- 📊 **Structured JSON Logging** - Easy log analysis
- 📈 **Execution Summaries** - Statistics and reports
- 🔍 **Configuration Validation** - Pre-execution checks
- 🐛 **Error Recovery** - Graceful failure handling

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 15+
- Google Drive API credentials
- SMTP email account

### Installation

```bash
# Clone repository
git clone https://github.com/gilangpramana21/bank-statement-distribution.git
cd bank-statement-distribution

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Generate environment file
bash create_env.sh

# Initialize database
python main.py init

# Add sample data (optional)
python add_sample_data.py
```

### Configuration

1. **Google Drive API**
   - Create project in [Google Cloud Console](https://console.cloud.google.com/)
   - Enable Google Drive API
   - Download `credentials.json`
   - Update `config.yaml` with folder IDs

2. **Email SMTP**
   - Get SMTP credentials (Gmail app password recommended)
   - Update `.env` with credentials
   - Update `config.yaml` with SMTP settings

3. **Database**
   - PostgreSQL should be running
   - Update `.env` with database credentials

### Usage

```bash
# One-time execution
python main.py run

# Start monthly scheduler
python main.py schedule

# Check system health
python main.py health

# Test without external services
python demo_without_db.py
```

---

## 📁 Project Structure

```
bank-statement-distribution/
├── src/                          # Source code
│   ├── statement_scanner.py     # Google Drive integration
│   ├── entity_grouper.py        # Entity-based file grouping
│   ├── package_manager.py       # ZIP packaging & splitting
│   ├── email_distributor.py     # Email sending with SMTP
│   ├── orchestrator.py          # Main workflow coordinator
│   ├── database.py              # Database connection & pooling
│   ├── models.py                # SQLAlchemy models
│   ├── security.py              # Encryption & credential management
│   ├── audit_logger.py          # Audit logging
│   ├── health_check.py          # Health monitoring
│   └── ...
├── tests/                        # Unit tests
├── scripts/                      # Utility scripts
├── docs/specs/                   # Requirements & design docs
├── main.py                       # Entry point
├── config.yaml                   # System configuration
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Docker image
├── docker-compose.yml            # Multi-container setup
└── README.md                     # This file
```

---

## 📚 Documentation

- **[START_HERE.md](START_HERE.md)** - Quick navigation guide
- **[QUICKSTART.md](QUICKSTART.md)** - 10-minute setup guide
- **[SETUP_COMPLETE.md](SETUP_COMPLETE.md)** - Post-setup instructions
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Testing instructions
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment
- **[API.md](API.md)** - API reference
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Code organization
- **[CLIENT_REQUIREMENTS_CHECKLIST.md](CLIENT_REQUIREMENTS_CHECKLIST.md)** - Requirements coverage

---

## 🗄️ Database Schema

### Tables
- **financiers** - Financier information and contact details
- **entity_mappings** - Entity-to-financier authorization mappings
- **statement_files** - Discovered statement files and metadata
- **delivery_status** - Email delivery tracking and retry state
- **audit_logs** - Comprehensive audit trail (24-month retention)
- **execution_summaries** - Monthly execution statistics
- **processing_state** - Idempotent processing state
- **system_health** - Health check results and connectivity status

---

## 🔧 Configuration Management

### Adding New Financiers

No code changes required! Simply add to database:

```sql
-- Add financier
INSERT INTO financiers (name, email_address, active_status)
VALUES ('PT Example Company', 'finance@example.com', 'ACTIVE');

-- Add entity mappings
INSERT INTO entity_mappings (financier_id, entity_name, authorized_date)
VALUES (1, 'SMI', '2024-01-01'),
       (1, 'PBS', '2024-01-01');
```

Or use the provided script:
```bash
python add_sample_data.py  # Modify script with your data
```

---

## 🐳 Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services included:
- **app** - Main application
- **scheduler** - Monthly scheduler
- **health** - Health check endpoint
- **postgres** - PostgreSQL database

---

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:8080/health
```

Response:
```json
{
  "status": "healthy",
  "last_execution": "2024-01-01T00:00:00Z",
  "pending_deliveries": 0,
  "failed_deliveries": 0,
  "google_drive": "connected",
  "email_server": "connected",
  "database": "connected"
}
```

### Logs
```bash
# Application logs
tail -f logs/bank_statements.log

# Audit logs (database)
psql -U postgres -d bank_statements \
  -c "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 10;"
```

---

## 🔐 Security

- **Encryption**: AES-256 for all credentials
- **TLS**: SMTP with STARTTLS or implicit TLS
- **Audit Trail**: All operations logged with timestamps
- **File Integrity**: SHA-256 checksums for validation
- **Authorization**: Financier-entity access control
- **Credential Rotation**: Database-driven, no code changes

---

## 🧪 Testing

```bash
# Test core modules (no external services)
python demo_without_db.py

# Test database connection
python -c "from src.database import db; print('✅ Connected!' if db.test_connection() else '❌ Failed')"

# Run unit tests
pytest tests/

# Test with sample data
python add_sample_data.py
python main.py run
```

---

## 🛠️ Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL status
brew services list | grep postgresql

# Restart PostgreSQL
brew services restart postgresql@15

# Test connection
psql -U postgres -d bank_statements -c "SELECT version();"
```

### Module Import Errors
```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Encryption Key Issues
```bash
# Regenerate .env file
bash create_env.sh
```

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for more troubleshooting tips.

---

## 📈 System Requirements

### Minimum
- **CPU**: 2 cores
- **RAM**: 2 GB
- **Storage**: 10 GB
- **Network**: Stable internet connection

### Recommended
- **CPU**: 4 cores
- **RAM**: 4 GB
- **Storage**: 50 GB (for logs and temporary files)
- **Network**: High-speed internet

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built with Python, PostgreSQL, and SQLAlchemy
- Google Drive API for file discovery
- SMTP for email distribution
- Docker for containerization

---

## 📞 Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Check documentation in the `docs/` folder
- Review logs: `tail -f logs/bank_statements.log`

---

## 🎯 Roadmap

- [ ] Web dashboard for monitoring and configuration
- [ ] Support for additional cloud storage providers (Dropbox, OneDrive)
- [ ] Advanced reporting and analytics
- [ ] Multi-language support
- [ ] API endpoints for integration

---

**Made with ❤️ for automating financial operations**
