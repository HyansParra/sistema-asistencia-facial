import cv2
import numpy as np
from deepface import DeepFace

def extraer_vector_rostro(archivos_bytes: bytes):
    """
    Toma los bytes de una imagen, la transforma al formato de OpenCV 
    y extrae su embedding de 128 dimensiones usando el modelo Facenet.
    """
    try:
        # Convertimos los bytes binarios en una matriz numérica que OpenCV entienda
        matriz_numeros = np.frombuffer(archivos_bytes, np.uint8)
        imagen = cv2.imdecode(matriz_numeros, cv2.IMREAD_COLOR)

        if imagen is None:
            print("Error: No se pudo decodificar la imagen recibida")
            return None

        # Usamos DeepFace para extraer las características del rostro
        # Usamos enforce_detection=False para que no se caiga el servidor si la iluminación es mala
        analisis = DeepFace.represent(
            img_path=imagen, 
            model_name="Facenet", 
            enforce_detection=False
        )
        
        # Extraemos el vector del rostro de 128 dimensiones
        vector = analisis[0]["embedding"]
        return vector

    except Exception as error:
        print(f"Error en el procesamiento de DeepFace: {error}")
        return None