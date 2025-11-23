import sys
import os
import random
import sqlite3

# Add project root to path
sys.path.append(os.getcwd())

from models.schedule_model import ScheduleModel

GRADES = ["AA", "BA", "BB", "CB", "CC", "DC", "DD", "FD", "FF"]

# Curriculum Data (Mapped from provided links with inferred codes)
CURRICULUM = {
    "Bilgisayar Mühendisliği": {
        # 1. Semester (Fall)
        1: [
            ("MAT103", "Analiz I"),
            ("INF101", "Bilgisayar Bilimine ve Programlamaya Giriş"),
            ("INF103", "Mantık"),
            ("INF107", "Bilgisayar Organizasyonu"),
            ("DEU121", "Teknik Almanca I"),
            ("ENG101", "İngilizce I"),
            ("TUR001", "Türkçe I")
        ],
        # 2. Semester (Spring)
        2: [
            ("MAT106", "Lineer Cebir"),
            ("INF102", "Nesnel Programlama"),
            ("INF104", "Özdevinirler ve Biçimsel Diller"),
            ("INF110", "İşletim Sistemleri"),
            ("DEU122", "Teknik Almanca II"),
            ("ENG102", "İngilizce II"),
            ("TUR002", "Türkçe II")
        ],
        # 3. Semester (Fall)
        3: [
            ("INF201", "Ayrık Yapılar"),
            ("INF203", "Algoritmalar ve Veri Yapıları I"),
            ("INF205", "Veritabanı Sistemleri"),
            ("INF209", "Bilgisayar Ağları"),
            ("INF211", "Bilgisayar ve Toplum Semineri"),
            ("ENG201", "İngilizce III"),
            ("AIT001", "Atatürk İlkeleri ve İnkılap Tarihi I")
        ],
        # 4. Semester (Spring)
        4: [
            ("MAT204", "Veri Analizinin İstatistiksel Yöntemleri"),
            ("INF202", "Yazılım Mühendisliği"),
            ("INF204", "Algoritmalar ve Veri Yapıları II"),
            ("INF208", "Gömülü Sistemler"),
            ("INF210", "Bilgisayar Mühendisleri için Etik Semineri"),
            ("ENG202", "İngilizce IV"),
            ("AIT002", "Atatürk İlkeleri ve İnkılap Tarihi II")
        ],
        # 5. Semester (Fall)
        5: [
            ("SDP", "Seçmeli Alan - Proje"),
            ("SDIa", "Seçmeli Dersler I - Uygulamalı Bilgisayar Mühendisliği"),
            ("SDIb", "Seçmeli Dersler I - Bilgisayar Donanımı"),
            ("SDIc", "Seçmeli Dersler I - Kuramsal ve Matematik"),
            ("ÜSD001", "Üniversite Seçmeli Ders Havuzu I"),
            ("ISG001", "İş Sağlığı ve Güvenliği I"),
            ("ENG301", "İleri İngilizce I")
        ],
        # 6. Semester (Spring)
        6: [
            ("SDIIa", "Seçmeli Dersler II - Uygulamalı Bilgisayar Mühendisliği"),
            ("SDIIb", "Seçmeli Dersler II - Bilgisayar Donanımı"),
            ("SDIIc", "Seçmeli Dersler II - Kuramsal ve Matematik"),
            ("ÜSD002", "Üniversite Seçmeli Ders Havuzu II"),
            ("ISG002", "İş Sağlığı ve Güvenliği II"),
            ("ENG302", "İleri İngilizce II")
        ],
        # 7. Semester (Fall)
        7: [
            ("INF499", "Mesleki Alan Stajı"),
            ("INF401", "Bilimsel Çalışma Yöntemleri"),
            ("SDIII", "Seçmeli Dersler III")
        ],
        # 8. Semester (Spring)
        8: [
            ("INF492", "Bitirme Tezi"),
            ("SDIV", "Seçmeli Dersler IV")
        ]
    },
    "Elektrik-Elektronik Mühendisliği": {
        # 1. Semester (Fall)
        1: [
            ("MAT103", "Analiz I"),
            ("PHY101", "Mekaniğin Temelleri"),
            ("ETE101", "Sayısal Tasarım"),
            ("ETE103", "Bilgisayar Bilimine ve Programlamaya Giriş"),
            ("ETE091", "Elektrik-Elektronik Mühendisliğine Giriş"),
            ("DEU121", "Teknik Almanca I"),
            ("ENG101", "İngilizce I")
        ],
        # 2. Semester (Spring)
        2: [
            ("MAT108", "Analiz II"),
            ("PHY102", "Elektrik ve Manyetizma"),
            ("MAT106", "Lineer Cebir"),
            ("SDII", "Seçmeli Ders Alanı II"), # ETE104 or INF102
            ("ETE092", "Bilimsel Çalışma Yöntemleri"),
            ("DEU122", "Teknik Almanca II"),
            ("ENG102", "İngilizce II")
        ],
        # 3. Semester (Fall)
        3: [
            ("MAT201", "Diferansiyel Denklemler"),
            ("ETE201", "Elektrik Devreleri I"),
            ("PHY103", "Modern Fizik"),
            ("ETE207", "Malzeme Teknolojisi"),
            ("ETE299", "Temel Staj"),
            ("TUR001", "Türkçe I"),
            ("ENG201", "İngilizce III")
        ],
        # 4. Semester (Spring)
        4: [
            ("MAT204", "Veri Analizinin İstatistiksel Yöntemleri"),
            ("ETE202", "Elektrik Devreleri II"),
            ("ETE208", "Ölçüm Teknikleri"),
            ("ETE292", "Proje Yönetimi"),
            ("TUR002", "Türkçe II"),
            ("ENG202", "İngilizce IV"),
            ("ÜSD000", "Üniversite Seçmeli Ders Havuzu")
        ],
        # 5. Semester (Fall)
        5: [
            ("ETE321", "Elektromanyetik Alanlar"),
            ("ETE303", "Sinyaller ve Sistemler"),
            ("ETE311", "Elektronik I: Yarı İletken Elemanlar"),
            ("ETE331", "Elektrik Makineleri I"),
            ("SDV", "Seçmeli Ders Alanı V")
        ],
        # 6. Semester (Spring)
        6: [
            ("ETE304", "Kontrol Mühendisliğinin Temelleri"),
            ("ETE372", "Telekomünikasyon"),
            ("SDT", "Seçmeli Ders Alanı T"),
            ("SDM", "Seçmeli Ders Alanı M"),
            ("SDVI", "Seçmeli Ders Alanı VI")
        ],
        # 7. Semester (Fall)
        7: [
            ("ETE499", "Mesleki Alan Stajı"),
            ("ISG001", "İş Sağlığı ve Güvenliği I"),
            ("AIT001", "Atatürk İlkeleri ve İnkılap Tarihi I"),
            ("ENG301", "İleri İngilizce I"),
            ("SDP", "Seçmeli Alan - Proje"),
            ("SDVII", "Seçmeli Ders Alanı VII")
        ],
        # 8. Semester (Spring)
        8: [
            ("ETE492", "Lisans Bitirme Çalışması"),
            ("ISG002", "İş Sağlığı ve Güvenliği II"),
            ("AIT002", "Atatürk İlkeleri ve İnkılap Tarihi II"),
            ("ENG302", "İleri İngilizce II"),
            ("MAT101", "Analiz I"), 
            ("FIZ101", "Fizik I"), 
            ("KIM101", "Yapı Malzemesi ve Kimyası I"), 
            ("INS101", "İnşaat Mühendisliğine Giriş"),
            ("TUR101", "Türkçe I")
        ],
        # 3. Semester
        3: [
            ("INS201", "Yapı Statiği I"), 
            ("INS203", "Mukavemet I"), 
            ("MAT201", "Diferansiyel Denklemler"), 
            ("INS207", "Jeoloji")
        ],
        # 5. Semester
        5: [
            ("INS301", "Yapı Statiği II"), 
            ("INS303", "Zemin Mekaniği I"), 
            ("INS305", "Akışkanlar Mekaniği"), 
            ("INS307", "Ulaştırma I")
        ],
        # 7. Semester
        7: [
            ("INS401", "Betonarme I"), 
            ("INS403", "Çelik Yapılar"), 
            ("INS405", "Su Kaynakları"), 
            ("INS407", "Temel İnşaatı")
        ]
    },
    "Endüstri Mühendisliği": {
        # 1. Semester
        1: [
            ("MAT103", "Analiz I"), 
            ("PHY101", "Mekaniğin Temelleri"), 
            ("CHM101", "Genel Kimya"), 
            ("WIN101", "Endüstri Mühendisliğine Giriş"),
            ("TUR001", "Türkçe I"),
            ("ENG101", "İngilizce I")
        ],
        # 2. Semester
        2: [
            ("MAT108", "Analiz II"),
            ("PHY102", "Elektrik ve Manyetizma"),
            ("MAT106", "Lineer Cebir"),
            ("WIN102", "Bilgisayar Destekli Teknik Resim"),
            ("TUR002", "Türkçe II"),
            ("ENG102", "İngilizce II")
        ],
        # 3. Semester
        3: [
            ("WIN201", "Olasılık Teorisi"), 
            ("WIN203", "Bilgisayar Programlama"), 
            ("WIN205", "Maliyet Muhasebesi"), 
            ("WIN207", "Malzeme Bilimi"),
            ("ENG201", "İngilizce III"),
            ("AIT001", "Atatürk İlkeleri ve İnkılap Tarihi I")
        ],
        # 4. Semester
        4: [
            ("WIN202", "İstatistik"),
            ("WIN204", "Yöneylem Araştırması I - Deterministik Modeller"),
            ("WIN206", "İş Etüdü ve Ergonomi"),
            ("WIN208", "Üretim Yöntemleri"),
            ("ENG202", "İngilizce IV"),
            ("AIT002", "Atatürk İlkeleri ve İnkılap Tarihi II")
        ],
        # 5. Semester
        5: [
            ("WIN301", "Yöneylem Araştırması II - Rassal Modeller"), 
            ("WIN303", "Üretim Planlama ve Kontrol I"), 
            ("WIN305", "Kalite Kontrol"), 
            ("SD_IKTISAT", "Seçmeli Alan I - İktisadi Bilimler"),
            ("ZSD_I", "Zorunlu Seçmeli Alan I")
        ],
        # 6. Semester
        6: [
            ("WIN302", "Tesis Planlama"),
            ("WIN304", "Üretim Planlama ve Kontrol II"),
            ("WIN306", "Yönetim Bilişim Sistemleri"),
            ("SD_ARASTIRMA", "Seçmeli Alan II - Araştırma Alanı"),
            ("ZSD_II", "Zorunlu Seçmeli Alan II")
        ],
        # 7. Semester
        7: [
            ("SD_PROJE", "Seçmeli Alan - Proje"), 
            ("WIN401", "Tedarik Zinciri Yönetimi"), 
            ("WIN403", "Benzetim"), 
            ("ISG001", "İş Sağlığı ve Güvenliği I"),
            ("ENG301", "İleri İngilizce I")
        ],
        # 8. Semester
        8: [
            ("WIN402", "Bitirme Çalışması"),
            ("ISG002", "İş Sağlığı ve Güvenliği II"),
            ("ENG302", "İleri İngilizce II")
        ]
    },
    "Makine Mühendisliği": {
        # 1. Semester
        1: [
            ("MAT101", "Analiz I"), 
            ("FIZ101", "Fizik I"), 
            ("KIM101", "Kimya"), 
            ("MAK101", "Makine Mühendisliğine Giriş"),
            ("TUR101", "Türkçe I")
        ],
        # 3. Semester
        3: [
            ("MAK201", "Statik"), 
            ("MAK203", "Dinamik"), 
            ("MAK205", "Termodinamik I"), 
            ("MAK207", "Malzeme I")
        ],
        # 5. Semester
        5: [
            ("MAK301", "Akışkanlar Mekaniği I"), 
            ("MAK303", "Makine Elemanları I"), 
            ("MAK305", "Isı Transferi"), 
            ("MAK307", "İmalat Yöntemleri I")
        ],
        # 7. Semester
        7: [
            ("MAK401", "Makine Tasarımı I"), 
            ("MAK403", "Otomatik Kontrol"), 
            ("MAK405", "Motorlar"), 
            ("MAK407", "Enerji Dönüşüm Sistemleri")
        ]
    },
    "Mekatronik Mühendisliği": {
        # 1. Semester
        1: [
            ("MAT101", "Analiz I"), 
            ("FIZ101", "Fizik I"), 
            ("BIL101", "Bilgisayar Bilimine Giriş"), 
            ("MEK101", "Mekatronik Mühendisliğine Giriş"),
            ("TUR101", "Türkçe I")
        ],
        # 3. Semester
        3: [
            ("MEK201", "Kinematik ve Dinamik"), 
            ("MAT201", "Diferansiyel Denklemler"), 
            ("MEK203", "Malzeme Teknolojisi I"), 
            ("MEK205", "Elektrik Devreleri II")
        ],
        # 5. Semester
        5: [
            ("MEK301", "Endüstriyel Otomasyon Teknolojisi"), 
            ("MEK303", "Sinyaller ve Sistemler"), 
            ("MEK305", "Algoritmalar ve Veri Yapıları I"), 
            ("MEK307", "Mekatronik Projesi")
        ],
        # 7. Semester
        7: [
            ("MEK401", "Robotik"), 
            ("MEK403", "Otomatik Kontrol"), 
            ("MEK405", "Gömülü Sistemler"), 
            ("MEK407", "Mekatronik Tasarım I")
        ]
    }
}

