from fastapi import APIRouter

router = APIRouter(prefix="/media-test", tags=["Pruebas Multimedia Integradas"])

@router.post("/ejecutar_flujo_multimedia_mejorado")
async def ejecutar_flujo_multimedia_mejorado():
    from app.services.image_service import generate_module_image
    from app.services.pdf_service import generate_module_pdf
    from app.services.audio_service import generate_module_audio
    
    title = "Estructuras de control en Python"
    desc = "Exploración en profundidad del diseño de software, patrones de arquitectura y optimización de código."
    content_sample = (
        "El desarrollo de software profesional con Python exige una comprensión sólida de cómo se gestiona "
        "la memoria y los hilos de ejecución bajo el capó. A lo largo de esta unidad, romperemos los paradigmas "
        "básicos para adentrarnos en las entrañas del lenguaje, analizando el comportamiento del Garbage Collector "
        "y los mecanismos de concurrencia.\n\n"
        "La optimización prematura es la raíz de todos los males en la ingeniería; sin embargo, diseñar código "
        "limpio, modularizado y estructurado mediante patrones de diseño creacionales y estructurales garantiza "
        "que la base de código sea escalable ante la llegada de nuevos requerimientos de negocio.\n\n"
        "Finalmente, complementaremos el estudio técnico implementando pruebas unitarias automatizadas robustas "
        "y perfiles de rendimiento (profiling) que permitan identificar cuellos de botella críticos antes de "
        "que el sistema sea desplegado en arquitecturas Cloud de producción."
    )
    
    # 1. Generamos primero la imagen con el nuevo modelo Flux
    img_path = await generate_module_image(title, desc, "prueba_mejorada.png")
    
    # 2. Generamos el PDF (el cual absorberá e incrustará automáticamente la imagen de arriba)
    pdf_path = generate_module_pdf(title, content_sample, desc, "prueba_mejorada.pdf")
    
    # 3. Generamos el Audio
    audio_path = generate_module_audio(title, content_sample, "prueba_mejorada.mp3")
    
    return {
        "status": "success",
        "pdf_generated": pdf_path,
        "image_generated": img_path,
        "audio_generated": audio_path
    }