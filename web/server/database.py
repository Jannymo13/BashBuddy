import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DB_POOLER")

# Create engine
engine = create_engine(DATABASE_URL, echo=False)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

def fetch_all_from_table(table_name):
    """
    Fetch all rows from a specified table.
    
    Args:
        table_name (str): Name of the table to query
    
    Returns:
        list: List of dictionaries containing the rows
    """
    try:
        db = SessionLocal()
        query = text(f"SELECT * FROM {table_name} LIMIT 100")
        result = db.execute(query)
        
        # Convert rows to list of dictionaries
        columns = result.keys()
        rows = [dict(zip(columns, row)) for row in result.fetchall()]
        
        db.close()
        return rows
    except Exception as e:
        raise Exception(f"Database error: {str(e)}")

def list_tables():
    """
    List all tables in the database.
    
    Returns:
        list: List of table names
    """
    try:
        db = SessionLocal()
        query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        result = db.execute(query)
        tables = [row[0] for row in result.fetchall()]
        db.close()
        return tables
    except Exception as e:
        raise Exception(f"Database error: {str(e)}")

def execute_query(sql_query, params=None):
    """
    Execute a custom SQL query.
    
    Args:
        sql_query (str): SQL query to execute
        params (dict, optional): Parameters for the query
    
    Returns:
        list: List of dictionaries containing the results
    """
    try:
        db = SessionLocal()
        query = text(sql_query)
        result = db.execute(query, params or {})
        
        # Convert rows to list of dictionaries
        columns = result.keys()
        rows = [dict(zip(columns, row)) for row in result.fetchall()]
        
        db.close()
        return rows
    except Exception as e:
        raise Exception(f"Database error: {str(e)}")
