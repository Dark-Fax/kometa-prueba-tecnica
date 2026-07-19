# Kometa — Generador de Cursos con IA sobre Moodle

Aplicación fullstack que, a partir de una instrucción en lenguaje natural, genera con IA la estructura completa de un curso (texto, imagen, PDF y podcast por módulo) y lo publica en una instancia local de Moodle vía su API REST.

## Stack

- **Backend:** FastAPI (Python), async con `httpx` para la integración con Moodle.
- **IA de texto:** Groq (`llama-3.1-8b-instant` / `llama-3.3-70b-versatile`), Structured Outputs vía JSON Schema + Pydantic.
- **IA de imagen:** Pollinations.ai (gratuito, sin API key), con prompt generado dinámicamente por IA a partir de cada módulo.
- **PDF:** ReportLab, con parser propio de markdown básico (encabezados, negrita, código, listas, tablas).
- **Audio:** guion generado por Groq + conversión a voz con `gTTS`.
- **Base de datos interna:** SQLite, esquema normalizado (`tasks`, `courses`, `modules`, `media`), archivos multimedia guardados como BLOB.
- **Moodle:** 4.4.4 LTS, vía Docker Compose (`bitnamilegacy/moodle:4.4` + `mariadb:10.11`).
- **Frontend:** HTML + Alpine.js + Tailwind CSS (CDN, sin build step), separado en shell + partials + CSS + JS.

---

## Cómo levantar el proyecto desde cero

### Requisitos previos
- Docker y Docker Compose instalados.
- Python 3.11+ instalado, con `pip`.
- Una extensión de servidor local para el frontend (recomendado: **Live Server** de VSCode).
- Una cuenta gratuita en Groq Cloud (console.groq.com) para obtener una API key.

### 1. Levantar Moodle local (Docker)

Desde la raíz del repositorio:
```bash
docker compose up -d
```

Esto levanta dos contenedores:
- `moodle_db`: MariaDB 10.11.
- `moodle_app`: Moodle 4.4, expuesto en `http://localhost:8080`.

El primer arranque tarda entre 2 y 5 minutos (Moodle se instala solo). Verifica el progreso con:
```bash
docker compose logs -f moodle
```

Una vez arriba, entra a `http://localhost:8080` y confirma que carga el sitio. Credenciales por defecto definidas en `docker-compose.yml`:
- Usuario: `admin`
- Contraseña: `Admin123!`

### 2. Habilitar Web Services y generar un token

Dentro de Moodle, como administrador:

1. **Site administration → Server → Web services → Enable web services** (activar).
2. **Site administration → Server → Web services → Manage protocols → REST protocol** (activar).
3. **Site administration → Server → Web services → External services**: crea un servicio externo personalizado (ej. "Kometa API") y agrégale las siguientes funciones — son las únicas que la aplicación necesita y las únicas que confirmé como funcionales en Moodle 4.4 core (ver sección de limitaciones más abajo):
   - `core_course_create_courses`
   - `core_course_get_contents`
   - `core_course_get_courses`
   - `core_webservice_get_site_info`
   - `core_files_upload`
   - `core_course_delete_courses`
4. **Site administration → Server → Web services → Manage tokens**: crea un token para el usuario admin, asociado al servicio creado en el paso anterior. Copia ese token.

### 3. Configurar el backend

```bash
cd backend
python -m venv venv
```

Activa el entorno virtual:
- Windows (PowerShell): `venv\Scripts\activate`
- macOS/Linux: `source venv/bin/activate`

Instala dependencias:
```bash
pip install -r requirements.txt
```

Crea el archivo `.env` en `backend/` (usa `.env.example` como plantilla) con tus credenciales reales:
```
MOODLE_API_URL=http://localhost:8080/webservice/rest/server.php
MOODLE_TOKEN=el_token_que_generaste_en_el_paso_2
GROQ_API_KEY=tu_api_key_de_groq
DATABASE_PATH=tasks.db
```

Levanta el servidor:
```bash
uvicorn app.main:app --reload --port 8000
```

