from database import get_connection

try:
    conn = get_connection()
    print("Conexión exitosa")
    conn.close()
except Exception as e:
    print("Error de conexión")
    print(e)
