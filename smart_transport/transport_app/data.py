import random
from datetime import datetime

# Real GPS coordinates for Tamil Nadu bus stops
STOP_COORDS = {
    'Chennai':         [13.0827, 80.2707],
    'Tambaram':        [12.9249, 80.1000],
    'Chengalpattu':    [12.6819, 79.9760],
    'Tindivanam':      [12.2253, 79.6530],
    'Villupuram':      [11.9401, 79.4861],
    'Coimbatore':      [11.0168, 76.9558],
    'Tiruppur':        [11.1085, 77.3411],
    'Erode':           [11.3410, 77.7172],
    'Salem':           [11.6643, 78.1460],
    'Madurai':         [9.9252,  78.1198],
    'Dindigul':        [10.3624, 77.9695],
    'Karur':           [10.9601, 78.0766],
    'Trichy':          [10.7905, 78.7047],
    'Kanchipuram':     [12.8342, 79.7036],
    'Vandalur':        [12.8833, 80.0833],
    'Lalgudi':         [10.8667, 78.8167],
    'Papanasam':       [10.9333, 79.2667],
    'Thanjavur':       [10.7870, 79.1378],
    'Dharmapuri':      [12.1211, 78.1582],
    'Krishnagiri':     [12.5186, 78.2137],
    'Vellore':         [12.9165, 79.1325],
    'Polur':           [12.5167, 79.3833],
    'Tiruvannamalai':  [12.2253, 79.0747],
    'Tirunelveli':     [8.7139,  77.7567],
    'Nagercoil':       [8.1833,  77.4119],
    'Kanyakumari':     [8.0883,  77.5385],
    'Mettupalayam':    [11.2987, 76.9366],
    'Coonoor':         [11.3530, 76.7959],
    'Ooty':            [11.4102, 76.6950],
    'Pondicherry':     [11.9416, 79.8083],
}

BUS_ROUTES = [
    {
        'bus_number': '109A',
        'route_name': 'Chennai → Villupuram',
        'stops': ['Chennai', 'Tambaram', 'Chengalpattu', 'Tindivanam', 'Villupuram'],
        'timings': ['06:00', '08:30', '11:00', '14:00', '17:30', '20:00'],
    },
    {
        'bus_number': '300',
        'route_name': 'Coimbatore → Salem',
        'stops': ['Coimbatore', 'Tiruppur', 'Erode', 'Salem'],
        'timings': ['05:30', '07:00', '09:30', '12:00', '15:00', '18:00'],
    },
    {
        'bus_number': '47C',
        'route_name': 'Madurai → Trichy',
        'stops': ['Madurai', 'Dindigul', 'Karur', 'Trichy'],
        'timings': ['06:00', '09:00', '12:00', '15:00', '18:00'],
    },
    {
        'bus_number': '15B',
        'route_name': 'Chennai → Kanchipuram',
        'stops': ['Chennai', 'Tambaram', 'Vandalur', 'Kanchipuram'],
        'timings': ['06:30', '08:00', '10:00', '13:00', '16:00', '19:00'],
    },
    {
        'bus_number': '222',
        'route_name': 'Trichy → Thanjavur',
        'stops': ['Trichy', 'Lalgudi', 'Papanasam', 'Thanjavur'],
        'timings': ['07:00', '09:00', '11:00', '14:00', '17:00'],
    },
    {
        'bus_number': '88',
        'route_name': 'Salem → Krishnagiri',
        'stops': ['Salem', 'Dharmapuri', 'Krishnagiri'],
        'timings': ['06:00', '10:00', '14:00', '18:00'],
    },
    {
        'bus_number': '55D',
        'route_name': 'Vellore → Tiruvannamalai',
        'stops': ['Vellore', 'Polur', 'Tiruvannamalai'],
        'timings': ['07:30', '11:00', '14:30', '17:30'],
    },
    {
        'bus_number': '33',
        'route_name': 'Tirunelveli → Kanyakumari',
        'stops': ['Tirunelveli', 'Nagercoil', 'Kanyakumari'],
        'timings': ['06:00', '09:00', '12:00', '15:00', '18:00'],
    },
    {
        'bus_number': '77',
        'route_name': 'Coimbatore → Ooty',
        'stops': ['Coimbatore', 'Mettupalayam', 'Coonoor', 'Ooty'],
        'timings': ['06:00', '08:00', '10:00', '13:00', '16:00'],
    },
    {
        'bus_number': '12E',
        'route_name': 'Chennai → Pondicherry',
        'stops': ['Chennai', 'Chengalpattu', 'Tindivanam', 'Villupuram', 'Pondicherry'],
        'timings': ['06:00', '07:30', '09:00', '11:00', '14:00', '17:00'],
    },
]

