import streamlit as st
import pandas as pd
import geopandas as gpd
import zipfile
import os
import folium
from streamlit_folium import st_folium
import branca.colormap as cm
import plotly.graph_objects as go

# ------------------------------------------------------------------------------

# 📌 Establecer título y favicon de la aplicación
st.set_page_config(page_title="PC-MX", page_icon="🔥")

st.title("🔥 Puntos de calor por estado")
'''
ADRIÁN ISRAEL SILVA CARDOZA 
al.asilva@centrogeo.edu.mx 

Doctorado Integrado en Ciencias Geoespaciales con orientación en Observación de la Tierra 
Centro de Investigación en Ciencias de Información Geoespacial A.C.

Procesos de Ciencia de Datos Geoespaciales | Dr. Gandhi Samuel Hernández Chan

Fecha - 4 de abril 2025
'''

# ------------------------------------------------------------------------------
# 📌 Función para cargar archivos SHP comprimidos en ZIP
TEMP_FOLDER = "temp_shp"

# 📌 **Función para cargar archivos SHP una vez y almacenarlos**
@st.cache_data
def load_shapefile(zip_path):
    """Carga el SHP desde un ZIP y almacena los datos en caché."""
    
    if not os.path.exists(TEMP_FOLDER):  
        os.makedirs(TEMP_FOLDER)  # ✅ Crear carpeta si no existe
    
    zip_name = os.path.basename(zip_path)
    extracted_shp = os.path.join(TEMP_FOLDER, zip_name.replace(".zip", ".shp"))

    # ✅ Si el archivo ya se extrajo, úsalo directo
    if os.path.exists(extracted_shp):
        return gpd.read_file(extracted_shp)

    # ✅ Extraer y almacenar el archivo SHP
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(TEMP_FOLDER)  
        shp_files = [f for f in os.listdir(TEMP_FOLDER) if f.endswith(".shp")]

        if not shp_files:
            st.error("❌ No se encontró un archivo .shp en el ZIP.")
            return None

        gdf = gpd.read_file(os.path.join(TEMP_FOLDER, shp_files[0]))
        return gdf.to_crs("EPSG:4326")  # Convertir coordenadas a lat/lon estándar

# ------------------------------------------------------------------------------
# 📌 Interfaz para subir archivo SHP comprimido
st.subheader("Carga tu archivo ZIP con SHP:")
uploaded_file = st.file_uploader("Selecciona el archivo ZIP", type=["zip"])

