$(function() {
    var latlng = [$('#id_latitude').val(), $('#id_longitude').val()];
    var map = L.map('map').setView(
        latlng, 12
    );
    map.doubleClickZoom.disable();
    L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    var maxDistCircle = L.circle(
        latlng,
        $('#id_maximum_distance').val(),
        {
            color: "#cc0000",
            opacity: .8,
            fillOpacity: .2,
            weight: 1
        }
    );
    maxDistCircle.addTo(map);
    var marker = L.marker(latlng);
    marker.addTo(map);
    marker.dragging.enable();
    marker.on('dragend', function() {
        var markLatLng = marker.getLatLng();
        maxDistCircle.setLatLng(markLatLng);
        $('#id_latitude').val(markLatLng.lat.toFixed(5));
        $('#id_longitude').val(markLatLng.lng.toFixed(5));
        map.panTo(markLatLng);
    });
    map.on('dblclick', function(e) {
        marker.setLatLng(e.latlng);
        maxDistCircle.setLatLng(e.latlng);
        $('#id_latitude').val(e.latlng.lat.toFixed(5));
        $('#id_longitude').val(e.latlng.lng.toFixed(5));
        map.panTo(e.latlng);
    });
    $('#id_latitude,#id_longitude').on('change keyup', function() {
        var newlatlng = [
            $('#id_latitude').val(),
            $('#id_longitude').val()
        ];
        marker.setLatLng(newlatlng);
        maxDistCircle.setLatLng(newlatlng);
    });
    $('#id_maximum_distance').on('change keyup', function() {
        maxDistCircle.setRadius($('#id_maximum_distance').val());
    });
    map.on('locationfound', function(e) {
        $('#id_latitude').val(e.latlng.lat.toFixed(5));
        $('#id_longitude').val(e.latlng.lng.toFixed(5));
        marker.setLatLng(e.latlng);
        maxDistCircle.setLatLng(e.latlng);
        map.panTo(e.latlng);
    });
    $('#current-pos').click(function() {
        map.locate();
        return false;
    });
});