import os
from gtts import gTTS
from app.services.ai_client import client as groq_client

OUTPUT_DIR = "generated_files"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_podcast_script(module_title: str, module_content: str) -> str:
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un guionista de podcasts educativos. Convierte el contenido dado en un guion breve, "
                    "natural y hablado en español, de 100-150 palabras, como si un profesor lo explicara en audio. "
                    "Es mandatorio que el guion mencione explícitamente 2 o 3 conceptos concretos del contenido del módulo. " # ◄— NUEVO
                    "Responde SOLO con el guion, sin acotaciones ni formato adicional."
                ),
            },
            {"role": "user", "content": f"Módulo: {module_title}\n\nContenido: {module_content}"},
        ],
        temperature=0.5,
    )
    return response.choices[0].message.content

def generate_module_audio(module_title: str, module_content: str, filename: str) -> str:
    script = generate_podcast_script(module_title, module_content)
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    # ◄— CAMBIO AQUÍ: Se añade tld="com.mx" para entonación mexicana/latina más fluida
    tts = gTTS(text=script, lang="es", tld="com.mx", slow=False)
    tts.save(filepath)
    return filepath