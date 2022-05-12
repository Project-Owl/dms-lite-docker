$(document).ready(function() {

    $(".gmaps-button").click(function(e) {
        e.preventDefault();
        const embed = $(this).parent().find("#gmaps-embed");
        var newIframe = document.createElement("iframe");
        newIframe.setAttribute("src", "https://maps.google.com/maps?q=" + $(this).attr("gpsData") + "&z=15&output=embed");
        newIframe.style.width = "400px";
        newIframe.style.height = "300px";
        embed.append(newIframe);
        setActiveMap("gmaps", $(this).parent());
        $(this).off();
        $(this).click((e) => {
            e.preventDefault();
            setActiveMap(embed.is(":visible") ? null : "gmaps", $(this).parent());
        });
    });

    $(".osm-button").click(function(e) {
        e.preventDefault();
        const embed = $(this).parent().find("#osm-embed");
        const lat = parseFloat($(this).attr("lat"));
        const lon = parseFloat($(this).attr("lon"));
        embed[0].style.width = "400px";
        embed[0].style.height = "300px";
        var map = L.map(embed[0]).setView([lat, lon], 15);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
        L.marker([lat, lon]).addTo(map);
        setActiveMap("osm", $(this).parent());
        $(this).off();
        $(this).click((e) => {
            e.preventDefault();
            setActiveMap(embed.is(":visible") ? null : "osm", $(this).parent());
        });
    });

    const cookies = document.cookie.split(';').map(c => c.split('='));
    let detailedView = false;
    let mapType = 'none';
    for (let i = 0; i < cookies.length; i++) {
        cookies[i][0] = cookies[i][0].trim();
        if (cookies[i][0] == 'detailedView' && cookies[i][1] == 'true')
            detailedView = true;
        else if (cookies[i][0] == 'mapType')
            mapType = cookies[i][1];
    }
    if (detailedView) {
        if (mapType == 'google')
            $('.gmaps-button').trigger('click');
        else if (mapType == 'osm')
            $('.osm-button').trigger('click');
    }

});

function setActiveMap(activeMap, parent) {
    const osmEmbed = parent.find("#osm-embed");
    const gmapsEmbed = parent.find("#gmaps-embed");
    const gmapsActive = activeMap == "gmaps";
    const osmActive = activeMap == "osm";
    parent.find(".gmaps-button").text((gmapsActive ? "Hide" : "View") + " (Google Maps)");
    parent.find(".osm-button").text((osmActive ? "Hide" : "View") + " (OpenStreetMap)");
    osmEmbed.toggle(osmActive);
    gmapsEmbed.toggle(gmapsActive);
}
