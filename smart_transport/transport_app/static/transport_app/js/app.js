let countdown = 30;
let timer;
let map, busMarkers = {}, routeLayer = null;

// ── Boot ─────────────────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  initMap();
  loadStops();
  loadLiveBoard();
  loadSidebar();
  startTimer();

  ['source', 'destination'].forEach(id =>
    document.getElementById(id).addEventListener('keydown', e => {
      if (e.key === 'Enter') doSearch();
    })
  );

  document.getElementById('weather-stop').addEventListener('keydown', e => {
    if (e.key === 'Enter') loadWeather();
  });
});

// ── MAP INIT (Leaflet + OpenStreetMap — free, no key) ─────────────────────────
function initMap() {
  map = L.map('map').setView([11.0, 78.5], 7);

  // OpenStreetMap tiles — completely free
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 18,
  }).addTo(map);

  // Load all stop markers on map
  fetch('/api/stop-coords/').then(r => r.json()).then(coords => {
    Object.entries(coords).forEach(([stop, latlng]) => {
      if (latlng.length === 2) {
        L.circleMarker(latlng, {
          radius: 5, color: '#1e3a8a', fillColor: '#3b82f6',
          fillOpacity: 0.8, weight: 2,
        }).addTo(map).bindPopup(`<b>${stop}</b>`);
      }
    });
  });

  // Load live bus markers
  loadBusMarkers();
}

// ── Bus Markers on Map ────────────────────────────────────────────────────────
function loadBusMarkers() {
  fetch('/api/live/').then(r => r.json()).then(data => {
    Object.entries(data).forEach(([busNum, live]) => {
      if (!live.lat || !live.lng) return;

      const icon = L.divIcon({
        className: '',
        html: `<div style="background:#0f172a;color:white;padding:2px 6px;border-radius:4px;font-size:11px;font-weight:800;white-space:nowrap;box-shadow:0 2px 6px rgba(0,0,0,0.3)">🚌 ${busNum}</div>`,
        iconAnchor: [20, 10],
      });

      if (busMarkers[busNum]) {
        busMarkers[busNum].setLatLng([live.lat, live.lng]);
      } else {
        busMarkers[busNum] = L.marker([live.lat, live.lng], { icon })
          .addTo(map)
          .bindPopup(`<b>Bus ${busNum}</b><br>At: ${live.at}<br>Next: ${live.next}<br>Status: ${live.status}`);
      }
    });
  });
}

// ── API 2: OpenRouteService — Draw real road path on map ──────────────────────
function drawRoadRoute(busNumber) {
  // Remove previous route layer
  if (routeLayer) { map.removeLayer(routeLayer); routeLayer = null; }

  fetch(`/api/road-route/?bus=${busNumber}`)
    .then(r => r.json())
    .then(data => {
      if (data.error) {
        console.warn('ORS:', data.error);
        return;
      }
      // Draw the actual road path as a blue polyline
      routeLayer = L.polyline(data.path, {
        color: '#2563eb', weight: 4, opacity: 0.8,
      }).addTo(map);

      map.fitBounds(routeLayer.getBounds(), { padding: [30, 30] });

      // Show route info popup at midpoint
      const mid = data.path[Math.floor(data.path.length / 2)];
      L.popup()
        .setLatLng(mid)
        .setContent(`<b>${data.route_name}</b><br>🛣 ${data.distance_km} km · ⏱ ${data.duration_min} min`)
        .openOn(map);
    })
    .catch(() => console.warn('Road route unavailable'));
}

// ── API 1: OpenWeatherMap — Weather at a stop ─────────────────────────────────
function loadWeather() {
  const stop = document.getElementById('weather-stop').value.trim();
  if (!stop) return;

  const el = document.getElementById('weather-result');
  el.innerHTML = '<div class="w-loading">Loading weather...</div>';

  fetch(`/api/weather/?stop=${encodeURIComponent(stop)}`)
    .then(r => r.json())
    .then(d => {
      if (d.error) {
        el.innerHTML = `<div class="w-error">⚠ ${d.error}</div>`;
        return;
      }
      el.innerHTML = `
        <div class="weather-card">
          <div class="w-top">
            <img src="https://openweathermap.org/img/wn/${d.icon}@2x.png" alt="${d.description}" class="w-icon"/>
            <div>
              <div class="w-temp">${d.temp}°C</div>
              <div class="w-desc">${d.description}</div>
            </div>
          </div>
          <div class="w-details">
            <span>💧 ${d.humidity}%</span>
            <span>💨 ${d.wind_speed} m/s</span>
            <span>🌡 Feels ${d.feels_like}°C</span>
          </div>
          <div class="w-stop">📍 ${d.stop}</div>
          ${d.note ? `<div class="w-note">ℹ️ ${d.note}</div>` : ''}
        </div>`;

      // Also show weather on map
      const coords = stop;
      fetch('/api/stop-coords/').then(r => r.json()).then(all => {
        const c = all[stop];
        if (c) {
          L.popup()
            .setLatLng(c)
            .setContent(`<b>${stop}</b><br>${d.temp}°C · ${d.description}<br>💧${d.humidity}% 💨${d.wind_speed}m/s`)
            .openOn(map);
          map.setView(c, 10);
        }
      });
    })
    .catch(() => {
      el.innerHTML = '<div class="w-error">⚠ Weather service unavailable</div>';
    });
}

