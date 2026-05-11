import requests
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .data import (search_routes, get_all_routes, get_all_stops,
                   get_live, update_live_position, BUS_ROUTES, STOP_COORDS)


def index(request):
    return render(request, 'transport_app/index.html')


@api_view(['GET'])
def api_search(request):
    source = request.GET.get('source', '').strip()
    destination = request.GET.get('destination', '').strip()
    if not source or not destination:
        return Response({'error': 'source and destination required'}, status=400)
    return Response({'routes': search_routes(source, destination)})


@api_view(['GET'])
def api_routes(request):
    return Response({'routes': get_all_routes()})


@api_view(['GET'])
def api_stops(request):
    return Response({'stops': get_all_stops()})


@api_view(['GET'])
def api_live(request):
    return Response({
        r['bus_number']: get_live(r['bus_number'], r['stops'])
        for r in BUS_ROUTES
    })


@api_view(['POST'])
@csrf_exempt
def api_update_location(request):
    """Real GPS update — POST { bus_number, lat, lng }"""
    bus_number = request.data.get('bus_number')
    lat = request.data.get('lat')
    lng = request.data.get('lng')
    if not all([bus_number, lat, lng]):
        return Response({'error': 'bus_number, lat, lng required'}, status=400)
    route = next((r for r in BUS_ROUTES if r['bus_number'] == bus_number), None)
    if not route:
        return Response({'error': f'Bus {bus_number} not found'}, status=404)
    update_live_position(bus_number, float(lat), float(lng), route['stops'])
    return Response({'success': True})


@api_view(['GET'])
def api_stop_coords(request):
    return Response(STOP_COORDS)


# ── API 1: OpenWeatherMap ─────────────────────────────────────────────────────

IMPORT_WEATHER = {
    'Chennai':        {'temp': 34, 'feels_like': 38, 'description': 'Hazy Sunshine',   'icon': '01d', 'humidity': 72, 'wind_speed': 3.2},
    'Coimbatore':     {'temp': 29, 'feels_like': 31, 'description': 'Partly Cloudy',    'icon': '02d', 'humidity': 65, 'wind_speed': 4.1},
    'Salem':          {'temp': 31, 'feels_like': 33, 'description': 'Clear Sky',        'icon': '01d', 'humidity': 58, 'wind_speed': 2.8},
    'Madurai':        {'temp': 36, 'feels_like': 40, 'description': 'Hot and Sunny',    'icon': '01d', 'humidity': 60, 'wind_speed': 3.5},
    'Trichy':         {'temp': 33, 'feels_like': 36, 'description': 'Mostly Sunny',     'icon': '01d', 'humidity': 63, 'wind_speed': 3.0},
    'Ooty':           {'temp': 18, 'feels_like': 16, 'description': 'Cool and Misty',   'icon': '10d', 'humidity': 85, 'wind_speed': 5.2},
    'Kanyakumari':    {'temp': 30, 'feels_like': 33, 'description': 'Sea Breeze',       'icon': '02d', 'humidity': 78, 'wind_speed': 6.1},
    'Pondicherry':    {'temp': 32, 'feels_like': 35, 'description': 'Humid and Warm',   'icon': '02d', 'humidity': 80, 'wind_speed': 4.0},
    'Vellore':        {'temp': 30, 'feels_like': 32, 'description': 'Partly Cloudy',    'icon': '02d', 'humidity': 62, 'wind_speed': 2.5},
    'Thanjavur':      {'temp': 33, 'feels_like': 36, 'description': 'Sunny',            'icon': '01d', 'humidity': 66, 'wind_speed': 2.9},
}

def _simulated_weather(stop, note='⏳ API key created — activates in 2-3 hrs. Showing sample data until then.'):
    base = IMPORT_WEATHER.get(stop, {'temp': 30, 'feels_like': 32, 'description': 'Warm and Sunny', 'icon': '01d', 'humidity': 65, 'wind_speed': 3.0})
    return Response({**base, 'stop': stop, 'note': note})

@api_view(['GET'])
def api_weather(request):
    """
    GET /api/weather/?stop=Chennai
    Calls OpenWeatherMap free API and returns weather for that stop.
    """
    stop = request.GET.get('stop', '').strip()
    if not stop:
        return Response({'error': 'stop name required'}, status=400)

    coords = STOP_COORDS.get(stop)
    if not coords:
        return Response({'error': f'Stop {stop} not found'}, status=404)

    api_key = settings.OPENWEATHER_API_KEY
    url = (
        f'https://api.openweathermap.org/data/2.5/weather'
        f'?lat={coords[0]}&lon={coords[1]}&appid={api_key}&units=metric'
    )

    # If key not configured yet, return simulated weather
    if not api_key or api_key == 'your_openweathermap_api_key_here':
        return _simulated_weather(stop)

    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()

        if resp.status_code == 401:
            return _simulated_weather(stop, note='⏳ API key created — activates in 2-3 hrs. Showing sample data until then.')

        if resp.status_code != 200:
            return _simulated_weather(stop, note='Weather API unavailable — showing simulated data')

        return Response({
            'stop': stop,
            'temp': round(data['main']['temp']),
            'feels_like': round(data['main']['feels_like']),
            'description': data['weather'][0]['description'].title(),
            'icon': data['weather'][0]['icon'],
            'humidity': data['main']['humidity'],
            'wind_speed': data['wind']['speed'],
            'note': None,
        })
    except Exception:
        return _simulated_weather(stop, note='Weather service unavailable — showing simulated data')


# ── API 2: OpenRouteService ───────────────────────────────────────────────────

@api_view(['GET'])
def api_road_route(request):
    """
    GET /api/road-route/?bus=300
    Calls OpenRouteService free API and returns the actual road path
    (list of lat/lng points) for a bus route — used to draw on the map.
    """
    bus_number = request.GET.get('bus', '').strip()
    route = next((r for r in BUS_ROUTES if r['bus_number'] == bus_number), None)
    if not route:
        return Response({'error': f'Bus {bus_number} not found'}, status=404)

    # Build coordinates list [lng, lat] — ORS uses lng,lat order
    coords = []
    for stop in route['stops']:
        c = STOP_COORDS.get(stop)
        if c:
            coords.append([c[1], c[0]])  # ORS wants [lng, lat]

    if len(coords) < 2:
        return Response({'error': 'Not enough stop coordinates'}, status=400)

    api_key = settings.ORS_API_KEY
    url = 'https://api.openrouteservice.org/v2/directions/driving-car/geojson'
    headers = {
        'Authorization': api_key,
        'Content-Type': 'application/json',
    }
    body = {'coordinates': coords}

    try:
        resp = requests.post(url, json=body, headers=headers, timeout=10)
        data = resp.json()

        if resp.status_code != 200:
            return Response({'error': data.get('error', {}).get('message', 'ORS API error')}, status=502)

        # Extract the road path coordinates from GeoJSON
        road_coords = data['features'][0]['geometry']['coordinates']
        # Convert [lng, lat] → [lat, lng] for Leaflet
        path = [[pt[1], pt[0]] for pt in road_coords]

        summary = data['features'][0]['properties']['summary']
        return Response({
            'bus_number': bus_number,
            'route_name': route['route_name'],
            'path': path,
            'distance_km': round(summary['distance'] / 1000, 1),
            'duration_min': round(summary['duration'] / 60),
        })
    except requests.exceptions.Timeout:
        return Response({'error': 'Route service timeout'}, status=504)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
