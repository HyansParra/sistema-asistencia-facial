import cv2
import numpy as np
from deepface import DeepFace

def extraer_vector_rostro(archivos_bytes: bytes):
    """
    Procesa los bytes de una imagen para extraer su embedding facial de 128 dimensiones.

    Utiliza el modelo Facenet tras decodificar el flujo binario en una estructura de tres canales.

    Args:
        archivos_bytes (bytes): Flujo binario de la imagen capturada por el sensor web.

    Returns:
        list: Vector de características numéricas que representa las facciones del rostro,
              o None si ocurre una falla en la decodificación o el análisis.
    """
    try:
        matriz_numeros = np.frombuffer(archivos_bytes, np.uint8)
        imagen = cv2.imdecode(matriz_numeros, cv2.IMREAD_COLOR)

        if imagen is None:
            print("Error: No se pudo decodificar la imagen recibida")
            return None

        # Se deshabilita 'enforce_detection' para evitar excepciones bloqueantes en el hilo
        # principal si la captura presenta subexposición, reflejos o desenfoque temporal.
        analisis = DeepFace.represent(
            img_path=imagen, 
            model_name="Facenet", 
            enforce_detection=False
        )
        
        vector = analisis[0]["embedding"]
        return vector

    except Exception as error:
        print(f"Error en el procesamiento de DeepFace: {error}")
        return None