if uploaded_file:
    zip_path = f"uploaded_{uploaded_file.name}"
    with open(zip_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    gdf = load_shapefile(zip_path)

    if gdf is not None:
        st.write("✅ Archivo cargado correctamente.")
        
        # 📌 Mostrar tabla sin la columna `geometry`
        gdf_no_geom = gdf.drop(columns=["geometry"])
        st.dataframe(gdf_no_geom)  

        # ------------------------------------------------------------------------------
        # 📌 **SECCIÓN 2: Gráfico - Top 10 Estados con Mayor Frecuencia**
        st.header("📊 Top 10 - Estados con mayor frecuencia e intensidad calórica (frpn)")
        '''
        Los estados se obtuvieron de la intersección de los puntos de calor de FIRMS con el marco geoestadístico de INEGI (2023)
        '''

        top_estados = gdf.groupby("CEN").agg({"CEN": "count", "frpn": "sum"}).rename(columns={"CEN": "Frecuencia de pc", "frpn": "Intensidad calórica (MW)"})
        top_estados = top_estados.sort_values("Frecuencia de pc", ascending=False).head(10)

        fig = go.Figure()

        # 📌 Barras de frecuencia en eje izquierdo
        fig.add_trace(go.Bar(
            x=top_estados.index,
            y=top_estados["Frecuencia de pc"],
            name="Frecuencia de pc",
            marker_color="blue",
            yaxis="y"
        ))

        # 📌 Línea de intensidad FRPN en eje derecho
        fig.add_trace(go.Scatter(
            x=top_estados.index,
            y=top_estados["Intensidad calórica (MW)"],
            name="Intensidad calórica (MW)",
            mode="lines+markers",
            line=dict(color="red", width=2),
            yaxis="y2"
        ))

        fig.update_layout(
            title="Top 10 Estados con mayor frecuencia de pc e intensidad calórica (frpn)",
            xaxis_title="Estado",
            yaxis=dict(title="Frecuencia de pc", color="blue"),
            yaxis2=dict(title="Intensidad calórica (MW)", color="red", overlaying="y", side="right"),
            legend_title="Indicadores",
            template="plotly_dark"
        )

        st.plotly_chart(fig)

        # -------------------------------------------------------------------------------------
        # 📌 **SECCIÓN 3: Gráfico - Top 10 Tipos de Vegetación**
        st.header("📊 Top 10 Tipos de vegetación con mayor frecuencia e intensidad calorica")
        '''
        Los tipos de vegetación se obtuvieron de la intersección de los puntos de calor de FIRMS con la serie de uso
        de suelo y vegetación de INEGI (2021)
        '''

        top_vegetacion = gdf.groupby("DESC2").agg({"DESC2": "count", "frpn": "sum"}).rename(columns={"DESC2": "Frecuencia de pc", "frpn": "Intensidad calórica (MW)"})
        top_vegetacion = top_vegetacion.sort_values("Frecuencia de pc", ascending=False).head(10)

        fig = go.Figure()

        # 📌 Barras de frecuencia en eje izquierdo
        fig.add_trace(go.Bar(
            x=top_vegetacion.index,
            y=top_vegetacion["Frecuencia de pc"],
            name="Frecuencia de pc",
            marker_color="green",
            yaxis="y"
        ))

        # 📌 Línea de intensidad FRPN en eje derecho
        fig.add_trace(go.Scatter(
            x=top_vegetacion.index,
            y=top_vegetacion["Intensidad calórica (MW)"],
            name="Intensidad calórica (MW)",
            mode="lines+markers",
            line=dict(color="orange", width=2),
            yaxis="y2"
        ))

        fig.update_layout(
            title="Top 10 - Tipos de vegetación con mayor frecuencia de pc e intensidad calórica",
            xaxis_title="Tipo de vegetación",
            yaxis=dict(title="Frecuencia de pc", color="green"),
            yaxis2=dict(title="Intensidad calórica (MW)", color="orange", overlaying="y", side="right"),
            legend_title="Indicadores",
            template="plotly_dark"
        )

        st.plotly_chart(fig)

        # ------------------------------------------------------------------------------
        # 📌 **SECCIÓN 4: Filtrar Estados y Graficar**
        st.header("🎯 Filtrar estados y generar gráficos")

        estados_seleccionados = st.multiselect(
            "Selecciona los estados", gdf["CEN"].unique(), default=["JAL", "MEX"], key="multiselect_estados"
        )

        df_filtrado_estados = gdf[gdf["CEN"].isin(estados_seleccionados)]

        if not df_filtrado_estados.empty:
            st.subheader("📊 Frecuencia e intensidad calórica por estado")

            top_estados = df_filtrado_estados.groupby("CEN").agg(
                {"CEN": "count", "frpn": "sum"}
            ).rename(columns={"CEN": "Frecuencia de pc", "frpn": "Intensidad calórica (MW)"})

            fig = go.Figure()

            fig.add_trace(go.Bar(
                x=top_estados.index,
                y=top_estados["Frecuencia de pc"],
                name="Frecuencia de pc",
                marker_color="blue",
                yaxis="y"
            ))

            fig.add_trace(go.Scatter(
                x=top_estados.index,
                y=top_estados["Intensidad calórica (MW)"],
                name="Intensidad calórica (MW)",
                mode="lines+markers",
                line=dict(color="red", width=2),
                yaxis="y2"
            ))

            fig.update_layout(
                xaxis_title="Estado",
                yaxis=dict(title="Frecuencia de pc", color="blue"),
                yaxis2=dict(title="Intensidad calórica (MW)", color="red", overlaying="y", side="right"),
                template="plotly_dark"
            )

            st.plotly_chart(fig)
        # ------------------------------------------------------------------------------          
        # 📌 **SECCIÓN 5: Filtrar Tipos de Vegetación y Graficar**
        st.header("🌱 Filtrar Tipos de vegetación y generar gráficos")

        vegetacion_seleccionada = st.multiselect(
            "Selecciona los tipos de vegetación", gdf["DESC2"].unique(), default=["BOSQUE DE ENCINO", "BOSQUE DE PINO"], key="multiselect_vegetacion"
        )

        df_filtrado_vegetacion = gdf[gdf["DESC2"].isin(vegetacion_seleccionada)]

        if not df_filtrado_vegetacion.empty:
            st.subheader("📊 Frecuencia de puntos de calor e intensidad calórica por tipo de vegetación")

            top_vegetacion = df_filtrado_vegetacion.groupby("DESC2").agg(
                {"DESC2": "count", "frpn": "sum"}
            ).rename(columns={"DESC2": "Frecuencia de pc", "frpn": "Intensidad calórica (MW)"})

            fig = go.Figure()

            fig.add_trace(go.Bar(
                x=top_vegetacion.index,
                y=top_vegetacion["Frecuencia de pc"],
                name="Frecuencia de pc",
                marker_color="green",
                yaxis="y"
            ))

            fig.add_trace(go.Scatter(
                x=top_vegetacion.index,
                y=top_vegetacion["Intensidad calórica (MW)"],
                name="Intensidad calórica (MW)",
                mode="lines+markers",
                line=dict(color="orange", width=2),
                yaxis="y2"
            ))

            fig.update_layout(
                xaxis_title="Tipo de vegetación",
                yaxis=dict(title="Frecuencia de pc", color="green"),
                yaxis2=dict(title="Intensidad calórica (MW)", color="orange", overlaying="y", side="right"),
                template="plotly_dark"
            )

            st.plotly_chart(fig)
