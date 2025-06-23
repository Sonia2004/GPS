let map = L.map('map').setView([19.9561, -99.5307], 14); // Coordenadas de Jilotepec
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

let routeControl;
let waypoints = [];
let mapClickEnabled = false;
let mapNullClickEnabled = false;

// Precios de gasolina
let prices = {
    regular: 24.531,
    premium: 27.095,
    diesel: 25.132
};

// Consumo de gasolina (litros por 100 km)
let consumption = {
    regular: 10,
    premium: 10,
    diesel: 10
};

function addRoute() {
    let input = document.querySelector('.location-input');
    let location = input.value;

    $.getJSON(`https://nominatim.openstreetmap.org/search?format=json&q=${location}`, function(data) {
        if (data && data.length > 0) {
            let latLng = L.latLng(data[0].lat, data[0].lon);
            waypoints.push(latLng);
            updateRoute();

            let marker = L.marker(latLng, {draggable: true}).addTo(map);
            marker.bindPopup(location).openPopup();
            marker.on('dragend', function() {
                waypoints[waypoints.indexOf(latLng)] = marker.getLatLng();
                updateRoute();
            });
        } else {
            mapNullClickEnabled = true;
            $('#mapNullModal').modal('show'); // Mostrar el modal
        }
    });

    input.value = '';
}

function updateRoute() {
    if (routeControl) {
        map.removeControl(routeControl);
    }

    if (waypoints.length > 1) {
        routeControl = L.Routing.control({
            waypoints: waypoints,
            router: L.Routing.osrmv1({
                serviceUrl: 'https://router.project-osrm.org/route/v1',
                language: 'es'  // Configuración del idioma en español
            }),
            createMarker: function() { return null; },
            lineOptions: {
                styles: [{ color: 'red', opacity: 1, weight: 5 }]
            },
            formatter: new L.Routing.Formatter({language: 'es'})
        }).on('routesfound', function(e) {
            let routes = e.routes;
            let summary = routes[0].summary;
            let distance = summary.totalDistance / 1000; // Convertir a kilómetros

            let litersRegular = (distance * consumption.regular) / 100;
            let costRegular = litersRegular * prices.regular;

            let litersPremium = (distance * consumption.premium) / 100;
            let costPremium = litersPremium * prices.premium;

            let litersDiesel = (distance * consumption.diesel) / 100;
            let costDiesel = litersDiesel * prices.diesel;

            document.getElementById('distance').innerHTML = `Distancia: ${distance.toFixed(2)} km`;
            document.getElementById('gasoline').innerHTML = `Consumo de gasolina: ${litersRegular.toFixed(2)} litros (Promedio)`;
            document.getElementById('cost').innerHTML = `Costo Total: $${costRegular.toFixed(2)} MXN (Promedio)`;
        }).addTo(map);

        map.fitBounds(L.latLngBounds(waypoints));
    }
}

function enableMapClick() {
    mapClickEnabled = true;
    $('#mapModal').modal('show'); // Mostrar el modal
}

map.on('click', function(e) {
    if (mapClickEnabled) {
        waypoints.push(e.latlng);
        updateRoute();

        let marker = L.marker(e.latlng, {draggable: true}).addTo(map);
        marker.bindPopup("Punto " + waypoints.length).openPopup();
        marker.on('dragend', function() {
            waypoints[waypoints.indexOf(e.latlng)] = marker.getLatLng();
            updateRoute();
        });

        mapClickEnabled = false;
    }
});

$(document).on('focus', '.location-input', function() {
    $(this).autocomplete({
        source: function(request, response) {
            $.getJSON(`https://nominatim.openstreetmap.org/search?format=json&limit=5&q=${request.term}`, function(data) {
                response(data.map(function(item) {
                    return {
                        label: item.display_name,
                        value: item.display_name
                    };
                }));
            });
        },
        minLength: 3,
    });
});
