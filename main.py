from fastapi import FastAPI, File, UploadFile, Form # Importamos FastAPI y herramientas para manejar archivos y formularios en las rutas
from fastapi.middleware.cors import CORSMiddleware # Middleware para manejar CORS y permitir peticiones desde el frontend
from fastapi.staticfiles import StaticFiles # Para servir archivos estáticos como HTML, CSS y JS desde una carpeta específica
from fastapi.responses import RedirectResponse # Para redirigir a la página principal de marcación de asistencia

# Inicializamos la aplicación FastAPI
app = FastAPI(
    title="Sistema de Asistencia por Reconocimiento Facial",
    description="API para el control de asistencia usando DeepFace, Supabase y LangChain"
)

# Configuramos CORS para evitar bloqueos de seguridad del navegador al hacer peticiones
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permite peticiones desde cualquier origen local
    allow_credentials=True, # Permite el uso de cookies y credenciales en las peticiones
    allow_methods=["*"], # Permite todos los métodos HTTP (GET, POST, etc.)
    allow_headers=["*"], # Permite todos los encabezados en las peticiones (como Content-Type, Authorization, etc.)
)

# Montamos la carpeta 'estaticos' para servir los archivos del frontend (HTML, CSS, JS)
app.mount("/estaticos", StaticFiles(directory="estaticos"), name="estaticos")

@app.get("/")
def ruta_principal():
    """
    Ruta raíz que redirige automáticamente a la pantalla de marcación de asistencia.
    """
    return RedirectResponse(url="/estaticos/index.html")

@app.get("/estado")
def verificar_estado():
    """
    Endpoint simple para verificar que el servidor está encendido y respondiendo.
    """
    return {"estado": "operativo", "mensaje": "El servidor de asistencia funciona correctamente"}

@app.post("/marcar")
async def recibir_marca(foto: UploadFile = File(...), tipo_registro: str = Form(...)):
    """
    Recibe el archivo de imagen y el tipo de marca (ENTRADA/SALIDA) desde la interfaz web.
    """
    # Esto imprimirá la confirmación en terminal de VS Code
    print(f"--> Solicitud recibida para Registro: {tipo_registro} | Archivo: {foto.filename}")
    
    return {
        "estado": "recibido", 
        "mensaje": f"Captura recibida con éxito para registrar {tipo_registro}"
    }