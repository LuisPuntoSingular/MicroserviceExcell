from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from functionsAssits import (calcular_horas, calcular_horas_extras, obtener_codigo)
import pandas as pd
import tempfile
import re
from datetime import timedelta

app = FastAPI()

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","https://www.autopackerp.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/procesar-excel")
async def procesar_excel(
    file: UploadFile = File(...),
    fecha_inicio: str = Form(...),
    fecha_final: str = Form(...)
):
    try:
        print(f"Fecha inicio recibida: {fecha_inicio}")
        print(f"Fecha final recibida: {fecha_final}")
        # Determina el sufijo y el motor de lectura según la extensión del archivo
        if file.filename.endswith(".xls"):
            suffix = ".xls"
            engine = "xlrd"
        elif file.filename.endswith(".xlsx"):
            suffix = ".xlsx"
            engine = "openpyxl"
        else:
            return JSONResponse(
                status_code=400,
                content={"error": "Formato de archivo no soportado. Solo se permiten .xls y .xlsx"}
            )

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # Lee la hoja específica SIN encabezados
        df = pd.read_excel(
            tmp_path,
            sheet_name="Reporte de Asistencia",
            engine=engine,
            header=None
        )

        # Obtiene los días del periodo (fila 4, columnas desde el índice 0 en adelante)
        dias = df.iloc[3, :].dropna().tolist()
        dias = [int(d) for d in dias if str(d).isdigit()]

        # Descompón las fechas recibidas para obtener solo el día del mes
        fecha_inicio_dt = pd.to_datetime(fecha_inicio)
        fecha_final_dt = pd.to_datetime(fecha_final)
        dia_inicio = fecha_inicio_dt.day
        dia_final = fecha_final_dt.day

        registros = []
        fila = 4  # Empieza en la fila 5 (índice 4)
        while fila < len(df):
            id_empleado = df.iloc[fila, 2]
            if pd.isna(id_empleado):
                fila += 2
                continue

            # Recorre todos los días de la fila 4 (desde el índice 0)
            for i, dia in enumerate(dias):
                # Solo procesa los días dentro del rango solicitado
                if not (dia_inicio <= dia <= dia_final):
                    continue
                # Fila par: horas de entrada/salida
                if fila+1 < len(df):
                    celda = df.iloc[fila+1, i]
                    entrada, salida = None, None
                    if pd.notna(celda):
                        celda_str = str(celda).replace(" ", "")
                        horas_encontradas = re.findall(r"\d{2}:\d{2}", celda_str)
                        if len(horas_encontradas) >= 2:
                            entrada = horas_encontradas[0]
                            salida = horas_encontradas[1]
                        elif len(horas_encontradas) == 1:
                            entrada = horas_encontradas[0]
                            salida = None
                        elif ":" in celda_str:
                            entrada = celda_str
                            salida = None
                    else:
                        entrada = None
                        salida = None
                    # Construye la fecha real usando año y mes de fecha_inicio y el día correspondiente
                    try:
                        fecha_actual = pd.Timestamp(year=fecha_inicio_dt.year, month=fecha_inicio_dt.month, day=dia)
                    except Exception:
                        continue  # Si el día no existe en el mes, lo ignora
                    # ...existing code...
                    horas = calcular_horas(entrada, salida)
                    dia_semana = fecha_actual.weekday()
                    horas_extras = calcular_horas_extras(horas, dia_semana, entrada)  # <-- pasa entrada aquí
                    codigo = obtener_codigo(entrada, horas, salida, dia_semana)
                    # ...existing code...
                    registros.append({
                        "ID": id_empleado,
                        "Fecha": fecha_actual.strftime("%Y-%m-%d"),
                        "Entrada": entrada if pd.notna(entrada) else None,
                        "Salida": salida if pd.notna(salida) else None,
                        "Horas": horas,
                        "DiaSemana": dia_semana,
                        "HorasExtras": horas_extras,
                        "Codigo": codigo
                    })
            fila += 2

        return registros

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})