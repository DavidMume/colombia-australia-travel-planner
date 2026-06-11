const MONTHS = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
];
const PLANNING_YEAR = 2026;
const DATA_VERSION = "2026-06-11-spelling-review";

const state = { airports: {}, routes: [], bridgeDestinations: [], filtered: [], selectedId: null };
const map = L.map("map", { scrollWheelZoom: false }).setView([5, 20], 2);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "&copy; OpenStreetMap contributors",
  maxZoom: 18,
}).addTo(map);
const routeLayer = L.layerGroup().addTo(map);

function parseCsv(text) {
  const rows = [];
  let row = [], field = "", quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    if (char === '"' && quoted && text[i + 1] === '"') { field += '"'; i += 1; }
    else if (char === '"') quoted = !quoted;
    else if (char === "," && !quoted) { row.push(field); field = ""; }
    else if ((char === "\n" || char === "\r") && !quoted) {
      if (char === "\r" && text[i + 1] === "\n") i += 1;
      row.push(field); field = "";
      if (row.some(Boolean)) rows.push(row);
      row = [];
    } else field += char;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  const headers = rows.shift();
  return rows.map(values => Object.fromEntries(headers.map((header, index) => [header, values[index] || ""])));
}

function isAvailableInMonth(route, month) {
  if (!route.available_from) return true;
  const availableFrom = new Date(`${route.available_from}T00:00:00`);
  const endOfSelectedMonth = new Date(PLANNING_YEAR, month, 0);
  return endOfSelectedMonth >= availableFrom;
}

function availabilityLabel(route) {
  if (route.availability_status === "scheduled" && route.available_from) {
    const date = new Date(`${route.available_from}T00:00:00`);
    return `Programada desde ${date.toLocaleDateString("es-CO", { day: "numeric", month: "short", year: "numeric" })}`;
  }
  return route.availability_status === "verified" ? "Tramos vigentes" : "Ruta verificada";
}

function calculateScoreBreakdown(route, month) {
  const touristStops = route.stopovers.filter(code => state.airports[code]?.isTourist).length;
  const stops = Math.max(0, 30 - route.total_stops * 8);
  const duration = Math.max(0, 25 - Math.max(route.approximate_duration_hours - 20, 0) * 1.25);
  const visa = { low: 20, medium: 12, high: 3 }[route.visa_complexity] || 8;
  const tourism = Math.min(15, touristStops * 5 + ({ high: 5, medium: 3, low: 0 }[route.tourist_potential] || 0));
  const season = route.season_recommendations.best_months.includes(month) ? 5 : 1;
  const verification = route.availability_status === "verified" ? 5 : 4;
  const total = Math.round(stops + duration + visa + tourism + season + verification);
  return { total, stops: Math.round(stops), duration: Math.round(duration), visa, tourism, season, verification };
}

function airportLabel(code) {
  const airport = state.airports[code];
  return airport ? `${airport.city} (${code})` : code;
}

function uniqueCodes(key) {
  return [...new Set(state.routes.map(route => route[key]))].sort();
}

function fillSelect(id, codes, preferred) {
  const select = document.getElementById(id);
  select.innerHTML = codes.map(code => `<option value="${code}" ${code === preferred ? "selected" : ""}>${airportLabel(code)}</option>`).join("");
}

function renderHubBridges() {
  const destinationCode = document.getElementById("bridge-destination").value;
  const destination = state.bridgeDestinations.find(item => item.code === destinationCode);
  const selectedCode = document.getElementById("hub-select").value;
  const hub = destination?.hubs.find(item => item.code === selectedCode);
  if (!hub) return;
  document.querySelector(".hub-intro").textContent = hub.summary;
  document.getElementById("hub-bridges").innerHTML = hub.bridges.map(bridge => `
    <article class="bridge-card">
      <h3>${hub.code} → ${bridge.code} → ${destination.code}</h3>
      <p><strong>${bridge.name}:</strong> ${bridge.note}</p>
      <div class="bridge-links">
        <a href="${bridge.hub_url}" target="_blank" rel="noreferrer">Ver ${hub.code} → ${bridge.code}</a>
        <a href="${bridge.destination_url}" target="_blank" rel="noreferrer">Ver ${bridge.code} → ${destination.code}</a>
      </div>
    </article>
  `).join("");
}

function updateHubOptions() {
  const destinationCode = document.getElementById("bridge-destination").value;
  const destination = state.bridgeDestinations.find(item => item.code === destinationCode);
  document.getElementById("hub-select").innerHTML = destination.hubs.map(hub =>
    `<option value="${hub.code}">${hub.name} (${hub.code})</option>`
  ).join("");
  renderHubBridges();
}

