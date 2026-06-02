from fastapi import FastAPI, File, UploadFile, Form # Importamos FastAPI y herramientas para manejar archivos y formularios en las rutas
from fastapi.middleware.cors import CORSMiddleware # Middleware para manejar CORS y permitir peticiones desde el frontend
from fastapi.staticfiles import StaticFiles # Para servir archivos estáticos como HTML, CSS y JS desde una carpeta específica
from fastapi.responses import RedirectResponse # Para redirigir a la página principal de marcación de asistencia
from typing import List # List para poder recibir multiples archivos juntos
import numpy as np # numpy para hacer el promedio matemático de vectores
import conexion_bd # Importamos las funciones de conexión a la base de datos y manejo de empleados
import reconocimiento # Importamos la función para extraer el vector facial usando DeepFace


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
    print(f"Solicitud recibida para Registro: {tipo_registro} | Archivo: {foto.filename}")
    
    return {
        "estado": "recibido", 
        "mensaje": f"Captura recibida con éxito para registrar {tipo_registro}"
    }

# Endpoint para registrar un nuevo empleado con su vector facial promedio a partir de 5 fotos
@app.post("/registrar")
async def registrar_empleado(
    rut: str = Form(...), 
    nombre_completo: str = Form(...), 
    fotos: List[UploadFile] = File(...)
):
    """
    Recibe los datos de un nuevo trabajador junto a una ráfaga de 5 fotos de distintos ángulos.
    Extrae los vectores de cada una, calcula el promedio y guarda en Supabase.
    """
    vectores_extraidos = []

    print(f"Iniciando registro para: {nombre_completo} ({rut}) | Procesando {len(fotos)} ángulos faciales...")

    for foto in fotos:
        try:
            contenido_bytes = await foto.read()
            vector = reconocimiento.extraer_vector_rostro(contenido_bytes)
            
            if vector is not None:
                vectores_extraidos.append(vector)
        except Exception as e:
            print(f"Error procesando uno de los ángulos de registro: {e}")

    if not vectores_extraidos:
        return {"estado": "error", "detalle": "No se pudo detectar un rostro claro en los ángulos enviados"}

    # Promediamos la matriz de 5 vectores para conseguir el vector definitivo
    matriz_vectores = np.array(vectores_extraidos)
    vector_promedio = np.mean(matriz_vectores, axis=0)
    vector_final_lista = vector_promedio.tolist()

    # Guardamos los datos finales en Supabase
    resultado_bd = conexion_bd.guardar_nuevo_empleado(rut, nombre_completo, vector_final_lista)

    if resultado_bd:
        return {
            "estado": "exito",
            "mensaje": f"Empleado {nombre_completo} registrado exitosamente"
        }
    else:
        return {"estado": "error", "detalle": "El RUT ya se encuentra registrado o hubo una falla al insertar en Supabase"}