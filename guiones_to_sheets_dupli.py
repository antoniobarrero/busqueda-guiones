import os
import re
from datetime import datetime
from docx import Document
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# === CONFIGURACIÓN ===

CARPETA_DOCX = "2024"  # Carpeta con los archivos .docx
NOMBRE_HOJA_GOOGLE = "Base de Guiones"  # Nombre de la hoja de cálculo

# === CONEXIÓN CON GOOGLE SHEETS ===

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open(NOMBRE_HOJA_GOOGLE).sheet1

# === FUNCIONES ===

def extraer_datos_archivo(nombre_archivo):
    nombre = os.path.splitext(nombre_archivo)[0]
    partes = nombre.split("_", 3)
    disco = partes[0]
    año = partes[1]
    mes = partes[2]
    titulo = partes[3] if len(partes) > 3 else ""
    
    # Determinar estación
    estaciones = {
        "invierno": ["12", "01", "02"],
        "primavera": ["03", "04", "05"],
        "verano": ["06", "07", "08"],
        "otoño": ["09", "10", "11"]
    }
    estacion = next((est for est, meses in estaciones.items() if mes in meses), "desconocida")
    
    return disco, año, mes, estacion, titulo

def extraer_contenido_docx(ruta):
    doc = Document(ruta)
    localizaciones = []
    texto = []

    for p in doc.paragraphs:
        if p.text.strip():
            # Ignorar si está en cursiva (rótulo)
            if any(run.italic for run in p.runs):
                continue
            if "LOCALIZACIÓN" in p.text.upper():
                # Quitar "LOCALIZACIÓN:" y limpiar el texto
                texto_limpio = re.sub(r"(?i)localización\s*:", "", p.text).strip()
                if texto_limpio:
                    localizaciones.append(texto_limpio)
            else:
                texto.append(p.text.strip())
    
    return "; ".join(localizaciones), " ".join(texto)

# === OBTENER LISTA DE ARCHIVOS YA PROCESADOS ===

archivos_existentes = sheet.col_values(1)  # Columna "Archivo"

# === PROCESAR ARCHIVOS NUEVOS ===

carpeta_absoluta = os.path.join(os.getcwd(), CARPETA_DOCX)
archivos = [f for f in os.listdir(carpeta_absoluta) if f.endswith(".docx")]

for archivo in archivos:
    if archivo in archivos_existentes:
        print(f"Ya procesado: {archivo} — se omite.")
        continue

    ruta_completa = os.path.join(carpeta_absoluta, archivo)
    disco, año, mes, estacion, titulo = extraer_datos_archivo(archivo)
    localizaciones, texto = extraer_contenido_docx(ruta_completa)

    # Escribir en Google Sheet
