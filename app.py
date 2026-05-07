import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import base64

# Configure page layout to wide and set title
st.set_page_config(layout="wide", page_title="OYA Dashboard")

# Initialize CurrentScreen property in session state
if 'CurrentScreen' not in st.session_state:
    st.session_state.CurrentScreen = "Météo"

# ---------------------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------------------
st.sidebar.title("Tableau de bord OYA")

# Add logo to the sidebar
st.sidebar.markdown("<br>", unsafe_allow_html=True) 
col_side_empty, col_side_logo, col_side_empty2 = st.sidebar.columns([1, 4, 1])
with col_side_logo:
    # Check for logo.png or logo.jpg
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    elif os.path.exists("logo.jpg"):
        st.image("logo.jpg", use_container_width=True)
    else:
        st.markdown("<div style='text-align:center; padding: 10px; border: 1px dashed rgba(255,255,255,0.3); border-radius: 8px; color:rgba(255,255,255,0.6);'>Placez <b>logo.png</b> dans votre dossier</div>", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Navigation menu
selected_menu = st.sidebar.radio(
    "Navigation",
    ["Météo", "Réglages OYA"],
    index=["Météo", "Réglages OYA"].index(st.session_state.CurrentScreen)
)
st.session_state.CurrentScreen = selected_menu

# --- UTILITY FUNCTIONS ---

# Function to map WMO weather codes to emojis and CSS gradients
def get_weather_info(wmo_code):
    if wmo_code in [0, 1]: return "☀️", "linear-gradient(to bottom, #4A90E2, #87CEEB)" # Sun
    elif wmo_code in [2, 3]: return "☁️", "linear-gradient(to bottom, #757F9A, #D7DDE8)" # Cloud
    elif wmo_code in [45, 48]: return "🌫️", "linear-gradient(to bottom, #B9935A, #E7E9BB)" # Fog
    elif wmo_code in [51, 53, 55, 61, 63, 65, 80, 81, 82]: return "🌧️", "linear-gradient(to bottom, #2c3e50, #3498db)" # Rain
    elif wmo_code in [71, 73, 75, 85, 86]: return "❄️", "linear-gradient(to bottom, #E0EAFC, #CFDEF3)" # Snow
    elif wmo_code in [95, 96, 99]: return "⛈️", "linear-gradient(to bottom, #141E30, #243B55)" # Thunderstorm
    return "🌡️", "linear-gradient(to bottom, #2C3E50, #000000)"

# Function to display an image with custom CSS opacity using base64 encoding
def get_transparent_image_html(filepath, opacity=0.65):
    with open(filepath, "rb") as img_file:
        encoded_string = base64.b64encode(img_file.read()).decode()
    ext = filepath.split('.')[-1]
    return f'<img src="data:image/{ext};base64,{encoded_string}" style="width: 100%; border-radius: 15px; opacity: {opacity}; object-fit: cover;">'

# Dictionaries for French day translations
short_days_fr = {"Monday": "Lun", "Tuesday": "Mar", "Wednesday": "Mer", "Thursday": "Jeu", "Friday": "Ven", "Saturday": "Sam", "Sunday": "Dim"}
full_days_fr = {"Monday": "Lundi", "Tuesday": "Mardi", "Wednesday": "Mercredi", "Thursday": "Jeudi", "Friday": "Vendredi", "Saturday": "Samedi", "Sunday": "Dimanche"}

# Fetch weather data with caching to prevent excessive API calls
@st.cache_data(ttl=3600)
def fetch_weather(city_name):
    # Geocoding API (DataGouv)
    url_geo = f"https://api-adresse.data.gouv.fr/search/?q={city_name}"
    geo_response = requests.get(url_geo, timeout=8)
    geo_response.raise_for_status()
    geo_data = geo_response.json()
    
    if not geo_data['features']:
        return None, f"Ville '{city_name}' introuvable."
        
    coords = geo_data['features'][0]['geometry']['coordinates']
    lon, lat = coords[0], coords[1]

    # Weather API (Open-Meteo)
    meteo_url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,wind_gusts_10m,weathercode"
        f"&hourly=temperature_2m,relative_humidity_2m,wind_gusts_10m,precipitation"
        f"&daily=temperature_2m_max,temperature_2m_min,weathercode"
        f"&timezone=Europe%2FParis"
    )
    meteo_response = requests.get(meteo_url, timeout=10)
    meteo_response.raise_for_status()
    return meteo_response.json(), None

