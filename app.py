from flask import Flask, render_template
import folium
import networkx as nx

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def dijkstra():
    # Creamos un grafo vacío
    G = nx.Graph()

    # Creamos un mapa de folium centrado en una ubicación inicial
    mapa = folium.Map(location=[19.685, -98.87], zoom_start=10)

    # Lista para almacenar los marcadores de los puntos seleccionados
    marcadores = []
    ubicaciones = []

    # Función para manejar el evento de hacer clic en el mapa
    def al_hacer_clic_en_mapa(evento):
        lat, lon = evento.latlng
        marcador = folium.Marker(location=[lat, lon])
        mapa.add_child(marcador)
        marcadores.append(marcador)
        ubicaciones.append((lat, lon))
        if len(ubicaciones) > 1:
            # Calcular la ruta óptima usando el algoritmo de Dijkstra
            ruta_optima = calcular_ruta_optima_dijkstra(ubicaciones)
            # Agregar la ruta al mapa
            folium.PolyLine(locations=ruta_optima, color='blue').add_to(mapa)

    # Función para calcular la distancia Manhattan entre dos puntos
    def calcular_distancia_manhattan(p1, p2):
        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

    # Función para calcular la ruta óptima utilizando Dijkstra
    def calcular_ruta_optima_dijkstra(ubicaciones):
        ruta_optima = []
        G.clear()
        # Agregar los nodos al grafo utilizando las coordenadas
        for i, ubicacion in enumerate(ubicaciones):
            G.add_node(i, pos=ubicacion)
        # Agregar las aristas al grafo con distancia Manhattan
        for i in range(len(ubicaciones)):
            for j in range(i+1, len(ubicaciones)):
                dist = calcular_distancia_manhattan(ubicaciones[i], ubicaciones[j])
                G.add_edge(i, j, weight=dist)
        # Calcular la ruta óptima utilizando Dijkstra
        ruta_optima_dijkstra = nx.dijkstra_path(
            G, source=0, target=len(ubicaciones)-1, weight='weight')
        for nodo in ruta_optima_dijkstra:
            ruta_optima.append(ubicaciones[nodo])
        return ruta_optima

    # Agregamos el control de eventos de clic al mapa
    mapa.add_child(folium.ClickForMarker(popup='Punto seleccionado'))

    # Ejecutamos la función al_hacer_clic_en_mapa cuando se hace clic en el mapa
    mapa.on_click(al_hacer_clic_en_mapa)

    # Mostramos el mapa
    return mapa

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)


