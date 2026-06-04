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

# endpoint principal para recibir la foto del marcador de asistencia, procesarla y registrar la marca en la base de datos
@app.post("/marcar")
async def recibir_marca(foto: UploadFile = File(...), tipo_registro: str = Form(...)):
    """
    Procesa el fotograma en vivo del marcador de asistencia, extrae sus facciones matemáticas,
    identifica al empleado en Supabase y efectúa el registro de asistencia.
    """
    try:
        # leemos el contenido del archivo de imagen enviado en la petición y lo convertimos a bytes para su procesamiento
        contenido_bytes = await foto.read()

        # convertimos la imagen a un vector facial usando la función de reconocimiento facial basada en DeepFace
        vector_actual = reconocimiento.extraer_vector_rostro(contenido_bytes)
        if vector_actual is None:
            return {"estado": "error", "detalle": "No se pudo detectar un rostro legible en la imagen"}

        # buscamos en la BD de Supabase una posible coincidencia con el vector facial extraído
        coincidencia = conexion_bd.buscar_coincidencia_facial(vector_actual)
        if not coincidencia:
            return {"estado": "error", "detalle": "Acceso denegado: Rostro no registrado en el sistema"}

        # Extraemos los datos arrojados por nuestra función almacenada RPC
        # La función RPC devuelve ID del empleado, RUT, nombre y distancia de coseno calculada entre el vector actual y el vector almacenado en la base de datos para esa persona
        empleado_id = coincidencia.get("id")
        rut_empleado = coincidencia.get("rut")
        nombre_empleado = coincidencia.get("nombre_completo")
        distancia_calculada = coincidencia.get("distancia")

        print(f"Coincidencia evaluada: {nombre_empleado} ({rut_empleado}) | Distancia Coseno: {distancia_calculada:.4f}")

        # control de seguridad adicional 
        # si la distancia de coseno es mayor a un umbral predefinido, se considera que no es una coincidencia confiable y se niega el acceso
        UMBRAL_CONFIANZA = 0.40
        if distancia_calculada > UMBRAL_CONFIANZA:
            return {"estado": "error", "detalle": "Acceso denegado: El rostro no coincide con el personal registrado"}

        # Si la identidad es confirmada, registra la marca de asistencia en la base de datos usando el ID del empleado y el tipo de registro (entrada o salida)
        resultado_asistencia = conexion_bd.registrar_marca_asistencia(empleado_id, tipo_registro)
        if not resultado_asistencia:
            return {"estado": "error", "detalle": "Falla del sistema al almacenar el registro de asistencia"}

        # Respondemos de forma exitosa indicando el nombre para actualizar el frontend
        tipo_texto = "ENTRADA" if tipo_registro.upper() == "ENTRADA" else "SALIDA"
        return {
            "estado": "exito",
            "mensaje": f"{tipo_texto} registrada correctamente para {nombre_empleado}"
        }
        # En caso de cualquier error inesperado durante el proceso, se responde con un mensaje de error genérico para evitar exponer detalles internos del servidor
    except Exception as error:
        print(f"Error crítico detectado en el módulo de asistencia: {error}")
        return {"estado": "error", "detalle": "Ocurrió un inconveniente interno en el servidor"}

# Endpoint para validar el acceso del administrador al panel de registro de empleados
@app.post("/login")
async def login_administrador(usuario: str = Form(...), clave: str = Form(...)):
    """
    Verifica las credenciales del administrador contra las variables configuradas en el archivo .env.
    """
    import os
    # obtenemos los valores guardados de forma segura en memoria RAM
    usuario_valido = os.getenv("ADMIN_USUARIO")
    clave_valida = os.getenv("ADMIN_CLAVE")

    print(f"Intento de inicio de sesión - Usuario proporcionado: {usuario}")

    # Validación de credenciales con respuesta clara para el frontend
    if usuario == usuario_valido and clave == clave_valida:
        return {
            "estado": "autorizado",
            "mensaje": "Credenciales correctas"
        }
    else:
        return {
            "estado": "denegado",
            "detalle": "El usuario o la contraseña no coinciden"
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