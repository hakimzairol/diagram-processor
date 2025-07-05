import psycopg2
import psycopg2.extras
import config

def sanitize_name(name_str: str) -> str:
    """Sanitizes a string to be a valid PostgreSQL schema or table name component."""
    s = name_str.lower().replace(" ", "_").replace("-", "_")
    return "".join(c for c in s if c.isalnum() or c == '_')

def setup_session_schema_and_table(session_schema_name: str) -> bool:
    """Ensures a schema exists and creates the fishbone_diagram table within it."""
    conn = None
    try:
        conn = psycopg2.connect(**config.DB_PARAMS)
        with conn.cursor() as cur:
            print(f"Ensuring schema '{session_schema_name}' exists...")
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {session_schema_name};")
            
            print(f"Ensuring fishbone_diagram table exists in schema '{session_schema_name}'...")
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {session_schema_name}.fishbone_diagram (
                    diagram_id SERIAL PRIMARY KEY,
                    group_no INTEGER NOT NULL,
                    category_name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    activity VARCHAR(50) NOT NULL
                );
            """)
        conn.commit()
        print(f"✅ Schema '{session_schema_name}' and fishbone_diagram table are ready.")
        return True
    except (Exception, psycopg2.Error) as error:
        print(f"❌ Error setting up schema or table for '{session_schema_name}': {error}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()

def fetch_distinct_category_names(session_schema_name: str) -> list[str]:
    """Fetches distinct category names used so far in the session schema."""
    conn = None
    try:
        conn = psycopg2.connect(**config.DB_PARAMS)
        with conn.cursor() as cur:
            cur.execute(f"SELECT DISTINCT category_name FROM {session_schema_name}.fishbone_diagram ORDER BY category_name;")
            return [row[0] for row in cur.fetchall()]
    except psycopg2.errors.UndefinedTable:
        # This is expected on the first run for a new schema.
        return []
    except (Exception, psycopg2.Error) as error:
        print(f"❌ Error fetching distinct category names from schema '{session_schema_name}': {error}")
        return []
    finally:
        if conn: conn.close()

def insert_diagram_data(data_list: list[dict], session_schema_name: str, activity_name: str) -> int:
    """Inserts extracted data into the fishbone_diagram table."""
    if not data_list:
        print("ℹ️ No data to insert.")
        return 0
    
    conn = None
    inserted_count = 0
    try:
        conn = psycopg2.connect(**config.DB_PARAMS)
        with conn.cursor() as cur:
            for row in data_list:
                cur.execute(
                    f"INSERT INTO {session_schema_name}.fishbone_diagram (group_no, category_name, description, activity) VALUES (%s, %s, %s, %s)",
                    (row['group_no'], row['category_name'], row['description'], activity_name)
                )
                inserted_count += 1
        conn.commit()
        print(f"✅ Inserted {inserted_count} records into '{session_schema_name}.fishbone_diagram'.")
    except (Exception, psycopg2.Error) as error:
        print(f"❌ Error inserting data into schema '{session_schema_name}': {error}")
        if conn: conn.rollback()
        return 0
    finally:
        if conn: conn.close()
    return inserted_count

def create_category_views(session_schema_name: str):
    """Creates or replaces views for each distinct category_name within the session schema."""
    conn = None
    try:
        conn = psycopg2.connect(**config.DB_PARAMS)
        with conn.cursor() as cur:
            cur.execute(f"SELECT DISTINCT category_name FROM {session_schema_name}.fishbone_diagram;")
            distinct_category_names = [row[0] for row in cur.fetchall()]

            if not distinct_category_names:
                print(f"ℹ️ No categories found in '{session_schema_name}.fishbone_diagram' to create views for.")
                return

            print(f"\nCreating/Updating views in schema '{session_schema_name}'...")
            for cat_name_original in distinct_category_names:
                view_name = f"view_cat_{sanitize_name(cat_name_original)}"
                view_sql = f"""
                CREATE OR REPLACE VIEW {session_schema_name}.{view_name} AS
                SELECT diagram_id, group_no, category_name, description, activity
                FROM {session_schema_name}.fishbone_diagram
                WHERE category_name = %s;
                """
                cur.execute(view_sql, (cat_name_original,))
                print(f"  -> View '{session_schema_name}.{view_name}' created/updated for category '{cat_name_original}'.")
            conn.commit()
            print(f"✅ Views created successfully.")

    except (Exception, psycopg2.Error) as error:
        print(f"❌ Error creating views in schema '{session_schema_name}': {error}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()
        
def get_all_session_schemas() -> list[str]:
    conn = None
    schemas = []
    try:
        conn = psycopg2.connect(**config.DB_PARAMS)
        with conn.cursor() as cur:
            # This query specifically looks for schemas containing our target table
            cur.execute("""
                SELECT table_schema
                FROM information_schema.tables
                WHERE table_name = 'fishbone_diagram'
            """)
            schemas = [row[0] for row in cur.fetchall()]
    except (Exception, psycopg2.Error) as error:
        print(f"❌ Error fetching session schemas: {error}")
    finally:
        if conn: conn.close()
    return schemas  


def get_data_from_schema(session_schema_name: str) -> list[dict]:
    """Fetches all data from the fishbone_diagram table within a specific schema."""
    conn = None
    data = []
    try:
        conn = psycopg2.connect(**config.DB_PARAMS)
        # Use a dictionary cursor to get results as dicts
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(f"SELECT * FROM {session_schema_name}.fishbone_diagram ORDER BY diagram_id;")
            # Convert Row objects to standard dicts
            data = [dict(row) for row in cur.fetchall()]
    except (Exception, psycopg2.Error) as error:
        print(f"❌ Error fetching data from schema '{session_schema_name}': {error}")
    finally:
        if conn: conn.close()
    return data


def get_all_data_from_all_schemas() -> list[dict]:
    """Fetches all data from all session schemas and adds a 'session' column."""
    all_data = []
    session_schemas = get_all_session_schemas()
    for schema in session_schemas:
        schema_data = get_data_from_schema(schema)
        for row in schema_data:
            row['session'] = schema # Add the session name to each row
            all_data.append(row)
    return all_data












