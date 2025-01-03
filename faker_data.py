import sqlite3

# Database connection
conn = sqlite3.connect('company_data.db')
cur = conn.cursor()

# --- Helper Function ---

def get_table_names():
    """Gets a list of all table names in the database."""
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return [table[0] for table in cur.fetchall()]

def clear_table_data(table_name):
    """Clears all existing data from a table."""
    print(f"Clearing data from table '{table_name}'...")
    cur.execute(f"DELETE FROM {table_name}")
    conn.commit()
    print(f"Data cleared from table '{table_name}'.")

# --- Main Execution ---

if __name__ == "__main__":
    table_names = get_table_names()

    # Clear data from tables in reversed order to handle foreign key constraints
    for table_name in reversed(table_names):
        clear_table_data(table_name)

    conn.close()
    print("Data deletion process finished! All tables are now empty but retain their schema.")