import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo  # Permite localizar el tiempo exacto usando la base de datos de tzdata
from supabase import create_client, Client
from dotenv import load_dotenv

# Carga inicial de variables de entorno globales
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Error: Faltan las credenciales de Supabase en el archivo .env")

base_datos: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def guardar_nuevo_empleado(rut: str, nombre: str, vector: list):
    """
    Inserta un nuevo registro de personal en la tabla 'empleados' junto con su vector maestro.
    """
    try:
        datos = {
            "rut": rut,
            "nombre_completo": nombre,
            "vector_facial": vector
        }
        resultado = base_datos.table("empleados").insert(datos).execute()
        return resultado.data
    except Exception as e:
        print(f"Error al guardar empleado: {e}")
        return None

def registrar_marca_asistencia(empleado_id: str, tipo: str):
    """
    Registra una marca temporal de ENTRADA o SALIDA vinculada al ID del empleado.

    Captura de manera explícita la fecha y hora bajo el huso horario de Chile 
    (America/Santiago) para anular el comportamiento UTC por defecto de Supabase.
    """
    try:
        # Obtención del objeto datetime localizado de forma estricta en la zona horaria chilena
        ahora_chile = datetime.now(ZoneInfo("America/Santiago"))
        
        datos = {
            "empleado_id": empleado_id,
            "tipo_registro": tipo.upper(),
            # Forzamos el envío de las cadenas formateadas con el tiempo local de la marca
            "fecha_date": ahora_chile.strftime("%Y-%m-%d"),
            "hora_time": ahora_chile.strftime("%H:%M:%S")
        }
        resultado = base_datos.table("asistencia").insert(datos).execute()
        return resultado.data
    except Exception as e:
        print(f"Error al registrar asistencia: {e}")
        return None
    
def buscar_coincidencia_facial(vector_rostro: list):
    """
    Ejecuta un procedimiento remoto (RPC) en Supabase para calcular la distancia
    de coseno entre el vector capturado y los registros de la base de datos.
    """
    try:
        resultado = base_datos.rpc(
            "buscar_rostro_coincidente", 
            {"vector_buscado": vector_rostro}
        ).execute()
        
        if resultado.data and len(resultado.data) > 0:
            return resultado.data[0]
            
        return None
    except Exception as e:
        print(f"Error al buscar coincidencia en la BD: {e}")
        return None
    
def verificar_duplicados_empleado(rut_formateado: str, nombre_completo: str):
    """
    Verifica la existencia previa de las llaves naturales (RUT y Nombre Completo).

    Aplica limpieza de espacios contiguos y una comparación insensible a mayúsculas/minúsculas 
    para garantizar la unicidad de los datos antes del enrolamiento físico.
    """
    try:
        res_rut = base_datos.table("empleados").select("rut").eq("rut", rut_formateado).execute()
        if res_rut.data:
            return "El RUT ingresado ya se encuentra registrado en el sistema"
            
        nombre_limpio = re.sub(r'\s+', ' ', nombre_completo).strip()
            
        res_nombre = base_datos.table("empleados").select("nombre_completo").ilike("nombre_completo", nombre_limpio).execute()
        if res_nombre.data:
            return "Ya existe un empleado registrado con ese mismo nombre completo"
            
        return None
    except Exception as e:
        print(f"Error al verificar duplicados en la base de datos: {e}")
        return "Error interno de comunicación al verificar duplicados"