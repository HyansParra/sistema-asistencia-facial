import os
import traceback
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import conexion_bd 

def analizar_datos_asistencia(pregunta_administrador: str) -> str:
    """
    Orquesta un pipeline RAG (Retrieval-Augmented Generation) para responder dudas de auditoría de RRHH.

    Descarga la nómina completa y el historial transaccional de marcas desde Supabase,
    reconstruye los eventos unificando las dimensiones de fecha y hora, y delega la inferencia
    a Gemini bajo directrices de estricta fidelidad a los datos provistos.
    """
    try:
        respuesta_empleados = conexion_bd.base_datos.table("empleados").select("id, rut, nombre_completo").execute()
        empleados = respuesta_empleados.data if respuesta_empleados.data else []

        respuesta_asistencia = conexion_bd.base_datos.table("asistencia").select("empleado_id, tipo_registro, fecha_date, hora_time").execute()
        registros = respuesta_asistencia.data if respuesta_asistencia.data else []

        # Construcción del contexto plano estructurado para el consumo optimizado del LLM
        contexto_empleados = "--- LISTA DE PERSONAL REGISTRADO ---\n"
        for emp in empleados:
            contexto_empleados += f"ID: {emp['id']} | RUT: {emp['rut']} | Nombre: {emp['nombre_completo']}\n"

        contexto_asistencia = "\n--- HISTORIAL DE MARCAS DE ASISTENCIA ---\n"
        for reg in registros:
            # Resolución de llave foránea en memoria para asociar el nombre del trabajador al evento
            nombre = next((e['nombre_completo'] for e in empleados if e['id'] == reg['empleado_id']), "Desconocido")
            contexto_asistencia += f"Trabajador: {nombre} | Evento: {reg['tipo_registro']} | Momento: {reg['fecha_date']} a las {reg['hora_time']}\n"

        contexto_final = contexto_empleados + contexto_asistencia

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "Error del sistema: No se detectó la llave de acceso GEMINI_API_KEY en el archivo .env"

        # Configuración del modelo fundacional con baja temperatura para minimizar la variabilidad cognitiva
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=0.2 
        )

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

        pipeline_analitico = plantilla_instrucciones | llm
        respuesta_ia = pipeline_analitico.invoke({
            "contexto": contexto_final,
            "pregunta": pregunta_administrador
        })

        return respuesta_ia.content

    except Exception as error:
        print(f"Falla crítica en el script de inteligencia: {error}")
        traceback.print_exc()
        return "Lo siento, ocurrió un error al procesar tu solicitud. Por favor, intenta nuevamente."