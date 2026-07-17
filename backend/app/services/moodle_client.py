import httpx 
from app.config import settings

class ModdleClient:
    def __init__(self):
        self.token = settings.MOODLE_TOKEN
        self.base_url= settings.MOODLE_API_URL

    async def _make_requests(self, function_name: str, params: dict = None) -> dict:
        if params is None:
            params = {}

        # Parametros globales necesarios para la API de Moodle
        query_params = {
            "wstoken": self.token,
            "wsfunction": function_name,
            "moodlewsrestformat": "json"
        }
        

        async with httpx.AsyncClient() as client:
            # Enviaremos los parámetros del curso en el cuerpo del POST (data)
            # y credenciales en URL (params), para evitar conflictos con PHP
            response = await client.post(self.base_url, params=query_params, data=params)
            response.raise_for_status()
            return response.json()

    async def get_site_info(self) -> dict:
        return await self._make_requests("core_webservice_get_site_info")

    async def create_course(self, fullname: str, shortname: str, categoryid: int = 1, summary: str = "") -> dict:
        # Formato de parámetros que Moodle exige estrictamente
        params = {
            "courses[0][fullname]": fullname,
            "courses[0][shortname]": shortname,
            "courses[0][categoryid]": str(categoryid),
            "courses[0][format]": "topics",
            "courses[0][numsections]": 4,
            "courses[0][summary]": summary,
        }
        return await self._make_requests("core_course_create_courses", params)
    
    ##PRUEBAS##
    async def get_course_contents(self, course_id: int) -> list:
        """
        Obtiene el contenido detallado de un curso, incluyendo las secciones 
        con sus respectivos IDs reales de la base de datos.
        """
        params = {"courseid": str(course_id)}
        return await self._make_requests("core_course_get_contents", params)

    async def upload_file(self, filepath: str, filename: str) -> dict:
        """
        Sube un archivo al área draft del usuario. Devuelve metadata con la 
        URL para referenciarlo luego en el summary del curso. 
        """

        # 1. Moodle tiene un script para subir archivos llamado 'upload.php'.
        # Como nuestra base_url apunta a 'server.php', aquí cambiamos el final de la URL
        # para dirigir la petición al lugar correcto de la instalación local.
        if "webservice/rest/server.php" in self.base_url:
            url = self.base_url.replace("webservice/rest/server.php", "webservice/upload.php")
        else:
            url = self.base_url.replace("server.php", "upload.php")

        # 2. Le pasamos el Token de Kometa 
        # y le decimos que tire el archivo a la "zona de borradores" (draft) del usuario.
        params = {"token": self.token, "filearea": "draft"}
        
        # 3. Abrimos el archivo local (ej: test_files/prueba.txt) en modo lectura de bytes ("rb").
        with open(filepath, "rb") as f:
            # Empaquetamos el archivo bajo la clave "file", que es el nombre que Moodle exige en el formulario HTTP.
            files = {"file": (filename, f)}
            
            # 4. Levantamos el cliente HTTP asíncrono para hacer la petición sin bloquear el servidor.
            async with httpx.AsyncClient() as client:
                # Disparamos el POST con la URL modificada, el token en los parámetros y los bytes del archivo.
                response = await client.post(url, params=params, files=files, timeout=30)
                
                # Si Moodle responde con un error (ej: 404, 500, 403), esto levanta una excepción
                response.raise_for_status()
                
                # 5. Moodle responde con una lista de diccionarios, algo como: [{"itemid": 123, ...}]
                data = response.json()
                
                # Evaluamos: Si lo que llegó es una lista y tiene al menos un archivo procesado...
                if isinstance(data, list) and len(data) > 0:
                    return data[0]  # Extraemos y retornamos SOLO el diccionario del archivo (con su itemid).
                
                return {} # Si por alguna razón la lista llegó vacía, devolvemos un diccionario vacío seguro.

    async def delete_courses(self, course_ids: list) -> dict:
            
            """Elimina cursos de Moodle por sus IDs. Utilidad de desarrollo/pruebas."""
            params = {}
            for i, cid in enumerate(course_ids):
                params[f"courseids[{i}]"] = str(cid)
            return await self._make_requests("core_course_delete_courses", params)

moodle_client = ModdleClient()