Verifica que responde correctamente:
- `http://localhost:8000/health` → debe devolver `{"status": "ok"}`.
- `http://localhost:8000/docs` → Swagger UI con todos los endpoints disponibles.
- `http://localhost:8000/moodle/prueba_conexion` → confirma que el token es válido y la conexión con Moodle funciona.

### 4. Levantar el frontend

El frontend es HTML + Alpine.js + Tailwind puro, sin build step, pero **necesita ser servido por un servidor HTTP local** (no abrir el `index.html` directo con doble clic), porque carga las pantallas (`partials/*.html`) dinámicamente vía `fetch()`, y eso falla bajo el protocolo `file://` por restricciones de CORS del navegador.

**Opción recomendada — Live Server (VSCode):**
1. Instala la extensión "Live Server" en VSCode si no la tienes.
2. Abre la carpeta `frontend/` en VSCode.
3. Clic derecho sobre `index.html` → **"Open with Live Server"**.
4. Se abrirá automáticamente en algo como `http://127.0.0.1:5500/index.html`.

**Opción alternativa — servidor HTTP de Python:**
```bash
cd frontend
python -m http.server 5500
```
Y abre `http://localhost:5500` en el navegador.

Con el backend (`localhost:8000`), Moodle (`localhost:8080`) y el frontend (`localhost:5500` o similar) corriendo simultáneamente, la aplicación queda completamente funcional.

### 5. Verificación del flujo completo

1. En el frontend, escribe una instrucción (ej. *"crea un curso de Excel intermedio con 4 módulos"*) y confirma.
2. Espera la generación de la estructura (10-20 segundos) → debe mostrar la vista previa con los módulos.
3. Opcionalmente, edita el título, resumen o contenido de algún módulo antes de confirmar.
4. Click en "Confirmar y Publicar en Moodle" → este paso genera imagen, PDF y audio por cada módulo, y tarda entre 30 y 90 segundos (no cierres la ventana).
5. Al terminar, verás un enlace directo al curso real creado en Moodle, y un chat habilitado para hacer preguntas sobre el contenido generado.
6. En el sidebar, la lista de "cursos recientes" permite volver a ver un curso publicado (te lleva a Moodle) o eliminarlo (borra tanto de Moodle como de la base de datos local).

---

## Decisiones técnicas y limitaciones documentadas

Esta sección explica el *por qué* detrás de las decisiones más importantes, con foco en lo que no salió como esperaba al principio y cómo lo resolví.

### Elección y cambios de proveedor de IA

Probé tres proveedores en orden, y documento cada cambio con la causa real:

1. **OpenAI (GPT):** lo descarté por costo — Structured Outputs de forma sostenida requiere plan de pago.
2. **Google Gemini:** lo descarté tras un fallo reproducible de cuota. El plan gratuito devolvió `RESOURCE_EXHAUSTED` con `limit: 0` para `gemini-2.0-flash` desde la primera petición real, no por acumulación de uso.
3. **Groq (`llama-3.1-8b-instant`, luego `llama-3.3-70b-versatile` para instrucciones más complejas):** el proveedor con el que me quedé. Gratuito, rápido, soporta salida JSON estructurada. Implementé manejo explícito de reintentos con backoff exponencial ante error 429 (rate limit) **y** ante `json_validate_failed` (el modelo a veces trunca el JSON en instrucciones que combinan código + tablas + muchos módulos).

### Limitación central: creación de actividades/secciones vía Web Services de Moodle 4.4

Este fue el hallazgo técnico más importante del proyecto, y el que terminó definiendo la arquitectura de publicación de contenido. Lo documento con detalle porque me tomó tres intentos independientes confirmar que era una limitación real de la plataforma, no un error mío:

**Intento 1 — `core_course_add_module`:** no existe como función de webservice en Moodle 4.4 core. Lo confirmé con un `dml_missing_record_exception` al intentar habilitarla — la función ni siquiera está registrada en la tabla `external_functions` de la base de datos, es decir, no es un problema de permisos sino que simplemente no está expuesta vía API en esta versión.

