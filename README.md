# Kometa — Generador de cursos con IA integrado a Moodle

Este proyecto es una aplicación fullstack que crea cursos en Moodle a partir de una instrucción en lenguaje natural. El usuario escribe qué quiere enseñar, revisa una vista previa del curso antes de publicarlo, y al confirmar la aplicación genera el contenido (texto, PDF, imágenes y un podcast en audio) y lo publica directamente en una instancia de Moodle vía su API REST.

Fue desarrollado como prueba técnica para Kometa.

## Por qué existe este proyecto

Crear un curso completo a mano (estructura, contenido de cada módulo, material de apoyo en distintos formatos) toma horas. Esta aplicación reduce ese trabajo a escribir una instrucción y confirmar una vista previa, delegando la generación de contenido a un modelo de IA y la publicación al API de Moodle.

## Cómo funciona el flujo

1. El usuario escribe una instrucción, por ejemplo: *"crea un curso de Excel intermedio con 4 módulos"*.
2. La aplicación genera la estructura del curso (nombre, módulos, descripciones) usando IA y la muestra en una pantalla de carga mientras procesa.
3. Se muestra una vista previa del curso completo. Nada se publica sin que el usuario confirme.
4. Al confirmar, la aplicación genera el contenido de cada módulo (texto, PDF, imagen y podcast) y publica el curso en Moodle.
5. Una vez publicado, el usuario puede abrir el curso directamente en Moodle y hacer preguntas sobre su contenido a través de un chat.

## Stack técnico

**Backend**
- FastAPI (Python), con procesamiento asíncrono para no bloquear al cliente mientras se genera contenido.
- `httpx` para las llamadas al API de Moodle y a los servicios de IA.
- Groq API para generar la estructura del curso y responder el chat.
- Pollinations.ai (Flux) para generar las imágenes de cada módulo.
- SQLite como almacenamiento temporal del estado de cada tarea en proceso.

**Moodle**
- Versión 4.4.4 LTS, levantada con Docker Compose (`mariadb:10.11` + `bitnamilegacy/moodle:4.4`).

**Frontend**
- Alpine.js para el estado de la interfaz y las llamadas a los endpoints.
- Tailwind CSS para los estilos.

## Cómo levantar el proyecto

```bash
# 1. Levantar Moodle y la base de datos
docker compose up -d
```

Moodle queda disponible en `http://localhost:8080` (usuario `admin`, contraseña `Admin123!`). Los datos persisten entre reinicios gracias a los volúmenes de Docker.

**Configurar el Web Service de Moodle:**
1. Entrar a Site administration → Server → Web services.
2. Habilitar los servicios web y el protocolo REST.
3. Crear un servicio externo, asociarle las funciones necesarias y generar un token.
4. Guardar el token y la URL del API en `backend/.env`, en las variables `MOODLE_TOKEN` y `MOODLE_API_URL`.

```bash
# 2. Levantar el backend
cd backend
uvicorn main:app --reload

# 3. Levantar el frontend
cd frontend
python -m http.server 5500
```

La aplicación queda disponible en `http://localhost:5500`.

## Decisiones de arquitectura

Durante el desarrollo se encontraron dos limitaciones del API core de Moodle 4.4:

- `core_course_add_module` y `mod_resource_add_resource` no están disponibles sin plugins de terceros, así que no es posible crear actividades individuales por sección solo con llamadas REST estándar.
- `core_course_edit_section` está deprecada y solo permite cambiar visibilidad, no el contenido de la sección.

Para no depender de plugins externos, todo el contenido de un curso (módulos, descripciones y las imágenes generadas) se arma como un único bloque de HTML y se envía en el parámetro `summary` de `core_course_create_courses`.

El trade-off de esta decisión: en el menú lateral de Moodle las secciones se ven con nombres genéricos ("Sección 1", "Sección 2"), pero el contenido completo del curso queda disponible y visible en el cuerpo principal de la página, que es donde el estudiante realmente lee el material.

## Endpoints del backend

| Método | Ruta | Qué hace |
|---|---|---|
| GET | `/health` | Confirma que el backend está corriendo. |
| GET | `/moodle/prueba_conexion` | Confirma que el token y la conexión a Moodle funcionan. |
| POST | `/courses/generate` | Recibe la instrucción y arranca la generación en segundo plano. |
| GET | `/courses/status/{task_id}` | Devuelve el estado de la generación y, cuando termina, la estructura del curso. |
| POST | `/courses/confirm/{task_id}` | Genera el contenido multimedia y publica el curso en Moodle. |
| POST | `/courses/{task_id}/chat` | Responde preguntas sobre el contenido real del curso ya publicado. |

## Estructura del frontend

El frontend está dividido en pantallas independientes que se cargan dinámicamente según el estado del flujo:

- `screen-1-instruccion.html` — donde el usuario escribe qué quiere enseñar.
- `screen-2-loading.html` — pantalla de espera mientras se genera la estructura del curso.
- `screen-3-preview.html` — vista previa del curso, con cada módulo en un acordeón desplegable.
- `screen-4-publishing.html` — pantalla de espera mientras se publica en Moodle.
- `screen-5-success.html` — confirmación de publicación, con link directo al curso en Moodle.
- `screen-6-chat.html` — chat para preguntar sobre el contenido del curso ya publicado.

La lógica está separada en tres archivos: `app.js` maneja el estado global y la navegación entre pantallas, `api.js` contiene las funciones que llaman al backend, y `polling.js` maneja la consulta periódica del estado mientras se genera el curso.

## Qué se implementó como extra

- Botones de preguntas rápidas en el chat, para no tener que escribir siempre.
- Mensajes de error visibles directamente en la interfaz cuando algo falla, en vez de un `alert()`.
- Un límite de tiempo en la consulta de estado, para evitar que la pantalla de carga quede esperando indefinidamente si algo falla en el backend.

## Qué falta

- Modo oscuro.
- El estado de "Conectado a Moodle" que se ve en el pie de página es solo visual por ahora; no verifica la conexión real.
- El video interactivo mencionado como extra opcional en el enunciado no se implementó.

## Dónde pedir ayuda

Cualquier duda sobre cómo levantar el proyecto o sobre las decisiones tomadas, revisar este README primero. Si algo no queda claro, abrir un issue en el repositorio.

## Autoría

Proyecto desarrollado individualmente como prueba técnica para Kometa.
