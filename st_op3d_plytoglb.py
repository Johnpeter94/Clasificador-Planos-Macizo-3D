import streamlit as st
import open3d as o3d
import numpy as np
import plotly.graph_objects as go

st.set_page_config(layout="wide")

st.title("Visualización 3D de Nube de Puntos con Plotly (Con Colores Originales)")

uploaded_file = st.file_uploader("Sube tu archivo .ply o .pcd", type=["ply", "pcd"])

if uploaded_file is not None:
    temp_path = "temp_pointcloud.ply"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.read())

    pcd = o3d.io.read_point_cloud(temp_path)

    if len(pcd.points) == 0:
        st.error("El archivo no contiene puntos o está dañado.")
    else:
        points = np.asarray(pcd.points)
        colors = np.asarray(pcd.colors)

        if colors.size == 0:
            st.warning("El archivo NO tiene colores. Se asignará color rojo por defecto.")
            plot_colors = "red"
        else:
            # Convertir colores 0–1 → 0–255 formato Plotly
            colors = (colors * 255).astype(np.uint8)

            # Convertir a formato rgb(r,g,b)
            plot_colors = [f"rgb({r},{g},{b})" for r, g, b in colors]

        fig = go.Figure(
            data=[go.Scatter3d(
                x=points[:, 0],
                y=points[:, 1],
                z=points[:, 2],
                mode='markers',
                marker=dict(
                    size=2,
                    opacity=0.9,
                    color=plot_colors  # 👉 AQUÍ USAMOS LOS COLORES REALES
                )
            )]
        )

        fig.update_layout(
            width=900,
            height=700,
            scene=dict(
                xaxis_title="X",
                yaxis_title="Y",
                zaxis_title="Z",
                aspectmode='data'
            )
        )

        st.plotly_chart(fig, use_container_width=True)
        st.success("Nube cargada exitosamente con colores originales 🎨")
else:
    st.info("Sube un archivo para visualizarlo.")
