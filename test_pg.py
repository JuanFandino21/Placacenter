from psycopg import connect
from psycopg.rows import tuple_row

url = "postgresql://postgres:ZXTjHSGoFSarPONgruaiKATVEHGJFyve@shuttle.proxy.rlwy.net:51524/railway?sslmode=require"

try:
    with connect(url, row_factory=tuple_row) as cn:
        with cn.cursor() as cur:
            cur.execute("SELECT version();")
            print("OK ->", cur.fetchone()[0])
except Exception as e:
    print("FALLO ->", e)
