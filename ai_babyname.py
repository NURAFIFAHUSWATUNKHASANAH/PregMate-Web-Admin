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

Buat 10 nama bayi.

ATURAN OUTPUT KETAT:
- Tidak boleh ada penjelasan
- Tidak boleh ada markdown (``` atau **)
- Tidak boleh ada numbering
- Nama bayi HARUS minimal 2–3 kata (tidak boleh 1 kata saja)
- WAJIB format ini:

• Nama - arti

DATA:
Kategori: {category}
Gender: {gender}
Makna: {keyword}
"""

    try:
        response = model.generate_content(prompt)

        text = response.text.strip() if response.text else ""

        # 🔥 CLEAN OUTPUT (PENTING UNTUK RAILWAY)
        text = text.replace("```", "")
        text = text.replace("*", "•")

        return text

    except Exception as e:
        print("AI ERROR:", e)

        return """
• Muhammad Zaki Alfarizi - cerdas dan bijaksana
• Ahmad Rayyan Fathurrahman - penuh cahaya keberkahan
• Malik Alif Pratama - pemimpin yang adil
• Farhan Zidan Ramadhan - kebahagiaan dan ilmu
• Ilham Rizky Pratama - rezeki dan inspirasi
• Naufal Hafiz Alfarizi - penjaga yang baik
• Rayhan Daffa Alif - suci dan harum
• Zidan Malik Hakim - bijaksana dan kuat
• Hafiz Alif Pratama - pelindung kebaikan
• Azzam Pratama Hakim - tekad kuat
"""