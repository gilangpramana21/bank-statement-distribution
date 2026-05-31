# Testing Guide - Bank Statement Distribution System

## ✅ System Status

**Database**: PostgreSQL 15.17 ✅ Running  
**Tables**: 8 tables created ✅  
**Sample Data**: 3 financiers, 9 entity mappings ✅  
**Environment**: `.env` configured ✅

---

## 🗄️ Database Information

### Connection Details
- **Host**: localhost
- **Port**: 5432
- **Database**: bank_statements
- **User**: postgres
- **Password**: postgres

### Sample Financiers

| ID | Name | Email | Entities |
|----|------|-------|----------|
| 2 | PT Sumber Makmur Indah | finance@smi.co.id | SMI, PT SMI, Sumber Makmur |
| 3 | PT Perdana Bangun Sejahtera | accounting@pbs.co.id | PBS, PT PBS, Perdana Bangun |
| 4 | CV Mitra Usaha Bersama | admin@mub.co.id | MUB, CV MUB, Mitra Usaha |

---

## 🧪 Testing Commands

### 1. Test Database Connection
```bash
python -c "from src.database import db; print('✅ Connected!' if db.test_connection() else '❌ Failed')"
```

### 2. Test Core Modules (Without Database Operations)
```bash
python demo_without_db.py
```

### 3. Query Database Directly

**List all financiers:**
```bash
/opt/homebrew/opt/postgresql@15/bin/psql -U postgres -d bank_statements \
  -c "SELECT * FROM financiers;"
```

**List all entity mappings:**
```bash
/opt/homebrew/opt/postgresql@15/bin/psql -U postgres -d bank_statements \
  -c "SELECT m.entity_name, f.name FROM entity_mappings m JOIN financiers f ON m.financier_id = f.financier_id;"
```

**Check statement files:**
```bash
/opt/homebrew/opt/postgresql@15/bin/psql -U postgres -d bank_statements \
  -c "SELECT * FROM statement_files;"
```

### 4. Add More Sample Data
```bash
python add_sample_data.py
```

---

## 🚀 Running the Full System

### Prerequisites
Before running the full system, you need:

1. **Google Drive API Credentials** (for scanning statements)
   - Create a project in Google Cloud Console
   - Enable Google Drive API
   - Download credentials JSON
   - Place in project root or configure path in `config.yaml`

2. **SMTP Email Configuration** (for sending emails)
   - Update `.env` with real email credentials:
     ```
     EMAIL_USER=your-email@gmail.com
     EMAIL_PASSWORD=your-app-password
     ```

3. **Statement Files in Google Drive**
   - Organize files in folder structure: `/BankName/EntityName/statements.pdf`
   - Example: `/BCA/SMI/statement_jan2024.pdf`

### Run Commands

**One-time execution:**
```bash
python main.py run
```

**Start scheduler (runs monthly):**
```bash
python main.py schedule
```

**Check system health:**
```bash
python main.py health
```

---

## 🔍 Monitoring & Logs

### View Application Logs
```bash
tail -f logs/bank_statements.log
```

### View Audit Logs (Database)
```bash
/opt/homebrew/opt/postgresql@15/bin/psql -U postgres -d bank_statements \
  -c "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 10;"
```

### Check System Health
```bash
/opt/homebrew/opt/postgresql@15/bin/psql -U postgres -d bank_statements \
  -c "SELECT * FROM system_health ORDER BY check_timestamp DESC LIMIT 5;"
```

---

## 🐛 Troubleshooting

### Database Connection Issues

**Check if PostgreSQL is running:**
```bash
brew services list | grep postgresql
```

**Restart PostgreSQL:**
```bash
brew services restart postgresql@15
```

**Test connection manually:**
```bash
/opt/homebrew/opt/postgresql@15/bin/psql -U postgres -d bank_statements -c "SELECT version();"
```

### Module Import Errors

**Activate virtual environment:**
```bash
source venv/bin/activate
```

**Reinstall dependencies:**
```bash
pip install -r requirements.txt
```

### Encryption Key Issues

**Regenerate .env file:**
```bash
bash create_env.sh
```

---

## 📊 Database Schema

### Tables Created
1. **financiers** - Financier information
2. **entity_mappings** - Entity to financier mappings
3. **statement_files** - Discovered statement files
4. **delivery_status** - Email delivery tracking
5. **audit_logs** - System audit trail
6. **execution_summaries** - Monthly execution summaries
7. **processing_state** - Idempotent processing state
8. **system_health** - Health check results

### View Schema
```bash
/opt/homebrew/opt/postgresql@15/bin/psql -U postgres -d bank_statements -c "\d+ financiers"
```

---

## 🔐 Security Notes

- `.env` file contains sensitive credentials - **DO NOT commit to git**
- Encryption key is auto-generated - keep it secure
- Database passwords should be encrypted in production
- Use app-specific passwords for Gmail SMTP

---

## 📝 Next Steps

1. **Configure Google Drive API**
   - Follow: https://developers.google.com/drive/api/quickstart/python
   - Download credentials and update `config.yaml`

2. **Configure Email SMTP**
   - For Gmail: Enable 2FA and create app password
   - Update `.env` with real credentials

3. **Test with Real Data**
   - Upload sample statements to Google Drive
   - Run: `python main.py run`
   - Check logs and database for results

4. **Deploy to Production**
   - See `DEPLOYMENT.md` for Docker deployment
   - Configure production environment variables
   - Set up monitoring and alerting

---

## 🆘 Support

For issues or questions:
1. Check logs: `logs/bank_statements.log`
2. Review documentation: `README.md`, `QUICKSTART.md`
3. Check database state with SQL queries above
4. Run demo script to isolate issues: `python demo_without_db.py`