**Intento 2 — `core_course_edit_section` / `core_courseformat_update_course`:** según la documentación oficial de Moodle, `core_course_edit_section` solo acepta acciones de tipo `hide`, `show`, `stealth`, `setmarker`, `removemarker` — nunca soportó edición de nombre o contenido de sección, pese a lo que su nombre sugiere. Su reemplazo aparente, `core_courseformat_update_course`, resultó ser un endpoint interno usado por el editor AJAX de la interfaz web de Moodle, sin contrato estable ni documentación pública para uso externo — lo descarté tras confirmar errores de parámetros no resueltos incluso alineando la firma con el código fuente de Moodle.

**Intento 3 — `mod_label_add_instance` / `mod_resource_add_instance`:** mismo resultado que el intento 1. Son funciones internas de PHP (las usa Moodle cuando se guarda un formulario desde la interfaz web), no funciones de webservice expuestas — no aparecen en `external_functions` y no son invocables vía `webservice/rest/server.php`.

**Lo que terminé haciendo:** consolidar todo el contenido generado (texto de cada módulo, imagen, enlace de descarga del PDF, reproductor de audio) como HTML enriquecido dentro del campo `summary` del curso, enviado en la misma llamada que lo crea (`core_course_create_courses`), que sí está soportada de forma nativa y estable. Cada módulo se presenta visualmente como una tarjeta delimitada (borde de color, badge "MÓDULO N") para compensar la ausencia de secciones reales navegables. Las tablas de contenido se muestran únicamente en el PDF adjunto (donde ReportLab las renderiza correctamente) y las reemplacé por una nota de referencia dentro de Moodle, porque el markdown de tabla en crudo era ilegible como texto plano.

**Alternativas que investigué y descarté por riesgo/tiempo, sin llegar a implementarlas:**
- Plugin `local_wsmanagesections` — expondría edición de secciones vía webservice, pero requiere instalar un plugin de terceros no verificado dentro del contenedor, con riesgo de romper el entorno a pocas horas de la entrega.
- Plugin hipotético `local_course_api` — mismo riesgo, y además no confirmé que existiera como plugin oficial en el repositorio de Moodle.
- Formatos de curso alternativos (`format_tiles`, `format_grid`) — resolverían la estética de navegación por secciones, pero requieren instalar un plugin adicional; opté por resolver la estética directamente en el HTML del `summary` (tarjetas con CSS inline) sin dependencias externas.

### Adjuntos de archivos: de `core_files_upload` a base64 embebido

Implementé y probé `core_files_upload` para subir PDF/imagen/audio al área "draft" del usuario en Moodle. Sin embargo, las URLs de descarga generadas (`draftfile.php`) resultaron ser privadas a la sesión del usuario que subió el archivo — al acceder desde otra sesión o en modo incógnito, Moodle devuelve `brokenfile.php` (archivo no accesible). Confirmé esto de forma reproducible antes de descartar el enfoque.

**Lo que terminé haciendo:** codificar los archivos generados (PDF, imagen, audio) como `data URI` en base64 e incrustarlos directamente dentro del HTML del `summary` del curso. Esto es 100% autocontenido — no depende de sesión, cookies, ni configuración adicional de Moodle — y lo verifiqué abriendo el curso publicado en una ventana de incógnito distinta a la que lo generó.

**El trade-off que acepté:** el HTML del summary crece considerablemente en tamaño (varios PDFs e imágenes en base64 por curso), lo cual es aceptable para el alcance de esta prueba (un curso local a la vez) pero no sería la arquitectura que elegiría para producción a escala.

### Esquema de base de datos

Migré de una única tabla `tasks` con contenido en JSON plano a un esquema normalizado (`tasks`, `courses`, `modules`, `media`), con los archivos multimedia guardados como BLOB en SQLite en vez de en el sistema de archivos local. Esto me permite: (a) que el proyecto sea reproducible sin depender de una carpeta de archivos generados fuera de control de versiones, y (b) alimentar directamente el chat de dudas y el panel de "cursos recientes" con consultas SQL simples, sin tener que reparsear JSON.

### Chat de dudas con memoria conversacional

