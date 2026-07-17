from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.models.task_schema import GenerateRequest, TaskResponse
from app.services import course_service
from app.services import chat_service
from app.models.course_schema import CourseStructure
from app.models.task_schema import ChatRequest, ChatResponse


router = APIRouter(prefix="/courses", tags=["Courses"])

@router.post("/generate", response_model=TaskResponse)
def generate(request: GenerateRequest, background_tasks: BackgroundTasks):
    task_id = course_service.create_generation_task(request.instruction)
    background_tasks.add_task(course_service.run_generation, task_id, request.instruction)
    return TaskResponse(task_id=task_id, status="processing")

@router.get("/status/{task_id}", response_model=TaskResponse)
def status(task_id: str):
    task = course_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    course_data = course_service.get_preview(task_id)

    return TaskResponse(
        task_id=task["id"],
        status=task["status"],
        course_data=course_data,
        moodle_course_id=None,
        error_message=task["error_message"],
    )

@router.post("/confirm/{task_id}")
async def confirm(task_id: str):
    try:
        course_id = await course_service.confirm_and_publish(task_id)
        return {"published": True, "moodle_course_id": course_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/{task_id}/chat", response_model=ChatResponse)
def chat(task_id: str, request: ChatRequest):
    try:
        answer = chat_service.answer_course_question(task_id, request.question)
        return ChatResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))