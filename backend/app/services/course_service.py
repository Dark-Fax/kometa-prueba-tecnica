"""
Orquesta el flujo completo: IA genera estructura -> se guarda en preview (memoria) ->
al confirmar, se genera multimedia por módulo (+ portada del curso), se guarda como
BLOB en SQLite (tablas courses/modules/media), se arma el summary con base64 y
markdown convertido a HTML, y se publica en Moodle.
"""
import uuid
import base64
import os
import re
from app.db import get_connection
from app.services.ai_client import generate_course_structure
from app.services.moodle_client import moodle_client
from app.services.pdf_service import generate_module_pdf
from app.services.image_service import generate_module_image, generate_course_cover
from app.services.audio_service import generate_module_audio
from app.models.course_schema import CourseStructure


def create_generation_task(instruction: str) -> str:
    task_id = str(uuid.uuid4())
    conn = get_connection()
    conn.execute(
        "INSERT INTO tasks (id, status, instruction) VALUES (?, ?, ?)",
        (task_id, "processing", instruction),
    )
    conn.commit()
    conn.close()
    return task_id


# Cache en memoria del preview de texto (antes de confirmar, nada se persiste en
# courses/modules/media aún, tal como exige el enunciado: "nada se publica sin confirmación").
_PREVIEW_CACHE = {}


def _save_preview(task_id: str, structure: CourseStructure):
    _PREVIEW_CACHE[task_id] = structure


def get_preview(task_id: str):
    return _PREVIEW_CACHE.get(task_id)


def run_generation(task_id: str, instruction: str):
    conn = get_connection()
    try:
        structure: CourseStructure = generate_course_structure(instruction)
        _save_preview(task_id, structure)
        conn.execute(
            "UPDATE tasks SET status = ? WHERE id = ?",
            ("completed", task_id),
        )
    except Exception as e:
        conn.execute(
            "UPDATE tasks SET status = ?, error_message = ? WHERE id = ?",
            ("error", str(e), task_id),
        )
    conn.commit()
    conn.close()


def get_task(task_id: str) -> dict:
    conn = get_connection()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)


def _file_to_bytes(filepath: str) -> bytes:
    with open(filepath, "rb") as f:
        return f.read()


