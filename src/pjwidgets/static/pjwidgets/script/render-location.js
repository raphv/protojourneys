function renderLocation(widget_id) {
    var mapdata = window['MAP_DATA_'+widget_id],
        latlng = L.latLng([mapdata.latitude, mapdata.longitude]),
        map = null,
        targetCircle = null,
        locInnerCircle = null,
        locOuterCircle = null,
        $locinfo = $('#locinfo-'+widget_id),
        $there = $('#there-'+widget_id),
        $notthere = $('#not-there-'+widget_id);
    if (mapdata.show_map) {
        map = L.map('location-map-'+widget_id).setView(
            latlng, 12
        );
        L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
        targetCircle = L.circle(
            latlng,
            mapdata.maximum_distance,
            {
                color: "#cc0000",
                opacity: .8,
                fillOpacity: .2,
                weight: 1
            }
        );
        targetCircle.addTo(map);
        L.marker(latlng).addTo(map);
        locInnerCircle = L.circle(
            latlng,
            0,
            {
                color: "#0000cc",
                opacity: 0,
                fillOpacity: 0,
                weight: 6
            }
        );
        locInnerCircle.addTo(map);
        locOuterCircle = L.circle(
            latlng,
            0,
            {
                color: "#0000cc",
                opacity: 0,
                fillOpacity: 0,
                weight: 1
            }
        );
        locOuterCircle.addTo(map);
    }
    function distplay(dist) {
        var metric = (dist < 1000) ? (dist.toFixed(0) + 'm') : ((dist/1000).toFixed(1) + 'km');
        var imperial = (dist < 1609) ? ((dist/0.9144).toFixed(0) + 'yds') : ((dist/1609.34).toFixed(1) + 'mi');
        return metric + ' (' + imperial + ')';
    }
    $(window).on('positionfound', function(evt, coords) {
        var loclatlng = [coords.latitude, coords.longitude],
            dist = latlng.distanceTo(loclatlng),
            loctext = 'You are '+distplay(dist)+' away from target location.',
            location_ok = (dist <= mapdata.maximum_distance);
        if (location_ok) {
            $locinfo.removeClass('location-error').addClass('location-ok');
            $there.show();
            $notthere.hide();
        } else {
            $locinfo.removeClass('location-ok').addClass('location-error');
            $there.hide();
            $notthere.show();
            loctext += ' You must be within '+distplay(mapdata.maximum_distance)+' for content to be triggered.';
        }
        $locinfo.text(loctext);
        if (mapdata.show_map) {
            locInnerCircle.setStyle({
                opacity: 1,
            }).setLatLng(loclatlng);
            locOuterCircle.setStyle({
                opacity: .8,
                fillOpacity: .2,
            }).setLatLng(loclatlng).setRadius(coords.accuracy);
            targetCircle.setStyle({
                color: location_ok ? '#008000' : '#cc0000'
            });
        }
    }).on('positionerror', function() {
        $locinfo.text('Browser location not found.')
            .removeClass('location-ok').addClass('location-error');
        $there.hide();
        $notthere.show();
        if (mapdata.show_map) {
            locInnerCircle.setStyle({
                opacity: 0,
            });
            locOuterCircle.setStyle({
                opacity: 0,
                fillOpacity: 0,
            }).setRadius(0);
            targetCircle.setStyle({
                color: '#cc0000'
            });
        }
    });
}
$(function() {
    function getPos() {
        navigator.geolocation.getCurrentPosition(
            function(pos) {
                $(window).trigger('positionfound', [pos.coords]);
            }, 
            function() {
                $(window).trigger('positionerror');
            }
        );
    }
    var interval = setInterval(getPos, 30000);
    getPos();
});