// ── Stops datalist ────────────────────────────────────────────────────────────
function loadStops() {
  fetch('/api/stops/').then(r => r.json()).then(d => {
    document.getElementById('stops-list').innerHTML =
      d.stops.map(s => `<option value="${s}">`).join('');
  });
}

// ── Live Board ────────────────────────────────────────────────────────────────
function loadLiveBoard() {
  fetch('/api/routes/')
    .then(r => r.json())
    .then(d => {
      document.getElementById('live-list').innerHTML =
        d.routes.map(r => busCard(r)).join('');
      loadBusMarkers();
    })
    .catch(() => {
      document.getElementById('live-list').innerHTML =
        '<div class="empty"><div class="icon">❌</div>Cannot connect to server.</div>';
    });
}

function busCard(r) {
  const live = r.live;
  const atIdx = live.at_index;
  const isLate = live.delay > 0;
  const isGps = live.source === 'gps';

  const track = r.stops.map((stop, i) => {
    const dotCls = i < atIdx ? 'done' : i === atIdx ? 'here' : 'ahead';
    const stopCls = i < atIdx ? 'done' : '';
    const lblCls = i === atIdx ? 'here-lbl' : '';
    return `<div class="track-stop ${stopCls}">
      <div class="t-dot ${dotCls}"></div>
      <div class="t-label ${lblCls}">${stop}</div>
    </div>`;
  }).join('');

  const chips = r.timings.map((t, i) =>
    `<span class="t-chip ${i === 0 ? 'next' : ''}">${t}</span>`
  ).join('');

  const minsText = typeof r.mins_until === 'number' ? `in ${r.mins_until} min` : r.mins_until;

  return `
    <div class="bus-card" onclick="onBusClick('${r.bus_number}', ${live.lat || 0}, ${live.lng || 0})">
      <div class="card-head">
        <span class="bus-tag">${r.bus_number}</span>
        <span class="route-name">${r.route_name}</span>
        <span class="status ${isGps ? 'gps-live' : isLate ? 'late' : 'on-time'}">
          ${isGps ? '📡 GPS' : live.status}
        </span>
      </div>
      <div class="card-body">
        <div class="location-row">
          🚌 At <span class="loc-now">&nbsp;${live.at}&nbsp;</span>
          <span class="loc-arrow">→</span>
          Next: <span class="loc-next">&nbsp;${live.next}</span>
        </div>
        <div class="track">${track}</div>
        <div class="timings-row">${chips}</div>
      </div>
      <div class="card-foot">
        <span>Next departure: <span class="next-dep">${r.next_dep}</span></span>
        <span class="mins">${minsText}</span>
      </div>
    </div>`;
}

// Click bus card → show road route on map + zoom to bus
function onBusClick(busNumber, lat, lng) {
  drawRoadRoute(busNumber);   // OpenRouteService API call
  if (lat && lng) map.setView([lat, lng], 10);
}

// ── Auto Refresh ──────────────────────────────────────────────────────────────
function startTimer() {
  clearInterval(timer);
  countdown = 30;
  timer = setInterval(() => {
    countdown--;
    const el = document.getElementById('timer');
    if (el) el.textContent = `Refreshes in ${countdown}s`;
    if (countdown <= 0) {
      loadLiveBoard();
      countdown = 30;
    }
  }, 1000);
}

