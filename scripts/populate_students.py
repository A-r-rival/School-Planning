import sys
import os
import random
import sqlite3

# Add project root to path
sys.path.append(os.getcwd())

from models.schedule_model import ScheduleModel

GRADES = ["AA", "BA", "BB", "CB", "CC", "DC", "DD", "FD", "FF"]

# ==========================================
# DEPARTMENT DATA (Curriculum + Pools)
# Format: (Code, Name, ECTS)
# ==========================================

DEPARTMENTS_DATA = {
    "Bilgisayar Mühendisliği": {
        "curriculum": {
            1: [("MAT103", "Analiz I", 6), ("INF101", "Bilgisayar Bilimine ve Programlamaya Giriş", 6), ("INF103", "Mantık", 6), ("INF107", "Bilgisayar Organizasyonu", 6), ("DEU121", "Teknik Almanca I", 2), ("ENG101", "İngilizce I", 2), ("TUR001", "Türkçe I", 2)],
            2: [("MAT106", "Lineer Cebir", 6), ("INF102", "Nesnel Programlama", 6), ("INF104", "Özdevinirler ve Biçimsel Diller", 6), ("INF110", "İşletim Sistemleri", 6), ("DEU122", "Teknik Almanca II", 2), ("ENG102", "İngilizce II", 2), ("TUR002", "Türkçe II", 2)],
            3: [("INF201", "Ayrık Yapılar", 6), ("INF203", "Algoritmalar ve Veri Yapıları I", 6), ("INF205", "Veritabanı Sistemleri", 6), ("INF209", "Bilgisayar Ağları", 6), ("INF211", "Bilgisayar ve Toplum Semineri", 2), ("ENG201", "İngilizce III", 2), ("AIT001", "Atatürk İlkeleri ve İnkılap Tarihi I", 2)],
            4: [("MAT204", "Veri Analizinin İstatistiksel Yöntemleri", 6), ("INF202", "Yazılım Mühendisliği", 6), ("INF204", "Algoritmalar ve Veri Yapıları II", 6), ("INF208", "Gömülü Sistemler", 6), ("INF210", "Bilgisayar Mühendisleri için Etik Semineri", 2), ("ENG202", "İngilizce IV", 2), ("AIT002", "Atatürk İlkeleri ve İnkılap Tarihi II", 2)],
            5: [("SDP", "Seçmeli Alan - Proje", 6), ("SDIa", "Seçmeli I - Uygulamalı Bilgisayar", 6), ("SDIb", "Seçmeli I - Bilgisayar Donanımı", 6), ("SDIc", "Seçmeli I - Kuramsal", 6), ("USD001", "Üniversite Seçmeli I", 2), ("ISG001", "İş Sağlığı ve Güvenliği I", 2), ("ENG301", "İleri İngilizce I", 2)],
            6: [("SDIIa_1", "Seçmeli II - Uygulamalı 1", 6), ("SDIIa_2", "Seçmeli II - Uygulamalı 2", 6), ("SDIIb", "Seçmeli II - Donanım", 6), ("SDIIc", "Seçmeli II - Kuramsal", 6), ("USD002", "Üniversite Seçmeli II", 2), ("ISG002", "İş Sağlığı ve Güvenliği II", 2), ("ENG302", "İleri İngilizce II", 2)],
            7: [("INF499", "Mesleki Alan Stajı", 6), ("INF401", "Bilimsel Çalışma Yöntemleri", 6), ("SDIII_1", "Seçmeli III - 1", 6), ("SDIII_2", "Seçmeli III - 2", 6), ("SDIII_3", "Seçmeli III - 3", 6)],
            8: [("INF492", "Bitirme Tezi", 12), ("SDIV_1", "Seçmeli IV - 1", 6), ("SDIV_2", "Seçmeli IV - 2", 6), ("SDIV_3", "Seçmeli IV - 3", 6)]
        },
        "pools": {
            "SDP": [("WIN311", "Proje I: Yenilik ve Teknoloji", 6), ("MEC319", "Mekatronik Projesi", 6), ("INF303", "Yazılım Mühendisliği Projesi", 6), ("ETE491", "EEE Projesi", 6)],
            "SDIa": [("INF501", "Akıllı Sistemler", 6), ("INF502", "Makine Öğrenmesi", 6), ("INF503", "Yapay Sinir Ağları", 6), ("INF504", "Doğal Dil İşleme", 6), ("INF505", "Veri Madenciliği", 6), ("INF522", "Web Mühendisliği", 6), ("INF523", "İnsan-Makine İletişimi", 6)],
            "SDIb": [("INF601", "Gerçek Zamanlı Sistemler", 6), ("INF602", "Derleyici Tasarımı", 6), ("ETE101", "Sayısal Tasarım", 6), ("ETE201", "Elektrik Devreleri I", 6), ("ETE442", "Gömülü Sistemler", 6)],
            "SDIc": [("INF701", "Yapay Zeka", 6), ("INF703", "Kriptoloji", 6), ("MAT302", "Numerik Matematik", 6), ("MAT305", "Matematiksel Modelleme", 6)],
            "SDIIa": [("INF501", "Akıllı Sistemler", 6), ("INF502", "Makine Öğrenmesi", 6), ("INF503", "Yapay Sinir Ağları", 6), ("INF504", "Doğal Dil İşleme", 6), ("INF505", "Veri Madenciliği", 6), ("INF522", "Web Mühendisliği", 6), ("INF523", "İnsan-Makine İletişimi", 6)],
            "SDIIb": [("INF601", "Gerçek Zamanlı Sistemler", 6), ("INF602", "Derleyici Tasarımı", 6), ("ETE101", "Sayısal Tasarım", 6), ("ETE201", "Elektrik Devreleri I", 6), ("ETE442", "Gömülü Sistemler", 6)],
            "SDIIc": [("INF701", "Yapay Zeka", 6), ("INF703", "Kriptoloji", 6), ("MAT302", "Numerik Matematik", 6), ("MAT305", "Matematiksel Modelleme", 6)],
            "SDIII": [("INF501", "Akıllı Sistemler", 6), ("INF502", "Makine Öğrenmesi", 6), ("INF503", "Yapay Sinir Ağları", 6), ("INF522", "Web Mühendisliği", 6), ("ETE442", "Gömülü Sistemler", 6), ("INF701", "Yapay Zeka", 6), ("BWL007", "Dijital Pazarlama", 6), ("ING406", "Mühendisler İçin Hukuk", 6)],
            "SDIV": [("INF501", "Akıllı Sistemler", 6), ("INF502", "Makine Öğrenmesi", 6), ("INF503", "Yapay Sinir Ağları", 6), ("INF522", "Web Mühendisliği", 6), ("ETE442", "Gömülü Sistemler", 6), ("INF701", "Yapay Zeka", 6), ("BWL007", "Dijital Pazarlama", 6), ("ING406", "Mühendisler İçin Hukuk", 6)],
            "USD": [("ELC101", "Fotoğrafçılık", 2), ("ELC102", "Sinema Tarihi", 2), ("ELC103", "İletişim Becerileri", 2)]
        }
    },
    "Elektrik-Elektronik Mühendisliği": {
        "curriculum": {
            1: [("MAT103", "Analiz I", 6), ("PHY101", "Mekaniğin Temelleri", 6), ("ETE101", "Sayısal Tasarım", 6), ("ETE103", "Bilg. Bil. ve Prog. Giriş", 6), ("ETE091", "EEE Giriş", 2), ("DEU121", "Teknik Almanca I", 2), ("ENG101", "İngilizce I", 2)],
            2: [("MAT108", "Analiz II", 6), ("PHY102", "Elektrik ve Manyetizma", 6), ("MAT106", "Lineer Cebir", 6), ("SDII", "Seçmeli Ders Alanı II", 6), ("ETE092", "Bilimsel Çalışma Yöntemleri", 2), ("DEU122", "Teknik Almanca II", 2), ("ENG102", "İngilizce II", 2)],
            3: [("MAT201", "Diferansiyel Denklemler", 6), ("ETE201", "Elektrik Devreleri I", 6), ("PHY103", "Modern Fizik", 6), ("ETE207", "Malzeme Teknolojisi", 6), ("ETE299", "Temel Staj", 2), ("TUR001", "Türkçe I", 2), ("ENG201", "İngilizce III", 2)],
            4: [("MAT204", "Veri Analizinin İstat. Yönt.", 6), ("ETE202", "Elektrik Devreleri II", 6), ("ETE208", "Ölçüm Teknikleri", 6), ("ETE292", "Proje Yönetimi", 2), ("TUR002", "Türkçe II", 2), ("ENG202", "İngilizce IV", 2), ("USD000", "Üniversite Seçmeli", 6)],
            5: [("ETE321", "Elektromanyetik Alanlar", 6), ("ETE303", "Sinyaller ve Sistemler", 6), ("ETE311", "Elektronik I", 6), ("ETE331", "Elektrik Makineleri I", 6), ("SDV", "Seçmeli Ders Alanı V", 6)],
            6: [("ETE304", "Kontrol Müh. Temelleri", 6), ("ETE372", "Telekomünikasyon", 6), ("SDT", "Seçmeli Ders Alanı T", 6), ("SDM", "Seçmeli Ders Alanı M", 6), ("SDVI", "Seçmeli Ders Alanı VI", 6)],
            7: [("ETE499", "Mesleki Alan Stajı", 6), ("ISG001", "İş Sağlığı ve Güvenliği I", 2), ("AIT001", "Atatürk İlkeleri I", 2), ("ENG301", "İleri İngilizce I", 2), ("SDP", "Seçmeli Alan - Proje", 6), ("SDVII_1", "Seçmeli VII - 1", 6), ("SDVII_2", "Seçmeli VII - 2", 6)],
            8: [("ETE492", "Lisans Bitirme Çalışması", 12), ("ISG002", "İş Sağlığı ve Güvenliği II", 2), ("AIT002", "Atatürk İlkeleri II", 2), ("ENG302", "İleri İngilizce II", 2), ("SDVIII_1", "Seçmeli VIII - 1", 6), ("SDVIII_2", "Seçmeli VIII - 2", 6)]
        },
        "pools": {
            "SDII": [("ETE104", "Mikroişlemciler", 6), ("INF102", "Nesnel Programlama", 6)],
            "SDM": [("MAT302", "Numerik Matematik", 6), ("MAT392", "Kompleks Analiz", 6)],
            "SDT": [("ETE312", "Elektronik II: Devre Teknolojisi", 6), ("ETE374", "Sayısal Sinyal İşlemenin Temelleri", 6)],
            "SDP": [("ETE491", "EEE Projesi", 6), ("MEC319", "Mekatronik Projesi", 6), ("INF303", "Yazılım Müh. Projesi", 6)],
            "SDV": [("ETE104", "Mikroişlemciler", 6), ("ETE312", "Elektronik II", 6), ("ETE442", "Gömülü Sistemler", 6), ("INF102", "Nesnel Programlama", 6), ("INF501", "Akıllı Sistemler", 6)],
            "SDVI": [("ETE104", "Mikroişlemciler", 6), ("ETE312", "Elektronik II", 6), ("ETE442", "Gömülü Sistemler", 6), ("INF102", "Nesnel Programlama", 6), ("INF501", "Akıllı Sistemler", 6)],
            "SDVII": [("ETE412", "Optik Haberleşme", 6), ("ETE414", "İşlemsel Yükselteçler", 6), ("ETE433", "Elektrik Makineleri II", 6), ("ETE441", "FPGA Programlama", 6), ("ETE456", "Akıllı Kontrol", 6), ("INF513", "Derin Öğrenme", 6)],
            "SDVIII": [("ETE412", "Optik Haberleşme", 6), ("ETE414", "İşlemsel Yükselteçler", 6), ("ETE433", "Elektrik Makineleri II", 6), ("ETE441", "FPGA Programlama", 6), ("ETE456", "Akıllı Kontrol", 6), ("INF513", "Derin Öğrenme", 6)],
            "USD": [("ELC101", "Fotoğrafçılık", 6), ("ELC102", "Sinema Tarihi", 6)]
        }
    },
    "Endüstri Mühendisliği": {
        "curriculum": {
            1: [("WIN091", "Endüstri Müh. Giriş", 2), ("WIN103", "İşletmeye Giriş", 6), ("WIN107", "Tasarım Tek. I", 6), ("WIN109", "Statik", 6), ("MAT103", "Analiz I", 6), ("DEU121", "Teknik Almanca I", 2), ("ENG101", "İngilizce I", 2)],
            2: [("WIN092", "Bilimsel Çalışma Yönt.", 2), ("WIN104", "İktisada Giriş", 6), ("WIN112", "Mukavemet", 6), ("MAT106", "Lineer Cebir", 6), ("MAT108", "Analiz II", 6), ("DEU118", "İşletme Almancası", 2), ("ENG102", "İngilizce II", 2)],
            3: [("WIN203", "Bilg. Bil. ve Prog. Giriş", 6), ("WIN207", "Yatırım ve Finansman", 6), ("WIN209", "Yöneylem Arş. I", 6), ("WIN299", "Temel Staj", 2), ("MAT201", "Diferansiyel Denklemler", 6), ("ENG201", "İngilizce III", 2), ("TUR001", "Türkçe I", 2)],
            4: [("WIN204", "Muhasebe ve Bilanço", 6), ("WIN208", "Nesnel Programlama", 6), ("WIN212", "EEE Temelleri", 6), ("WIN292", "Proje Yönetimi", 2), ("MAT204", "İstatistiksel Yöntemler", 6), ("ENG202", "İngilizce IV", 2), ("TUR002", "Türkçe II", 2)],
            5: [("WIN313", "Lojistik Yönetimi", 6), ("WIN315", "Veritabanı Sistemleri", 6), ("SDP", "Seçmeli Alan - Proje", 6), ("SDI", "Seçmeli Alan I - İktisat", 6), ("ZSDI", "Zorunlu Seçmeli I", 6)],
            6: [("WIN302", "Fabrika Yönetimine Giriş", 6), ("WIN314", "Kalite Yönetimi", 6), ("SDII", "Seçmeli Alan II - Araştırma", 6), ("ZSDII", "Zorunlu Seçmeli II", 6), ("USD000", "Üniversite Seçmeli", 6)],
            7: [("WIN403", "Proje II: Endüstri Projesi", 6), ("WIN499", "Mesleki Alan Stajı", 6), ("AIT001", "Atatürk İlkeleri I", 2), ("ENG301", "İleri İngilizce I", 2), ("ISG001", "İş Sağlığı ve Güvenliği I", 2), ("ZSDI_1", "Zorunlu Seçmeli I - 1", 6), ("ZSDI_2", "Zorunlu Seçmeli I - 2", 6)],
            8: [("WIN492", "Bitirme Tezi", 12), ("AIT002", "Atatürk İlkeleri II", 2), ("ENG302", "İleri İngilizce II", 2), ("ISG002", "İş Sağlığı ve Güvenliği II", 2), ("ZSDII_1", "Zorunlu Seçmeli II - 1", 6), ("ZSDII_2", "Zorunlu Seçmeli II - 2", 6)]
        },
        "pools": {
            "SDP": [("WIN311", "Proje I: Yenilik Yönetimi", 6), ("INF303", "Yazılım Müh. Projesi", 6), ("MEC319", "Mekatronik Projesi", 6)],
            "SDI": [("WIN309", "Pazarlama", 6), ("WIN317", "İşletmesel Veri Analizi", 6), ("WIN321", "Yöneticilik", 6), ("VWL203", "İktisadi Tarih", 6)],
            "SDII": [("WIN316", "Yöneylem Arş. II", 6), ("ING406", "Mühendisler İçin Hukuk", 6), ("VWL210", "Para ve Finans", 6)],
            "ZSDI": [("WIN320", "Makine Öğrenmesi", 6), ("WIN323", "Havayolu Yönetimi", 6), ("WIN405", "Sürdürülebilir Üretim", 6), ("INF505", "Veri Madenciliği", 6), ("MAB301", "Takım Tezgahları", 6)],
            "ZSDII": [("WIN306", "Üretim Enformasyon Sis.", 6), ("WIN318", "Ergonomi", 6), ("WIN408", "Montaj Teknolojisi", 6), ("INF502", "Makine Öğrenmesi", 6), ("MAB210", "İmalat Teknolojisi", 6)],
            "USD": [("ELC101", "Fotoğrafçılık", 6), ("ELC102", "Sinema Tarihi", 6)]
        }
    },
    "Makine Mühendisliği": {
        "curriculum": {
            1: [("MAT103", "Analiz I", 6), ("MAB107", "Teknik Çizim ve CAD", 6), ("MAB109", "Statik", 6), ("MAB105", "Bilg. Bil. ve Prog. Giriş", 6), ("MAB091", "Makine Müh. Giriş", 2), ("ENG101", "İngilizce I", 2), ("DEU121", "Teknik Almanca I", 2)],
            2: [("MAT108", "Analiz II", 6), ("MAT106", "Lineer Cebir", 6), ("MAB112", "Mukavemet", 6), ("MAB108", "Tasarım Tek. I", 6), ("MAB092", "Bilimsel Çalışma Yönt.", 2), ("ENG102", "İngilizce II", 2), ("DEU122", "Teknik Almanca II", 2)],
            3: [("MAB213", "EEE Temelleri", 6), ("MAB203", "Tasarım Tek. II", 6), ("MAB205", "Kinematik ve Dinamik", 6), ("MAB207", "Malzeme Teknolojisi I", 6), ("MAB209", "Temel Staj", 2), ("AIT001", "Atatürk İlkeleri I", 2), ("ENG201", "İngilizce III", 2)],
            4: [("MAB210", "İmalat Teknolojisi Temelleri", 6), ("MAB216", "Ölçüm Teknikleri", 6), ("MAT204", "İstatistiksel Yönt.", 6), ("MAB214", "Dif. Denk. ve Sayısal", 6), ("MAB292", "Proje Yönetimi", 2), ("AIT002", "Atatürk İlkeleri II", 2), ("ENG202", "İngilizce IV", 2)],
            5: [("MAB301", "Takım Tezgâhları", 6), ("MAB317", "Titreşim ve Dinamik", 6), ("MAB303", "Termodinamik", 6), ("SDUx", "Uzmanlık Seçmeli I", 6), ("ISG001", "İş Sağlığı ve Güvenliği I", 2), ("ENG301", "İleri İngilizce I", 2), ("TUR001", "Türkçe I", 2)],
            6: [("MAB312", "Isı Transferi", 6), ("MAB314", "Akışkanlar Mekaniği", 6), ("SDK", "Kontrol Seçmeli", 6), ("SDP", "Proje Seçmeli", 6), ("TUR002", "Türkçe II", 2), ("ISG002", "İş Sağlığı ve Güvenliği II", 2), ("ENG302", "İleri İngilizce II", 2)],
            7: [("MAB499", "Mesleki Alan Stajı", 6), ("SUP", "Uygulamalı Proje", 6), ("SDUx_1", "Uzmanlık Seçmeli II-1", 6), ("SDUx_2", "Uzmanlık Seçmeli II-2", 6), ("USD000", "Üniversite Seçmeli", 6)],
            8: [("MAB492", "Bitirme Tezi", 12), ("SDUx_3", "Uzmanlık Seçmeli III-1", 6), ("SDUx_4", "Uzmanlık Seçmeli III-2", 6), ("SDUx_5", "Uzmanlık Seçmeli III-3", 6)]
        },
        "pools": {
            "SDK": [("MAB308", "Kontrol Müh. Temelleri", 6), ("ETE304", "Kontrol Müh. Temelleri", 6)],
            "SDP": [("MAB391", "Proje: Üretim", 6), ("MAB392", "Proje: Tasarım", 6), ("MAB393", "Proje: Uzay Havacılık", 6), ("MAB394", "Proje: Taşıt", 6)],
            "SUP": [("MAB391", "Proje: Üretim", 6), ("MAB392", "Proje: Tasarım", 6), ("MAB393", "Proje: Uzay Havacılık", 6), ("MAB394", "Proje: Taşıt", 6)],
            "SDU_A": [("WIN302", "Fabrika Yönetimi", 6), ("MAB311", "İmalat Tek. I", 6), ("MAB409", "İmalat Tek. II", 6), ("MAB411", "Yüzey Teknolojisi", 6)],
            "SDU_B": [("MAB305", "Tasarım Tek. III", 6), ("MAB353", "Sonlu Elemanlar", 6), ("MAB001", "Sürekli Ortamlar", 6), ("MAB413", "Makine Bilişim Tek.", 6)],
            "SDU_C": [("MAB456", "Akışkan Makineleri", 6), ("MAB355", "CFD I", 6), ("MAB455", "Havacılık Giriş", 6), ("MAB407", "Aerodinamik", 6)],
            "SDU_D": [("MAB354", "Araç Teknolojisi", 6), ("MAB304", "Dişli Teorisi", 6), ("MAB401", "Katı Cisim Sim.", 6), ("MAB405", "Motor Teknolojileri", 6)],
            "USD": [("ELC101", "Fotoğrafçılık", 6), ("ELC102", "Sinema Tarihi", 6)]
        }
    },
    "Mekatronik Mühendisliği": {
        "curriculum": {
            1: [("MAT103", "Analiz I", 6), ("MEC107", "Tasarım Tek. I", 6), ("MEC109", "Statik", 6), ("MEC105", "Bilg. Bil. Giriş", 6), ("MEC091", "Mühendisliğe Giris", 2), ("DEU121", "Teknik Almanca I", 2), ("ENG101", "İngilizce I", 2)],
            2: [("MAT108", "Analiz II", 6), ("PHY102", "Elektrik ve Manyetizma", 6), ("MEC112", "Mukavemet", 6), ("MAT106", "Lineer Cebir", 6), ("MEC092", "Bilimsel Yöntemler", 2), ("DEU122", "Teknik Almanca II", 2), ("ENG102", "İngilizce II", 2)],
            3: [("MAT201", "Diferansiyel Denklemler", 6), ("MEC213", "Elektrik Devreleri I", 6), ("MEC209", "Kinematik ve Dinamik", 6), ("MEC207", "Malzeme Teknolojisi I", 6), ("MEC299", "Temel Staj", 2), ("TUR001", "Türkçe I", 2), ("ENG201", "İngilizce III", 2)],
            4: [("MAT204", "İstatistik", 6), ("MEC214", "Elektrik Devreleri II", 6), ("MEC208", "Ölçüm Teknikleri", 6), ("MEC218", "Nesnel Programlama", 6), ("MEC292", "Proje Yönetimi", 2), ("TUR002", "Türkçe II", 2), ("ENG202", "İngilizce IV", 2)],
            5: [("MEC313", "End. Otomasyon Tek.", 6), ("MEC311", "Sinyaller ve Sistemler", 6), ("MEC317", "Algoritma ve Veri Y.", 6), ("MEC319", "Mekatronik Projesi", 6), ("ZSD_I", "Zorunlu Seçmeli I", 6)],
            6: [("MEC308", "Endüstriyel Robotik I", 6), ("MEC302", "Kontrol Müh. Temelleri", 6), ("SDP_I", "Seçmeli Proje I", 6), ("ZSD_II", "Zorunlu Seçmeli II", 6), ("USD000", "Üniversite Seçmeli", 6)],
            7: [("MEC499", "Mesleki Alan Stajı", 6), ("ISG001", "İş Sağlığı ve Güvenliği I", 2), ("AIT001", "Atatürk İlkeleri I", 2), ("ENG301", "İleri İngilizce I", 2), ("SDP_II", "Seçmeli Proje II", 6), ("ZSD_III_1", "Zorunlu Seçmeli III - 1", 6), ("ZSD_III_2", "Zorunlu Seçmeli III - 2", 6)],
            8: [("MEC492", "Bitirme Tezi", 12), ("ISG002", "İş Sağlığı ve Güv. II", 2), ("AIT002", "Atatürk İlkeleri II", 2), ("ENG302", "İleri İngilizce II", 2), ("ZSD_IV_1", "Zorunlu Seçmeli IV - 1", 6), ("ZSD_IV_2", "Zorunlu Seçmeli IV - 2", 6)]
        },
        "pools": {
            "SDP_I": [("MEC423", "Robotik Projesi I", 6), ("MEC425", "Üretim Projesi I", 6), ("MEC427", "Akıllı Sis. Proj. I", 6)],
            "SDP_II": [("MEC424", "Robotik Projesi II", 6), ("MEC426", "Üretim Projesi II", 6), ("MEC428", "Akıllı Sis. Proj. II", 6)],
            "ZSD_I": [("MEC321", "Görüntü Tabanlı Oto. I", 6), ("MEC002", "Uygulamalı Kontrol", 6), ("MEC312", "Elektrik Devre Elemanları", 6)],
            "ZSD_II": [("MEC324", "Görüntü Tabanlı Oto. II", 6), ("MEC421", "Endüstriyel Robotik II", 6), ("INF205", "Veritabanı Sistemleri", 6)],
            "ZSD_III": [("INF202", "Yazılım Mühendisliği", 6), ("ETE456", "Akıllı Kontrol", 6), ("INF523", "İnsan-Makine Etkileşimi", 6), ("ETE331", "Elektrik Makinaları I", 6)],
            "ZSD_IV": [("ETE104", "Mikroişlemciler", 6), ("WIN302", "Fabrika Yönetimi", 6), ("INF502", "Makine Öğrenmesi", 6), ("MEC036", "Gömülü Sistemler", 6)],
            "USD": [("ELC101", "Fotoğrafçılık", 6), ("ELC102", "Sinema Tarihi", 6)]
        }
    },
    "İnşaat Mühendisliği": {
        "curriculum": {
            1: [("MAT103", "Analiz I", 6), ("BAU109", "Statik", 6), ("DEU121", "Teknik Almanca I", 2), ("BAU107", "Tasarım Teknikleri", 6), ("PHY103", "Modern Fizik", 6), ("ENG101", "İngilizce I", 2), ("BAU091", "İnşaat Müh. Giriş", 2)],
            2: [("MAT108", "Analiz II", 6), ("MAT106", "Lineer Cebir", 6), ("DEU122", "Teknik Almanca II", 2), ("BAU102", "Taşıyıcı Sistemler", 6), ("BAU092", "Bilimsel Çalışma Yönt.", 2), ("ENG102", "İngilizce II", 2), ("BAU112", "Mukavemet", 6)],
            3: [("MAT201", "Diferansiyel Denklemler", 6), ("BAU209", "Kinematik ve Dinamik", 6), ("ENG201", "İngilizce III", 2), ("AIT001", "Atatürk İlkeleri I", 2), ("BAU201", "Yapı Malz. ve Kimyası I", 6), ("BAU202", "Yapı Statiği I", 6), ("TUR001", "Türkçe I", 2)],
            4: [("AIT002", "Atatürk İlkeleri II", 2), ("ENG202", "İngilizce IV", 2), ("BAU203", "Yapı İnşaatı I", 6), ("BAU204", "Yapı Statiği II", 6), ("BAU205", "Akışkanlar Mekaniği", 6), ("BAU206", "Yapı Malz. ve Kimyası II", 2), ("ZSD_1", "Zorunlu Seçmeli 1", 6)],
            5: [("BAU301", "Yapı İnşaatı II", 6), ("BAU303", "Ulaştırma", 6), ("ZSD_2", "Zorunlu Seçmeli 2", 6), ("ZSD_3", "Zorunlu Seçmeli 3", 6), ("ZSD_4", "Zorunlu Seçmeli 4", 6)],
            6: [("ZSD_5", "Zorunlu Seçmeli 5", 6), ("ZSD_6", "Zorunlu Seçmeli 6", 6), ("ZSD_7", "Zorunlu Seçmeli 7", 6), ("ZSD_8", "Zorunlu Seçmeli 8", 6), ("BAU302", "Zemin Mekaniği I", 6)],
            7: [("ENG301", "İleri İngilizce I", 2), ("BSP201", "Şantiye Stajı", 4), ("ISG001", "İş Sağlığı ve Güvenliği I", 2), ("BUP403", "Büro Stajı", 4), ("ZSD_9", "Zorunlu Seçmeli 9", 6), ("USD000", "Üniversite Seçmeli", 6), ("BAU304", "Zemin Mekaniği II", 6)],
            8: [("ZSD_10", "Zorunlu Seçmeli 10", 6), ("ZSD_11", "Zorunlu Seçmeli 11", 6), ("TUR002", "Türkçe II", 2), ("ISG002", "İş Sağlığı ve Güvenliği II", 2), ("BAU492", "Lisans Bitirme Çalışması", 12), ("ENG302", "İleri İngilizce II", 2)]
        },
        "pools": {
            "ZSD": [("BAU251", "Nümerik Metotlar", 6), ("BAU252", "Yapı Fiziği", 6), ("MAT204", "İstatistik", 6), ("BAU305", "Stokastik Sistemler", 6), ("BAU350", "Proje I", 6), ("BAU351", "Sistem Tekniği", 6), ("INF101", "Bilg. Bil. Giriş", 6), ("BAU352", "Yapı İşletmesi I", 6), ("BAU353", "İnşaat Hukuku", 6), ("BAU354", "Yapı Statiği III", 6), ("BAU355", "Geodezi", 6), ("BAU356", "Jeoloji", 6), ("BAU357", "İnşaat Bilişimi", 6), ("BAU451", "Su Kaynakları", 6), ("BAU452", "Kentsel Su", 6), ("BAU454", "Yapı İnşaatı III", 6), ("BAU460", "BIM", 6)],
            "USD": [("ELC101", "Fotoğrafçılık", 6), ("ELC102", "Sinema Tarihi", 6)]
        }
    }
}

