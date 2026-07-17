import logging
import os
import time
from groq import Groq, APIStatusError, APIConnectionError
from app.config import settings
from app.models.course_schema import CourseStructure

# Configuración del registrador estándar de Python
logger = logging.getLogger("app.services.ai_client")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

logger.info("Inicializando cliente de servicios de Groq Cloud...")

try:
    # Verificamos la existencia de la API Key en las configuraciones compartidas
    if not getattr(settings, "GROQ_API_KEY", None):
        logger.error("La variable de entorno GROQ_API_KEY no se encuentra configurada en las configuraciones base.")
        client = None
    else:
        # Inicialización del cliente oficial de Groq
        client = Groq(api_key=settings.GROQ_API_KEY)
        logger.info("Cliente de Groq Cloud inicializado correctamente.")
except Exception as e:
    logger.critical(f"Fallo crítico al instanciar el cliente de Groq: {str(e)}")
    client = None

def generate_course_structure(instruction: str) -> CourseStructure:
    """
    Recibe una instrucción en lenguaje natural y genera una estructura de curso
    homologada bajo el esquema de validación estricta de CourseStructure (Pydantic).
    
    Implementa un mecanismo defensivo de reintentos automáticos ante errores 429 (Rate Limits).
    """
    if client is None:
        logger.error("Operación abortada: El cliente de Groq Cloud no está inicializado.")
        raise RuntimeError("El cliente de IA no se encuentra disponible.")

    # Selección de modelo optimizado para texto estructurado y velocidad en Groq
    target_model = "llama-3.3-70b-versatile" 

    logger.info("Iniciando proceso de generación de estructura del curso vía Groq.")
    logger.info(f"Instrucción de entrada: '{instruction}'")
    logger.info(f"Modelo seleccionado: '{target_model}'")

    # Configuración de políticas de resiliencia
    max_retries = 3
    retry_delay = 4  # Tiempo base de espera en segundos

    for attempt in range(max_retries):
        try:
            # Invocación al servicio de chat completions con restricción de formato estructurado
            response = client.chat.completions.create(
                model=target_model,
                messages=[
                    {
                        "role": "system", 
                        "content": (
                            "Eres un diseñador instruccional experto para la plataforma Kometa. "
                            "Tu tarea es generar estructuras de cursos altamente coherentes y organizadas en ESPAÑOL. "
                            "Debes responder EXCLUSIVAMENTE con un objeto JSON válido. "
                            "Es mandatorio que las llaves (keys) del JSON estén estrictamente en INGLÉS y coincidan con este molde:\n\n"
                            "{\n"
                            "  \"course_name\": \"Nombre del curso en español\",\n"
                            "  \"course_summary\": \"Resumen general del curso en español\",\n"
                            "  \"modules\": [\n"
                            "    {\n"
                            "      \"title\": \"Título del Módulo 1 en español\",\n"
                            "      \"description\": \"Descripción breve en español\",\n"
                            "      \"content\": \"Contenido desarrollado y extenso del módulo en español\"\n"
                            "    }\n"
                            "  ]\n"
                            "}\n\n"
                            "No agregues texto aclaratorio, introductorio ni bloques de código Markdown (```json)."
                        )
                    },
                    {"role": "user", "content": f"Genera la estructura educativa para la siguiente solicitud: {instruction}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )

            logger.info("Conexión con Groq Cloud establecida de manera exitosa.")
            
            # Recuperación del contenido crudo en formato String JSON
            json_payload = response.choices[0].message.content
            
            # Validación y parseo explícito contra el modelo de Pydantic
            parsed_structure = CourseStructure.model_validate_json(json_payload)
            
            logger.info("Estructura de curso validada y parseada exitosamente contra el esquema CourseStructure.")
            return parsed_structure

        except APIStatusError as status_err:
            # Intercepción específica para códigos de sobrecarga de cuotas (Rate Limits)
            if status_err.status_code == 429:
                if attempt < max_retries - 1:
                    sleep_time = retry_delay * (attempt + 1)
                    logger.warning(f"Error 429 (Rate Limit) detectado en Groq. Reintentando en {sleep_time}s... (Intento {attempt + 1}/{max_retries})")
                    time.sleep(sleep_time)
                    continue
            logger.error(f"Error de estado HTTP reportado por Groq (Código {status_err.status_code}): {status_err.message}")
            raise status_err
            
        except APIConnectionError as conn_err:
            logger.error(f"Fallo de conectividad de red con los servidores de Groq: {str(conn_err)}")
            raise conn_err
            
        except Exception as e:
            logger.error(f"Excepción inesperada durante el procesamiento del JSON o la validación Pydantic: {str(e)}")
            raise e