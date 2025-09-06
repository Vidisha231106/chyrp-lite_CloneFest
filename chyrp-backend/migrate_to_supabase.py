#!/usr/bin/env python3
"""
Database Migration Script for Supabase PostgreSQL
This script helps migrate your existing data to Supabase PostgreSQL
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from database import engine, Base
from models import *  # Import all models

# Load environment variables
load_dotenv()

def test_supabase_connection():
    """Test connection to Supabase PostgreSQL database."""
    try:
        database_url = os.getenv("SUPABASE_DATABASE_URL")
        if not database_url:
            print("❌ SUPABASE_DATABASE_URL not found in environment variables")
            return False
        
        # Test connection
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Successfully connected to Supabase PostgreSQL database")
            return True
            
    except Exception as e:
        print(f"❌ Failed to connect to Supabase database: {e}")
        return False

def create_tables():
    """Create all tables in Supabase database."""
    try:        
        print("🔄 Creating tables in Supabase database...")
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False

def main():
    """Main migration function."""
    print("🚀 Starting Supabase PostgreSQL Migration")
    print("=" * 50)
    
    # Test connection
    if not test_supabase_connection():
        sys.exit(1)
    
    # Create tables
    if not create_tables():
        sys.exit(1)
    
    print("=" * 50)
    print("🎉 Migration completed successfully!")
    print("\nNext steps:")
    print("1. Update your .env file with Supabase credentials")
    print("2. Run: python3 -m uvicorn main:app --reload")
    print("3. Test your API at: http://localhost:8000/docs")

if __name__ == "__main__":
    main()


