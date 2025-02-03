import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import getpass

def setup_database():
    try:
        # Get system username
        system_user = getpass.getuser()
        
        # Connect to PostgreSQL server as the system user
        conn = psycopg2.connect(
            dbname='postgres',
            user=system_user,
            host='localhost'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Create database if it doesn't exist
        cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'nutritiondb'")
        exists = cur.fetchone()
        if not exists:
            cur.execute('CREATE DATABASE nutritiondb')
            print("Created database 'nutritiondb'")
        
        cur.close()
        conn.close()
        
        print("Database setup completed successfully")
        return True
        
    except Exception as e:
        print(f"Database setup error: {str(e)}")
        return False

if __name__ == "__main__":
    setup_database() 