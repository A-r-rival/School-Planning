
import pypdf
import os

file_path = os.path.join("A. Donem 1 Rapor", "OTOMATİK ÜNIVERSITE DERS PROGRAMI OLUŞTURMA SİSTEMİ.pdf")

try:
    reader = pypdf.PdfReader(file_path)
    with open("report_pdf_content.txt", "w", encoding="utf-8") as f:
        f.write(f"Reading PDF file: {file_path}\n\n")
        f.write("-" * 50 + "\n")
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                f.write(f"--- PAGE {i+1} ---\n")
                f.write(text + "\n\n")
                
    print("Successfully wrote PDF content to report_pdf_content.txt")
        
except Exception as e:
    print(f"Error reading PDF: {e}")