# Elective Pools
ELECTIVE_POOLS = {
    # --- Bilgisayar Mühendisliği Pools ---
    "SDP": [ # Proje
        ("WIN311", "Yenilik ve Teknoloji Yönetimi Projesi"),
        ("MEC319", "Mekatronik Projesi"),
        ("INF303", "Yazılım Mühendisliği Projesi"),
        ("ETE491", "Elektrik-Elektronik Mühendisliği Projesi")
    ],
    "POOL_APPLIED_CS": [ # SDIa, SDIIa, SDIII, SDIV
        ("INF501", "Veri Tabanı Yönetimi"), ("INF502", "Web Programlama"), ("INF503", "Mobil Programlama"),
        ("INF504", "Oyun Programlama"), ("INF505", "Yapay Zeka Uygulamaları"), ("INF506", "Bilgisayar Grafikleri"),
        ("INF507", "Robotik Programlama"), ("INF508", "Bilgisayar Simülasyonları"), ("INF509", "Gömülü Sistem Uygulamaları"),
        ("INF510", "IoT Uygulamaları"), ("INF511", "Siber Güvenlik"), ("INF512", "Makine Öğrenmesi"),
        ("INF513", "Veri Madenciliği"), ("INF514", "Ağ Programlama"), ("INF515", "Bulut Bilişim"),
        ("INF516", "İşletim Sistemi Uygulamaları"), ("INF517", "Donanım-Programlama Entegrasyonu"), ("INF518", "Bilgisayarla Görü"),
        ("INF519", "Ses ve Görüntü İşleme"), ("INF520", "Otonom Sistemler"), ("INF521", "Yapay Sinir Ağları"),
        ("INF522", "Paralel ve Dağıtık Sistemler"), ("INF523", "Bilgi Güvenliği"), ("INF524", "Veri Analitiği"),
        ("INF525", "Akıllı Sistemler"), ("INF526", "Sanal Gerçeklik Uygulamaları"), ("INF527", "AR ve MR Uygulamaları"),
        ("INF528", "Bilgisayar Destekli Tasarım"), ("INF529", "Büyük Veri Uygulamaları"), ("INF530", "Veri Tabanı Performans Analizi"),
        ("INF531", "Yapay Zeka ve Robotik"), ("INF532", "IoT ve Akıllı Ev Sistemleri"), ("INF533", "Gömülü Sistem Tasarımı"),
        ("INF534", "İleri Programlama Teknikleri")
    ],
    "POOL_HARDWARE": [ # SDIb, SDIIb
        ("ETE501", "Mikroişlemci Sistemleri"), ("ETE502", "FPGA Tasarımı"), ("ETE503", "Sayısal Devre Tasarımı"),
        ("ETE504", "Donanım-Programlama Entegrasyonu"), ("ETE505", "Bilgisayar Mimarisi"), ("ETE506", "Gömülü Sistemler"),
        ("ETE507", "Donanım Simülasyonları"), ("ETE508", "İleri Mikroişlemciler")
    ],
    "POOL_THEORY": [ # SDIc, SDIIc
        ("MAT301", "Sayısal Analiz"), ("MAT302", "Olasılık ve İstatistik"), ("MAT303", "Diferansiyel Denklemler"),
        ("MAT304", "Lineer Cebir Uygulamaları"), ("MAT305", "Matematiksel Modelleme"), ("MAT306", "Kriptografi Temelleri"),
        ("MAT307", "Mantıksal ve Kuramsal Bilgisayar Bilimi"), ("MAT308", "İleri Matematiksel Analiz")
    ],

    # --- Elektrik-Elektronik Mühendisliği Pools ---
    "SDII": [
        ("ETE104", "Mikroişlemciler"),
        ("INF102", "Nesnel Programlama")
    ],
    "SDV": [
        ("ETE104", "Mikroişlemciler"), ("ETE312", "Elektronik II: Devre Teknolojisi"), ("ETE374", "Sayısal Sinyal İşlemenin Temelleri"),
        ("ETE414", "İşlemsel Yükselteçler ile Devre Tasarımı"), ("ETE434", "Elektrik Enerjisi Kaynakları"), ("ETE441", "FPGA Programlama"),
        ("ETE442", "Gömülü Sistemler"), ("ETE444", "Donanım Betimleme Dili ile Tasarım"), ("ETE456", "Sistem Tanımlama ve Akıllı Kontrol"),
        ("ETE461", "Klinik Veri Yönetimi"), ("ETE464", "Yapay Sinir Ağları"), ("ETE477", "Elektroakustik"),
        ("ETE487", "Yenilenebilir Enerji Teknolojisi"), ("ETE393", "Elektroteknik: Seçilmiş Konular I"), ("ETE394", "Elektroteknik: Seçilmiş Konular II"),
        ("INF102", "Nesnel Programlama"), ("INF501", "Akıllı Sistemler"), ("INF502", "Makine Öğrenmesi"),
        ("INF510", "Bilişim Sistemleri Güvenliği"), ("INF513", "Derin Öğrenme"), ("INF518", "Bilgisayar Görmesinin Temelleri"),
        ("INF523", "İnsan-Makine İletişimi"), ("INF701", "Yapay Zekâ"), ("MAT302", "Numerik Matematik"),
        ("MAT392", "Kompleks Analiz"), ("MEC002", "Uygulamalı Kontrol Mühendisliği"), ("MEC308", "Endüstriyel Robotik I"),
        ("MEC313", "Endüstriyel Otomasyon Teknolojisi")
    ],
    "SDM": [
        ("MAT302", "Numerik Matematik"),
        ("MAT392", "Kompleks Analiz")
    ],
    "SDT": [
        ("ETE312", "Elektronik II: Devre Teknolojisi"),
        ("ETE374", "Sayısal Sinyal İşlemenin Temelleri")
    ],
    "POOL_EEM_PROJECT": [ # EEM 7. Semester Project
        ("ETE491", "Elektrik-Elektronik Mühendisliği Projesi"),
        ("MEC319", "Mekatronik Projesi"),
        ("INF303", "Yazılım Mühendisliği Projesi")
    ],
    "POOL_EEM_ADVANCED": [ # SDVII, SDVIII
        ("ETE104", "Mikroişlemciler"), ("ETE412", "Optik Haberleşme Tekniği"), ("ETE414", "İşlemsel Yükselteçler ile Devre Tasarımı"),
        ("ETE417", "RF Ön Uç Bileşenleri ve Devreler"), ("ETE415", "Elektronik Laboratuvarı"), ("ETE421", "Elektromanyetik Dalgaların Temelleri"),
        ("ETE422", "Anten Teorisine Giriş"), ("ETE433", "Elektrik Makineleri II"), ("ETE434", "Elektrik Enerjisi Kaynakları"),
        ("ETE439", "Güç Elektroniği"), ("ETE441", "FPGA Programlama"), ("ETE442", "Gömülü Sistemler"),
        ("ETE444", "Donanım Betimleme Dili ile Tasarım"), ("ETE447", "Analog Tümdevreler"), ("ETE448", "VLSI Tasarımına Giriş"),
        ("ETE451", "Doğrusal Olmayan Kontrol Sistemleri"), ("ETE452", "Hibrit Sistemler"), ("ETE453", "Ayrık Zamanlı Kontrol Sistemleri"),
        ("ETE454", "Çok Girdili Çok Çıktılı Sistemler"), ("ETE455", "Ayrık Olaylı Sistemler"), ("ETE456", "Sistem Tanımlama ve Akıllı Kontrol"),
        ("ETE459", "Doğrusal Olmayan Dinamik Sistemler"), ("ETE461", "Klinik Veri Yönetimi"), ("ETE464", "Yapay Sinir Ağları"),
        ("ETE466", "Makine Öğrenmesiyle Biyomedikal Modelleme"), ("ETE467", "Güvenilir Yapay Zeka"), ("ETE471", "Haberleşme Ağları"),
        ("ETE473", "Sayısal Haberleşme Sistemleri"), ("ETE474", "Sayısal Görüntü İşleme"), ("ETE475", "Sayısal Sinyal İşleme"),
        ("ETE476", "Bilgi Kuramı"), ("ETE477", "Elektroakustik"), ("ETE479", "Yüksek Frekans Tekniği"),
        ("ETE481", "Aydınlatma Teknolojisi"), ("ETE482", "Yüksek Gerilim Tekniği"), ("ETE484", "Güç Dağıtım Sistemleri"),
        ("ETE486", "Akıllı Şebekeler"), ("ETE487", "Yenilenebilir Enerji Teknolojisi"), ("ETE490", "İşletmede Mesleki Eğitim"),
        ("ETE498", "Tıbbi Cihazlarda Test, Kontrol ve Kalibrasyon"), ("INF102", "Nesnel Programlama"), ("INF501", "Akıllı Sistemler"),
        ("INF502", "Makine Öğrenmesi"), ("INF510", "Bilişim Sistemleri Güvenliği"), ("INF513", "Derin Öğrenme"),
        ("INF518", "Bilgisayar Görmesinin Temelleri"), ("INF523", "İnsan-Makine İletişimi"), ("INF701", "Yapay Zekâ"),
        ("MAT302", "Numerik Matematik"), ("MAT392", "Kompleks Analiz"), ("MEC002", "Uygulamalı Kontrol Mühendisliği"),
        ("MEC308", "Endüstriyel Robotik I"), ("MEC313", "Endüstriyel Otomasyon Teknolojisi"), ("MEC321", "Görüntü Tabanlı Otomasyon I"),
        ("MEC324", "Görüntü Tabanlı Otomasyon II"), ("MEC421", "Endüstriyel Robotik II")
    ],
    # --- Endüstri Mühendisliği Pools ---
    "POOL_IE_PROJECT": [ # Seçmeli Alan - Proje
        ("WIN311", "Proje I: Yenilik ve Teknoloji Yönetimi Projesi"),
        ("INF303", "Yazılım Mühendisliği Projesi"),
        ("MEC319", "Mekatronik Projesi")
    ],
    "POOL_IE_ECON": [ # Seçmeli Alan I - İktisadi Bilimler
        ("WIN309", "Pazarlama ve Üretim Yönetimi"),
        ("WIN317", "İşletmesel Veri Analizi"),
        ("WIN321", "Mühendisler için Yöneticilik"),
        ("VWL203", "İktisadi Tarih")
    ],
    "POOL_IE_RESEARCH": [ # Seçmeli Alan II - Endüstri Mühendisliği Araştırma Alanı
        ("WIN316", "Yöneylem Araştırması II - Rassal Modeller"),
        ("ING406", "Mühendisler İçin Hukuk"),
        ("VWL210", "Para, Banka ve Finans Piyasaları")
    ],
    "POOL_IE_ELECTIVE_I": [ # Zorunlu Seçmeli Alan I
        ("WIN320", "Makine Öğrenmesi"), ("WIN323", "Havayolu Yönetimi"),
        ("WIN405", "Sürdürülebilir Üretim için Ürün Yaşam Döngüsü"),
        ("WIN406", "Endüstriyel Enformasyon Teknolojisi ve Sanal Ürün Geliştirme"),
        ("WIN407", "Üretim Planlama ve Yönetimi"), ("WIN409", "Elektromobilite için Pil Üretim Teknolojisi"),
        ("WIN411", "Endüstri Mühendisliği: Seçilmiş Konular I"), ("WIN423", "Altı Sigma ve Problem Çözme"),
        ("ETE101", "Sayısal Tasarım"), ("ETE201", "Elektrik Devreleri I"), ("INF203", "Algoritmalar ve Veri Yapıları I"),
        ("INF503", "Yapay Sinir Ağları"), ("INF505", "Veri Madenciliği"), ("INF510", "Bilişim Sistemleri Güvenliği"),
        ("INF522", "Web Mühendisliği"), ("INF523", "İnsan-Makine Etkileşimi"),
        ("MAB203", "Tasarım Teknikleri II: Mekanik Parça Tasarımı"), ("MAB207", "Malzeme Teknolojisi I"),
        ("MAB301", "Takım Tezgahları"), ("MAB303", "Termodinamik"), ("MAB311", "İmalat Teknolojisi I"),
        ("MEC313", "Endüstriyel Otomasyon Teknolojisi")
    ],
    "POOL_IE_ELECTIVE_II": [ # Zorunlu Seçmeli Alan II
        ("WIN306", "Üretim ve Lojistik için Enformasyon Sistemleri"), ("WIN318", "Ergonomi: Metod-Zaman Ölçümü ve İş Bilimi"),
        ("WIN320", "Makine Öğrenmesi"), ("WIN406", "Endüstriyel Enformasyon Teknolojisi ve Sanal Ürün Geliştirme"),
        ("WIN408", "Montaj Teknolojisi Temelleri"), ("WIN409", "Elektromobilite için Pil Üretim Teknolojisi"),
        ("WIN412", "Endüstri Mühendisliği: Seçilmiş Konular II"), ("WIN422", "Havaalanı Yönetimi"),
        ("WIN424", "Mühendisler için Phyton"), ("WIN490", "İşletmede Mesleki Eğitim"), ("INF202", "Yazılım Mühendisliği"),
        ("INF502", "Makine Öğrenmesi"), ("INF503", "Yapay Sinir Ağları"), ("INF505", "Veri Madenciliği"),
        ("INF510", "Bilişim Sistemleri Güvenliği"), ("INF522", "Web Mühendisliği"), ("INF523", "İnsan-Makine Etkileşimi"),
        ("ING404", "Girişimcilik"), ("MAB207", "Malzeme Teknolojisi I"), ("MAB210", "İmalat Teknolojisinin Temelleri"),
        ("MAB354", "Araç Teknolojisinin Temelleri"), ("MAT302", "Numerik Matematik"), ("MEC208", "Ölçüm Teknikleri"),
        ("MEC308", "Endüstriyel Robotik I")
    ]
}

