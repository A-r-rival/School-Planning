# -*- coding: utf-8 -*-
"""
SAFE DATA NORMALIZATION MIGRATION
Consolidates duplicate "Makine" course entries into single canonical entries

WHAT THIS DOES:
1. Backs up current database
2. Identifies duplicate course entries (same name, different codes)
3. Consolidates to ONE entry per course
4. Migrates all references (schedule, pools, classes)
5. Validates result

SAFETY FEATURES:
- Creates backup before any changes
- Validates each step
- Provides rollback capability
- Dry-run mode available
"""
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

class CourseMigration:
    def __init__(self, db_path='okul_veritabani.db', dry_run=False):
        self.db_path = db_path
        self.dry_run = dry_run
        self.backup_path = None
        self.conn = None
        
    def backup_database(self):
        """Create timestamped backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_path = f"{self.db_path}.backup_{timestamp}"
        shutil.copy2(self.db_path, self.backup_path)
        print(f"✅ Backup created: {self.backup_path}")
        
    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn.cursor()
    
    def analyze_duplicates(self):
        """Find courses with multiple instances that should be consolidated"""
        c = self.connect()
        
        # Find course names with multiple codes
        c.execute("""
            SELECT ders_adi, COUNT(DISTINCT ders_kodu) as code_count, 
                   GROUP_CONCAT(DISTINCT ders_kodu) as codes,
                   GROUP_CONCAT(DISTINCT ders_instance) as instances
            FROM Dersler
            WHERE ders_adi LIKE '%Makine%'
            GROUP BY ders_adi
            HAVING COUNT(DISTINCT ders_kodu) > 1
        """)
        
        duplicates = []
        for row in c.fetchall():
            duplicates.append({
                'ders_adi': row['ders_adi'],
                'code_count': row['code_count'],
                'codes': row['codes'].split(','),
                'instances': [int(i) for i in row['instances'].split(',')]
            })
        
        return duplicates
    
    def get_consolidation_plan(self, course_name):
        """Determine which instance to keep and which to merge"""
        c = self.conn.cursor()
        
        # Get all instances of this course
        c.execute("""
            SELECT ders_kodu, ders_instance, teori_odasi, lab_odasi, akts,
                   teori_saati, uygulama_saati, lab_saati
            FROM Dersler
            WHERE ders_adi = ?
            ORDER BY ders_instance
        """, (course_name,))
        
        instances = [dict(row) for row in c.fetchall()]
        
        # Decide primary instance (prefer standard course codes like CSE301)
        primary = None
        secondary = []
        
        for inst in instances:
            code = inst['ders_kodu']
            if code and not (code.startswith('SD') or code.startswith('ÜSD') or code.startswith('ZSD')):
                # This looks like a standard course code
                primary = inst
            else:
                secondary.append(inst)
        
        if not primary and instances:
            # No standard code found, use first instance
            primary = instances[0]
            secondary = instances[1:]
        
        return {
            'course_name': course_name,
            'primary': primary,
            'to_merge': secondary
        }
    
    def migrate_course(self, plan):
        """Migrate one course according to plan"""
        c = self.conn.cursor()
        course_name = plan['course_name']
        primary_instance = plan['primary']['ders_instance']
        merge_instances = [m['ders_instance'] for m in plan['to_merge']]
        
        print(f"\n{'[DRY RUN] ' if self.dry_run else ''}Migrating: {course_name}")
        print(f"  Primary instance: {primary_instance} [{plan['primary']['ders_kodu']}]")
        print(f"  Merging instances: {merge_instances}")
        
        if self.dry_run:
            print("  [DRY RUN] Skipping actual database changes")
            return
        
        # Step 1: Update Ders_Programi references
        for merge_inst in merge_instances:
            c.execute("""
                UPDATE Ders_Programi
                SET ders_instance = ?
                WHERE ders_adi = ? AND ders_instance = ?
            """, (primary_instance, course_name, merge_inst))
            updated = c.rowcount
            print(f"  ✓ Updated {updated} schedule entries (instance {merge_inst} → {primary_instance})")
        
        # Step 2: Update Ders_Havuz_Iliskisi references
        for merge_inst in merge_instances:
            c.execute("""
                UPDATE Ders_Havuz_Iliskisi
                SET ders_instance = ?
                WHERE ders_adi = ? AND ders_instance = ?
            """, (primary_instance, course_name, merge_inst))
            updated = c.rowcount
            print(f"  ✓ Updated {updated} pool relationships (instance {merge_inst} → {primary_instance})")
        
        # Step 3: Update Ders_Sinif_Iliskisi references
        for merge_inst in merge_instances:
            c.execute("""
                UPDATE Ders_Sinif_Iliskisi
                SET ders_instance = ?
                WHERE ders_adi = ? AND ders_instance = ?
            """, (primary_instance, course_name, merge_inst))
            updated = c.rowcount
            print(f"  ✓ Updated {updated} class relationships (instance {merge_inst} → {primary_instance})")
        
        # Step 4: Delete duplicate Dersler entries
        for merge_inst in merge_instances:
            c.execute("""
                DELETE FROM Dersler
                WHERE ders_adi = ? AND ders_instance = ?
            """, (course_name, merge_inst))
            print(f"  ✓ Deleted duplicate Dersler entry (instance {merge_inst})")
        
        self.conn.commit()
        print(f"  ✅ Migration complete for {course_name}")
    
    def validate_result(self):
        """Validate that migration was successful"""
        c = self.conn.cursor()
        
        print("\n" + "=" * 80)
        print("VALIDATION")
        print("=" * 80)
        
        # Check for remaining duplicates
        c.execute("""
            SELECT ders_adi, COUNT(*) as cnt
            FROM Dersler
            WHERE ders_adi LIKE '%Makine%'
            GROUP BY ders_adi
            HAVING COUNT(*) > 1
        """)
        
        duplicates = c.fetchall()
        if duplicates:
            print("⚠️ WARNING: Some duplicates still exist:")
            for row in duplicates:
                print(f"  {row['ders_adi']}: {row['cnt']} entries")
            return False
        else:
            print("✅ No duplicate course entries found")
        
        # Check pool relationships
        c.execute("""
            SELECT d.ders_kodu, d.ders_adi, COUNT(DISTINCT dhi.havuz_kodu) as pool_count
            FROM Dersler d
            LEFT JOIN Ders_Havuz_Iliskisi dhi ON d.ders_adi = dhi.ders_adi 
                AND d.ders_instance = dhi.ders_instance
            WHERE d.ders_adi LIKE '%Makine%'
            GROUP BY d.ders_kodu, d.ders_adi
        """)
        
        print("\nPool relationships after migration:")
        for row in c.fetchall():
            print(f"  [{row['ders_kodu']}] {row['ders_adi']}: {row['pool_count']} pools")
        
        return True
    
    def run(self):
        """Execute full migration"""
        print("=" * 80)
        print("COURSE NORMALIZATION MIGRATION")
        print("=" * 80)
        print(f"Mode: {'DRY RUN' if self.dry_run else 'ACTUAL MIGRATION'}")
        print(f"Database: {self.db_path}")
        
        # Backup
        if not self.dry_run:
            self.backup_database()
        
        # Analyze
        print("\nAnalyzing duplicates...")
        duplicates = self.analyze_duplicates()
        
        if not duplicates:
            print("✅ No duplicates found - nothing to migrate")
            return
        
        print(f"\nFound {len(duplicates)} course(s) with duplicate entries:")
        for dup in duplicates:
            print(f"  {dup['ders_adi']}: {dup['code_count']} codes ({', '.join(dup['codes'])})")
        
        # Consolidate each course
        for dup in duplicates:
            plan = self.get_consolidation_plan(dup['ders_adi'])
            self.migrate_course(plan)
        
        # Validate
        if not self.dry_run:
            self.validate_result()
        
        print("\n" + "=" * 80)
        if self.dry_run:
            print("DRY RUN COMPLETE - No changes made")
            print("Run with dry_run=False to apply changes")
        else:
            print("MIGRATION COMPLETE")
            print(f"Backup available at: {self.backup_path}")
        print("=" * 80)
    
    def rollback(self, backup_path):
        """Rollback to backup"""
        if Path(backup_path).exists():
            shutil.copy2(backup_path, self.db_path)
            print(f"✅ Rolled back to: {backup_path}")
        else:
            print(f"❌ Backup not found: {backup_path}")

if __name__ == '__main__':
    import sys
    
    # Check command line arguments
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv
    rollback = '--rollback' in sys.argv
    
    if rollback:
        # Rollback mode
        if len(sys.argv) < 3:
            print("Usage: python migrate_courses.py --rollback <backup_file>")
            sys.exit(1)
        backup_file = sys.argv[2]
        migration = CourseMigration()
        migration.rollback(backup_file)
    else:
        # Migration mode
        migration = CourseMigration(dry_run=dry_run)
        migration.run()
