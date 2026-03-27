import json
import math
import time
import threading
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

# Receiver location
RX_LAT = 36.1811
RX_LON = -86.7335

# Range model: track max observed range per 10-degree bearing slice
BEARING_SLICES = 36
RANGE_MODEL_FILE = "/data/range_model.json"

# Track aircraft we've already logged so we don't spam
seen = {}
SEEN_TTL = 600


def haversine_nm(lat1, lon1, lat2, lon2):
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return 3440.065 * 2 * math.asin(math.sqrt(a))


def bearing_from_rx(lat, lon):
    dlon = math.radians(lon - RX_LON)
    x = math.sin(dlon) * math.cos(math.radians(lat))
    y = math.cos(math.radians(RX_LAT)) * math.sin(math.radians(lat)) - \
        math.sin(math.radians(RX_LAT)) * math.cos(math.radians(lat)) * math.cos(dlon)
    return math.degrees(math.atan2(x, y)) % 360


DIR_NAMES = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
             "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]


def dir_name(bearing):
    return DIR_NAMES[int((bearing + 11.25) / 22.5) % 16]


class RangeModel:
    def __init__(self):
        self.slices = [None] * BEARING_SLICES
        self.altitudes = [None] * BEARING_SLICES
        self.observations = [0] * BEARING_SLICES
        self.load()

    def bearing_to_slice(self, bearing):
        return int(bearing / (360.0 / BEARING_SLICES)) % BEARING_SLICES

    def record_pickup(self, bearing, distance_nm, alt_ft=None):
        s = self.bearing_to_slice(bearing)
        self.observations[s] += 1
        if self.slices[s] is None or distance_nm > self.slices[s]:
            self.slices[s] = round(distance_nm, 1)
            self.altitudes[s] = alt_ft
            self.save()
            return True
        return False

    def save(self):
        try:
            with open(RANGE_MODEL_FILE, 'w') as f:
                json.dump({"slices": self.slices, "altitudes": self.altitudes,
                           "observations": self.observations}, f)
        except Exception as e:
            print(f"[error] Failed to save range model: {e}")

    def load(self):
        try:
            with open(RANGE_MODEL_FILE) as f:
                data = json.load(f)
                self.slices = data["slices"]
                self.altitudes = data.get("altitudes", [None] * BEARING_SLICES)
                self.observations = data["observations"]
                total = sum(1 for s in self.slices if s is not None)
                print(f"[model] Loaded range model: {total}/{BEARING_SLICES} slices have data")
        except FileNotFoundError:
            print("[model] No existing range model — starting fresh")
        except Exception as e:
            print(f"[error] Failed to load range model: {e}")

    def summary(self):
        filled = sum(1 for s in self.slices if s is not None)
        ranges = [s for s in self.slices if s is not None]
        if ranges:
            return (f"{filled}/{BEARING_SLICES} slices | "
                    f"min {min(ranges):.0f} NM | max {max(ranges):.0f} NM | "
                    f"avg {sum(ranges)/len(ranges):.0f} NM")
        return "no data yet"


def fetch_dump1090():
    try:
        url = "http://dump1090:8080/data/aircraft.json"
        req = urllib.request.Request(url, headers={"User-Agent": "skywatch/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return {(a.get("flight") or "").strip(): a
                    for a in data.get("aircraft", [])
                    if a.get("lat") is not None}
    except Exception:
        return {}


def cleanup_seen():
    now = time.time()
    stale = [k for k, v in seen.items() if now - v > SEEN_TTL]
    for k in stale:
        del seen[k]


COVERAGE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Antenna Coverage Map</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body { margin: 0; }
        #map { height: 100vh; width: 100%; }
        #info {
            position: absolute; bottom: 10px; left: 10px; z-index: 1000;
            background: rgba(0,0,0,0.8); color: #0f0; padding: 8px 12px;
            font-family: monospace; font-size: 12px; border-radius: 4px;
        }
        #legend {
            position: absolute; top: 10px; right: 10px; z-index: 1000;
            background: rgba(0,0,0,0.8); color: #ccc; padding: 8px 12px;
            font-family: monospace; font-size: 11px; border-radius: 4px;
        }
        .legend-row { margin: 2px 0; }
        .legend-dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; }
    </style>
