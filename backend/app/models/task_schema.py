from pydantic import BaseModel
from typing import Optional
from app.models.course_schema import CourseStructure

class GenerateRequest(BaseModel):
    instruction: str

class TaskResponse(BaseModel):
    task_id: str 
    status: str
    course_data: Optional[CourseStructure] = None
    moodle_course_id: Optional[int] = None
    error_message: Optional[str] = None 

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str