// ── Search ────────────────────────────────────────────────────────────────────
async function doSearch() {
  const src = document.getElementById('source').value.trim();
  const dst = document.getElementById('destination').value.trim();
  if (!src || !dst) return;

  document.getElementById('live-section').classList.add('hidden');
  document.getElementById('search-section').classList.remove('hidden');
  document.getElementById('search-label').textContent = `${src} → ${dst}`;
  document.getElementById('search-results').innerHTML =
    '<div class="empty"><div class="icon">🔍</div>Searching...</div>';

  let data;
  try {
    const res = await fetch(`/api/search/?source=${encodeURIComponent(src)}&destination=${encodeURIComponent(dst)}`);
    data = await res.json();
  } catch (e) {
    document.getElementById('search-results').innerHTML =
      '<div class="empty"><div class="icon">❌</div>Server error.</div>';
    return;
  }

  if (!data.routes || data.routes.length === 0) {
    document.getElementById('search-count').textContent = '0';
    document.getElementById('search-results').innerHTML = `
      <div class="empty">
        <div class="icon">🚌</div>
        <strong>No buses found</strong>
        <p style="margin-top:.4rem;font-size:.85rem">No direct bus from <b>${src}</b> to <b>${dst}</b></p>
        <p style="margin-top:.3rem;font-size:.8rem;color:#94a3b8">Try: Chennai, Coimbatore, Salem, Madurai, Trichy</p>
      </div>`;
    return;
  }

  document.getElementById('search-count').textContent =
    `${data.routes.length} bus${data.routes.length > 1 ? 'es' : ''}`;
  document.getElementById('search-results').innerHTML =
    data.routes.map(r => resultCard(r, src, dst)).join('');

  // Auto draw road route for first result
  if (data.routes.length > 0) drawRoadRoute(data.routes[0].bus_number);

  // Auto load weather for source stop
  document.getElementById('weather-stop').value = src;
  loadWeather();
}

function resultCard(r, src, dst) {
  const live = r.live;
  const isLate = live.delay > 0;
  const isGps = live.source === 'gps';

  const stopsHtml = r.intermediate_stops.map((s, i) => {
    let cls = 's-chip';
    if (s.toLowerCase() === src.toLowerCase()) cls += ' src';
    else if (s.toLowerCase() === dst.toLowerCase()) cls += ' dst';
    const arr = i < r.intermediate_stops.length - 1 ? '<span class="s-arr">→</span>' : '';
    return `<span class="${cls}">${s}</span>${arr}`;
  }).join('');

  const chips = r.timings.map((t, i) =>
    `<span class="t-chip ${i === 0 ? 'next' : ''}">${t}</span>`
  ).join('');

  const minsText = typeof r.mins_until === 'number' ? `${r.mins_until} min` : r.mins_until;
  const soonCls = typeof r.mins_until === 'number' && r.mins_until < 30 ? 'soon' : '';

  return `
    <div class="result-card" onclick="onBusClick('${r.bus_number}', ${live.lat || 0}, ${live.lng || 0})">
      <div class="result-head">
        <span class="bus-tag">${r.bus_number}</span>
        <div>
          <div style="font-weight:700;font-size:.9rem">${r.route_name}</div>
          <div style="font-size:.72rem;color:#64748b;margin-top:2px">
            🚌 Bus at <b>${live.at}</b> → <b>${live.next}</b>
            &nbsp;·&nbsp;
            <span class="status ${isGps ? 'gps-live' : isLate ? 'late' : 'on-time'}" style="padding:.1rem .45rem">
              ${isGps ? '📡 GPS' : live.status}
            </span>
          </div>
        </div>
        <div class="dep-block">
          <div class="dep-time">${r.next_dep}</div>
          <div class="dep-mins ${soonCls}">in ${minsText}</div>
        </div>
      </div>
      <div class="card-body">
        <div class="stops-row">${stopsHtml}</div>
        <div class="timings-row">${chips}</div>
      </div>
    </div>`;
}

function showLive() {
  document.getElementById('search-section').classList.add('hidden');
  document.getElementById('live-section').classList.remove('hidden');
  document.getElementById('source').value = '';
  document.getElementById('destination').value = '';
  if (routeLayer) { map.removeLayer(routeLayer); routeLayer = null; }
}

// ── Sidebar ───────────────────────────────────────────────────────────────────
function loadSidebar() {
  fetch('/api/routes/').then(r => r.json()).then(d => {
    document.getElementById('quick-routes').innerHTML = d.routes.slice(0, 7).map(r => `
      <div class="q-route" onclick="quickFill('${r.stops[0]}','${r.stops[r.stops.length - 1]}')">
        <span class="q-tag">${r.bus_number}</span>
        <span class="q-name">${r.stops[0]} → ${r.stops[r.stops.length - 1]}</span>
      </div>`).join('');
  });

  fetch('/api/stops/').then(r => r.json()).then(d => {
    document.getElementById('all-stops').innerHTML =
      d.stops.map(s => `<span class="stop-pill" onclick="fillStop('${s}')">${s}</span>`).join('');
  });
}

function quickFill(src, dst) {
  document.getElementById('source').value = src;
  document.getElementById('destination').value = dst;
  doSearch();
}

function fillStop(stop) {
  const s = document.getElementById('source');
  const d = document.getElementById('destination');
  if (!s.value) s.value = stop;
  else if (!d.value) { d.value = stop; doSearch(); }
  else s.value = stop;
}

function swapInputs() {
  const s = document.getElementById('source');
  const d = document.getElementById('destination');
  [s.value, d.value] = [d.value, s.value];
}
