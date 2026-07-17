"""
Chat de dudas sobre un curso ya publicado en Moodle. Responde basándose
ÚNICAMENTE en el contenido real almacenado en las tablas courses/modules
(no en respuestas genéricas).
"""
from app.services.ai_client import client as groq_client
from app.db import get_connection


def answer_course_question(task_id: str, question: str) -> str:
    conn = get_connection()
    course = conn.execute("SELECT * FROM courses WHERE task_id = ?", (task_id,)).fetchone()
    if not course:
        conn.close()
        raise ValueError("El curso no existe o aún no se ha publicado.")

    modules = conn.execute(
        "SELECT * FROM modules WHERE course_id = ? ORDER BY section_number", (course["id"],)
    ).fetchall()
    conn.close()

    context = f"Curso: {course['fullname']}\nResumen: {course['course_summary']}\n\n"
    for m in modules:
        context += f"Módulo {m['section_number']}: {m['title']}\n{m['description']}\n{m['content']}\n\n"

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un asistente que responde preguntas sobre un curso específico. "
                    "Responde ÚNICAMENTE basándote en el contenido proporcionado abajo. "
                    "Si la pregunta no puede responderse con ese contenido, dilo explícitamente "
                    "en vez de inventar información.\n\n"
                    f"CONTENIDO DEL CURSO:\n{context}"
                ),
            },
            {"role": "user", "content": question},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content