import sqlite3
import os

db_path = os.path.join('database', 'okul_veritabani.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS Program_Versiyonlari (
    versiyon_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad TEXT NOT NULL,
    aciklama TEXT,
    tarih DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 0
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS Ortak_Grup_Sablonlari (
    sablon_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad TEXT NOT NULL UNIQUE,
    aciklama TEXT,
    tarih DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS Ortak_Grup_Sablon_Detay (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sablon_id INTEGER NOT NULL,
    ders_adi TEXT NOT NULL,
    ders_instance INTEGER NOT NULL,
    grup_id INTEGER NOT NULL,
    FOREIGN KEY(sablon_id) REFERENCES Ortak_Grup_Sablonlari(sablon_id) ON DELETE CASCADE
)
''')

try:
    c.execute('ALTER TABLE Ders_Programi ADD COLUMN versiyon_id INTEGER REFERENCES Program_Versiyonlari(versiyon_id) ON DELETE CASCADE')
    print('Added versiyon_id to Ders_Programi')
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e).lower():
        print('Column versiyon_id already exists in Ders_Programi.')
    else:
        print(f'Error altering Ders_Programi: {e}')

c.execute('SELECT COUNT(*) FROM Ders_Programi WHERE versiyon_id IS NULL')
count = c.fetchone()[0]
if count > 0:
    c.execute("INSERT INTO Program_Versiyonlari (ad, aciklama, is_active) VALUES ('Eski Program', 'Versiyonlama oncesi', 1)")
    default_version_id = c.lastrowid
    c.execute('UPDATE Ders_Programi SET versiyon_id = ? WHERE versiyon_id IS NULL', (default_version_id,))
    print(f'Migrated {count} rows in Ders_Programi to default versiyon_id {default_version_id}.')

conn.commit()
conn.close()
print('Migration completed successfully.')
