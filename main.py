from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from typing import List
import numpy as np
import os
import traceback
import conexion_bd
import inteligencia
import reconocimiento
import validaciones

app = FastAPI(
    title="Sistema de Asistencia por Reconocimiento Facial",
    description="API para el control de asistencia usando DeepFace, Supabase y LangChain"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/estaticos", StaticFiles(directory="estaticos"), name="estaticos")

@app.get("/")
def ruta_principal():
    """
    Redirige de forma automática la raíz del servidor hacia el marcador de asistencia.
    """
    return RedirectResponse(url="/estaticos/index.html")

@app.get("/estado")
def verificar_estado():
    """
    Endpoint de diagnóstico (Heartbeat) para verificar la disponibilidad del servicio.
    """
    return {"estado": "operativo", "mensaje": "El servidor de asistencia funciona correctamente"}

@app.post("/marcar")
async def recibir_marca(foto: UploadFile = File(...), tipo_registro: str = Form(...)):
    """
    Procesa un fotograma en tiempo real para identificar un empleado y registrar su asistencia.

    Extrae el vector de características de la captura, consulta la similitud vectorial en la 
    base de datos y valida el acceso basándose en un umbral estricto de distancia de coseno.
    """
    try:
        contenido_bytes = await foto.read()

        vector_actual = reconocimiento.extraer_vector_rostro(contenido_bytes)
        if vector_actual is None:
            return {"estado": "error", "detalle": "No se pudo detectar un rostro legible en la imagen"}

        coincidencia = conexion_bd.buscar_coincidencia_facial(vector_actual)
        if not coincidencia:
            return {"estado": "error", "detalle": "Acceso denegado: Rostro no registrado en el sistema"}

        empleado_id = coincidencia.get("id")
        rut_empleado = coincidencia.get("rut")
        nombre_empleado = coincidencia.get("nombre_completo")
        distancia_calculada = coincidencia.get("distancia")

        print(f"Coincidencia evaluada: {nombre_empleado} ({rut_empleado}) | Distancia Coseno: {distancia_calculada:.4f}")

        # Regla de Negocio: Valores de distancia inferiores a 0.40 garantizan 
        # que el rostro pertenece a la misma persona bajo el modelo Facenet.
        UMBRAL_CONFIANZA = 0.40
        if distancia_calculada > UMBRAL_CONFIANZA:
            return {"estado": "error", "detalle": "Acceso denegado: El rostro no coincide con el personal registrado"}

        resultado_asistencia = conexion_bd.registrar_marca_asistencia(empleado_id, tipo_registro)
        if not resultado_asistencia:
            return {"estado": "error", "detalle": "Falla del sistema al almacenar el registro de asistencia"}

        tipo_texto = "ENTRADA" if tipo_registro.upper() == "ENTRADA" else "SALIDA"
        return {
            "estado": "exito",
            "mensaje": f"{tipo_texto} registrada correctamente para {nombre_empleado}"
        }
        
    except Exception as error:
        print(f"Error crítico detectado en el módulo de asistencia: {error}")
        return {"estado": "error", "detalle": "Ocurrió un inconveniente interno en el servidor"}

@app.post("/login")
async def login_administrador(usuario: str = Form(...), clave: str = Form(...)):
    """
    Autentica las credenciales de administración contrastándolas con variables de entorno.
    """
    usuario_valido = os.getenv("ADMIN_USUARIO")
    clave_valida = os.getenv("ADMIN_CLAVE")

    print(f"Intento de inicio de sesión - Usuario proporcionado: {usuario}")

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
    
@app.post("/verificar-datos")
async def verificar_datos_registro(rut: str = Form(...), nombre_completo: str = Form(...)):
    """
    Filtro de validación previo a la activación del flujo biométrico de la cámara web.
    """
    if not validaciones.validar_rut_chileno(rut):
        return {"estado": "error", "detalle": "El RUT ingresado no es válido o el dígito verificador es incorrecto"}
        
    rut_formateado = validaciones.formatear_rut(rut)
    
    mensaje_duplicado = conexion_bd.verificar_duplicados_empleado(rut_formateado, nombre_completo)
    if mensaje_duplicado:
        return {"estado": "error", "detalle": mensaje_duplicado}
        
    return {"estado": "exito", "mensaje": "Datos correctos para iniciar capturas"}

@app.post("/registrar")
async def registrar_empleado(
    rut: str = Form(...), 
    nombre_completo: str = Form(...), 
    fotos: List[UploadFile] = File(...)
):
    """
    Enrola un nuevo trabajador calculando un vector maestro a partir de una ráfaga multi-ángulo.

    Valida la consistencia de los datos de identidad, extrae de forma independiente las 
    características de los 5 ángulos solicitados y genera un promedio matemático para mitigar 
    variaciones de iluminación o perspectiva en futuras marcaciones.
    """
    if not validaciones.validar_rut_chileno(rut):
        return {"estado": "error", "detalle": "El RUT ingresado no es válido o el dígito verificador es incorrecto"}

    rut_formateado = validaciones.formatear_rut(rut)

    mensaje_duplicado = conexion_bd.verificar_duplicados_empleado(rut_formateado, nombre_completo)
    if mensaje_duplicado:
        return {"estado": "error", "detalle": mensaje_duplicado}

    vectores_extraidos = []
    print(f"Iniciando registro para: {nombre_completo} ({rut_formateado}) | Procesando {len(fotos)} ángulos faciales...")

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

    # Generación del vector maestro definitivo promediando las matrices de los embeddings analizados
    matriz_vectores = np.array(vectores_extraidos)
    vector_promedio = np.mean(matriz_vectores, axis=0)
    vector_final_lista = vector_promedio.tolist()

    resultado_bd = conexion_bd.guardar_nuevo_empleado(rut_formateado, nombre_completo.strip(), vector_final_lista)

    if resultado_bd:
        return {
            "estado": "exito",
            "mensaje": f"Empleado {nombre_completo} registrado exitosamente"
        }
    else:
        return {"estado": "error", "detalle": "Hubo una falla al insertar el registro en Supabase"}
    
@app.get("/kpis")
def obtener_metricas_dashboard():
    """
    Calcula en tiempo real los indicadores clave de rendimiento (KPIs) de asistencia para la jornada actual.
    """
    from datetime import datetime
    try:
        res_emp = conexion_bd.base_datos.table("empleados").select("id").execute()
        res_asist = conexion_bd.base_datos.table("asistencia").select("empleado_id, fecha_date").execute()

        total_empleados = len(res_emp.data) if res_emp.data else 0
        marcas = res_asist.data if res_asist.data else []

        # Filtrado estricto comparando el formato ISO de la fecha del servidor frente a la columna transaccional
        fecha_hoy_str = datetime.now().strftime("%Y-%m-%d")
        marcas_hoy = []
        
        for m in marcas:
            fecha_marca = m.get("fecha_date")
            if fecha_marca and str(fecha_marca) == fecha_hoy_str:
                marcas_hoy.append(m)

        # Determina la cantidad de trabajadores únicos que registran actividad en el día
        empleados_presentes = len(set(m["empleado_id"] for m in marcas_hoy))

        return {
            "total_empleados": total_empleados,
            "total_marcas_hoy": len(marcas_hoy),
            "empleados_presentes": empleados_presentes
        }
    except Exception as e:
        print(f"Error al calcular KPIs del panel: {e}")
        traceback.print_exc()
        return {"total_empleados": 0, "total_marcas_hoy": 0, "empleados_presentes": 0}

@app.post("/chat")
async def chat_analitico_auditor(pregunta: str = Form(...)):
    """
    Enruta las consultas analíticas en lenguaje natural hacia el pipeline basado en LLM.
    """
    print(f"Consulta recibida: '{pregunta}'")
    respuesta_ia = inteligencia.analizar_datos_asistencia(pregunta)
    return {"respuesta": respuesta_ia}