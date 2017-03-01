function renderMap(map_id) {
    var map_data = window['MAP_DATA_' + map_id];
    var map = L.map('map-' + map_id).setView(
        map_data.centre, map_data.zoom
    );
    L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    var BaseIcon = L.Icon.extend({
        options: {
            iconSize:[25,41],
            iconAnchor:[12,41],
            popupAnchor:[1,-34]
        }
    });
    var locatebutton = L.control({
        position: 'topright'
    });
    var currentpos = null;
    locatebutton.onAdd = function(map) {
        var div = L.DomUtil.create('div', 'leaflet-control leaflet-bar'),
            a = L.DomUtil.create('a', 'locate-button fa fa-lg fa-crosshairs', div);
        a.href = "#";
        a.addEventListener('click', function(evt) {
            if (currentpos) {
                map.panTo(currentpos);
            }
            map.locate();
            evt.preventDefault();
        }, false);
        return div;
    };
    locatebutton.addTo(map);
    var locInnerCircle = L.circle(
        [0,0],
        0,
        {
            color: "#0000ff",
            opacity: 0,
            fillOpacity: 0,
            weight: 6
        }
    );
    var locOuterCircle = L.circle(
        [0,0],
        10,
        {
            color: "#0000ff",
            opacity: 0,
            fillOpacity: 0,
            weight: 1
        }
    );
    locOuterCircle.addTo(map);
    locInnerCircle.addTo(map);
    map.on('locationfound', function(e) {
        currentpos = e.latlng;
        map.panTo(e.latlng);
        locInnerCircle.setStyle({
            opacity: 1,
        }).setLatLng(e.latlng);
        locOuterCircle.setStyle({
            opacity: .8,
            fillOpacity: .2,
        }).setLatLng(e.latlng).setRadius(e.accuracy);
        map_data.locations.forEach(function(loc) {
            loc.distance = e.latlng.distanceTo(loc.position);
            loc.marker.setPopupContent(getPopupContent(loc));
        });
    });
    map.on('locationerror', function() {
        currentpos = null;
        locInnerCircle.setStyle({
            opacity: 0,
        });
        locOuterCircle.setStyle({
            opacity: 0,
            fillOpacity: 0,
        });
        map_data.locations.forEach(function(loc) {
            delete loc.distance;
            loc.marker.setPopupContent(getPopupContent(loc));
        });
    });
    var icons = {};
    function getIcon(colour) {
        icons[colour] = icons[colour] || new BaseIcon({
            iconUrl: window.ICON_BASE + 'l-marker-' + colour + '.png'
        });
        return { icon: icons[colour] };
    }
    function getPopupContent(location) {
        var div = $('<div>'),
            baselabel = location.label;
        if (location.distance) {
            if (location.distance > 500) {
                baselabel += (' (' + (location.distance/1000).toFixed(1) + 'km)');
            } else {
                baselabel += (' (' + location.distance.toFixed(0) + 'm)');
            }
        }
        if (location.url) {
            $('<a>').attr({
                href: location.url,
                target: '_blank'
            }).text(baselabel).appendTo(div);
        } else {
            div.text(baselabel);
        }
        return div.html();
    }
    map_data.locations.forEach(function(loc) {
        loc.marker = L.marker(loc.position, getIcon(loc.colour));
        loc.marker.addTo(map);
        loc.marker.bindPopup(getPopupContent(loc));
    });
    $('#map-autocomplete-'+map_id).autocomplete({
        source: map_data.locations,
        minLength: 0,
        select: function(event, ui) {
            _(map_data.locations).each(function(loc) {
                loc.marker.closePopup();
            });
            map.panTo(ui.item.position);
            ui.item.marker.openPopup();
        }
    });
}
