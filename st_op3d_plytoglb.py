import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import struct

st.set_page_config(page_title="Visor 3D de Nubes de Puntos", layout="wide")

st.title("🌐 Visualizador 3D de Nubes de Puntos (Compatible con Streamlit Cloud)")
st.write("Sube un archivo .xyz, .txt, .csv o .ply")

uploaded = st.file_uploader("Selecciona tu nube de puntos", type=["xyz", "txt", "csv", "ply"])

# ==========================
# FUNCIÓN PARA LEER PLY SIMPLE (ASCII o BINARIO LITTLE ENDIAN)
# ==========================
def load_ply(file_bytes):
    data = file_bytes.read().decode(errors="ignore")

    # Detectamos cabecera
    header_lines = data.splitlines()
    is_binary = False
    vertex_count = 0
    header_end = 0

    for i, line in enumerate(header_lines):
        if "format binary_little_endian" in line:
            is_binary = True
        if "element vertex" in line:
            vertex_count = int(line.split()[-1])
        if line.strip() == "end_header":
            header_end = i + 1
            break

    # Si es ASCII → leemos directo
    if not is_binary:
        df = pd.read_csv(
            file_bytes,
            sep=r"\s+",
            skiprows=header_end,
            names=["x", "y", "z", "r", "g", "b"],
            nrows=vertex_count
        )
        return df

    # Si es BINARIO → parseo manual
    # Regresamos bytes completos
    raw = file_bytes.getvalue()

    # La cabecera está en texto, obtenemos su longitud en bytes
    header_text = "\n".join(header_lines[:header_end]) + "\n"
    header_len = len(header_text.encode())

    # Por cada vertex: 3 floats (xyz) + 3 uchar (rgb)
    df_data = []
    offset = header_len
    for _ in range(vertex_count):
        x, y, z = struct.unpack_from("<fff", raw, offset)
        offset += 12

        r, g, b = struct.unpack_from("BBB", raw, offset)
        offset += 3

        df_data.append([x, y, z, r, g, b])

    df = pd.DataFrame(df_data, columns=["x", "y", "z", "r", "g", "b"])
    return df

# ==========================
# PROCESAMIENTO PRINCIPAL
# ==========================
if uploaded:
    ext = uploaded.name.split(".")[-1].lower()

    if ext in ["xyz", "txt"]:
        df = pd.read_csv(uploaded, sep=r"\s+", names=["x", "y", "z"], engine="python")
        df["r"] = 255
        df["g"] = 255
        df["b"] = 255

    elif ext == "csv":
        df = pd.read_csv(uploaded)

        if "x" not in df.columns or "y" not in df.columns or "z" not in df.columns:
            st.error("El CSV debe contener columnas x, y, z.")
            st.stop()

        if not {"r", "g", "b"}.issubset(df.columns):
            df["r"] = 255
            df["g"] = 255
            df["b"] = 255

    elif ext == "ply":
        df = load_ply(uploaded)

    else:
        st.error("Formato no soportado.")
        st.stop()

    st.success(f"Nube cargada con {len(df):,} puntos")

    # ======================
    # VISUALIZACIÓN PLOTLY
    # ======================
    color = ['rgb({},{},{})'.format(r,g,b) for r,g,b in zip(df["r"], df["g"], df["b"])]

    fig = px.scatter_3d(
        df,
        x="x",
        y="y",
        z="z",
        color=color,
        width=1200,
        height=800
    )

    fig.update_traces(marker=dict(size=2))

    st.plotly_chart(fig, use_container_width=True)