El chat inicial respondía solo con la pregunta actual como contexto. Lo amplié para recibir el historial de la conversación (últimos turnos) desde el frontend y pasarlo como mensajes previos al modelo, permitiendo preguntas de seguimiento sin repetir contexto (ej. "¿qué se ve en el módulo 2?" seguido de "¿y tiene ejercicios?").

### Renderizado de markdown en el frontend

Tanto el contenido de los módulos como las respuestas del chat vienen formateados en markdown desde el backend (encabezados, listas, tablas, código). En vez de sumar una librería externa solo para esto, escribí un parser propio en JavaScript que convierte ese markdown a HTML, y lo uso en dos lugares: la vista previa del curso y las respuestas del chat. Mantiene el mismo criterio de formato que el PDF (que usa su propio parser en `pdf_service.py`), así el contenido se ve consistente sin importar dónde lo estés leyendo.

---

## Qué implementé como extra (no obligatorio según el enunciado)

- **Edición de contenido antes de publicar:** el usuario puede modificar título, resumen y contenido de cualquier módulo en la vista previa antes de confirmar la publicación.
- **Ejercicios por módulo:** cada módulo incluye una lista de ejercicios prácticos generados por IA, mostrados en la vista previa.
- **Portada de curso generada por IA:** además de la imagen por módulo, genero una portada única para el curso completo.
- **Panel de cursos recientes (CRUD parcial):** listado de cursos ya publicados con portada, acceso directo a Moodle, y eliminación (sincronizada entre Moodle y la base de datos local). No incluye edición de cursos ya publicados — solo lectura y borrado.
- **Formato enriquecido en PDF:** parser propio de markdown básico (encabezados, negrita, cursiva, bloques de código, listas y tablas con ajuste de ancho automático), en vez de texto plano.
- **Renderizado de markdown en frontend:** parser propio en JavaScript para mostrar el contenido con formato tanto en la vista previa como en el chat, sin librerías externas.
- **Semáforo de conexión con Moodle:** el frontend consulta `/moodle/health` al cargar la app y cada 30 segundos, mostrando el estado en un indicador visual (verde/rojo) en el footer, con un banner de alerta si se pierde la conexión.
- **Manejo de reintentos ante fallos de la API de IA:** backoff exponencial ante rate limits y ante JSON malformado de Groq.
- **Reproducibilidad del entorno:** `docker-compose.yml` con healthcheck corregido, `.env.example` documentado.

## Qué no implementé y por qué

- **Autenticación de usuarios:** fuera de alcance explícito según el enunciado.
- **Multi-curso en paralelo:** fuera de alcance explícito según el enunciado.
- **Secciones de Moodle nombradas/navegables individualmente:** limitación de la API de Moodle 4.4 core, documentada en detalle arriba. La mitigo con tarjetas visuales dentro del `summary`.
- **Multimedia visible en la vista previa (antes de confirmar):** decisión consciente. Generar imagen/PDF/audio toma entre 30 y 90 segundos; hacerlo en el paso de vista previa (antes de que el usuario decida publicar) implicaría ese costo de tiempo y cómputo incluso si el usuario descarta el curso. Decidí generar la multimedia únicamente tras la confirmación explícita, y mostrarla en un placeholder en preview indicando que se generará al confirmar.
- **Regeneración individual de una pieza de multimedia** (ej. "no me gustó el audio del módulo 3, genera otro"): lo identifiqué como una mejora valiosa, pero requiere separar la generación de multimedia de la publicación en Moodle en dos pasos distintos — un cambio de arquitectura que no aborde por el riesgo de romper el flujo ya validado a pocas horas de la entrega.
- **Video interactivo:** extra no implementado por prioridad de tiempo.
- **Instalación de plugins de terceros en Moodle** (`local_wsmanagesections`, formatos de curso alternativos): los investigué como posible solución a la limitación de secciones, y los descarté por riesgo de tiempo — ver la sección de limitaciones arriba.

---

<sub>© 2026 Andrés Felipe Murcia Fuentes. Repositorio compartido con fines de evaluación técnica del proceso de selección de Kometa. No se autoriza su uso, copia o distribución fuera de ese contexto sin autorización expresa del autor. Ver [LICENSE](./LICENSE).</sub>