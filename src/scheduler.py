"""
Scheduler for automated execution of bank statement distribution.
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from src.config import config
from src.orchestrator import Orchestrator
from src.logger import setup_logging, get_logger

logger = get_logger(__name__)


class DistributionScheduler:
    """Scheduler for automated distribution workflow."""
    
    def __init__(self):
        """Initialize scheduler."""
        self.scheduler = BlockingScheduler()
        self.orchestrator = None
    
    def scheduled_job(self):
        """Execute scheduled distribution job."""
        try:
            logger.info("scheduled_job_started", 
                       timestamp=datetime.utcnow().isoformat())
            
            # Create new orchestrator instance
            self.orchestrator = Orchestrator()
            
            # Execute workflow
            summary = self.orchestrator.execute()
            
            logger.info("scheduled_job_completed",
                       execution_id=summary['execution_id'],
                       files_processed=summary['files_processed'],
                       emails_sent=summary['emails_sent'])
            
        except Exception as e:
            logger.error("scheduled_job_failed", error=str(e))
    
    def start(self):
        """Start the scheduler."""
        try:
            if not config.get('scheduler.enabled', True):
                logger.info("scheduler_disabled")
                return
            
            # Get cron expression from config
            cron_expression = config.get('scheduler.cron_expression', '0 0 1 * *')
            timezone = config.get('scheduler.timezone', 'UTC')
            
            # Parse cron expression
            # Format: minute hour day month day_of_week
            parts = cron_expression.split()
            
            if len(parts) != 5:
                raise ValueError(f"Invalid cron expression: {cron_expression}")
            
            minute, hour, day, month, day_of_week = parts
            
            # Create trigger
            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week,
                timezone=timezone
            )
            
            # Add job
            self.scheduler.add_job(
                self.scheduled_job,
                trigger=trigger,
                id='distribution_job',
                name='Bank Statement Distribution',
                replace_existing=True
            )
            
            logger.info("scheduler_started",
                       cron_expression=cron_expression,
                       timezone=timezone)
            
            print(f"\nScheduler started!")
            print(f"Cron expression: {cron_expression}")
            print(f"Timezone: {timezone}")
            print(f"Next run: {self.scheduler.get_jobs()[0].next_run_time}")
            print("\nPress Ctrl+C to exit\n")
            
            # Start scheduler (blocking)
            self.scheduler.start()
            
        except KeyboardInterrupt:
            logger.info("scheduler_stopped_by_user")
            self.stop()
        
        except Exception as e:
            logger.error("scheduler_start_failed", error=str(e))
            raise
    
    def stop(self):
        """Stop the scheduler."""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("scheduler_stopped")
        
        except Exception as e:
            logger.error("scheduler_stop_failed", error=str(e))


def main():
    """Main entry point for scheduler."""
    # Setup logging
    setup_logging()
    
    logger.info("scheduler_initializing")
    
    # Create and start scheduler
    scheduler = DistributionScheduler()
    scheduler.start()


if __name__ == '__main__':
    main()
