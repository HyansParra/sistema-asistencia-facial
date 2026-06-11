import os # Para manejar las variables de entorno
import re # Para limpiar espacios extra en los nombres de los empleados
from supabase import create_client, Client # Para interactuar con la base de datos de Supabase
from dotenv import load_dotenv # Importamos la herramienta para leer el archivo .env

# Cargamos las variables de entorno desde el archivo .env para hacer la conexion con Supabase
load_dotenv()

# Cargamos las variables de entorno desde el archivo .env para hacer la conexion con Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Verificamos que las credenciales existan antes de intentar conectar con Supabase
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Error: Faltan las credenciales de Supabase en el archivo .env")

# Creamos el cliente de Supabase para interactuar con la base de datos
base_datos: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def guardar_nuevo_empleado(rut: str, nombre: str, vector: list):
    """
    Inserta un nuevo empleado en la base de datos junto con su vector facial.
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
    Registra un evento de ENTRADA o SALIDA para un empleado.
    """
    try:
        datos = {
            "empleado_id": empleado_id,
            "tipo_registro": tipo.upper()
        }
        resultado = base_datos.table("asistencia").insert(datos).execute()
        return resultado.data
    except Exception as e:
        print(f"Error al registrar asistencia: {e}")
        return None
    
def buscar_coincidencia_facial(vector_rostro: list):
    """
    Llama a la función interna de Supabase para comparar el vector 
    actual con el de todos los empleados registrados.
    """
    try:
        # Llamamos a la función RPC personalizada que compara el vector recibido con los almacenados en la BD
        resultado = base_datos.rpc(
            "buscar_rostro_coincidente", 
            {"vector_buscado": vector_rostro}
        ).execute()
        
        # Si encuentra registros, devolvemos el primer resultado
        if resultado.data and len(resultado.data) > 0:
            return resultado.data[0]
            
        return None
    except Exception as e:
        print(f"Error al buscar coincidencia en la BD: {e}")
        return None
    
def verificar_duplicados_empleado(rut_formateado: str, nombre_completo: str):
    """
    Revisa si el RUT o el nombre ya existen en Supabase.
    Devuelve un texto con el error si encuentra algo repetido, o None si está todo OK.
    """
    try:
        # Busca si el RUT ya existe para no duplicarlo
        res_rut = base_datos.table("empleados").select("rut").eq("rut", rut_formateado).execute()
        if res_rut.data:
            return "El RUT ingresado ya se encuentra registrado en el sistema"
            
        # Borra espacios extras al inicio, al final y junta los espacios dobles entre medio
        nombre_limpio = re.sub(r'\s+', ' ', nombre_completo).strip()
            
        # El ilike de Supabase busca sin importar mayúsculas o minúsculas
        res_nombre = base_datos.table("empleados").select("nombre_completo").ilike("nombre_completo", nombre_limpio).execute()
        if res_nombre.data:
            return "Ya existe un empleado registrado con ese mismo nombre completo"
            
        return None
    except Exception as e:
        print(f"Error al verificar duplicados en la base de datos: {e}")
        return "Error interno de comunicación al verificar duplicados"