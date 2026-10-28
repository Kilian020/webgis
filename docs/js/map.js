const map = L.map('map').setView([52.3737, 4.8995], 17);

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap-bijdragers'
}).addTo(map);

fetch('data/panden.geojson')
  .then(r => r.json())
  .then(data => {
    L.geoJSON(data, {
      style: f => ({
        color: '#444', weight: 0.5,
        fillColor: f.properties.kleur, fillOpacity: 0.8
      }),
      onEachFeature: (f, layer) => {
        const p = f.properties;
        layer.bindPopup(
          `<b>Bouwjaar: ${p.bouwjaar}</b><br>` +
          `Periode: ${p.periode}<br>` +
          `Oppervlakte: ${p.oppervlakte_m2} m²`
        );
      }
    }).addTo(map);
  });