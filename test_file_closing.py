import time
import os

print("=== TEST 1: Kapatmadan veri yazma ===")

# KAPATMADAN
f1 = open('test_no_close.txt', 'w')
f1.write("Bu mesaj belki yazılır, belki yazılmaz!")
# NOT: Kapatmıyoruz!

print("✓ Dosya açıldı ve yazıldı (teoride)")
print("  Dosya boyutu:", os.path.getsize('test_no_close.txt') if os.path.exists('test_no_close.txt') else "Henüz yok!")

# Bekle
time.sleep(1)

print("\n=== TEST 2: Flush ile zorla ===")
f1.flush()  # Buffer'ı diske yaz
print("✓ flush() çağrıldı")
print("  Dosya boyutu:", os.path.getsize('test_no_close.txt'))

print("\n=== TEST 3: Dosyayı kapat ===")
f1.close()
print("✓ Dosya kapatıldı")
print("  Dosya boyutu:", os.path.getsize('test_no_close.txt'))

print("\n=== TEST 4: with kullanarak ===")
with open('test_with_close.txt', 'w') as f2:
    f2.write("Bu mesaj KESIN yazılır!")
    
print("✓ with bloğu bitti")
print("  Dosya boyutu:", os.path.getsize('test_with_close.txt'))

print("\n=== TEST 5: Çok dosya açma ===")
files = []
try:
    for i in range(2000):
        f = open(f'test_leak_{i}.txt', 'w')
        files.append(f)
        if i % 500 == 0:
            print(f"Açılan dosya sayısı: {i}")
except Exception as e:
    print(f"❌ HATA (dosya #{i}): {e}")
    
print(f"Toplam açık dosya: {len(files)}")

# Temizlik
for f in files:
    f.close()
    
# Test dosyalarını sil
import glob
for f in glob.glob("test_*.txt"):
    os.remove(f)
    
print("\n✓ Temizlik tamamlandı")