</head>
<body>
    <div id="map"></div>
    <div id="info">loading...</div>
    <div id="legend">
        <b>Max pickup altitude</b>
        <div class="legend-row"><span class="legend-dot" style="background:#ff3333"></span>&lt;5k ft</div>
        <div class="legend-row"><span class="legend-dot" style="background:#ff8800"></span>5-15k ft</div>
        <div class="legend-row"><span class="legend-dot" style="background:#ffff00"></span>15-25k ft</div>
        <div class="legend-row"><span class="legend-dot" style="background:#00ff88"></span>25-35k ft</div>
        <div class="legend-row"><span class="legend-dot" style="background:#00ffff"></span>&gt;35k ft</div>
    </div>
    <script>
        var RX_LAT = 36.1811, RX_LON = -86.7335;
        var map = L.map('map', {zoomSnap: 0.25, zoomDelta: 0.25}).setView([RX_LAT, RX_LON], 7);
        var baseLayers = {
            'Dark': L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                attribution: 'CartoDB'
            }),
            'Topo': L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
                attribution: 'OpenTopoMap',
                maxZoom: 17
            }),
            'Terrain': L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
                attribution: 'Esri'
            }),
            'Satellite': L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                attribution: 'Esri'
            }),
            'Street': L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: 'OSM'
            })
        };
        baseLayers['Dark'].addTo(map);
        L.control.layers(baseLayers, null, {position: 'topleft'}).addTo(map);

        L.circleMarker([RX_LAT, RX_LON], {
            radius: 6, color: '#fff', fillColor: '#0f0', fillOpacity: 1, weight: 2
        }).addTo(map).bindPopup('Receiver - East Nashville');

        var coverageLayer = null;
        var dotLayer = L.layerGroup().addTo(map);

        function altColor(alt) {
            if (alt === null || alt === undefined) return '#666';
            if (alt < 5000) return '#ff3333';
            if (alt < 15000) return '#ff8800';
            if (alt < 25000) return '#ffff00';
            if (alt < 35000) return '#00ff88';
            return '#00ffff';
        }

        function destPoint(lat, lon, bearing, distNm) {
            var R = 3440.065;
            var d = distNm / R;
            var brng = bearing * Math.PI / 180;
            var lat1 = lat * Math.PI / 180;
            var lon1 = lon * Math.PI / 180;
            var lat2 = Math.asin(Math.sin(lat1) * Math.cos(d) + Math.cos(lat1) * Math.sin(d) * Math.cos(brng));
            var lon2 = lon1 + Math.atan2(Math.sin(brng) * Math.sin(d) * Math.cos(lat1),
                                          Math.cos(d) - Math.sin(lat1) * Math.sin(lat2));
            return [lat2 * 180 / Math.PI, lon2 * 180 / Math.PI];
        }

        function draw(data) {
            var slices = data.slices;
            var altitudes = data.altitudes || [];
            var observations = data.observations;
            var n = slices.length;
            var step = 360 / n;

            var polyPoints = [];
            for (var i = 0; i < n; i++) {
                var range = slices[i];
                if (range === null || range === 0) range = 0.5;
                polyPoints.push(destPoint(RX_LAT, RX_LON, i * step, range));
            }
            polyPoints.push(polyPoints[0]);

            if (coverageLayer) map.removeLayer(coverageLayer);
            dotLayer.clearLayers();

            coverageLayer = L.polygon(polyPoints, {
                color: '#0f0', weight: 1.5, fillColor: '#0f0', fillOpacity: 0.1
            }).addTo(map);

            for (var i = 0; i < n; i++) {
                if (slices[i] === null) continue;
                var j = (i + 1) % n;
                var range_i = slices[i] || 0.5;
                var range_j = slices[j] !== null ? slices[j] : range_i;
                var p1 = destPoint(RX_LAT, RX_LON, i * step, range_i);
                var p2 = destPoint(RX_LAT, RX_LON, j * step, range_j);
                L.polygon([[RX_LAT, RX_LON], p1, p2], {
                    color: altColor(altitudes[i]), weight: 0,
                    fillColor: altColor(altitudes[i]), fillOpacity: 0.25
                }).addTo(dotLayer);
            }

            for (var i = 0; i < n; i++) {
                if (slices[i] === null) continue;
                var pt = destPoint(RX_LAT, RX_LON, i * step, slices[i]);
                var alt = altitudes[i];
                var altStr = alt !== null && alt !== undefined ? Math.round(alt/1000) + 'k ft' : '?';
                L.circleMarker(pt, {
                    radius: 5, color: '#000', weight: 1,
                    fillColor: altColor(alt), fillOpacity: 0.9
                }).addTo(dotLayer).bindTooltip(
                    Math.round(slices[i]) + ' NM @ ' + altStr +
                    ' (' + observations[i] + ' obs)',
                    {direction: 'top'}
                );
            }

            var filled = slices.filter(function(s) { return s !== null; }).length;
            var ranges = slices.filter(function(s) { return s !== null; });
            var avg = ranges.length ? Math.round(ranges.reduce(function(a,b){return a+b;},0) / ranges.length) : 0;
            var totalObs = observations.reduce(function(a,b){return a+b;},0);
            document.getElementById('info').innerHTML =
                filled + '/' + n + ' bearings | ' +
                'max ' + Math.round(Math.max.apply(null, ranges.concat([0]))) + ' NM | ' +
                'avg ' + avg + ' NM | ' +
                totalObs + ' observations';
        }

        function update() {
            fetch('/api/coverage')
                .then(function(r) { return r.json(); })
                .then(draw);
        }

        setInterval(update, 10000);
        update();
    </script>
