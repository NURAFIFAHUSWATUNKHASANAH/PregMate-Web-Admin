from flask import jsonify, request
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-flash-lite-latest")


def generate_baby_name(keyword, category, gender):

    prompt = f"""
Anda adalah ahli pemberi nama bayi profesional.

Buatkan 10 rekomendasi nama bayi.

Kriteria:
Kategori: {category}
Jenis kelamin: {gender}
Kata kunci / makna / deskripsi: {keyword}

CATATAN PENTING:
Keyword bisa berupa 1 kata atau kalimat panjang (contoh: "seorang yang pandai dan bijaksana").
Pahami keyword sebagai MAKNA atau KONSEP utama, bukan sekadar kata.

LANGKAH BERPIKIR (WAJIB DIIKUTI):
1. Identifikasi makna inti dari keyword
2. Ubah makna inti menjadi maksimal 1–2 sifat utama (adjective)
3. Cari nama yang sesuai dengan sifat tersebut
4. Pastikan arti nama SELALU konsisten dengan sifat yang dipilih

ATURAN KETAT:
- WAJIB: Nama harus memiliki hubungan langsung dengan keyword
- WAJIB: Arti nama harus sesuai dengan sifat dari keyword
- WAJIB: Nama bayi HARUS minimal 2–3 kata (tidak boleh 1 kata saja)
- WAJIB: Nama harus terdengar seperti nama manusia asli (natural & realistis)
- JANGAN membuat nama yang tidak berhubungan dengan makna
- Jika keyword abstrak, pecah hanya menjadi maksimal 2 sifat utama saja
- Gunakan bahasa Indonesia / Islami / modern yang umum dipakai
- Tidak boleh menambahkan cerita atau penjelasan tambahan
- Tidak boleh keluar dari konteks makna keyword

❌ JANGAN:
- Jangan membuat arti yang tidak sesuai keyword
- Jangan mengarang filosofi tambahan
- Jangan menambahkan penjelasan panjang
- Jangan keluar dari kategori makna keyword

FORMAT WAJIB (TIDAK BOLEH DIUBAH):

Nama Bayi
• Nama - arti
• Nama - arti
• Nama - arti
• Nama - arti
• Nama - arti
• Nama - arti
• Nama - arti
• Nama - arti
• Nama - arti
• Nama - arti
"""

    try:
        response = model.generate_content(prompt)

        if response.text:
            return response.text.strip()

        return "Tidak ada rekomendasi nama"

    except Exception as e:
        print("AI ERROR:", e)

        return """
Nama Bayi
• Muhammad Zaki Alfarizi - cerdas dan penuh ilmu
• Ahmad Rayyan Fathurrahman - pembawa keberkahan
• Azzam Pratama Hakim - bertekad kuat dan bijaksana
• Malik Alif Prasetyo - pemimpin yang adil
• Farhan Zaki Ramadhan - bahagia dan cerdas
• Ilham Rizky Pratama - inspirasi rezeki
• Naufal Fathir Alfarizi - dermawan dan berilmu
• Rayhan Daffa Alif - harum dan suci
• Zidan Malik Ramadhan - pertumbuhan dan kepemimpinan
• Hafiz Alif Pratama - penjaga yang baik
"""