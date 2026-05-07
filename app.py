import streamlit as st
import json
import os
import calendar
from datetime import datetime
import requests
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="KineSueldo 👩🏻‍⚕️", page_icon="👩🏻‍⚕️", layout="wide")

# ------------------------
# CSS PERSONALIZADO
# ------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Fondo general */
.stApp {
    background: linear-gradient(135deg, #f0f4ff 0%, #faf0ff 50%, #f0fff4 100%);
}

/* Título principal */
h1 {
    font-family: 'DM Serif Display', serif !important;
    color: #4a3f6b !important;
    font-size: 2.4rem !important;
}

h2, h3 {
    font-family: 'DM Sans', sans-serif !important;
    color: #4a3f6b !important;
    font-weight: 600 !important;
}

/* Tarjetas de resumen */
.kine-card {
    background: white;
    border-radius: 16px;
    padding: 20px 24px;
    box-shadow: 0 2px 16px rgba(100, 80, 160, 0.08);
    border-left: 4px solid #8b73c8;
    margin-bottom: 8px;
}

.kine-card-value {
    font-size: 1.8rem;
    font-weight: 600;
    color: #4a3f6b;
    font-family: 'DM Serif Display', serif;
}

.kine-card-label {
    font-size: 0.85rem;
    color: #8a84a3;
    margin-top: 2px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Barra de progreso */
.progress-container {
    background: white;
    border-radius: 16px;
    padding: 20px 24px;
    box-shadow: 0 2px 16px rgba(100, 80, 160, 0.08);
    margin-bottom: 16px;
}

.progress-bar-bg {
    background: #ede9f7;
    border-radius: 999px;
    height: 14px;
    width: 100%;
    margin: 10px 0 6px 0;
    overflow: hidden;
}

.progress-bar-fill {
    height: 14px;
    border-radius: 999px;
    background: linear-gradient(90deg, #8b73c8, #b89ee8);
    transition: width 0.5s ease;
}

.progress-labels {
    display: flex;
    justify-content: space-between;
    font-size: 0.82rem;
    color: #8a84a3;
}

/* Días del calendario */
.dia-normal {
    background: white;
    border-radius: 12px;
    padding: 8px;
    box-shadow: 0 1px 6px rgba(100,80,160,0.07);
    margin-bottom: 6px;
}

.dia-sabado {
    background: #d0e4ff;
    border-radius: 12px;
    padding: 8px;
    box-shadow: 0 1px 6px rgba(80,120,200,0.15);
    border-left: 4px solid #5b8dee;
    margin-bottom: 6px;
}

.dia-feriado {
    background: #ffd6de;
    border-radius: 12px;
    padding: 8px;
    box-shadow: 0 1px 6px rgba(200,80,100,0.15);
    border-left: 4px solid #e05c7a;
    margin-bottom: 6px;
}

.dia-numero {
    font-family: 'DM Serif Display', serif;
    font-size: 1.2rem;
    color: #4a3f6b;
    font-weight: 400;
}

/* Botones */
.stButton > button {
    background: linear-gradient(135deg, #8b73c8, #a98fe0) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 8px 24px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    box-shadow: 0 2px 10px rgba(139, 115, 200, 0.3) !important;
    transition: all 0.2s !important;
}

.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(139, 115, 200, 0.4) !important;
}

/* Inputs */
.stNumberInput > div > div > input {
    border-radius: 8px !important;
    border-color: #ddd8f0 !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* Selectbox */
.stSelectbox > div > div {
    border-radius: 8px !important;
    border-color: #ddd8f0 !important;
}

/* Separador */
hr {
    border-color: #ede9f7 !important;
}

/* Header días semana */
.dia-header {
    text-align: center;
    font-weight: 600;
    color: #8b73c8;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 4px 0 8px 0;
}
</style>
""", unsafe_allow_html=True)

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
    sheet = client.open_by_key(st.secrets["gcp_service_account"]["SHEET_ID"])
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
# UI PRINCIPAL
# ------------------------
st.markdown("# 💆‍♀️ KineSueldo")
st.markdown("<p style='color:#8a84a3; margin-top:-12px; margin-bottom:24px;'>Calculadora de sueldo mensual</p>", unsafe_allow_html=True)

# ------------------------
# SELECCIÓN DE MES
# ------------------------
año_actual = datetime.now().year
mes_actual = datetime.now().month
dia_actual = datetime.now().day

col1, col2, _ = st.columns([1, 1, 3])
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
st.markdown("### 💰 Valores por hora")
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

st.markdown("---")

# ------------------------
# CALENDARIO (calcular totales primero para la barra)
# ------------------------
cal = calendar.monthcalendar(año, mes)
dias_del_mes = calendar.monthrange(año, mes)[1]

total = 0
horas_totales = 0
resumen = {t: 0 for t in TIPOS}

# Pre-calcular para la barra de progreso
total_preview = 0
horas_preview = 0
for semana in cal:
    for i, dia in enumerate(semana):
        if dia == 0:
            continue
        fecha = f"{año}-{mes:02d}-{dia:02d}"
        if fecha not in horas_data:
            horas_data[fecha] = {"KDYM": 0.0, "SJ": 0.0}
        kdym = horas_data[fecha]["KDYM"]
        sj = horas_data[fecha]["SJ"]
        horas_preview += kdym + sj
        total_preview += kdym * precios.get("KDYM", 0)
        feriado = es_feriado(año, mes, dia)
        if feriado:
            tipo_sj = "SJ_FERIADO"
        elif i == 5:
            tipo_sj = "SJ_SABADO"
        else:
            tipo_sj = "SJ_MOTOR"
        total_preview += sj * precios.get(tipo_sj, 0)

# ------------------------
# BARRA DE PROGRESO DEL MES
# ------------------------
if año == año_actual and mes == mes_actual:
    progreso = min(dia_actual / dias_del_mes, 1.0)
    dias_restantes = dias_del_mes - dia_actual
    porcentaje = int(progreso * 100)

    st.markdown(f"""
    <div class="progress-container">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-weight:600; color:#4a3f6b; font-size:1rem;">📅 Progreso del mes</span>
            <span style="font-weight:600; color:#8b73c8;">{porcentaje}% del mes transcurrido</span>
        </div>
        <div class="progress-bar-bg">
            <div class="progress-bar-fill" style="width:{porcentaje}%;"></div>
        </div>
        <div class="progress-labels">
            <span>1 de {calendar.month_name[mes]}</span>
            <span>Hoy: día {dia_actual} · Faltan {dias_restantes} días</span>
            <span>{dias_del_mes} de {calendar.month_name[mes]}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ------------------------
# TARJETAS RESUMEN
# ------------------------
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"""
    <div class="kine-card">
        <div class="kine-card-value">${total_preview:,.0f}</div>
        <div class="kine-card-label">💵 Acumulado del mes</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="kine-card">
        <div class="kine-card-value">{horas_preview:.1f} hs</div>
        <div class="kine-card-label">⏱️ Horas trabajadas</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    promedio = (total_preview / horas_preview) if horas_preview > 0 else 0
    st.markdown(f"""
    <div class="kine-card">
        <div class="kine-card-value">${promedio:,.0f}</div>
        <div class="kine-card-label">📊 Promedio por hora</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ------------------------
# CALENDARIO
# ------------------------
st.markdown("### 🗓️ Calendario de horas")

dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
cols_header = st.columns(7)
for i, d in enumerate(dias_semana):
    cols_header[i].markdown(f"<div class='dia-header'>{d}</div>", unsafe_allow_html=True)

for semana in cal:
    cols = st.columns(7)
    for i, dia in enumerate(semana):
        if dia == 0:
            cols[i].write("")
            continue

        fecha = f"{año}-{mes:02d}-{dia:02d}"
        if fecha not in horas_data:
            horas_data[fecha] = {"KDYM": 0.0, "SJ": 0.0}

        feriado = es_feriado(año, mes, dia)
        es_sabado = (i == 5)

        if feriado:
            clase = "dia-feriado"
        elif es_sabado:
            clase = "dia-sabado"
        else:
            clase = "dia-normal"

        with cols[i]:
            st.markdown(f"<div class='{clase}'><span class='dia-numero'>{dia}</span></div>", unsafe_allow_html=True)

            kdym = st.number_input("KDYM", key=f"{fecha}_KDYM",
                                   value=float(horas_data[fecha]["KDYM"]),
                                   min_value=0.0, step=1.0, label_visibility="collapsed")
            horas_data[fecha]["KDYM"] = kdym
            horas_totales += kdym
            kdym_val = kdym * precios.get("KDYM", 0)
            total += kdym_val
            resumen["KDYM"] += kdym_val

            sj = st.number_input("SJ", key=f"{fecha}_SJ",
                                 value=float(horas_data[fecha]["SJ"]),
                                 min_value=0.0, step=1.0, label_visibility="collapsed")
            horas_data[fecha]["SJ"] = sj
            horas_totales += sj

            if feriado:
                tipo_sj = "SJ_FERIADO"
            elif es_sabado:
                tipo_sj = "SJ_SABADO"
            else:
                tipo_sj = "SJ_MOTOR"

            sj_val = sj * precios.get(tipo_sj, 0)
            total += sj_val
            resumen[tipo_sj] += sj_val

# ------------------------
# GUARDAR HORAS
# ------------------------
if st.button("💾 Guardar horas"):
    guardar_horas(horas_data)
    st.success("Horas guardadas correctamente ✅")

# ------------------------
# RESULTADOS
# ------------------------
st.markdown("---")
st.markdown("### 📋 Resumen del mes")

cols_res = st.columns(len(TIPOS))
for i, tipo in enumerate(TIPOS):
    cols_res[i].metric(tipo, f"${resumen[tipo]:,.0f}")

st.markdown("---")

col_tot1, col_tot2 = st.columns(2)
col_tot1.markdown(f"""
<div class="kine-card">
    <div class="kine-card-value">${total:,.0f}</div>
    <div class="kine-card-label">💵 Ganancia total del mes</div>
</div>
""", unsafe_allow_html=True)

col_tot2.markdown(f"""
<div class="kine-card">
    <div class="kine-card-value">{horas_totales:.1f} hs</div>
    <div class="kine-card-label">⏱️ Total horas trabajadas</div>
</div>
""", unsafe_allow_html=True)
