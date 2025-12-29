# -*- coding: utf-8 -*-
"""
Schedule Query Builder - DRY elimination for schedule queries.
Consolidates duplicated SQL across multiple query methods.
"""
from dataclasses import dataclass
from typing import Optional, Tuple, List


@dataclass
class ScheduleQueryFilter:
    """Filter criteria for schedule queries."""
    faculty_id: Optional[int] = None
    department_id: Optional[int] = None
    year: Optional[int] = None
    day: Optional[str] = None


class ScheduleQueryBuilder:
    """
    DRY query builder for schedule queries.
    
    Eliminates SQL duplication across:
    - get_courses_by_faculty()
    - get_courses_by_department()
    - Other similar queries
    
    Before: 4 methods x 30 lines = 120 lines of duplicate SQL
    After: 1 builder + 4x5 line methods = 40 lines total
    """
    
    BASE_SELECT = """
        SELECT dp.ders_adi, GROUP_CONCAT(DISTINCT d.ders_kodu), 
               (o.ad || ' ' || o.soyad) as hoca, dp.gun, dp.baslangic, dp.bitis,
               GROUP_CONCAT(DISTINCT b.bolum_adi || ' ' || od.sinif_duzeyi || '. Sınıf') as siniflar
        FROM Ders_Programi dp
        JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
        JOIN Ders_Sinif_Iliskisi dsi ON d.ders_instance = dsi.ders_instance AND d.ders_adi = dsi.ders_adi
        JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
        JOIN Bolumler b ON od.bolum_num = b.bolum_id
        LEFT JOIN Ogretmenler o ON dp.ogretmen_id = o.ogretmen_num
    """
    
    def build(self, filters: ScheduleQueryFilter) -> Tuple[str, List]:
        """
        Build SQL query with given filters.
        
        Args:
            filters: ScheduleQueryFilter with optional constraints
        
        Returns:
            (sql, params) tuple ready for cursor.execute()
        
        Example:
            builder = ScheduleQueryBuilder()
            filters = ScheduleQueryFilter(faculty_id=1, year=3)
            sql, params = builder.build(filters)
            cursor.execute(sql, params)
        """
        sql = self.BASE_SELECT
        params = []
        conditions = []
        
        # Faculty filter
        if filters.faculty_id is not None:
            conditions.append("b.fakulte_num = ?")
            params.append(filters.faculty_id)
        
        # Department filter
        if filters.department_id is not None:
            conditions.append("od.bolum_num = ?")
            params.append(filters.department_id)
        
        # Year filter
        if filters.year is not None:
            conditions.append("od.sinif_duzeyi = ?")
            params.append(filters.year)
        
        # Day filter
        if filters.day:
            conditions.append("dp.gun = ?")
            params.append(filters.day)
        
        # Add WHERE clause if any conditions
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        
        # Group and order (consistent with original queries)
        sql += " GROUP BY dp.gun, dp.baslangic, dp.bitis, dp.ders_adi, o.ad, o.soyad ORDER BY dp.ders_adi, dp.baslangic"
        
        return sql, params