def _markdown_to_html_simple(text: str) -> str:
    """
    Convierte markdown básico a HTML simple para el summary de Moodle.
    Las tablas NO se renderizan aquí (se ven mal como texto plano con pipes);
    se reemplazan por una nota, ya que la tabla completa sí está en el PDF adjunto.
    """
    # Reemplaza bloques de tabla markdown por una nota simple
    text = re.sub(
        r'(\|.+\|\n)+',
        '<p style="color:#718096;font-style:italic;">📊 Consulta la tabla completa en el PDF adjunto del módulo.</p>\n',
        text
    )
    text = re.sub(
        r'```(?:\w+)?\n(.*?)```',
        r'<pre style="background:#f4f4f4;padding:10px;border-radius:4px;"><code>\1</code></pre>',
        text, flags=re.DOTALL
    )
    text = re.sub(r'^### (.+)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'^- (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    text = re.sub(r'(<li>.*</li>\n?)+', lambda m: f'<ul>{m.group(0)}</ul>', text, flags=re.DOTALL)
    text = text.replace('\n\n', '</p><p>').replace('\n', '<br/>')
    return f"<p>{text}</p>"


async def confirm_and_publish(task_id: str, options: dict = None, edited_course_data: dict = None) -> int:
    """
    Genera portada + multimedia por módulo, la guarda como BLOB en SQLite,
    arma el summary desde esos bytes (base64, con markdown convertido a HTML)
    y publica el curso real en Moodle. Único punto de escritura tanto en
    Moodle como en las tablas courses/modules/media.
    """
    task = get_task(task_id)
    if not task or task["status"] != "completed":
        raise ValueError("La tarea no existe o no está lista para publicar.")

    structure = get_preview(task_id)
    if not structure:
        raise ValueError("No se encontró el preview generado para esta tarea.")
    if edited_course_data:
        structure = CourseStructure.model_validate(edited_course_data)

    conn = get_connection()

    cover_path = await generate_course_cover(structure.course_name, structure.course_summary)
    cover_bytes = _file_to_bytes(cover_path)
    os.remove(cover_path)

    cursor = conn.execute(
        "INSERT INTO courses (task_id, fullname, shortname, course_summary, cover_image) VALUES (?, ?, ?, ?, ?)",
        (task_id, structure.course_name, f"kometa-{task_id[:8]}", structure.course_summary, cover_bytes),
    )
    course_db_id = cursor.lastrowid

    cover_b64 = base64.b64encode(cover_bytes).decode("utf-8")
    summary_html = f'<img src="data:image/png;base64,{cover_b64}" width="500" /><br/>'
    summary_html += f"<p>{structure.course_summary}</p><hr/>"

    for i, module in enumerate(structure.modules, start=1):
        cursor = conn.execute(
            "INSERT INTO modules (course_id, section_number, title, description, content) VALUES (?, ?, ?, ?, ?)",
            (course_db_id, i, module.title, module.description, module.content),
        )
        module_db_id = cursor.lastrowid

        safe_prefix = f"modulo_{i}"
        img_path = await generate_module_image(module.title, module.description, f"{safe_prefix}.png")
        pdf_path = generate_module_pdf(module.title, module.content, module.description, f"{safe_prefix}.pdf")
        audio_path = generate_module_audio(module.title, module.content, f"{safe_prefix}.mp3")

        img_bytes = _file_to_bytes(img_path)
        pdf_bytes = _file_to_bytes(pdf_path)
        audio_bytes = _file_to_bytes(audio_path)

        conn.execute(
            "INSERT INTO media (module_id, media_type, filename, mimetype, data) VALUES (?, ?, ?, ?, ?)",
            (module_db_id, "image", f"{safe_prefix}.png", "image/png", img_bytes),
        )
        conn.execute(
            "INSERT INTO media (module_id, media_type, filename, mimetype, data) VALUES (?, ?, ?, ?, ?)",
            (module_db_id, "pdf", f"{safe_prefix}.pdf", "application/pdf", pdf_bytes),
        )
        conn.execute(
            "INSERT INTO media (module_id, media_type, filename, mimetype, data) VALUES (?, ?, ?, ?, ?)",
            (module_db_id, "audio", f"{safe_prefix}.mp3", "audio/mpeg", audio_bytes),
        )

        os.remove(img_path)
        os.remove(pdf_path)
        os.remove(audio_path)

        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        summary_html += f'<div style="border:2px solid #DD6B20;border-radius:8px;padding:20px;margin:20px 0;background:#FFFAF5;">'
        summary_html += f'<div style="display:inline-block;background:#1A365D;color:white;padding:4px 12px;border-radius:4px;font-size:12px;font-weight:bold;margin-bottom:10px;">MÓDULO {i}</div>'
        summary_html += f"<h3 style='color:#1A365D;margin-top:8px;'>{module.title}</h3>"
        summary_html += f"<p><em>{module.description}</em></p>"
        summary_html += f'<img src="data:image/png;base64,{img_b64}" width="400" /><br/>'
        summary_html += _markdown_to_html_simple(module.content)
        summary_html += f'<p><a href="data:application/pdf;base64,{pdf_b64}" download="modulo_{i}.pdf">📄 Descargar PDF del módulo</a></p>'
        summary_html += f'<p><audio controls src="data:audio/mpeg;base64,{audio_b64}"></audio></p>'
        summary_html += "</div>"

    shortname = f"kometa-{task_id[:8]}"
    result = await moodle_client.create_course(
        fullname=structure.course_name,
        shortname=shortname,
        summary=summary_html,
    )
    moodle_course_id = result[0]["id"] if isinstance(result, list) else result["id"]

    conn.execute("UPDATE courses SET moodle_course_id = ? WHERE id = ?", (moodle_course_id, course_db_id))
    conn.commit()
    conn.close()

    return moodle_course_id


def list_courses() -> list:
    """Lista los cursos ya publicados, con portada en base64, para el panel de 'cursos recientes'."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT c.id, c.moodle_course_id, c.fullname, c.course_summary, c.cover_image,
                        (SELECT COUNT(*) FROM modules WHERE course_id = c.id) as module_count
                        FROM courses c ORDER BY c.created_at DESC
                        """).fetchall()
    conn.close()
    result = []
    for r in rows:
        cover_b64 = base64.b64encode(r["cover_image"]).decode("utf-8") if r["cover_image"] else None
        result.append({
            "id": r["id"],
            "moodle_course_id": r["moodle_course_id"],
            "fullname": r["fullname"],
            "course_summary": r["course_summary"],
            "module_count": r["module_count"],
            "cover_base64": cover_b64,
        })
    return result


async def delete_course(course_db_id: int):
    """Elimina un curso tanto de Moodle como de la BD local (courses/modules/media)."""
    conn = get_connection()
    row = conn.execute("SELECT moodle_course_id FROM courses WHERE id = ?", (course_db_id,)).fetchone()
    if not row:
        conn.close()
        raise ValueError("Curso no encontrado.")

    if row["moodle_course_id"]:
        await moodle_client.delete_courses([row["moodle_course_id"]])

    module_ids = [m["id"] for m in conn.execute("SELECT id FROM modules WHERE course_id = ?", (course_db_id,)).fetchall()]
    for mid in module_ids:
        conn.execute("DELETE FROM media WHERE module_id = ?", (mid,))
    conn.execute("DELETE FROM modules WHERE course_id = ?", (course_db_id,))
    conn.execute("DELETE FROM courses WHERE id = ?", (course_db_id,))
    conn.commit()
    conn.close()