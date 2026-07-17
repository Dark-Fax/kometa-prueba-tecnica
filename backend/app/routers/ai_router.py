from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.ai_client import generate_course_structure

router = APIRouter(prefix="/ai", tags=["AI"])

class InstructionRequest(BaseModel):
    instruction: str 

@router.post("/generate-structure")
def generate_structure(request: InstructionRequest):
    try: 
        structure = generate_course_structure(request.instruction)
        return structure
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando estructura con Gemini: {str(e)}")