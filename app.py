import streamlit as st
import json
import os
import calendar
from datetime import datetime
import requests

ARCHIVO_PRECIOS = "precios.json"
ARCHIVO_HORAS = "horas.json"

TIPOS = ["KDYM", "SJ_SABADO", "SJ_FERIADO", "SJ_MOTOR"]

# ------------------------
# Feriados (ejemplo)
# ------------------------
FERIADOS = [
    "2026-01-01",
    "2026-03-24",
    "2026-04-02",
    "2026-02-04"
]

def es_feriado(año, mes, dia):
    return f"{año}-{mes:02d}-{dia:02d}" in FERIADOS


# ------------------------
# PRECIOS
# ------------------------
def cargar_precios():
    if not os.path.exists(ARCHIVO_PRECIOS):
        precios = {t: 0 for t in TIPOS}
        with open(ARCHIVO_PRECIOS, "w") as f:
            json.dump(precios, f)
        return precios
    else:
        with open(ARCHIVO_PRECIOS, "r") as f:
            return json.load(f)

def guardar_precios(precios):
    with open(ARCHIVO_PRECIOS, "w") as f:
        json.dump(precios, f, indent=4)


# ------------------------
# HORAS (NUEVO)
# ------------------------
def cargar_horas():
    if not os.path.exists(ARCHIVO_HORAS):
        return {}
    with open(ARCHIVO_HORAS, "r") as f:
        return json.load(f)

def guardar_horas(data):
    with open(ARCHIVO_HORAS, "w") as f:
        json.dump(data, f, indent=4)


# ------------------------
# UI
# ------------------------
st.title("💰 Calculadora de Sueldo Mensual")

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
# FECHA
# ------------------------
st.subheader("Seleccionar mes")

col1, col2 = st.columns(2)

año = int(col1.number_input("Año", value=datetime.now().year))
mes = int(col2.number_input("Mes", min_value=1, max_value=12, value=datetime.now().month))


# ------------------------
# CALENDARIO
# ------------------------
st.subheader("📅 Calendario de horas")

cal = calendar.monthcalendar(año, mes)

total = 0
resumen = {t: 0 for t in TIPOS}

dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
cols_header = st.columns(7)

for i, d in enumerate(dias_semana):
    cols_header[i].markdown(f"**{d}**")


for semana in cal:
    cols = st.columns(7)

    for i, dia in enumerate(semana):
        if dia == 0:
            cols[i].write("")
            continue

        fecha = f"{año}-{mes:02d}-{dia:02d}"

        # inicializar si no existe
        if fecha not in horas_data:
            horas_data[fecha] = {"KDYM": 0.0, "SJ": 0.0}

        with cols[i]:

            st.markdown(f"### {dia}")

            # -------------------
            # KDYM (persistente)
            # -------------------
            kdym = st.number_input(
                "KDYM",
                key=f"{fecha}_KDYM",
                value=horas_data[fecha]["KDYM"],
                min_value=0.0,
                step=1.0
            )

            horas_data[fecha]["KDYM"] = kdym

            kdym_val = kdym * precios["KDYM"]
            total += kdym_val
            resumen["KDYM"] += kdym_val

            # -------------------
            # SJ (persistente)
            # -------------------
            sj = st.number_input(
                "SJ",
                key=f"{fecha}_SJ",
                value=horas_data[fecha]["SJ"],
                min_value=0.0,
                step=1.0
            )

            horas_data[fecha]["SJ"] = sj

            es_sabado = (i == 5)
            feriado = es_feriado(año, mes, dia)

            if feriado:
                tipo_sj = "SJ_FERIADO"
            elif es_sabado:
                tipo_sj = "SJ_SABADO"
            else:
                tipo_sj = "SJ_MOTOR"

            sj_val = sj * precios[tipo_sj]
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
st.subheader("Resumen")

for tipo in TIPOS:
    st.write(f"{tipo}: ${resumen[tipo]:,.0f}")

st.markdown("---")
st.subheader(f"💵 Total del mes: ${total:,.0f}")
