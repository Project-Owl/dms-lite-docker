document.querySelectorAll('.gps-link').forEach(parent => {
  const lat = Number(parent.dataset.lat), lon = Number(parent.dataset.lon);
  if (!Number.isFinite(lat) || !Number.isFinite(lon) || Math.abs(lat)>90 || Math.abs(lon)>180) return;
  for (const [selector,provider] of [['.gmaps-button','Google Maps'],['.osm-button','OpenStreetMap']]) {
    const button = parent.querySelector(selector);
    let box;
    button.addEventListener('click',() => {
      if (!box) {
        box = document.createElement('div');box.style.width='min(400px, 100%)';box.style.height='300px';parent.append(box);
        if (selector === '.gmaps-button') {
          const frame = document.createElement('iframe');frame.title='Device location on Google Maps';
          frame.src='https://maps.google.com/maps?'+new URLSearchParams({q:`${lat},${lon}`,z:15,output:'embed'});
          frame.style.width='100%';frame.style.height='100%';box.append(frame);
        } else {
          const map = L.map(box).setView([lat,lon],15);
          L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OpenStreetMap contributors'}).addTo(map);
          L.marker([lat,lon]).addTo(map);
        }
      } else box.hidden=!box.hidden;
      button.textContent=(box.hidden?'View ':'Hide ')+provider;button.setAttribute('aria-expanded',String(!box.hidden));
    });
  }
});
