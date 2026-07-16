from fastapi import APIRouter, HTTPException, status 
from app.services.moodle_client import moodle_client

router = APIRouter(prefix="/moodle", tags=["Moodle"])

@router.get("/prueba_conexion")
async def prueba_conexion():
    try: 
        site_info = await moodle_client.get_site_info()
        return {
            "connected": True,
            "site_info": site_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error conectando a Moodle: {str(e)}")
    
@router.post("/prueba_crear_curso")
async def prueba_crear_curso():
    try: 
        # Se crea un curso de prueba en Moodle
        course_data = await moodle_client.create_course(
            fullname="Curso de Prueba",
            shortname="KOMETA-PRUEBA"
        )
        if isinstance(course_data, list) and len(course_data) > 0:
            return {
                "created": True,
                "course_id": course_data[0]["id"]
            }
        return {"created": False, "raw_response": course_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando el curso: {str(e)}")

    #PRUEBAS
    # Agregar estos endpoints al final de backend/app/routers/moodle_router.py

@router.get("/get_contents/{course_id}")
async def get_contents(course_id: int):
    """
    Endpoint para obtener la estructura real del curso y extraer los IDs de base de datos de las secciones.
    """
    try:
        contents = await moodle_client.get_course_contents(course_id)
        return {
            "success": True,
            "contents": contents
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo contenidos: {str(e)}")

@router.post("/prueba_upload/{filename}")
async def prueba_upload(filename: str):
    """
    Prueba de subida utilizando un archivo local de la carpeta test_files.
    """
    try:
        # 1. Llamamos al cliente de Moodle pasando la ruta del archivo y su nombre.
        # Ahora 'result' contiene el diccionario limpio con los datos del archivo.
        result = await moodle_client.upload_file(
            filepath=f"test_files/{filename}",
            filename=filename
        )
        
        # 2. Retornamos una respuesta estructurada.
        # .get("itemid") extrae el número identificador de forma segura.
        return {
            "uploaded": True, 
            "itemid": result.get("itemid"), 
            "details": result
        }
        
    except Exception as e:
        # Si algo falla (archivo no existe, token inválido, etc.), lanzamos un error 500.
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/limpiar_cursos_prueba")
async def limpiar_cursos_prueba():
    """
    Elimina todos los cursos excepto el curso 1 (Site home, no es un curso real).
    Útil solo durante desarrollo — no forma parte del flujo de producción.
    """
    try:
        courses = await moodle_client._make_requests("core_course_get_courses")
        ids_to_delete = [c["id"] for c in courses if c["id"] != 1]
        if not ids_to_delete:
            return {"deleted": 0, "message": "No hay cursos para eliminar."}
        result = await moodle_client.delete_courses(ids_to_delete)
        return {"deleted": len(ids_to_delete), "ids": ids_to_delete, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))