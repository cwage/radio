import json
import socket
import threading
import time
import re
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# Store recent aircraft positions: {reg: {flight, lat, lon, alt, timestamp, messages}}
aircraft = {}
LOCK = threading.Lock()
TTL = 3600  # keep aircraft for 1 hour


def parse_position(text):
    """Try to extract lat/lon from ACARS message text."""
    # Pattern like: N3608.0,W08640.8
    match = re.search(r'([NS])(\d{2})(\d{2}\.\d+),([EW])(\d{3})(\d{2}\.\d+)', text)
    if match:
        lat = int(match.group(2)) + float(match.group(3)) / 60
        if match.group(1) == 'S':
            lat = -lat
        lon = int(match.group(5)) + float(match.group(6)) / 60
        if match.group(4) == 'W':
            lon = -lon
        return lat, lon
    return None, None


def udp_listener():
    """Listen for acarsdec JSON messages on UDP."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', 5555))
    while True:
        data, _ = sock.recvfrom(8192)
        try:
            msg = json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        reg = msg.get('tail', '').strip()
        if not reg:
            continue

        flight = msg.get('flight', '').strip()
        text = msg.get('text', '')
        label = msg.get('label', '')
        timestamp = msg.get('timestamp', time.time())

        lat, lon = parse_position(text)

        with LOCK:
            if reg not in aircraft:
                aircraft[reg] = {
                    'reg': reg,
                    'flight': flight,
                    'lat': None,
                    'lon': None,
                    'messages': [],
                    'timestamp': time.time(),
                }

            ac = aircraft[reg]
            if flight:
                ac['flight'] = flight
            if lat is not None:
                ac['lat'] = lat
                ac['lon'] = lon
            ac['timestamp'] = time.time()
            ac['messages'].append({
                'label': label,
                'text': text[:200],
                'time': time.strftime('%H:%M:%S'),
            })
            # Keep last 20 messages per aircraft
            ac['messages'] = ac['messages'][-20:]


def cleanup():
    """Remove stale aircraft."""
    while True:
        time.sleep(60)
        now = time.time()
        with LOCK:
            stale = [k for k, v in aircraft.items() if now - v['timestamp'] > TTL]
            for k in stale:
                del aircraft[k]


MAP_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ACARS Live Map - Nashville</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body { margin: 0; font-family: monospace; }
        #map { height: 70vh; width: 100%; }
        #sidebar {
            height: 30vh; overflow-y: auto; padding: 10px;
            background: #1a1a1a; color: #0f0; font-size: 12px;
        }
        #sidebar h3 { margin: 0 0 8px 0; color: #0f0; }
        .msg-line { margin: 2px 0; border-bottom: 1px solid #333; padding: 2px 0; }
        .msg-reg { color: #ff0; }
        .msg-flight { color: #0ff; }
        .msg-time { color: #666; }
    </style>
</head>
<body>
    <div id="map"></div>
    <div id="sidebar">
        <h3>ACARS Messages</h3>
        <div id="messages"></div>
    </div>
    <script>
        var map = L.map('map').setView([36.1245, -86.6782], 11);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: 'OSM'
        }).addTo(map);

        // BNA airport marker
        L.marker([36.1245, -86.6782], {
            icon: L.divIcon({
                html: '<div style="background:#333;color:#fff;padding:2px 6px;border-radius:3px;font-size:11px;font-family:monospace;white-space:nowrap;">BNA</div>',
                iconSize: null
            })
        }).addTo(map);

        var markers = {};
        var allMessages = [];

        function update() {
            fetch('/api/aircraft')
                .then(r => r.json())
                .then(data => {
                    // Update markers
                    var seen = {};
                    data.forEach(ac => {
                        seen[ac.reg] = true;
                        if (ac.lat && ac.lon) {
                            if (markers[ac.reg]) {
                                markers[ac.reg].setLatLng([ac.lat, ac.lon]);
                                markers[ac.reg].setPopupContent(popupHtml(ac));
                            } else {
                                var m = L.marker([ac.lat, ac.lon], {
                                    icon: L.divIcon({
                                        html: '<div style="background:#000;color:#0f0;padding:2px 5px;border:1px solid #0f0;border-radius:3px;font-size:10px;font-family:monospace;white-space:nowrap;">' +
                                              (ac.flight || ac.reg) + '</div>',
                                        iconSize: null
                                    })
                                }).addTo(map);
                                m.bindPopup(popupHtml(ac));
                                markers[ac.reg] = m;
                            }
                        }

                        // Collect new messages for sidebar
                        if (ac.messages) {
                            ac.messages.forEach(msg => {
                                allMessages.push({
                                    reg: ac.reg,
                                    flight: ac.flight,
                                    label: msg.label,
                                    text: msg.text,
                                    time: msg.time,
                                });
                            });
                        }
                    });

                    // Remove stale markers
                    Object.keys(markers).forEach(k => {
                        if (!seen[k]) {
                            map.removeLayer(markers[k]);
                            delete markers[k];
                        }
                    });

                    // Update sidebar (last 50 messages)
                    allMessages = allMessages.slice(-50);
                    var html = '';
                    for (var i = allMessages.length - 1; i >= 0; i--) {
                        var m = allMessages[i];
                        html += '<div class="msg-line">' +
                            '<span class="msg-time">' + m.time + '</span> ' +
                            '<span class="msg-reg">' + m.reg + '</span> ' +
                            '<span class="msg-flight">' + (m.flight || '') + '</span> ' +
                            '[' + m.label + '] ' + m.text.substring(0, 100) +
                            '</div>';
                    }
                    document.getElementById('messages').innerHTML = html;
                });
        }

        function popupHtml(ac) {
            return '<b>' + (ac.flight || '?') + '</b><br>Reg: ' + ac.reg +
                   '<br>Pos: ' + (ac.lat ? ac.lat.toFixed(4) + ', ' + ac.lon.toFixed(4) : 'unknown');
        }

        setInterval(update, 3000);
        update();
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(MAP_HTML)


@app.route('/api/aircraft')
def api_aircraft():
    with LOCK:
        # Return aircraft with their latest messages only (not duplicating on every poll)
        result = []
        for ac in aircraft.values():
            result.append({
                'reg': ac['reg'],
                'flight': ac['flight'],
                'lat': ac['lat'],
                'lon': ac['lon'],
                'messages': ac['messages'][-3:],  # last 3 per aircraft per poll
            })
        return jsonify(result)


if __name__ == '__main__':
    t = threading.Thread(target=udp_listener, daemon=True)
    t.start()
    t2 = threading.Thread(target=cleanup, daemon=True)
    t2.start()
    app.run(host='0.0.0.0', port=8080)