# Map curriculum placeholders to pools
POOL_MAPPING = {
    # BM
    "SDIa": "POOL_APPLIED_CS", "SDIIa": "POOL_APPLIED_CS", "SDIII": "POOL_APPLIED_CS", "SDIV": "POOL_APPLIED_CS",
    "SDIb": "POOL_HARDWARE", "SDIIb": "POOL_HARDWARE",
    "SDIc": "POOL_THEORY", "SDIIc": "POOL_THEORY",
    # EEM
    "SDII": "SDII", "SDV": "SDV", "SDM": "SDM", "SDT": "SDT",
    "SDP": "POOL_EEM_PROJECT", # Default mapping, will check department context if needed
    "SDVII": "POOL_EEM_ADVANCED", "SDVIII": "POOL_EEM_ADVANCED",
    # IE
    "SD_PROJE": "POOL_IE_PROJECT",
    "SD_IKTISAT": "POOL_IE_ECON",
    "SD_ARASTIRMA": "POOL_IE_RESEARCH",
    "ZSD_I": "POOL_IE_ELECTIVE_I",
    "ZSD_II": "POOL_IE_ELECTIVE_II"
}

def get_course_from_pool(code, department):
    """Returns a random course from the pool if the code is a placeholder."""
    # Handle SDP specifically as it appears in both but with different pools potentially
    if code == "SDP":
        if department == "Bilgisayar Mühendisliği":
            pool = ELECTIVE_POOLS["SDP"]
        else:
            pool = ELECTIVE_POOLS["POOL_EEM_PROJECT"]
        return random.choice(pool)
    
    if code == "SD_PROJE": # Explicit IE Project
        return random.choice(ELECTIVE_POOLS["POOL_IE_PROJECT"])

    if code in POOL_MAPPING:
        pool_key = POOL_MAPPING[code]
        if pool_key in ELECTIVE_POOLS:
            return random.choice(ELECTIVE_POOLS[pool_key])
            
    # Direct pool access (if code matches pool key directly)
    if code in ELECTIVE_POOLS:
        return random.choice(ELECTIVE_POOLS[code])
        
    return None

