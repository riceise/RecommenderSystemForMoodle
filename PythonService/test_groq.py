import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def test_groq_qwen():
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    try:
        response = client.chat.completions.create(
            model="qwen/qwen3-32b", 
            messages=[
                {"role": "system", "content": "Ты полезный ассистент с доступом к актуальным знаниям."},
                {"role": "user", "content": "Расскажи о последних новостях в мире ИИ за начало 2026 года."}
            ],
            temperature=0.6,
            max_tokens=500,
            response_format={"type": "json_object"}  

        )
        print("✅ Groq работает!")
        print("-" * 30)
        print("Ответ:", response.choices[0].message.content)
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    test_groq_qwen()