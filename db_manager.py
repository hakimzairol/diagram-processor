# db_manager.py

import psycopg2
import psycopg2.extras
import config

def sanitize_name(name_str: str) -> str:
    """Sanitizes a string to be a valid PostgreSQL schema or table name component."""
    s = name_str.lower().replace(" ", "_").replace("-", "_")
    return "".join(c for c in s if c.isalnum() or c == '_')

# ==============================================================================
#                      FUNCTIONS FOR MIND MAP PROCESSOR
# ==============================================================================

def setup_mindmap_schema(session_schema_name: str) -> bool:
    """Sets up a new schema and the required tables for the Mind Map tool."""
    sanitized_name = sanitize_name(session_schema_name)
    if not sanitized_name:
        return False
    
    conn = None
    try:
        conn = psycopg2.connect(**config.DB_PARAMS)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {sanitized_name};")
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {sanitized_name}.diagram_data (
                id SERIAL PRIMARY KEY,
                group_no INTEGER,
                description TEXT,
                category_name VARCHAR(255),
                activity_name VARCHAR(255)
            );"""
            cur.execute(create_table_sql)
        print(f"✅ Mind Map schema '{sanitized_name}' and table are ready.")
        return True
    except Exception as e:
        print(f"❌ Error setting up Mind Map schema '{sanitized_name}': {e}")
        return False
    finally:
        if conn: conn.close()

def insert_mindmap_data(data_list: list[dict], session_schema_name: str, activity_name: str) -> int:
    """Inserts Mind Map data into the diagram_data table."""
    sanitized_name = sanitize_name(session_schema_name)
    if not data_list: return 0
    
    conn = None
    sql = f"""
        INSERT INTO {sanitized_name}.diagram_data (group_no, description, category_name, activity_name)
        VALUES (%s, %s, %s, %s);
    """
    try:
        conn = psycopg2.connect(**config.DB_PARAMS)
        with conn.cursor() as cur:
            for row in data_list:
                cur.execute(sql, (row['group_no'], row['description'], row['category_name'], activity_name))
        conn.commit()
        return len(data_list)
    except Exception as e:
        print(f"❌ Error inserting Mind Map data into '{sanitized_name}': {e}")
        if conn: conn.rollback()
        return 0
    finally:
        if conn: conn.close()

def get_all_mindmap_sessions() -> list[str]:
    """Gets all schemas that contain a 'diagram_data' table."""
    conn = None
    try:
        conn = psycopg2.connect(**config.DB_PARAMS)
        with conn.cursor() as cur:
            cur.execute("SELECT table_schema FROM information_schema.tables WHERE table_name = 'diagram_data'")
            return [row[0] for row in cur.fetchall()]
    except Exception as e:
        print(f"❌ Error fetching Mind Map sessions: {e}")
        return []
    finally:
        if conn: conn.close()

# (Other Mind Map helper functions like get_data_from_schema, delete_session_schema, etc. would go here if needed)

# ==============================================================================
#                      FUNCTIONS FOR FISHBONE PROCESSOR
# ==============================================================================

def create_fishbone_table_if_not_exists():
    """Creates the global fishbone_data table if it doesn't already exist."""
    conn = None
    create_table_command = """
    CREATE TABLE IF NOT EXISTS fishbone_data (
        id SERIAL PRIMARY KEY,
        session_name VARCHAR(255) NOT NULL,
        problem_statement TEXT,
        group_name TEXT,
        main_cause TEXT,
        sub_cause TEXT,
        detail TEXT NOT NULL
    );
    """
    try:
        conn = psycopg2.connect(**config.DB_PARAMS)
        with conn.cursor() as cur:
            cur.execute(create_table_command)
        conn.commit()
        print("✅ 'fishbone_data' table checked/created successfully.")
    except Exception as e:
        print(f"❌ Error while creating 'fishbone_data' table: {e}")
    finally:
        if conn: conn.close()

def insert_fishbone_data(session_name, problem_statement, group_name, verified_data):
    """Inserts verified fishbone data into the database."""
    conn = None
    sql = """
        INSERT INTO fishbone_data (session_name, problem_statement, group_name, main_cause, sub_cause, detail)
        VALUES (%s, %s, %s, %s, %s, %s);
    """
    try:
        conn = psycopg2.connect(**config.DB_PARAMS)
        with conn.cursor() as cur:
            for item in verified_data:
                cur.execute(sql, (
                    session_name, problem_statement, group_name,
                    item.get('main_cause'), item.get('sub_cause'), item.get('detail')
                ))
        conn.commit()
        return len(verified_data)
    except Exception as e:
        print(f"❌ Error inserting fishbone data: {e}")
        if conn: conn.rollback()
        return 0
    finally:
        if conn: conn.close()

def get_all_fishbone_sessions():
    """Retrieves a list of all unique session_name values from the fishbone_data table."""
    conn = None
    try:
        conn = psycopg2.connect(**config.DB_PARAMS)
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT session_name FROM fishbone_data ORDER BY session_name;")
            return [row[0] for row in cur.fetchall()]
    except Exception as e:
        print(f"❌ Error fetching fishbone sessions: {e}")
        return []
    finally:
        if conn: conn.close()