def get_course_from_pool(code, department, specialization=None):
    """
    Returns a random course (code, name, ects) from the pool if the code is a placeholder.
    Uses department-specific pools.
    """
    dept_data = DEPARTMENTS_DATA.get(department)
    if not dept_data:
        return None
    
    pools = dept_data["pools"]
    
    # Clean code suffix (e.g. SDIII_1 -> SDIII)
    base_code = code.split('_')[0]
    
    # Handle Specialization for Makine
    if department == "Makine Mühendisliği" and "SDUx" in base_code:
        if specialization:
            pool_key = f"SDU_{specialization}"
            if pool_key in pools:
                return random.choice(pools[pool_key])
        # Fallback if no specialization or pool not found
        return random.choice(pools.get("SDU_A", []))

    # Direct Match
    if code in pools:
        return random.choice(pools[code])
    
    # Base Code Match
    if base_code in pools:
        return random.choice(pools[base_code])
        
    # Generic Fallbacks based on naming convention if not explicitly in pools
    if "USD" in base_code and "USD" in pools:
        return random.choice(pools["USD"])
        
    if "ZSD" in base_code and "ZSD" in pools:
        return random.choice(pools["ZSD"])

    return None

def populate():
    print("Starting Student Population...")
    try:
        model = ScheduleModel()
    except Exception as e:
        print(f"Error connecting to DB: {e}")
        return

    # Clear existing data
    print("Clearing existing student data...")
    try:
        # Drop tables to ensure schema update for ECTS
        model.c.execute("DROP TABLE IF EXISTS Dersler")
        model.c.execute("DROP TABLE IF EXISTS Ogrenci_Notlari")
        model.c.execute("DROP TABLE IF EXISTS Verilen_Dersler")
        model.c.execute("DROP TABLE IF EXISTS Alinan_Dersler")
        model.c.execute("DROP TABLE IF EXISTS Ders_Sinif_Iliskisi")
        model.c.execute("DROP TABLE IF EXISTS Ogrenci_Donemleri")
        model.c.execute("DROP TABLE IF EXISTS Ogrenciler")
        model.conn.commit()
        
        # Recreate tables (ScheduleModel constructor called _create_tables but we dropped them)
        # We need to call _create_tables again
        model._create_tables()
        
    except Exception as e:
        print(f"Error clearing/recreating data: {e}")

    # Ensure Faculties and Departments exist
    faculties = ["Mühendislik Fakültesi"]
    for f in faculties:
        model.c.execute("INSERT OR IGNORE INTO Fakulteler (fakulte_adi) VALUES (?)", (f,))
    model.conn.commit()
    
    model.c.execute("SELECT fakulte_num FROM Fakulteler WHERE fakulte_adi = 'Mühendislik Fakültesi'")
    eng_faculty_id = model.c.fetchone()[0]
    
    departments = list(DEPARTMENTS_DATA.keys())
    dept_ids = {}
    
    for i, dept in enumerate(departments, 1):
        bolum_id = 100 + i
        bolum_num = 1000 + i
        model.c.execute("INSERT OR IGNORE INTO Bolumler (bolum_id, bolum_num, bolum_adi, fakulte_num) VALUES (?, ?, ?, ?)",
                       (bolum_id, bolum_num, dept, eng_faculty_id))
        dept_ids[dept] = (bolum_id, bolum_num)
    model.conn.commit()

    # Generate Students
    student_count = 0
    
    for dept_name, (bolum_id, bolum_num) in dept_ids.items():
        print(f"Processing {dept_name}...")
        curriculum = DEPARTMENTS_DATA[dept_name]["curriculum"]
        
        for year in range(1, 5): # 1st to 4th year
            # Current semester for this year in Fall
            current_semester = year * 2 - 1
            
            donem_sinif_num = f"{2024-year}_{bolum_num}_{year}"
            model.c.execute('''
                INSERT OR IGNORE INTO Ogrenci_Donemleri (donem_sinif_num, baslangic_yili, bolum_num, sinif_duzeyi)
                VALUES (?, ?, ?, ?)
            ''', (donem_sinif_num, 2024-year, bolum_id, year))
            
            # Create 10 students per year
            for i in range(1, 11):
                student_num = int(f"{2024-year}{bolum_id}{i:03d}")
                first_name = f"Ogrenci_{dept_name[:3]}_{year}"
                last_name = f"No_{i}"
                
                # Assign Specialization for Makine students
                specialization = None
                if dept_name == "Makine Mühendisliği":
                    specialization = random.choice(["A", "B", "C", "D"])
                
                model.c.execute('''
                    INSERT OR REPLACE INTO Ogrenciler (ogrenci_num, ad, soyad, girme_senesi, kacinci_donem, bolum_num, fakulte_num)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (student_num, first_name, last_name, 2024-year, current_semester, bolum_id, eng_faculty_id))
                
                # 1. Past Courses (Passed)
                passed_courses_list = []
                
                for past_sem in range(1, current_semester):
                    if past_sem in curriculum:
                        for course_code, course_name, course_ects in curriculum[past_sem]:
                            pool_course = get_course_from_pool(course_code, dept_name, specialization)
                            if pool_course:
                                real_code, real_name, real_ects = pool_course
                            else:
                                real_code, real_name, real_ects = course_code, course_name, course_ects
                                
                            passed_courses_list.append(real_name)
                            term_label = "Guz" if past_sem % 2 != 0 else "Bahar"
                            term_year = 2024 - year + (past_sem + 1) // 2 - 1
                            
                            # Insert Course with ECTS
                            model.c.execute("INSERT OR IGNORE INTO Dersler (ders_kodu, ders_instance, ders_adi, akts) VALUES (?, ?, ?, ?)", 
                                          (real_code, 1, real_name, real_ects))
                            
                            model.c.execute('''
                                INSERT INTO Ogrenci_Notlari (ogrenci_num, ders_kodu, ders_adi, harf_notu, durum, donem)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (student_num, real_code, real_name, "AA", "Geçti", f"{term_year}-{term_label}"))

                if passed_courses_list:
                    passed_str = ", ".join(passed_courses_list)
                    model.c.execute("INSERT OR REPLACE INTO Verilen_Dersler (ogrenci_num, ders_listesi) VALUES (?, ?)",
                                   (student_num, passed_str))
                
                # 2. Current Courses (Enrolled)
                if current_semester in curriculum:
                    for course_code, course_name, course_ects in curriculum[current_semester]:
                        pool_course = get_course_from_pool(course_code, dept_name, specialization)
                        if pool_course:
                            real_code, real_name, real_ects = pool_course
                        else:
                            real_code, real_name, real_ects = course_code, course_name, course_ects
                            
                        # Add course to Dersler with ECTS
                        model.c.execute("INSERT OR IGNORE INTO Dersler (ders_kodu, ders_instance, ders_adi, akts) VALUES (?, ?, ?, ?)", 
                                      (real_code, 1, real_name, real_ects))
                        
                        # Add to Ders_Sinif_Iliskisi
                        model.c.execute("INSERT OR IGNORE INTO Ders_Sinif_Iliskisi (ders_adi, ders_instance, donem_sinif_num) VALUES (?, ?, ?)", 
                                      (real_name, 1, donem_sinif_num))
                        
                        # Add to Ogrenci_Notlari (Current Semester)
                        grade_info = random.choice(GRADES)
                        grade_letter = grade_info
                        status = "Geçti" if grade_letter != "FF" else "Kaldı"
                        
                        model.c.execute("INSERT INTO Ogrenci_Notlari (ogrenci_num, ders_kodu, ders_adi, harf_notu, durum, donem) VALUES (?, ?, ?, ?, ?, ?)",
                                      (student_num, real_code, real_name, grade_letter, status, f"{2024}-Guz"))

                student_count += 1
                
    model.conn.commit()
    print(f"✅ Successfully created {student_count} students across {len(departments)} departments.")
    model.conn.close()

if __name__ == "__main__":
    populate()