function applyFilters() {
  const origin = document.getElementById("origin").value;
  const destination = document.getElementById("destination").value;
  const maxStops = Number(document.getElementById("max-stops").value);
  const month = Number(document.getElementById("month").value);
  const sort = document.getElementById("sort").value;

  const bridgeDest = document.getElementById("bridge-destination");
  if (bridgeDest.value !== origin) {
    bridgeDest.value = origin;
    updateHubOptions();
  }

  const includeUS = document.getElementById("include-us").checked;
  const US_AIRPORTS = new Set(["LAX", "SFO", "DFW", "JFK", "MIA", "ORD", "IAH", "ATL", "SEA"]);

  state.filtered = state.routes
    .filter(route =>
      route.origin === origin &&
      route.destination === destination &&
      route.total_stops <= maxStops &&
      isAvailableInMonth(route, month) &&
      (includeUS || !route.stopovers.some(c => US_AIRPORTS.has(c)))
    )
    .map(route => {
      const scoreBreakdown = calculateScoreBreakdown(route, month);
      return { ...route, calculatedScore: scoreBreakdown.total, scoreBreakdown };
    })
    .sort((a, b) => {
      if (sort === "stops") return a.total_stops - b.total_stops;
      if (sort === "duration") return a.approximate_duration_hours - b.approximate_duration_hours;
      return b.calculatedScore - a.calculatedScore;
    });

  state.selectedId = state.filtered.some(route => route.id === state.selectedId)
    ? state.selectedId
    : state.filtered[0]?.id;
  render();
}

function render() {
  const month = Number(document.getElementById("month").value);
  const touristCodes = new Set(state.filtered.flatMap(route => route.stopovers).filter(code => state.airports[code]?.isTourist));
  document.getElementById("route-count").textContent = state.filtered.length;
  document.getElementById("best-score").textContent = state.filtered[0] ? `${state.filtered[0].calculatedScore}/100` : "—";
  document.getElementById("tourist-stops").textContent = touristCodes.size;

  const container = document.getElementById("routes");
  if (!state.filtered.length) {
    container.innerHTML = '<div class="empty">No hay rutas precargadas para esta combinación. Prueba cambiando origen, destino o escalas.</div>';
    routeLayer.clearLayers();
    document.getElementById("map-title").textContent = "Mapa";
    return;
  }

  container.innerHTML = state.filtered.map(route => {
    const isBestMonth = route.season_recommendations.best_months.includes(month);
    const statusClass = ["scheduled", "verified"].includes(route.availability_status) ? "scheduled" : "status";
    const chips = route.stopovers.map(code => `<span class="chip">${airportLabel(code)}</span>`).join("");
    const segments = (route.segments || []).map(segment =>
      `<a href="${segment.source_url}" target="_blank" rel="noreferrer">${segment.from} → ${segment.to}</a> (${segment.duration})${segment.service_note ? ` <em>— ${segment.service_note}</em>` : ""}`
    ).join(" · ");
    const breakdown = route.scoreBreakdown;
    return `
      <article class="route-card ${route.id === state.selectedId ? "active" : ""}" data-id="${route.id}" tabindex="0">
        <div class="route-top">
          <h3>${route.name}</h3>
          <span class="score">${route.calculatedScore}</span>
        </div>
        <div class="route-meta">
          <span>${route.total_stops} escala${route.total_stops === 1 ? "" : "s"}</span>
          <span>aprox. ${route.approximate_duration_hours} h</span>
          <span>${isBestMonth ? "buena temporada" : "temporada regular"}</span>
        </div>
        <div class="chips">
          <span class="chip ${statusClass}">${availabilityLabel(route)}</span>
          ${chips}
        </div>
        <div class="route-details">
          <strong>Cómo se calcula (${route.calculatedScore}/100):</strong>
          escalas ${breakdown.stops}/30 · duración ${breakdown.duration}/25 · visa ${breakdown.visa}/20 ·
          turismo ${breakdown.tourism}/15 · temporada ${breakdown.season}/5 · verificación ${breakdown.verification}/5<br>
          <strong>Aerolíneas de referencia:</strong> ${route.airlines_example.join(", ")}<br>
          <strong>Tramos directos:</strong> ${segments}<br>
          <strong>Temporada:</strong> ${route.season_recommendations.notes}<br>
          <strong>Visa:</strong> ${route.visa_notes}
        </div>
      </article>`;
  }).join("");

  container.querySelectorAll(".route-card").forEach(card => {
    const select = () => { state.selectedId = card.dataset.id; render(); };
    card.addEventListener("click", select);
    card.addEventListener("keydown", event => { if (event.key === "Enter" || event.key === " ") select(); });
  });
  drawRoute(state.filtered.find(route => route.id === state.selectedId));
}

