// todo 1 reuse this for index,connection, and route, just pass a different *passed_route*
// might need to rewrite the API to pass a collection instaed of a single route
//  e.g. figure out how to pass through the list of route #s and then fetch and concatenate the individual route geojsons (probably write another API call, easier to do in python than JS?)


mapboxgl.accessToken = 'pk.eyJ1IjoiYml0c2FuZGF0b21zIiwiYSI6ImNqbDhvZnl1YjB4NHczcGxsbTF6bWRjMWQifQ.w2TI_q7ClI4JE5I7QU3hEA';
var map = new mapboxgl.Map({
    container: 'map',
    style: "mapbox://styles/mapbox/light-v9",
    center: [-74.50, 40], // starting position [lng, lat]
    zoom: 7 // starting zoom
});


// zoom implemented using https://stackoverflow.com/questions/49354133/turf-js-to-find-bounding-box-of-data-loaded-with-mapbox-gl-js


// e.g.
// var url_waypoints = ("/api/v1/maps?layer=waypoints&rt="+passed_route);
// for index, just set passed_route = "all" in the HTML

// var url_waypoints = ("/api/v1/maps?layer=waypoints&rt=all");
// var url_stops = ("/api/v1/maps?layer=stops&rt=all");
// var url_vehicles = ("/api/v1/maps?layer=vehicles&rt=all");

var url_waypoints = ("/api/v1/maps?layer=waypoints&rt="+passed_route);
var url_stops = ("/api/v1/maps?layer=stops&rt="+passed_route);
var url_vehicles = ("/api/v1/maps?layer=vehicles&rt="+passed_route);

map.on('load', function() {

    $.getJSON(url_waypoints, (geojson) => {
        map.addSource('waypoints_source', {
            type: 'geojson',
            data: geojson
        });
        map.fitBounds(turf.bbox(geojson), {padding: 20});

        map.addLayer({
            "id": "route",
            "type": "line",
            "source": "waypoints_source",
            "paint": {
                "line-color": "blue",
                "line-opacity": 0.75,
                "line-width": 3
            }
        });
    });

    $.getJSON(url_stops, (geojson) => {
        map.addSource('stops_source', {
            type: 'geojson',
            data: geojson
        });
        map.fitBounds(turf.bbox(geojson), {padding: 20});

        map.addLayer({
            "id": "route",
            "type": "line",
            "source": "stops_source",
            "paint": {
                "line-color": "blue",
                "line-opacity": 0.75,
                "line-width": 3
            }
        },"waypoints"); // layer to add before
    });


    $.getJSON(url_vehicles, (geojson) => {
        map.addSource('vehicles_source', {
            type: 'geojson',
            data: geojson
        });
        map.fitBounds(turf.bbox(geojson), {padding: 20});

        map.addLayer({
            "id": "vehicles",
            "type": "circle",
            "source": "vehicles_source",
            "paint": {
                "circle-radius": 4,
                "circle-opacity": 1,
                "circle-stroke-width": 3,
                "circle-stroke-color": "#f6c"
            }
         },"stops") // layer to add before
        ;

    })


});

// map.moveLayer("stops","waypoints");
// map.moveLayer("vehicles","stops");

map.addControl(new mapboxgl.NavigationControl());

