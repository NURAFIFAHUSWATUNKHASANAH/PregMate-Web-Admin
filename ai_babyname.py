from google import genai
import os

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_baby_name(keyword, category, gender):

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=f"""
Buat 5 nama bayi.

Kategori: {category}
Gender: {gender}
Makna: {keyword}

Format:
Nama - arti
""",
            config={
                "temperature": 0.6,
                "max_output_tokens": 300
            }
        )

        if not response.text:
            return fallback_babyname()

        return response.text.strip()

    except Exception as e:
        print("GEMINI ERROR:", e)
        return fallback_babyname()


def fallback_babyname():
    return """
Nama Bayi
• Muhammad Zaki - cerdas
• Ahmad Rayyan - bercahaya
• Azzam Malik - kuat
• Rayhan Fikri - bijaksana
• Naufal Ilham - inspiratif
"""