# ---------------------------------------------------------
# SCREEN 1: WEATHER DASHBOARD
# ---------------------------------------------------------
if st.session_state.CurrentScreen == "Météo":
    # City input layout
    col_input, _ = st.columns([1, 3])
    with col_input:
        city = st.text_input("📍 Ville de déploiement", "Montagny")
    
    if st.button("Actualiser la météo"):
        st.session_state.city_search = city

    if "city_search" in st.session_state:
        with st.spinner("Synchronisation avec les satellites..."):
            try:
                meteo_data, error_msg = fetch_weather(st.session_state.city_search)
                
                if error_msg:
                    st.error(error_msg)
                else:
                    # Extract current conditions
                    current = meteo_data.get('current', {})
                    current_weather_code = current.get('weathercode', 0)
                    icon, bg_gradient = get_weather_info(current_weather_code)

                    # Inject dynamic CSS based on weather conditions
                    st.markdown(f"""
                    <style>
                    .stApp {{
                        background: {bg_gradient};
                        color: white;
                    }}
                    .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp div {{
                        color: white !important;
                    }}
                    .oya-card {{
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 15px;
                        padding: 20px;
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        text-align: center;
                        transition: all 0.3s ease;
                    }}
                    </style>
                    """, unsafe_allow_html=True)

                    # Main Header and transparent OYA Image
                    st.markdown(f"<h1 style='text-align: center; font-size: 3rem;'>{st.session_state.city_search}</h1>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    col_img_empty, col_img_center, col_img_empty2 = st.columns([1, 4, 1])
                    with col_img_center:
                        if os.path.exists("IMAGE_OYA.jpg"):
                            st.markdown(get_transparent_image_html("IMAGE_OYA.jpg", opacity=0.65), unsafe_allow_html=True)
                        else:
                            st.markdown("<div style='text-align:center; padding: 40px; border: 2px dashed rgba(255,255,255,0.3); border-radius: 12px; color:rgba(255,255,255,0.6);'>Placez <b>IMAGE_OYA.jpg</b> dans votre dossier</div>", unsafe_allow_html=True)
                    
                    st.write("---")
                    
                    # --- INTERACTIVE DATA SECTION ---
                    st.write("### 📅 Analyse détaillée par journée")
                    
                    # Create DataFrame from hourly API data (including humidity)
                    hourly = meteo_data.get('hourly', {})
                    df_hourly = pd.DataFrame({
                        'Date': pd.to_datetime(hourly.get('time')),
                        'Température (°C)': hourly.get('temperature_2m'),
                        'Humidité (%)': hourly.get('relative_humidity_2m'),
                        'Rafales (km/h)': hourly.get('wind_gusts_10m'),
                        'Précipitations (mm)': hourly.get('precipitation'),
                    })
                    
                    now = pd.Timestamp.now(tz='Europe/Paris').tz_localize(None)
                    unique_dates = df_hourly['Date'].dt.date.unique()[:7]
                    
                    # Build date labels with full French day names
                    date_labels = []
                    for d in unique_dates:
                        if d == now.date():
                            date_labels.append(f"Aujourd'hui ({d.strftime('%d/%m')})")
                        else:
                            day_en = d.strftime('%A')
                            day_fr = full_days_fr.get(day_en, day_en)
                            date_labels.append(f"{day_fr} {d.strftime('%d/%m')}")
                    
                    # Day selector radio buttons (placed above the KPI cards to control them)
                    selected_label = st.radio("Afficher les données pour la journée du :", date_labels, horizontal=True)
                    selected_index = date_labels.index(selected_label)
                    target_date = unique_dates[selected_index]
                    
                    # Filter data for the selected date
                    df_hourly_filtered = df_hourly[df_hourly['Date'].dt.date == target_date].copy()
                    if target_date == now.date():
                        df_hourly_filtered = df_hourly_filtered[df_hourly_filtered['Date'] >= now.replace(minute=0, second=0, microsecond=0)]
                    df_hourly_filtered['Heure'] = df_hourly_filtered['Date'].dt.strftime('%H:%M')

                    # Check for safety warnings on the selected day
                    max_wind_day = df_hourly_filtered['Rafales (km/h)'].max()
                    wind_warning = max_wind_day > 36

                    # Compute values for the dynamic KPI cards
                    if target_date == now.date():
                        t_val = f"{current.get('temperature_2m', 0)}°"
                        w_val = f"{current.get('wind_gusts_10m', 0)} km/h"
                        h_val = f"{current.get('relative_humidity_2m', 0)}%"
                    else:
                        t_val = f"{df_hourly_filtered['Température (°C)'].max():.1f}°"
                        w_val = f"{max_wind_day:.1f} km/h"
                        h_val = f"{int(df_hourly_filtered['Humidité (%)'].mean())}%"

                    # Display dynamic KPI cards
                    st.markdown("<br>", unsafe_allow_html=True)
                    m1, m2, m3 = st.columns(3)
                    with m1:
                        st.markdown(f"<div class='oya-card'><h3>🌡️ Température</h3><h1>{t_val}</h1></div>", unsafe_allow_html=True)
                    with m2:
                        warning_icon = "⚠️" if wind_warning else "💨"
                        st.markdown(f"<div class='oya-card'><h3>{warning_icon} Rafales</h3><h1>{w_val}</h1></div>", unsafe_allow_html=True)
                    with m3:
                        st.markdown(f"<div class='oya-card'><h3>💧 Humidité</h3><h1>{h_val}</h1></div>", unsafe_allow_html=True)

                    # --- HOURLY CHARTS ---
                    st.write("### 🕒 Graphiques horaires")
                    
                    # Base Plotly layout configuration
                    layout_plotly = dict(
                        plot_bgcolor='rgba(0,0,0,0)', 
                        paper_bgcolor='rgba(0,0,0,0)', 
                        xaxis_tickangle=-45, 
                        margin=dict(l=0, r=0, t=30, b=0),
                        font=dict(color="white")
                    )

                    # Display charts in 3 columns
                    col_g1, col_g2, col_g3 = st.columns(3)
                    
                    with col_g1:
                        # Display warning context if threshold is met
                        if wind_warning:
                            st.write("**💨 Rafales (km/h) ⚠️**")
                        else:
                            st.write("**💨 Rafales (km/h)**")
                            
                        fig_wind = px.line(df_hourly_filtered, x='Heure', y='Rafales (km/h)', template='plotly_dark')
                        fig_wind.update_layout(**layout_plotly)
                        fig_wind.update_traces(line_color='#ff4b4b', line_width=3)
                        
                        # Add a safety threshold line at 36 km/h
                        fig_wind.add_hline(y=36, line_dash="dot", line_color="rgba(255, 255, 255, 0.4)", line_width=1.5)
                        
                        st.plotly_chart(fig_wind, use_container_width=True, key="wind_chart")
                        
                        # Display warning bubble below the chart
                        if wind_warning:
                            st.warning("⚠️ Il est recommandé de plier la structure pour sa sécurité.")
                            
                    with col_g2:
                        st.write("**🌡️ Température (°C)**")
                        fig_temp = px.line(df_hourly_filtered, x='Heure', y='Température (°C)', template='plotly_dark')
                        fig_temp.update_layout(**layout_plotly)
                        fig_temp.update_traces(line_color='#ffaa00', line_width=3)
                        st.plotly_chart(fig_temp, use_container_width=True, key="temp_chart")
                        
                    with col_g3:
                        st.write("**🌧️ Précipitations (mm)**")
                        fig_precip = px.bar(df_hourly_filtered, x='Heure', y='Précipitations (mm)', template='plotly_dark')
                        fig_precip.update_layout(**layout_plotly)
                        fig_precip.update_traces(marker_color='#00aaff')
                        st.plotly_chart(fig_precip, use_container_width=True, key="precip_chart")

                    st.write("---")

                    # --- 7-DAY FORECAST (Apple Style UI) ---
                    st.write("### 📅 Vue globale sur 7 jours")
                    daily = meteo_data.get('daily', {})
                    dates = pd.to_datetime(daily.get('time'))
                    
                    # Build HTML string for the 7-day forecast
                    html_forecast = "<div style='background: rgba(0,0,0,0.2); padding: 20px; border-radius: 15px; width: 100%; max-width: 800px; margin: 0 auto;'>"
                    
                    for i in range(len(dates)):
                        jour_en = dates[i].strftime('%A')
                        jour_fr = short_days_fr.get(jour_en, jour_en)
                        if i == 0: jour_fr = "Auj."
                        
                        icon_d, _ = get_weather_info(daily.get('weathercode')[i])
                        t_min = daily.get('temperature_2m_min')[i]
                        t_max = daily.get('temperature_2m_max')[i]
                        
                        html_forecast += f"""<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; font-size: 1.2rem;'>
<div style='width: 60px; text-align: left; font-weight: bold;'>{jour_fr}</div>
<div style='width: 40px; text-align: center; font-size: 1.4rem;'>{icon_d}</div>
<div style='width: 60px; text-align: right; color: #87CEEB; font-weight: bold; opacity: 0.9;'>{t_min}°</div>
<div style='flex-grow: 1; margin: 0 20px; height: 6px; background: rgba(255,255,255,0.15); border-radius: 10px; position: relative;'>
<div style='position: absolute; left: 20%; right: 20%; top: 0; bottom: 0; background: linear-gradient(90deg, #87CEEB, #ffffff); border-radius: 10px; opacity: 0.8;'></div>
</div>
<div style='width: 60px; text-align: right; color: white; font-weight: bold;'>{t_max}°</div>
</div>"""
                    
                    html_forecast += "</div>"
                    st.markdown(html_forecast, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Execution Error. Details: {e}")

# ---------------------------------------------------------
# SCREEN 2: MACHINE SETTINGS
# ---------------------------------------------------------
elif st.session_state.CurrentScreen == "Réglages OYA":
    st.title("⚙️ Paramètres OYA")
    max_wind = st.slider("Rafales de vent max (km/h)", 20, 80, 50)
    st.warning(f"Repli automatique si rafales > {max_wind} km/h.")