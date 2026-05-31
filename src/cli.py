"""
Command Line Interface for Bank Statement Distribution System.
"""

import sys
import argparse
from datetime import datetime
from src.config import config
from src.database import db
from src.orchestrator import Orchestrator
from src.logger import setup_logging, get_logger
from src.models import Base

logger = get_logger(__name__)


def init_database():
    """Initialize database tables."""
    try:
        print("Initializing database...")
        db.create_tables()
        print("Database initialized successfully!")
        
    except Exception as e:
        print(f"Database initialization failed: {e}")
        sys.exit(1)


def validate_config():
    """Validate system configuration."""
    try:
        print("Validating configuration...")
        
        errors = config.validate()
        
        if errors:
            print("\nConfiguration validation failed:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
        
        print("Configuration validated successfully!")
        
    except Exception as e:
        print(f"Configuration validation failed: {e}")
        sys.exit(1)


def run_distribution(entity: str = None, date: str = None):
    """
    Run the distribution workflow.
    
    Args:
        entity: Optional entity filter
        date: Optional date filter (ISO 8601 format)
    """
    try:
        print(f"\n{'='*60}")
        print("Bank Statement Distribution System")
        print(f"{'='*60}\n")
        
        if entity:
            print(f"Entity filter: {entity}")
        if date:
            print(f"Date filter: {date}")
        
        print("\nStarting distribution workflow...\n")
        
        # Create orchestrator
        orchestrator = Orchestrator()
        
        # Execute workflow
        summary = orchestrator.execute(
            entity_filter=entity,
            date_filter=date
        )
        
        # Print summary
        print(f"\n{'='*60}")
        print("Execution Summary")
        print(f"{'='*60}\n")
        print(f"Execution ID: {summary['execution_id']}")
        print(f"Start Time: {summary['start_time']}")
        print(f"End Time: {summary['end_time']}")
        print(f"Duration: {summary['duration_seconds']} seconds")
        print(f"\nFiles Discovered: {summary['files_discovered']}")
        print(f"Files Processed: {summary['files_processed']}")
        print(f"Emails Sent: {summary['emails_sent']}")
        print(f"Delivery Failures: {summary['delivery_failures']}")
        
        if summary['delivery_failures'] > 0:
            print("\nFailure Details:")
            for failure in summary.get('failure_details', []):
                print(f"  - {failure}")
        
        print(f"\n{'='*60}\n")
        
        if summary['delivery_failures'] > 0:
            sys.exit(1)
        
    except Exception as e:
        print(f"\nExecution failed: {e}")
        logger.error("cli_execution_failed", error=str(e))
        sys.exit(1)


def test_connections():
    """Test all system connections."""
    try:
        print("\nTesting system connections...\n")
        
        # Test database
        print("Testing database connection...", end=" ")
        if db.test_connection():
            print("✓ OK")
        else:
            print("✗ FAILED")
        
        # Test Google Drive
        print("Testing Google Drive API...", end=" ")
        try:
            from src.statement_scanner import StatementScanner
            scanner = StatementScanner()
            if scanner.service:
                print("✓ OK")
            else:
                print("✗ FAILED")
        except Exception as e:
            print(f"✗ FAILED: {e}")
        
        # Test Email
        print("Testing email server...", end=" ")
        try:
            from src.email_distributor import EmailDistributor
            distributor = EmailDistributor()
            if distributor.test_connection():
                print("✓ OK")
            else:
                print("✗ FAILED")
        except Exception as e:
            print(f"✗ FAILED: {e}")
        
        print("\nConnection tests completed!\n")
        
    except Exception as e:
        print(f"\nConnection test failed: {e}")
        sys.exit(1)


def show_health():
    """Show system health status."""
    try:
        from src.health_check import HealthCheckService
        
        print("\nChecking system health...\n")
        
        health_service = HealthCheckService()
        health_status = health_service.get_health_status()
        
        print(f"Overall Status: {health_status['status'].upper()}")
        print(f"Timestamp: {health_status['timestamp']}")
        print(f"Last Execution: {health_status.get('last_execution', 'N/A')}")
        
        print("\nConnectivity:")
        connectivity = health_status.get('connectivity', {})
        print(f"  Google Drive: {connectivity.get('google_drive', 'unknown')}")
        print(f"  Email Server: {connectivity.get('email_server', 'unknown')}")
        print(f"  Database: {connectivity.get('database', 'unknown')}")
        
        print("\nDeliveries:")
        deliveries = health_status.get('deliveries', {})
        print(f"  Pending: {deliveries.get('pending', 0)}")
        print(f"  Failed (24h): {deliveries.get('failed_last_24h', 0)}")
        
        print()
        
    except Exception as e:
        print(f"\nHealth check failed: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    # Setup logging
    setup_logging()
    
    # Create argument parser
    parser = argparse.ArgumentParser(
        description='Bank Statement Distribution System',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    subparsers.add_parser('init', help='Initialize database')
    
    # Validate command
    subparsers.add_parser('validate-config', help='Validate configuration')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run distribution workflow')
    run_parser.add_argument('--entity', type=str, help='Filter by entity name')
    run_parser.add_argument('--date', type=str, help='Filter by date (ISO 8601 format)')
    
    # Test command
    subparsers.add_parser('test-connections', help='Test system connections')
    
    # Health command
    subparsers.add_parser('health', help='Show system health status')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    if args.command == 'init':
        init_database()
    
    elif args.command == 'validate-config':
        validate_config()
    
    elif args.command == 'run':
        run_distribution(entity=args.entity, date=args.date)
    
    elif args.command == 'test-connections':
        test_connections()
    
    elif args.command == 'health':
        show_health()
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
