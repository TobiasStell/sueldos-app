import streamlit as st
import json
import calendar
from datetime import datetime
import requests
import gspread
from google.oauth2.service_account import Credentials

# ------------------------
# GOOGLE SHEETS
# ------------------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def get_sheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(st.secrets["SHEET_ID"])
    return sheet

def cargar_precios():
    sheet = get_sheet()
    ws = sheet.worksheet("precios")
    data = ws.get_all_records()
    if not data:
        return {t: 0 for t in TIPOS}
    return {row["tipo"]: float(row["valor"]) for row in data}

def guardar_precios(precios):
    sheet = get_sheet()
    ws = sheet.worksheet("precios")
    ws.clear()
    ws.append_row(["tipo", "valor"])
    for tipo, valor in precios.items():
        ws.append_row([tipo, valor])

def cargar_horas():
    sheet = get_sheet()
    ws = sheet.worksheet("horas")
    data = ws.get_all_records()
    resultado = {}
    for row in data:
        fecha = row["fecha"]
        resultado[fecha] = {
            "KDYM": float(row["KDYM"]),
            "SJ": float(row["SJ"])
        }
    return resultado

def guardar_horas(horas_data):
    sheet = get_sheet()
    ws = sheet.worksheet("horas")
    ws.clear()
    ws.append_row(["fecha", "KDYM", "SJ"])
    for fecha, vals in horas_data.items():
        ws.append_row([fecha, vals["KDYM"], vals["SJ"]])

# ------------------------
# FERIADOS
# ------------------------
@st.cache_data
def obtener_feriados(año):
    url = f"https://api.argentinadatos.com/v1/feriados/{año}"
    response = requests.get(url)
    if response.status_code != 200:
        return set()
    data = response.json()
    return {f["fecha"] for f in data}

TIPOS = ["KDYM", "SJ_SABADO", "SJ_FERIADO", "SJ_MOTOR"]

# ------------------------
# UI
# ------------------------
st.title("💰 Calculadora de Sueldo Mensual")

st.subheader("Seleccionar mes")
año_actual = datetime.now().year
mes_actual = datetime.now().month

col1, col2 = st.columns(2)
año = col1.selectbox("Año", [año_actual - 1, año_actual, año_actual + 1], index=1)
mes = col2.number_input("Mes", min_value=1, max_value=12, value=mes_actual)

FERIADOS = obtener_feriados(año)

def es_feriado(año, mes, dia):
    return f"{año}-{mes:02d}-{dia:02d}" in FERIADOS

precios = cargar_precios()
horas_data = cargar_horas()

# ------------------------
# PRECIOS
# ------------------------
st.subheader("Valores por hora")
cols = st.columns(len(TIPOS))
for i, tipo in enumerate(TIPOS):
    precios[tipo] = cols[i].number_input(
        tipo,
        min_value=0.0,
        value=float(precios.get(tipo, 0)),
        step=100.0
    )

if st.button("Guardar precios"):
    guardar_precios(precios)
    st.success("Precios guardados ✅")

# ------------------------
# CALENDARIO
# ------------------------
st.subheader("📅 Calendario de horas")

cal = calendar.monthcalendar(año, mes)
total = 0
horas_totales = 0
resumen = {t: 0 for t in TIPOS}

dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
cols_header = st.columns(7)
for i, d in enumerate(dias_semana):
    cols_header[i].markdown(f"**{d}**")

def estilo_dia(año, mes, dia, i):
    fecha = f"{año}-{mes:02d}-{dia:02d}"
    if fecha in FERIADOS:
        return "background-color:#ffe6e6; border-radius:8px; padding:4px;"
    elif i == 5:
        return "background-color:#e6f0ff; border-radius:8px; padding:4px;"
    else:
        return "padding:4px;"

for semana in cal:
    cols = st.columns(7)
    for i, dia in enumerate(semana):
        if dia == 0:
            cols[i].write("")
            continue

        fecha = f"{año}-{mes:02d}-{dia:02d}"
        if fecha not in horas_data:
            horas_data[fecha] = {"KDYM": 0.0, "SJ": 0.0}

        with cols[i]:
            style = estilo_dia(año, mes, dia, i)
            st.markdown(f"<div style='{style}'>", unsafe_allow_html=True)
            st.markdown(f"### {dia}")

            kdym = st.number_input("KDYM", key=f"{fecha}_KDYM",
                                   value=float(horas_data[fecha]["KDYM"]),
                                   min_value=0.0, step=1.0)
            horas_data[fecha]["KDYM"] = kdym
            horas_totales += kdym
            kdym_val = kdym * precios["KDYM"]
            total += kdym_val
            resumen["KDYM"] += kdym_val

            sj = st.number_input("SJ", key=f"{fecha}_SJ",
                                 value=float(horas_data[fecha]["SJ"]),
                                 min_value=0.0, step=1.0)
            horas_data[fecha]["SJ"] = sj
            horas_totales += sj

            feriado = es_feriado(año, mes, dia)
            if feriado:
                tipo_sj = "SJ_FERIADO"
            elif i == 5:
                tipo_sj = "SJ_SABADO"
            else:
                tipo_sj = "SJ_MOTOR"

            sj_val = sj * precios[tipo_sj]
            total += sj_val
            resumen[tipo_sj] += sj_val
            st.markdown("</div>", unsafe_allow_html=True)

# ------------------------
# GUARDAR HORAS
# ------------------------
if st.button("💾 Guardar horas"):
    guardar_horas(horas_data)
    st.success("Horas guardadas correctamente ✅")

# ------------------------
# RESULTADOS
# ------------------------
st.subheader("Resumen")
for tipo in TIPOS:
    st.write(f"{tipo}: ${resumen[tipo]:,.0f}")

st.markdown("---")
st.subheader(f"💵 Ganancia total del mes: ${total:,.0f}")
st.subheader(f"⏱️ Horas trabajadas del mes: {horas_totales:.1f} hs")