def populate():
    print("Starting Student Population...")
    model = ScheduleModel()
    
    # Clear existing data to avoid duplicates/stale data
    print("Clearing existing student data...")
    model.c.execute("DELETE FROM Ogrenci_Notlari")
    model.c.execute("DELETE FROM Verilen_Dersler")
    model.c.execute("DELETE FROM Alinan_Dersler")
    model.c.execute("DELETE FROM Ders_Sinif_Iliskisi")
    model.c.execute("DELETE FROM Ogrenci_Donemleri")
    model.c.execute("DELETE FROM Ogrenciler")
    model.conn.commit()
    
    # Ensure Faculties and Departments exist
    faculties = ["Mühendislik Fakültesi"]
    for f in faculties:
        model.c.execute("INSERT OR IGNORE INTO Fakulteler (fakulte_adi) VALUES (?)", (f,))
    model.conn.commit()
    
    model.c.execute("SELECT fakulte_num FROM Fakulteler WHERE fakulte_adi = 'Mühendislik Fakültesi'")
    eng_faculty_id = model.c.fetchone()[0]
    
    departments = list(CURRICULUM.keys())
    dept_ids = {}
    
    for i, dept in enumerate(departments, 1):
        # Using arbitrary IDs for bolum_id (100+i) and bolum_num (1000+i)
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
        curriculum = CURRICULUM.get(dept_name, {})
        
        for year in range(1, 5): # 1st to 4th year
            # Populate Ogrenci_Donemleri for this class
            # sinif_duzeyi: 1, 2, 3, 4
            # donem_sinif_num: e.g., "2023_BM_1"
            donem_sinif_num = f"{2024-year}_{bolum_num}_{year}"
            model.c.execute('''
                INSERT OR IGNORE INTO Ogrenci_Donemleri (donem_sinif_num, baslangic_yili, bolum_num, sinif_duzeyi)
                VALUES (?, ?, ?, ?)
            ''', (donem_sinif_num, 2024-year, bolum_id, year))
            
            # Create 20 students
            for i in range(1, 21):
                student_num = int(f"{2024-year}{bolum_id}{i:03d}") # e.g. 2023101001
                first_name = f"Ogrenci_{dept_name[:3]}_{year}"
                last_name = f"No_{i}"
                
                model.c.execute('''
                    INSERT OR REPLACE INTO Ogrenciler (ogrenci_num, ad, soyad, girme_senesi, kacinci_donem, bolum_num, fakulte_num)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (student_num, first_name, last_name, 2024-year, year*2-1, bolum_id, eng_faculty_id))
                
                # 1. Past Courses (Passed)
                passed_courses_list = []
                
                # Iterate through previous semesters (Odd and Even)
                # For a student in Year N (e.g., 3), they passed years 1 to N-1.
                # Semesters: 1, 2, 3, 4... (Year 1: 1-2, Year 2: 3-4)
                for past_year in range(1, year):
                    # Fall (Odd)
                    if past_year * 2 - 1 in curriculum:
                        for course_code, course_name in curriculum[past_year * 2 - 1]:
                            passed_courses_list.append(course_name)
                            # Add to Ogrenci_Notlari
                            model.c.execute('''
                                INSERT INTO Ogrenci_Notlari (ogrenci_num, ders_kodu, ders_adi, harf_notu, durum, donem)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (student_num, course_code, course_name, "AA", "Geçti", f"{2024-year+past_year}-Guz"))
                    
                    # Spring (Even)
                    if past_year * 2 in curriculum:
                        for course_code, course_name in curriculum[past_year * 2]:
                            passed_courses_list.append(course_name)
                            # Add to Ogrenci_Notlari
                            model.c.execute('''
                                INSERT INTO Ogrenci_Notlari (ogrenci_num, ders_kodu, ders_adi, harf_notu, durum, donem)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (student_num, course_code, course_name, "BA", "Geçti", f"{2024-year+past_year}-Bahar"))

                # Update Verilen_Dersler (Simple String)
                if passed_courses_list:
                    passed_str = ", ".join(passed_courses_list)
                    model.c.execute("INSERT OR REPLACE INTO Verilen_Dersler (ogrenci_num, ders_listesi) VALUES (?, ?)",
                                   (student_num, passed_str))
                
                # 2. Current Courses (Enrolled)
                # Enroll in current Fall semester courses (Year * 2 - 1)
                current_semester = year * 2 - 1
                if current_semester in curriculum:
                    for course_code, course_name in curriculum[current_semester]:
                        
                        # Check if this is a pool placeholder
                        pool_course = get_course_from_pool(course_code, dept_name)
                        if pool_course:
                            real_code, real_name = pool_course
                        else:
                            real_code, real_name = course_code, course_name
                            
                        # Add course to Dersler if not exists
                        # Schema: ders_kodu, ders_instance, ders_adi, teori_odasi, lab_odasi
                        # Primary Key is (ders_instance, ders_adi)
                        model.c.execute("INSERT OR IGNORE INTO Dersler (ders_kodu, ders_instance, ders_adi) VALUES (?, ?, ?)", 
                                      (real_code, 1, real_name))
                        
                        # Add to Ders_Sinif_Iliskisi
                        # Schema: ders_adi, ders_instance, donem_sinif_num
                        model.c.execute("INSERT OR IGNORE INTO Ders_Sinif_Iliskisi (ders_adi, ders_instance, donem_sinif_num) VALUES (?, ?, ?)", 
                                      (real_name, 1, donem_sinif_num))
                        
                        # Add to Alinan_Dersler (Transcript)
                        # Generate a random grade
                        grade_info = random.choice(GRADES)
                        grade_letter = grade_info[0]
                        status = "Geçti" if grade_letter != "FF" else "Kaldı"
                        
                        model.c.execute("INSERT INTO Ogrenci_Notlari (ogrenci_num, ders_kodu, ders_adi, harf_notu, durum, donem) VALUES (?, ?, ?, ?, ?, ?)",
                                      (student_num, real_code, real_name, grade_letter, status, f"{2024-year}-Guz"))
                        


                student_count += 1
    model.conn.commit()
    print(f"✅ Successfully created {student_count} students across {len(departments)} departments.")
    model.conn.close()

if __name__ == "__main__":
    populate()
