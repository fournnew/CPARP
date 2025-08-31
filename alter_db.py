import sqlite3

# connect
conn = sqlite3.connect("instance/c_refill.db")
cursor = conn.cursor()

# add new column on the db  
try:
    cursor.execute("ALTER TABLE refill ADD COLUMN file_path VARCHAR(255);")
    print("✅ Column 'file_path' added successfully!")
except sqlite3.OperationalError as e:
    print(f"⚠️ Skipping: {e}")

conn.commit()
conn.close()
