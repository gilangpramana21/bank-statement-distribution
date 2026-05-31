"""
Database connection and session management.
"""

from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from src.config import config
from src.models import Base
from src.security import decrypt_credential
import structlog

logger = structlog.get_logger(__name__)


class Database:
    """Database connection manager."""
    
    def __init__(self):
        """Initialize database connection."""
        self.engine = None
        self.SessionLocal = None
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize database engine and session factory."""
        try:
            # Decrypt database credentials
            db_user = config.db_user
            # For development, allow plain text passwords
            try:
                db_password = decrypt_credential(config.db_password) if config.db_password else None
            except:
                # If decryption fails, assume it's plain text (for development)
                db_password = config.db_password
            
            # Build connection string
            connection_string = (
                f"postgresql://{db_user}:{db_password}@"
                f"{config.db_host}:{config.db_port}/{config.db_name}"
            )
            
            # Create engine with connection pooling
            self.engine = create_engine(
                connection_string,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,  # Verify connections before using
                echo=False
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info("database_initialized", 
                       host=config.db_host, 
                       database=config.db_name)
            
        except Exception as e:
            logger.error("database_initialization_failed", error=str(e))
            raise
    
    def create_tables(self) -> None:
        """Create all database tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("database_tables_created")
        except Exception as e:
            logger.error("database_table_creation_failed", error=str(e))
            raise
    
    def drop_tables(self) -> None:
        """Drop all database tables (use with caution!)."""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("database_tables_dropped")
        except Exception as e:
            logger.error("database_table_drop_failed", error=str(e))
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get database session context manager.
        
        Yields:
            Database session
            
        Example:
            with db.get_session() as session:
                # Use session
                pass
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error("database_session_error", error=str(e))
            raise
        finally:
            session.close()
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            from sqlalchemy import text
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error("database_connection_test_failed", error=str(e))
            return False
    
    def close(self) -> None:
        """Close database connection."""
        if self.engine:
            self.engine.dispose()
            logger.info("database_connection_closed")


# Global database instance
db = Database()