</body>
</html>
"""


class CoverageHandler(BaseHTTPRequestHandler):
    model = None

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(COVERAGE_HTML.encode())
        elif self.path == '/api/coverage':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            data = {
                "slices": self.model.slices,
                "altitudes": self.model.altitudes,
                "observations": self.model.observations,
            }
            self.wfile.write(json.dumps(data).encode())
        else:
            self.send_response(404)
            self.end_headers()


def start_web(model):
    CoverageHandler.model = model
    server = HTTPServer(('0.0.0.0', 8081), CoverageHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    print("[web] Coverage map serving on port 8081")


def run():
    model = RangeModel()
    start_web(model)

    print(f"Skywatch starting — receiver at {RX_LAT}, {RX_LON}")
    print(f"Range model: {model.summary()}")
    print("---")

    cycle = 0
    while True:
        received = fetch_dump1090()

        for callsign, ac in received.items():
            if not callsign or callsign in seen:
                continue

            dist = haversine_nm(RX_LAT, RX_LON, ac["lat"], ac["lon"])
            bearing = bearing_from_rx(ac["lat"], ac["lon"])
            alt = ac.get("alt_baro")
            is_new_max = model.record_pickup(bearing, dist, alt)
            max_tag = " [NEW MAX]" if is_new_max else ""

            bearing_deg = round(bearing)
            dn = dir_name(bearing)
            alt_str = alt or "?"
            fr24_url = f"https://www.flightradar24.com/{callsign.strip()}"

            print(f"[RECEIVED]  {callsign:10s}  "
                  f"{dist:5.1f} NM {dn} ({bearing_deg} deg)  "
                  f"{alt_str:>6} ft{max_tag}")
            print(f"            {fr24_url}")

            seen[callsign] = time.time()

        if cycle % 4 == 0:  # status every ~60s
            print(f"[status] {len(received)} in range | model: {model.summary()}")

        cleanup_seen()
        cycle += 1
        time.sleep(15)


if __name__ == "__main__":
    run()
