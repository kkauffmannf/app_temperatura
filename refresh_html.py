import pandas as pd
import requests
import json
from datetime import timedelta
import folium
import branca.colormap as cm
from pathlib import Path
from dotenv import load_dotenv
import os

# define path and load credentials

local_path = '/home/karla/Documents/Incendios/app_temperatura/'
env_path = Path(f'{local_path}.') / '.env'
load_dotenv(dotenv_path=env_path)
DGAC_EMAIL = os.environ.get('DGAC_EMAIL')
DGAC_APIKEY = os.environ.get('DGAC_APIKEY')

# hace un request a la API de la direccion meteorologica de Chile

def refresh_web():

    # url = 'https://climatologia.meteochile.gob.cl/application/productos/datosRecientesRedEma'
    url = 'https://climatologia.meteochile.gob.cl/application/servicios/getDatosRecientesRedEma?usuario=' + DGAC_EMAIL + '&token=' + DGAC_APIKEY
    response = json.loads(requests.get(url).text)
    df_temp = pd.json_normalize(response['datosEstaciones'])
    df_temp['estacion.nombreEstacion'] = df_temp['estacion.nombreEstacion'].apply(lambda x: x.encode('latin_1').decode('utf8'))

    # extrae solo la primera entrada de la lista de diccionarios que hay
    # para cada estación en 'datos', ya que esa es la medición más reciente
    # se guarda en la columna 'datos_now'

    df_temp['datos_now'] = df_temp['datos'].str[0]

    # de la medición más reciente (formato diccionario)
    # se extrae la temperatura y el tiempo

    df_temp['momento'] = df_temp['datos_now'].str['momento']
    df_temp['temp_now'] = df_temp['datos_now'].str['temperatura']

    # se saca el grados Celsius y se transforma la columna a numérico

    df_temp['temp_now'] = df_temp['temp_now'].replace(to_replace ='°C', value = '', regex = True)
    df_temp['temp_now'] = pd.to_numeric(df_temp['temp_now'])
    df_temp['estacion.latitud'] = pd.to_numeric(df_temp['estacion.latitud'])
    df_temp['estacion.longitud'] = pd.to_numeric(df_temp['estacion.longitud'])
    df_temp.dropna(inplace=True)

    # Se le restan 4 horas para que quede en la hora de Chile continental. Se pasa
    # a string, porque al llevarlo a lista (necesario para el mapa) se pierde el 
    # formato original

    df_temp['momento'] = pd.to_datetime(df_temp.momento, format='%Y-%m-%d %H:%M:%S')
    df_temp['momento'] = df_temp['momento']- timedelta(hours=4, minutes=0)
    df_temp['momento'] = df_temp['momento'].dt.strftime('%H:%M')
    df_temp['momento'] = df_temp['momento'].astype(str)

    # Create a base map centered at a specific location
    map_center = [-33.447487, -70.673676]  # Coordinates for New York City
    map_zoom = 10
    map_object = folium.Map(location=map_center, zoom_start=map_zoom)

    lons = df_temp['estacion.longitud'].values.tolist()
    lats = df_temp['estacion.latitud'].values.tolist()
    temps = df_temp['temp_now'].values.tolist()
    momentos = df_temp['momento'].values.tolist()
    nombre_estacion = df_temp['estacion.nombreEstacion'].values.tolist()

    linear = cm.LinearColormap(["blue", "lightyellow" , "red"]).scale(min(temps), max(temps))

    for n in range(len(lons)-1):
        
        html_msg = """
                    <ul>
                    <li> Temperatura: {}</li>""".format(temps[n]) + """
                    <li> Hora registrada: {}</li>""".format(momentos[n]) + """
                    <li> Nombre lugar: {}</li>""".format(nombre_estacion[n]) + """
                    </ul>
                    """
        
        folium.CircleMarker([lats[n], lons[n]],
                            radius = 15,
                            stroke = False,
                            weight = 1,
                            color = 'black',
                            #tooltip = [temps[n], momentos[n]],
                            #tooltip = '<h1> This is a big popup</h1><br> With a few lines of code... <p><code>sfdsfds</p>',
                            tooltip = html_msg,
                            fillOpacity = 0.9,
                            fill_color = linear(temps[n])).add_to(map_object)
        
    linear.caption = "Temperaturas"
    linear.width = 200
    map_object.add_child(linear)
        
    # Display the map
    #map_object
    # Save the map to an HTML file
    map_object.save('templates/weather_test_now.html')
