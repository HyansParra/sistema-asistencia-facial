import os # Para leer de forma segura las credenciales del sistema a través de variables de entorno
from langchain_google_genai import ChatGoogleGenerativeAI # Conector oficial de LangChain para modelos de Google
from langchain_core.prompts import ChatPromptTemplate # Herramienta para estructurar las instrucciones del prompt
import conexion_bd # Importamos la conexion para extraer los datos de la base de datos de Supabase

def analizar_datos_asistencia(pregunta_administrador: str):
    """
    Recupera el estado actual de las tablas de Supabase, genera un contexto resumido
    y utiliza Gemini a través de LangChain para responder auditorías en lenguaje natural.
    """
    try:
        # Extraer los datos reales desde las tablas de la base de datos
        # Descargamos la nómina completa de empleados
        respuesta_empleados = conexion_bd.base_datos.table("empleados").select("id, rut, nombre_completo").execute()
        empleados = respuesta_empleados.data if respuesta_empleados.data else []

        # Descargamos el historial completo de registros de entrada y salida
        respuesta_asistencia = conexion_bd.base_datos.table("asistencia").select("empleado_id, tipo_registro, fecha_hora").execute()
        registros = respuesta_asistencia.data if respuesta_asistencia.data else []

        # Traducir los datos estructurados a un texto plano comprensible para la IA
        contexto_empleados = "--- LISTA DE PERSONAL REGISTRADO ---\n"
        for emp in empleados:
            contexto_empleados += f"ID: {emp['id']} | RUT: {emp['rut']} | Nombre: {emp['nombre_completo']}\n"

        contexto_asistencia = "\n--- HISTORIAL DE MARCAS DE ASISTENCIA ---\n"
        for reg in registros:
            # Buscamos el nombre del empleado asociado a cada registro de asistencia para mayor claridad
            nombre = next((e['nombre_completo'] for e in empleados if e['id'] == reg['empleado_id']), "Desconocido")
            contexto_asistencia += f"Trabajador: {nombre} | Evento: {reg['tipo_registro']} | Momento: {reg['fecha_hora']}\n"

        # Fusionamos ambos bloques en un único contexto definitivo
        contexto_final = contexto_empleados + contexto_asistencia

        # Validar e inicializar el motor de Inteligencia Artificial de Google
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "Error del sistema: No se detectó la llave de acceso GEMINI_API_KEY en el archivo .env"

        # Instanciamos a Gemini usando el modelo Flash optimizado para respuestas en tiempo real
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=0.2 # Configuración baja para asegurar respuestas verídicas basadas solo en los datos
        )

        # Definir las reglas de negocio y el comportamiento del asistente virtual
        plantilla_instrucciones = ChatPromptTemplate.from_messages([
            ("system", (
                "Eres un asistente virtual avanzado, experto en auditoría de Recursos Humanos y control de asistencia.\n"
                "Tu única fuente de verdad son los datos adjuntados a continuación. No puedes inventar eventos.\n\n"
                "REGISTROS EN TIEMPO REAL DEL SISTEMA:\n{contexto}\n\n"
                "Reglas de respuesta:\n"
                "1. Responde con un tono formal, claro y amigable en español.\n"
                "2. Si te preguntan quién asistió, quién faltó o los horarios, analiza detalladamente el historial provisto.\n"
                "3. Si la respuesta no se puede deducir con los datos entregados, indica con amabilidad que no posees registros suficientes."
            )),
            ("human", "{pregunta}")
        ])

        # agregamos el contexto y la pregunta del administrador al pipeline de LangChain
        pipeline_analitico = plantilla_instrucciones | llm
        respuesta_ia = pipeline_analitico.invoke({
            "contexto": contexto_final,
            "pregunta": pregunta_administrador
        })

        # Devolvemos el texto redactado por Gemini directo al solicitante
        return respuesta_ia.content

    except Exception as error:
        print(f"Falla crítica en el script de inteligencia: {error}")
        return "Lo siento, ocurrió un error al procesar tu solicitud. Por favor, intenta nuevamente."