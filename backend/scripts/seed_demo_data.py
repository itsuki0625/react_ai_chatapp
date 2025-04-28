#!/usr/bin/env python3
"""
Initial demo data insertion script.
Run this once to populate the database with demo seed data.
"""
import os
import sys
import logging
from sqlalchemy.orm import Session

# Ensure project root is in PYTHONPATH
top_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if top_dir not in sys.path:
    sys.path.append(top_dir)

from app.database.database import SessionLocal
from app.migrations.demo_data import insert_demo_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting initial demo data insertion...")
    db: Session = SessionLocal()
    try:
        insert_demo_data(db)
        db.commit()
        logger.info("Demo data inserted successfully.")
    except Exception as e:
        logger.error(f"Error inserting demo data: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main() 