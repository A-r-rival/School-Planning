import sqlite3
conn = sqlite3.connect('okul_veritabani.db')
print("Bolumler Sample Data:")
for row in conn.execute("SELECT * FROM Bolumler"):
    print(f"  {row}")

print("\nDers_Havuz_Iliskisi Sample Data:")
for row in conn.execute("SELECT * FROM Ders_Havuz_Iliskisi LIMIT 20"):
    print(f"  {row}")
conn.close()