function drawRoute(route) {
  routeLayer.clearLayers();
  if (!route) return;
  const codes = [route.origin, ...route.stopovers, route.destination];
  const points = codes.map(code => {
    const airport = state.airports[code];
    return airport ? [airport.latitude, airport.longitude] : null;
  }).filter(Boolean);
  const displayPoints = unwrapLongitudes(points);

  drawPacificAwarePath(displayPoints);
  codes.forEach((code, index) => {
    const airport = state.airports[code];
    if (!airport) return;
    const role = index === 0 ? "Origen" : index === codes.length - 1 ? "Destino" : "Escala";
    const color = role === "Escala" ? "#dd6f3b" : "#174d3a";
    L.circleMarker(displayPoints[index], {
      radius: role === "Escala" ? 7 : 9, color, fillColor: color, fillOpacity: .9,
    }).bindPopup(`<strong>${role}: ${airport.city} (${code})</strong><br>${airport.country}`).addTo(routeLayer);
  });
  map.fitBounds(displayPoints, { padding: [35, 35] });
  document.getElementById("map-title").textContent = route.name;
  setTimeout(() => map.invalidateSize(), 20);
}

function drawPacificAwarePath(points) {
  for (let index = 1; index < points.length; index += 1) {
    const path = unwrapLongitudes(greatCirclePoints(points[index - 1], points[index], 48), points[index - 1][1]);
    L.polyline(path, { color: "#dd6f3b", weight: 3, dashArray: "8 8" }).addTo(routeLayer);
  }
}

function unwrapLongitudes(points, initialLongitude = points[0][1]) {
  let previousLongitude = initialLongitude;
  return points.map(([latitude, longitude], index) => {
    let adjustedLongitude = longitude;
    if (index === 0 && Math.abs(adjustedLongitude - initialLongitude) > 180) {
      adjustedLongitude += adjustedLongitude < initialLongitude ? 360 : -360;
    }
    while (adjustedLongitude - previousLongitude > 180) adjustedLongitude -= 360;
    while (adjustedLongitude - previousLongitude < -180) adjustedLongitude += 360;
    previousLongitude = adjustedLongitude;
    return [latitude, adjustedLongitude];
  });
}

function greatCirclePoints(start, end, steps) {
  const toRadians = value => value * Math.PI / 180;
  const toDegrees = value => value * 180 / Math.PI;
  const [lat1, lon1, lat2, lon2] = [...start, ...end].map(toRadians);
  const distance = 2 * Math.asin(Math.sqrt(
    Math.sin((lat2 - lat1) / 2) ** 2 +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin((lon2 - lon1) / 2) ** 2
  ));
  if (!distance) return [start, end];

  return Array.from({ length: steps + 1 }, (_, index) => {
    const fraction = index / steps;
    const a = Math.sin((1 - fraction) * distance) / Math.sin(distance);
    const b = Math.sin(fraction * distance) / Math.sin(distance);
    const x = a * Math.cos(lat1) * Math.cos(lon1) + b * Math.cos(lat2) * Math.cos(lon2);
    const y = a * Math.cos(lat1) * Math.sin(lon1) + b * Math.cos(lat2) * Math.sin(lon2);
    const z = a * Math.sin(lat1) + b * Math.sin(lat2);
    return [toDegrees(Math.atan2(z, Math.sqrt(x * x + y * y))), toDegrees(Math.atan2(y, x))];
  });
}

async function init() {
  const [routesResponse, airportsResponse, hubsResponse] = await Promise.all([
    fetch(`/data/verified_routes.json?v=${DATA_VERSION}`),
    fetch(`/data/airports.csv?v=${DATA_VERSION}`),
    fetch(`/data/hub_bridges.json?v=${DATA_VERSION}`),
  ]);
  const routeData = await routesResponse.json();
  const hubData = await hubsResponse.json();
  const airportRows = parseCsv(await airportsResponse.text());

  state.airports = Object.fromEntries(airportRows.map(airport => [airport.iata_code, {
    ...airport,
    latitude: Number(airport.latitude),
    longitude: Number(airport.longitude),
    isTourist: airport.is_tourist_stopover.toLowerCase() === "true",
  }]));
  state.routes = routeData.routes;
  state.bridgeDestinations = hubData.destinations;

  fillSelect("origin", uniqueCodes("origin"), "BNE");
  fillSelect("destination", uniqueCodes("destination"), "BOG");
  document.getElementById("bridge-destination").innerHTML = state.bridgeDestinations.map(destination =>
    `<option value="${destination.code}">${destination.name} (${destination.code})</option>`
  ).join("");
  updateHubOptions();
  document.getElementById("month").innerHTML = MONTHS.map((month, index) =>
    `<option value="${index + 1}" ${index === new Date().getMonth() ? "selected" : ""}>${month}</option>`
  ).join("");
  document.getElementById("search-routes").addEventListener("click", applyFilters);
  document.getElementById("sort").addEventListener("change", applyFilters);
  document.getElementById("include-us").addEventListener("change", applyFilters);
  document.getElementById("hub-select").addEventListener("change", renderHubBridges);
  document.getElementById("bridge-destination").addEventListener("change", updateHubOptions);
  applyFilters();
}

init().catch(error => {
  console.error(error);
  document.getElementById("routes").innerHTML = '<div class="empty">No se pudieron cargar los datos de rutas.</div>';
});
