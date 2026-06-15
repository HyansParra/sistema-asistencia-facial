import re

def validar_rut_chileno(rut: str) -> bool:
    """
    Valida un RUT chileno mediante el algoritmo del dígito verificador (Módulo 11).

    Soporta cadenas con puntos, guiones, espacios o caracteres limpios.
    
    Args:
        rut (str): Cadena de texto con el RUT a evaluar.
        
    Returns:
        bool: True si el dígito verificador coincide con el cuerpo numérico, 
              False en caso contrario o si el formato inicial es inválido.
    """
    # Normalización del texto: retiene solo dígitos y el carácter verificador 'K'
    rut_limpio = re.sub(r'[^0-9kK]', '', rut).upper()
    
    if len(rut_limpio) < 2:
        return False
        
    cuerpo = rut_limpio[:-1]
    dv_ingresado = rut_limpio[-1]
    
    if not cuerpo.isdigit():
        return False
        
    # Aplicación del algoritmo Módulo 11
    suma = 0
    multiplicador = 2
    
    for caracter in reversed(cuerpo):
        suma += int(caracter) * multiplicador
        multiplicador = multiplicador + 1 if multiplicador < 7 else 2
        
    dv_esperado = 11 - (suma % 11)
    
    if dv_esperado == 11:
        dv_correcto = "0"
    elif dv_esperado == 10:
        dv_correcto = "K"
    else:
        dv_correcto = str(dv_esperado)
        
    return dv_ingresado == dv_correcto

def formatear_rut(rut: str) -> str:
    """
    Estandariza el formato del RUT al patrón persistido en la base de datos (XXXXXXXX-X).

    Elimina caracteres especiales de separación y asegura consistencia para evitar 
    falsos negativos en las búsquedas o duplicación de registros.
    """
    rut_limpio = re.sub(r'[^0-9kK]', '', rut).upper()
    if len(rut_limpio) < 2:
        return rut_limpio
        
    return f"{rut_limpio[:-1]}-{rut_limpio[-1]}"