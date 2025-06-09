from datetime import datetime, timedelta

def calcular_horas(entrada, salida):
    if not entrada or not salida:
        return 0
    try:
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                t_entrada = datetime.strptime(str(entrada), fmt)
                t_salida = datetime.strptime(str(salida), fmt)
                break
            except ValueError:
                continue
        else:
            return 0
        # Si la salida es menor que la entrada, asumimos que es al día siguiente
        delta = t_salida - t_entrada
        if delta.total_seconds() < 0:
            delta = delta + timedelta(days=1)
        horas = delta.total_seconds() / 3600
        return round(horas, 2)
    except Exception:
        return 0

def calcular_horas_extras(horas_trabajadas, dia_semana, entrada=None, salida=None):
    """
    Solo cuenta como horas extra el tiempo después de la jornada normal,
    sin importar si la entrada fue antes de las 8:00 am.
    """
    if not entrada or not salida:
        return 0

    try:
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                t_entrada = datetime.strptime(str(entrada), fmt)
                t_salida = datetime.strptime(str(salida), fmt)
                break
            except ValueError:
                continue
        else:
            return 0

        # Define horas normales según el día
        if dia_semana == 6:  # Domingo
            horas_normales = 0
        elif dia_semana == 5:  # Sábado
            horas_normales = 6
        else:  # Lunes a viernes
            horas_normales = 9

        # Hora de salida estándar (fin de jornada normal)
        t_salida_normal = t_entrada + timedelta(hours=horas_normales)

        # Si la salida real es después de la salida normal, hay extras
        if t_salida > t_salida_normal:
            extras = (t_salida - t_salida_normal).total_seconds() / 3600
        else:
            extras = 0

        return round(extras, 2)
    except Exception:
        return 0

def obtener_codigo(entrada, horas, salida, dia_semana):
    # Si no hay entrada ni salida: Falta
    if (not entrada or entrada == "" or str(entrada).lower() == "nan") and (not salida or salida == "" or str(salida).lower() == "nan"):
        return "F"
    # Si hay entrada pero no salida, o salida pero no entrada: Error
    if (entrada and (not salida or salida == "" or str(salida).lower() == "nan")) or (salida and (not entrada or entrada == "" or str(entrada).lower() == "nan")):
        return "?"
    try:
        entrada_str = str(entrada)
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                t_entrada = datetime.strptime(entrada_str, fmt)
                break
            except ValueError:
                continue
        else:
            return "F"
        hora_entrada = t_entrada.hour + t_entrada.minute / 60

        # Define horas requeridas según el día
        horas_requeridas = 6 if dia_semana == 5 else 9

        if hora_entrada <= 8 and horas >= horas_requeridas:
            return "A"
        elif hora_entrada > 8 and horas >= horas_requeridas:
            return "AR"
        elif horas < horas_requeridas:
            return "AP"
    except Exception:
        return "F"
    return "F"