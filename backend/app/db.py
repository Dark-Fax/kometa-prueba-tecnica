"""
Esquema normalizado: cursos, módulos y archivos multimedia (como BLOB),
en vez de guardar todo en tasks.course_data (JSON) y archivos locales.
"""
import sqlite3
from app.config import settings


def get_connection():
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            instruction TEXT NOT NULL,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            moodle_course_id INTEGER,
            fullname TEXT NOT NULL,
            shortname TEXT NOT NULL,
            course_summary TEXT,
            cover_image BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS modules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            section_number INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            content TEXT,
            FOREIGN KEY (course_id) REFERENCES courses(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_id INTEGER NOT NULL,
            media_type TEXT NOT NULL,      -- 'image' | 'pdf' | 'audio'
            filename TEXT NOT NULL,
            mimetype TEXT NOT NULL,
            data BLOB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (module_id) REFERENCES modules(id)
        )
    """)

    conn.commit()
    conn.close()