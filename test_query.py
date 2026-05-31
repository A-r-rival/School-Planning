import sqlite3
import re
conn = sqlite3.connect('d:/Git_Projects/School-Planning/database/okul_veritabani.db')
c = conn.cursor()
c.execute("SELECT department_id FROM Bolumler WHERE name LIKE '%Enerji Bilimi%'")
dept_id = c.fetchone()[0]
c.execute('''
    SELECT DISTINCT d.ad, d.ders_kodu 
    from Program_Grup pg
    JOIN Program_Grup_Dersleri pgd ON pg.grup_id = pgd.grup_id
    JOIN Program_Ders pd ON pgd.program_ders_id = pd.id
    JOIN Ders d ON pd.ders_id = d.ders_id
    WHERE pg.department_id = ? AND pg.sinif_yili = 3
''', (dept_id,))
print('Courses in DB for EBT Year 3:')
for r in c.fetchall():
    print(f"{r[1]}: {r[0]}")
