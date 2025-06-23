from flask import Flask, request, render_template, jsonify
import networkx as nx
import random
import math

app = Flask(__name__)

# Restricciones
RESTRICCIONES = {
    "distancia_max_km": 100,
    "tiempo_max_min": 60,
    "paradas_max": 10,
    "costo_total_max_mxn": 400
}

# Parámetros
RENDIMIENTO_KM_POR_LITRO = 10
PRECIO_LITRO_MXN = 22
COSTO_PEAJES_POR_KM = 3
VELOCIDAD_KM_POR_MIN = 1.5

# Zonas prohibidas definidas manualmente (coordenadas aproximadas)
ZONAS_PROHIBIDAS = [
    ((19.95, -99.54), (19.96, -99.53)),  # rectángulo 1
    ((19.94, -99.52), (19.945, -99.515)) # rectángulo 2
]

def esta_en_zona_prohibida(p):
    for (lat1, lon1), (lat2, lon2) in ZONAS_PROHIBIDAS:
        if min(lat1, lat2) <= p[0] <= max(lat1, lat2) and min(lon1, lon2) <= p[1] <= max(lon1, lon2):
            return True
    return False

# Distancias

def distancia_manhattan(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def distancia_euclidea(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

# Grafo

def construir_grafo(puntos, usar_manhattan=False):
    G = nx.Graph()
    for i, punto in enumerate(puntos):
        if esta_en_zona_prohibida(punto):
            continue
        G.add_node(i, pos=punto)
    for i in G.nodes:
        for j in G.nodes:
            if i >= j:
                continue
            p1, p2 = G.nodes[i]['pos'], G.nodes[j]['pos']
            if esta_en_zona_prohibida(p1) or esta_en_zona_prohibida(p2):
                continue
            dist = distancia_manhattan(p1, p2) if usar_manhattan else distancia_euclidea(p1, p2)
            G.add_edge(i, j, weight=dist)
    return G

# Algoritmos

def dijkstra(puntos):
    G = construir_grafo(puntos)
    try:
        ruta_nodos = nx.dijkstra_path(G, source=0, target=len(puntos)-1, weight='weight')
        return [G.nodes[n]['pos'] for n in ruta_nodos]
    except:
        return [puntos[0], puntos[-1]]

def manhattan(puntos):
    G = construir_grafo(puntos, usar_manhattan=True)
    try:
        ruta_nodos = nx.dijkstra_path(G, source=0, target=len(puntos)-1, weight='weight')
        return [G.nodes[n]['pos'] for n in ruta_nodos]
    except:
        return [puntos[0], puntos[-1]]

def hill_climbing(puntos):
    def calcular_distancia_total(ruta):
        return sum(distancia_euclidea(ruta[i], ruta[i+1]) for i in range(len(ruta)-1))

    if len(puntos) <= 2:
        return puntos

    ruta_actual = puntos[:]
    mejor_costo = calcular_distancia_total(ruta_actual)

    for _ in range(500):
        i, j = random.sample(range(1, len(ruta_actual)-1), 2)
        nueva_ruta = ruta_actual[:]
        nueva_ruta[i], nueva_ruta[j] = nueva_ruta[j], nueva_ruta[i]
        if any(esta_en_zona_prohibida(p) for p in nueva_ruta):
            continue
        nuevo_costo = calcular_distancia_total(nueva_ruta)
        if nuevo_costo < mejor_costo:
            ruta_actual = nueva_ruta
            mejor_costo = nuevo_costo

    return ruta_actual

def genetico(puntos):
    def calcular_costo(ruta):
        return sum(distancia_euclidea(ruta[i], ruta[i+1]) for i in range(len(ruta)-1))

    def cruzar(p1, p2):
        inicio, fin = sorted(random.sample(range(1, len(p1)-1), 2))
        centro = p1[inicio:fin]
        resto = [p for p in p2 if p not in centro]
        return resto[:inicio] + centro + resto[inicio:]

    def mutar(ruta):
        i, j = random.sample(range(1, len(ruta)-1), 2)
        ruta[i], ruta[j] = ruta[j], ruta[i]
        return ruta

    poblacion = [puntos[:1] + random.sample(puntos[1:-1], len(puntos)-2) + puntos[-1:] for _ in range(30)]

    for _ in range(50):
        poblacion = [r for r in poblacion if not any(esta_en_zona_prohibida(p) for p in r)]
        poblacion = sorted(poblacion, key=calcular_costo)
        nueva_gen = poblacion[:10]
        while len(nueva_gen) < 30:
            padres = random.sample(poblacion[:15], 2)
            hijo = cruzar(padres[0], padres[1])
            hijo = mutar(hijo)
            if not any(esta_en_zona_prohibida(p) for p in hijo):
                nueva_gen.append(hijo)
        poblacion = nueva_gen

    mejor_ruta = min(poblacion, key=calcular_costo)
    return mejor_ruta

# Métricas

def calcular_metricas(ruta):
    distancia_total = sum(distancia_euclidea(ruta[i], ruta[i+1]) for i in range(len(ruta)-1))
    tiempo_estimado = distancia_total / VELOCIDAD_KM_POR_MIN
    consumo_combustible = distancia_total / RENDIMIENTO_KM_POR_LITRO
    costo_combustible = consumo_combustible * PRECIO_LITRO_MXN
    costo_peajes = distancia_total * COSTO_PEAJES_POR_KM
    costo_total = costo_combustible + costo_peajes

    return {
        "distancia_total_km": round(distancia_total, 2),
        "tiempo_estimado_min": round(tiempo_estimado, 2),
        "consumo_combustible_litros": round(consumo_combustible, 2),
        "costo_combustible_mxn": round(costo_combustible, 2),
        "costo_peajes_mxn": round(costo_peajes, 2),
        "costo_total_mxn": round(costo_total, 2)
    }

# Rutas

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calcular-ruta', methods=['POST'])
def calcular_ruta():
    data = request.get_json()
    puntos = data.get("puntos")
    algoritmo = data.get("algoritmo")

    if not puntos or not algoritmo:
        return jsonify({"error": "Faltan datos obligatorios"}), 400

    if len(puntos) < 2:
        return jsonify({"error": "Se necesitan al menos dos puntos"}), 400

    if algoritmo == "dijkstra":
        ruta = dijkstra(puntos)
    elif algoritmo == "manhattan":
        ruta = manhattan(puntos)
    elif algoritmo == "hill":
        ruta = hill_climbing(puntos)
    elif algoritmo == "genetico":
        ruta = genetico(puntos)
    else:
        return jsonify({"error": "Algoritmo no reconocido"}), 400

    metricas = calcular_metricas(ruta)

    return jsonify({
        "ruta": ruta,
        "metricas": metricas
    })

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)


