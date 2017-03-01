$(function() {
    var map = L.map('map').setView(
        window.MAP_DATA.centre, window.MAP_DATA.zoom
    );
    map.doubleClickZoom.disable();
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
    var icons = {};
    function getIcon(colour) {
        icons[colour] = icons[colour] || new BaseIcon({
            iconUrl: window.ICON_BASE + 'l-marker-' + colour + '.png'
        });
        return icons[colour];
    }
    function getPopupContent(text, url) {
        var div = $('<div>');
        if (url) {
            $('<a>').attr({
                href: url,
                target: '_blank'
            }).text(text).appendTo(div);
        } else {
            div.text(text);
        }
        return div.html();
    }
    _(window.MAP_DATA.locations).each(function(loc) {
        loc.marker = L.marker(
            loc.position, {
                icon: getIcon(loc.colour),
                draggable: true
            }
        );
        loc.marker.addTo(map);
        var $item = $('input[name^="locations-"][name$="-id"][value="' + loc.id + '"]').parents("li.location");
        $item[0].marker = loc.marker;
        loc.marker.on('dragstart click', function() {
            $item.css('background', '#ffcc80');
            setTimeout(function() {
                $item.css('background', '');
            }, 500);
        });
        loc.marker.on('dragend', function() {
            var markLatLng = loc.marker.getLatLng();
            $item.find('input[name$="latitude"]').val(markLatLng.lat.toFixed(5));
            $item.find('input[name$="longitude"]').val(markLatLng.lng.toFixed(5));
        });
        function markerFromInput() {
            loc.marker.setLatLng([
                $item.find('input[name$="latitude"]').val(),
                $item.find('input[name$="longitude"]').val()
            ]);
        }
        function labelsFromInput() {
            var label = $item.find('input[name$="label"]').val();
            var url = $item.find('input[name$="link_url"]').val();
            $item.find('.location-label').text(label);
            loc.marker.setPopupContent(
                getPopupContent(label, url)
            );
        }
        $item.find('input[name$="latitude"],input[name$="longitude"]').on('keyup change', markerFromInput);
        $item.find('form').on('coordinates-changed', function() {
            markerFromInput();
            labelsFromInput();
        });
        $item.find('input[name$="label"]').on('keyup change', labelsFromInput);
        $item.find('.edit-location-button').click(function() {
            if (loc.editing) {
                loc.stopEditing();
            } else {
                loc.startEditing();
            }
            return false;
        });
        $item.find('.centre-button').click(function() {
            map.panTo(loc.marker.getLatLng());
        });
        if ($item.hasClass('show-open')) {
            loc.startEditing();
        }
    });
    var $empty = $('input[name^="locations-"][name$="-id"]').filter(function() {
        return !this.value;
    }).parents("li.location");
    var $emptylat = $empty.find('input[name$="latitude"]');
    var $emptylng = $empty.find('input[name$="longitude"]');
    var addMarker = L.marker(
        [0.,0.], {
            icon: getIcon('blue'),
            draggable: true
        }
    );
    $empty[0].marker = addMarker;
    addMarker.setOpacity(0);
    addMarker.addTo(map);
    addMarker.on('dragstart click', function() {
        $empty.css('background', '#ffcc80');
        setTimeout(function() {
            $empty.css('background', '');
        });
    });
    addMarker.on('dragend', function() {
        var markLatLng = addMarker.getLatLng();
        $emptylat.val(markLatLng.lat.toFixed(5));
        $emptylng.val(markLatLng.lng.toFixed(5));
    });
    map.on('dblclick', function(e) {
        addMarker.setLatLng(e.latlng);
        addMarker.setOpacity(1);
        $emptylat.val(e.latlng.lat.toFixed(5));
        $emptylng.val(e.latlng.lng.toFixed(5));
    });
    function setMarkerToInput() {
        var latval = $emptylat.val(),
            lngval = $emptylng.val();
        if (!isNaN(parseFloat(latval)) && !isNaN(parseFloat(lngval))) {
            addMarker.setOpacity(1);
            addMarker.setLatLng([latval, lngval]);
        } else {
            addMarker.setOpacity(0);
        }
    }
    $emptylat.on('change keyup', setMarkerToInput);
    $empty.on('coordinates-changed', setMarkerToInput);
    map.on('zoomend dragend', function(e) {
        var centre = map.getCenter(),
            zoom = map.getZoom();
        $('#id_zoom_level').val(zoom);
        $('#id_centre_latitude').val(centre.lat.toFixed(5));
        $('#id_centre_longitude').val(centre.lng.toFixed(5));
        return false;
    });
    map.on('locationfound', function(e) {
        $('#id_centre_latitude').val(e.latlng.lat.toFixed(5));
        $('#id_centre_longitude').val(e.latlng.lng.toFixed(5));
        map.panTo(e.latlng);
    });
    $('#current-pos').click(function() {
        map.locate();
        return false;
    });
    $('#id_zoom_level').on('change', function() {
        map.setZoom($(this).val());
    });
    $('#id_centre_latitude,#id_centre_longitude').on('change', function() {
        map.panTo([$('#id_centre_latitude').val(), $('#id_centre_longitude').val()]);
    });
    $('.geocoding').click(function() {
        var $item = $(this).parents('li.location');
        $.get('https://maps.googleapis.com/maps/api/geocode/json', {
            address: $item.find('input[name$="label"]').val(),
            key: window.MAP_DATA.api_key
        }, function(data) {
            if (data.results.length) {
                var loc = data.results[0];
                $item.find('input[name$="label"]').val(loc.formatted_address);
                $item.find('input[name$="latitude"]').val(loc.geometry.location.lat.toFixed(5));
                $item.find('input[name$="longitude"]').val(loc.geometry.location.lng.toFixed(5));
                $item.trigger('coordinates-changed');
            }
        });
    });
    $('.location-icon,.change-colour').click(function() {
        $(this).parents('li.location').find('.location-icon-selector').toggle();
        return false;
    });
    $('.location-icon-selector li').click(function() {
        var $this = $(this);
        var $item = $this.parents('li.location');
        var colour = $this.attr('data-colour');
        $item.find('.location-icon').attr("src", $(this).find('img').attr('src'));
        $item.find('input[name$="colour"]').val(colour);
        $(this).parent().hide();
        $item[0].marker.setIcon(getIcon(colour));
    });
});
