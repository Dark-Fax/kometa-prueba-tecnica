"""
Chat de dudas sobre un curso ya publicado en Moodle. Responde basándose
ÚNICAMENTE en el contenido real almacenado en las tablas courses/modules
(no en respuestas genéricas).
"""
from app.services.ai_client import client as groq_client
from app.db import get_connection


def answer_course_question(task_id: str, question: str, history: list = None) -> str:
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

    messages = [
        {
            "role": "system",
            "content": (
                "Eres un asistente que responde preguntas sobre un curso específico. "
                "Responde ÚNICAMENTE basándote en el contenido proporcionado abajo. "
                "Si la pregunta no puede responderse con ese contenido, dilo explícitamente. "
                "Usa formato markdown en tus respuestas: **negrita**, listas con '-', "
                "tablas markdown (| col | col |) cuando compares datos, saltos de línea entre preguntas de un quiz.\n\n"
                f"CONTENIDO DEL CURSO:\n{context}"
            ),
        }
    ]

    if history:
        for turn in history[-6:]:  # últimos 3 intercambios, evita prompt gigante
            messages.append({"role": "user", "content": turn.get("question", "")})
            messages.append({"role": "assistant", "content": turn.get("answer", "")})

    messages.append({"role": "user", "content": question})

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0.3,
    )
    return response.choices[0].message.content