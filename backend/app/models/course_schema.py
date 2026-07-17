from pydantic import BaseModel, Field
from typing import List

class ModuleContent(BaseModel):
    title: str = Field(description="Título del módulo")
    description: str = Field(description="Descripción breve del módulo")
    content: str = Field(description="Contenido explicativo extenso del módulo (300-500 palabras)")

class CourseStructure(BaseModel):
    course_name: str = Field(description="Nombre completo del curso")
    course_summary: str = Field(description="Resumen del curso, 2-3 frases")
    modules: List[ModuleContent] = Field(description="Lista de módulos/secciones del curso")