import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-flash-lite-latest")

def generate_recommendation(energi, mual, nyeri, tidur, nafsu_makan):

    prompt = f"""
        Anda adalah asisten kesehatan untuk ibu hamil.

        Analisis kondisi berikut:

        Energi (kondisi tubuh): {energi}/10
        Mual: {mual}/10
        Nyeri tubuh: {nyeri}/10
        Kualitas tidur: {tidur}/10
        Nafsu makan: {nafsu_makan}/10

        Berikan kesimpulan dan rekomendasi sederhana untuk ibu hamil.

        Format WAJIB:

        ANALISIS SINGKAT:
        1-2 kalimat ringkas menggambarkan kondisi ibu (contoh: kondisi cukup baik, namun ada keluhan ringan)

        Nutrisi
        • makanan 1
        • makanan 2
        • makanan 3
        • makanan 4

        Aktivitas
        • aktivitas 1
        • aktivitas 2

        Relaksasi
        • relaksasi 1
        • relaksasi 2

        Aturan:
        - Gunakan bahasa Indonesia
        - Jangan panjang (maks 2 kalimat untuk analisis)
        - Gunakan bahasa yang lembut dan empatik
        - Fokus pada ibu hamil
        - Hanya bullet point (kecuali analisis)
        """

    try:

        response = model.generate_content(prompt)

        if response.text:
            return response.text.strip()

        return "Tidak ada rekomendasi dari AI"

    except Exception as e:

        print("AI ERROR:", e)

        return """
            ANALISIS SINGKAT:
            Kondisi bunda cukup baik, namun tetap perlu menjaga pola makan dan istirahat.

            Nutrisi
            • Oatmeal dengan pisang
            • Sup sayur hangat
            • Yogurt dengan buah
            • Jus jeruk segar

            Aktivitas
            • Jalan santai 10 menit
            • Peregangan ringan

            Relaksasi
            • Latihan pernapasan
            • Dengarkan musik relaksasi
            """