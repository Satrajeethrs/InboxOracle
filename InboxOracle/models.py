#!/usr/bin/env python3

from sqlalchemy import create_engine, Column, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from loguru import logger

# Create the base class for declarative models
Base = declarative_base()

class Email(Base):
    """SQLAlchemy model for storing Gmail messages"""
    __tablename__ = 'emails'

    id = Column(String, primary_key=True)
    sender = Column(String, nullable=False)
    to = Column(String)
    subject = Column(String)
    body = Column(String)
    received = Column(DateTime, nullable=False)
    is_read = Column(Boolean, default=False)

    def __repr__(self):
        return f"<Email(id={self.id}, sender='{self.sender}', to='{self.to}', subject='{self.subject}')>"

def init_db(db_path='emails.db'):
    """
    Initialize the SQLite database and create tables.
    
    Args:
        db_path (str): Path to the SQLite database file
    
    Returns:
        tuple: (engine, Session) for database operations
    """
    try:
        # Create SQLite engine
        engine = create_engine(f'sqlite:///{db_path}')
        
        # Create all tables
        Base.metadata.create_all(engine)
        
        # Create session factory
        Session = sessionmaker(bind=engine)
        
        logger.info(f"Database initialized successfully at {db_path}")
        return engine, Session
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return None, None

if __name__ == '__main__':
    # Test database initialization
    engine, Session = init_db()
    if engine and Session:
        logger.success("Database setup successful!")
    else:
        logger.error("Database setup failed!")