# In-memory live GPS store — updated by /api/update-location/
# Format: { 'bus_number': {'lat': x, 'lng': y, 'at': stop, 'next': stop, ...} }
LIVE_POSITIONS = {}


def _interpolate(coord1, coord2, fraction):
    """Return a GPS point fraction of the way between two coordinates."""
    return [
        coord1[0] + (coord2[0] - coord1[0]) * fraction,
        coord1[1] + (coord2[1] - coord1[1]) * fraction,
    ]


def get_live(bus_number, stops):
    """
    If real GPS was posted via /api/update-location/ use that.
    Otherwise simulate position between two stops using current time.
    """
    if bus_number in LIVE_POSITIONS:
        return LIVE_POSITIONS[bus_number]

    # Simulate: use current minute to pick position between two stops
    seed = int(datetime.now().strftime('%H%M')) + sum(ord(c) for c in bus_number)
    random.seed(seed)
    idx = random.randint(0, len(stops) - 2)
    delay = random.choice([0, 0, 0, 5, 10])

    # Interpolate GPS between current stop and next stop
    c1 = STOP_COORDS.get(stops[idx], [11.0, 77.0])
    c2 = STOP_COORDS.get(stops[idx + 1], [11.0, 77.0])
    fraction = (datetime.now().second % 60) / 60
    pos = _interpolate(c1, c2, fraction)

    return {
        'lat': round(pos[0], 6),
        'lng': round(pos[1], 6),
        'at': stops[idx],
        'next': stops[idx + 1],
        'at_index': idx,
        'delay': delay,
        'status': 'On Time' if delay == 0 else f'{delay} min late',
        'source': 'simulated',
    }


def update_live_position(bus_number, lat, lng, stops):
    """Called when a real GPS update is received. Finds nearest stop."""
    nearest_idx = 0
    min_dist = float('inf')
    for i, stop in enumerate(stops):
        coord = STOP_COORDS.get(stop)
        if coord:
            dist = ((coord[0] - lat) ** 2 + (coord[1] - lng) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                nearest_idx = i

    next_idx = min(nearest_idx + 1, len(stops) - 1)
    LIVE_POSITIONS[bus_number] = {
        'lat': lat,
        'lng': lng,
        'at': stops[nearest_idx],
        'next': stops[next_idx],
        'at_index': nearest_idx,
        'delay': 0,
        'status': 'On Time',
        'source': 'gps',
    }


def next_departure(timings):
    now = datetime.now()
    for t in timings:
        h, m = map(int, t.split(':'))
        dep = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if dep > now:
            mins = int((dep - now).total_seconds() / 60)
            return t, mins
    return timings[0], 'Tomorrow'


def _find_stop(query, stops):
    q = query.strip().lower()
    for i, s in enumerate(stops):
        if q in s.lower() or s.lower() in q:
            return i
    return None


def search_routes(source, destination):
    results = []
    for r in BUS_ROUTES:
        si = _find_stop(source, r['stops'])
        di = _find_stop(destination, r['stops'])
        if si is not None and di is not None and si < di:
            dep, mins = next_departure(r['timings'])
            live = get_live(r['bus_number'], r['stops'])
            results.append({
                **r,
                'intermediate_stops': r['stops'][si:di + 1],
                'next_dep': dep,
                'mins_until': mins,
                'live': live,
                'stop_coords': {s: STOP_COORDS.get(s, []) for s in r['stops']},
            })
    return results


def get_all_routes():
    result = []
    for r in BUS_ROUTES:
        dep, mins = next_departure(r['timings'])
        live = get_live(r['bus_number'], r['stops'])
        result.append({
            **r,
            'next_dep': dep,
            'mins_until': mins,
            'live': live,
            'stop_coords': {s: STOP_COORDS.get(s, []) for s in r['stops']},
        })
    return result


def get_all_stops():
    stops = set()
    for r in BUS_ROUTES:
        stops.update(r['stops'])
    return sorted(stops)
