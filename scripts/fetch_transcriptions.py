import psycopg2    #for PostgreSQL connections

# Connect to your PostgreSQL database
conn = psycopg2.connect(
    host="localhost",
    database="podcast_etl",
    user="postgres",
    password="160803"
)
cur = conn.cursor()

# Fetch all rows from transcriptions table
cur.execute("SELECT * FROM transcriptions")
rows = cur.fetchall()      #fetch all rows

# Print each row
for row in rows:
    print(row)

cur.close()     #close the cursor
conn.close()    #close the db connection