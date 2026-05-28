# -*- coding: utf-8 -*-
import sqlite3

def upgrade(conn: sqlite3.Connection) -> None:
    """
    Havuzlar tablosunu oluşturur ve mevcut sistemdeki havuz verilerini yönetmek için altyapı sağlar.
    Havuzlar: havuz_kodu (PK), bolum_id, havuz_tipi, zorunlu_secim_sayisi, ust_havuz_kodu, donem_kisiti, aciklama
    """
    cursor = conn.cursor()
    
    # Create Havuzlar table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Havuzlar (
            havuz_kodu TEXT,
            bolum_id INTEGER,
            havuz_adi TEXT,
            havuz_tipi TEXT DEFAULT 'GENEL',
            zorunlu_secim_sayisi INTEGER DEFAULT 0,
            ust_havuz_kodu TEXT,
            donem_kisiti TEXT,
            aciklama TEXT,
            PRIMARY KEY (havuz_kodu, bolum_id),
            FOREIGN KEY (bolum_id) REFERENCES Bolumler(bolum_id) ON DELETE SET NULL
        )
    ''')
    
    conn.commit()

def downgrade(conn: sqlite3.Connection) -> None:
    """
    Havuzlar tablosunu siler.
    """
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS Havuzlar')
    conn.commit()
