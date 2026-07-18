import os
import httpx
from urllib.parse import quote
from app.services.ai_client import client as groq_client

OUTPUT_DIR = "generated_files"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def build_image_prompt(module_title: str, module_description: str) -> str:
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": (
                "Convierte el título y descripción de un módulo educativo en un prompt corto en INGLÉS "
                "para generar una ilustración 3D isométrica minimalista relacionada al tema específico. "
                "Menciona objetos/iconos concretos del tema (no genéricos). Máximo 25 palabras. "
                "Responde SOLO el prompt, sin comillas ni explicación."
            )},
            {"role": "user", "content": f"Título: {module_title}\nDescripción: {module_description}"},
        ],
        temperature=0.6,
    )
    return response.choices[0].message.content.strip()


async def generate_module_image(module_title: str, module_description: str, filename: str) -> str:
    specific_element = build_image_prompt(module_title, module_description)

    raw_prompt = (
        f"A clean minimalist 3D isometric icon of {specific_element}. "
        "Vibrant corporate colors, isolated on a solid pristine studio white background, "
        "professional tech corporate design, high resolution, no text, no words"
    )

    encoded_prompt = quote(raw_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=768&height=512&nologo=true&model=flux"
    filepath = os.path.join(OUTPUT_DIR, filename)

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(url)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(response.content)

    return filepath

async def generate_course_cover(course_name: str, course_summary: str) -> str:
    """Genera una portada única para el curso completo (distinta de las imágenes por módulo)."""
    specific_element = build_image_prompt(course_name, course_summary)
    raw_prompt = (
        f"A bold minimalist book cover illustration representing {specific_element}. "
        "Flat vector style, vibrant single accent color, clean composition, no text, no words"
    )
    encoded_prompt = quote(raw_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=500&height=350&nologo=true&model=flux"
    filepath = os.path.join(OUTPUT_DIR, "cover.png")
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(url)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(response.content)
    return filepath