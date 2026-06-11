import re

def validar_rut_chileno(rut: str) -> bool:
    """
    Valida si un RUT chileno es real usando el cálculo del dígito verificador.
    Funciona si viene con puntos, guiones o solo números.
    """
    # Deja solo los números y la K, eliminando puntos, guiones o espacios
    rut_limpio = re.sub(r'[^0-9kK]', '', rut).upper()
    
    if len(rut_limpio) < 2:
        return False
        
    cuerpo = rut_limpio[:-1]
    dv_ingresado = rut_limpio[-1]
    
    if not cuerpo.isdigit():
        return False
        
    
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
    Estandariza el RUT al formato de la base de datos: sin puntos y con guion (12345678-9).
    Esto evita problemas de duplicados o búsquedas fallidas en Supabase.
    """
    rut_limpio = re.sub(r'[^0-9kK]', '', rut).upper()
    if len(rut_limpio) < 2:
        return rut_limpio
    # Separa el último dígito con un guion, sin importar si el RUT es corto o largo
    return f"{rut_limpio[:-1]}-{rut_limpio[-1]}"