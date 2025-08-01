# db_manager.py
import psycopg2
import psycopg2.extras
import config

def sanitize_name(name_str: str) -> str:
    s = name_str.lower().replace(" ", "_").replace("-", "_")
    return "".join(c for c in s if c.isalnum() or c == '_')

# ==============================================================================
#                      MIND MAP PROCESSOR FUNCTIONS
# ==============================================================================

def setup_mindmap_schema(session_schema_name: str) -> bool:
    sanitized_name = sanitize_name(session_schema_name)
    if not sanitized_name: return False
    conn = None
    try:
        conn = psycopg2.connect(**config.DB_PARAMS)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {sanitized_name};")
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {sanitized_name}.diagram_data (
                id SERIAL PRIMARY KEY, group_no INTEGER, description TEXT,
                category_name VARCHAR(255), activity_name VARCHAR(255)
            );"""
            cur.execute(create_table_sql)
        print(f"✅ Mind Map schema '{sanitized_name}' ready.")
        return True
    except Exception as e:
        print(f"❌ Error setting up Mind Map schema '{sanitized_name}': {e}")
        return False
    finally:
        if conn: conn.close()

def insert_mindmap_data(data_list: list[dict], session_schema_name: str, activity_name: str) -> int:
    sanitized_name = sanitize_name(session_schema_name)
    if not data_list: return 0
    conn = None
    sql = f"INSERT INTO {sanitized_name}.diagram_data (group_no, description, category_name, activity_name) VALUES (%s, %s, %s, %s);"
    try:
        conn = psycopg2.connect(**config.DB_PARAMS)
        with conn.cursor() as cur:
            for row in data_list:
                cur.execute(sql, (row['group_no'], row['description'], row['category_name'], activity_name))
        conn.commit(); return len(data_list)
    except Exception as e:
        print(f"❌ Error inserting Mind Map data into '{sanitized_name}': {e}")
        if conn: conn.rollback()
        return 0
    finally:
        if conn: conn.close()

def get_all_mindmap_sessions() -> list[str]:
    conn = None
    try:
        conn = psycopg2.connect(**config.DB_PARAMS)
        with conn.cursor() as cur:
            cur.execute("SELECT table_schema FROM information_schema.tables WHERE table_name = 'diagram_data' ORDER BY table_schema")
            return [row[0] for row in cur.fetchall()]
    except Exception as e:
        print(f"❌ Error fetching Mind Map sessions: {e}")
        return []
    finally:
        if conn: conn.close()

def get_mindmap_data_from_schema(session_schema_name: str) -> list[dict]:
    conn = None; data = []
    try:
        conn = psycopg2.connect(**config.DB_PARAMS)
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(f"SELECT * FROM {sanitize_name(session_schema_name)}.diagram_data ORDER BY id;")
            data = [dict(row) for row in cur.fetchall()]
    except Exception as e:
        print(f"❌ Error fetching Mind Map data from schema '{session_schema_name}': {e}")
    finally:
        if conn: conn.close()
    return data

def delete_mindmap_session_schema(session_schema_name: str) -> bool:
    sanitized_name = sanitize_name(session_schema_name)
    if not sanitized_name: return False
    conn = None
    try:
        conn = psycopg2.connect(**config.DB_PARAMS)
        with conn.cursor() as cur:
            cur.execute(f"DROP SCHEMA {sanitized_name} CASCADE;")
        conn.commit(); print(f"✅ Schema '{sanitized_name}' deleted successfully.")
        return True
    except Exception as e:
        print(f"❌ Error deleting schema '{sanitized_name}': {e}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()

# ==============================================================================
#                      FISHBONE PROCESSOR FUNCTIONS
# ==============================================================================

def create_fishbone_table_if_not_exists():
    conn = None
    create_table_command = """
    CREATE TABLE IF NOT EXISTS fishbone_data (
        id SERIAL PRIMARY KEY, session_name VARCHAR(255) NOT NULL,
        problem_statement TEXT, group_name TEXT, main_cause TEXT,
        sub_cause TEXT, detail TEXT NOT NULL
    );"""
    try:
        conn = psycopg2.connect(**config.DB_PARAMS)
        with conn.cursor() as cur:
            cur.execute(create_table_command)
        conn.commit(); print("✅ 'fishbone_data' table checked/created successfully.")
    except Exception as e:
        print(f"❌ Error while creating 'fishbone_data' table: {e}")
    finally:
        if conn: conn.close()

def insert_fishbone_data(session_name, problem_statement, group_name, verified_data):
    conn = None
    sql = "INSERT INTO fishbone_data (session_name, problem_statement, group_name, main_cause, sub_cause, detail) VALUES (%s, %s, %s, %s, %s, %s);"
    try:
        conn = psycopg2.connect(**config.DB_PARAMS)
        with conn.cursor() as cur:
            for item in verified_data:
                cur.execute(sql, (session_name, problem_statement, group_name, item.get('main_cause'), item.get('sub_cause'), item.get('detail')))
        conn.commit()
        return len(verified_data)
    except Exception as e:
        print(f"❌ Error inserting fishbone data: {e}")
        if conn: conn.rollback()
        return 0
    finally:
        if conn: conn.close()

def get_all_fishbone_sessions():
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