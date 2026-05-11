from django.core.management.base import BaseCommand
from transport_app.db import get_routes_collection

SAMPLE_ROUTES = [
    {
        'bus_number': '109A',
        'route_name': 'Chennai - Villupuram',
        'stops': ['Chennai', 'Tambaram', 'Chengalpattu', 'Tindivanam', 'Villupuram'],
        'timings': ['06:00', '08:30', '11:00', '14:00', '17:30', '20:00'],
    },
    {
        'bus_number': '300',
        'route_name': 'Coimbatore - Salem',
        'stops': ['Coimbatore', 'Tiruppur', 'Erode', 'Salem'],
        'timings': ['05:30', '07:00', '09:30', '12:00', '15:00', '18:00'],
    },
    {
        'bus_number': '47C',
        'route_name': 'Madurai - Trichy',
        'stops': ['Madurai', 'Dindigul', 'Karur', 'Trichy'],
        'timings': ['06:00', '09:00', '12:00', '15:00', '18:00'],
    },
    {
        'bus_number': '15B',
        'route_name': 'Chennai - Kanchipuram',
        'stops': ['Chennai', 'Tambaram', 'Vandalur', 'Kanchipuram'],
        'timings': ['06:30', '08:00', '10:00', '13:00', '16:00', '19:00'],
    },
    {
        'bus_number': '222',
        'route_name': 'Trichy - Thanjavur',
        'stops': ['Trichy', 'Lalgudi', 'Papanasam', 'Thanjavur'],
        'timings': ['07:00', '09:00', '11:00', '14:00', '17:00'],
    },
    {
        'bus_number': '88',
        'route_name': 'Salem - Krishnagiri',
        'stops': ['Salem', 'Dharmapuri', 'Krishnagiri'],
        'timings': ['06:00', '10:00', '14:00', '18:00'],
    },
    {
        'bus_number': '55D',
        'route_name': 'Vellore - Tiruvannamalai',
        'stops': ['Vellore', 'Polur', 'Tiruvannamalai'],
        'timings': ['07:30', '11:00', '14:30', '17:30'],
    },
    {
        'bus_number': '33',
        'route_name': 'Tirunelveli - Kanyakumari',
        'stops': ['Tirunelveli', 'Nagercoil', 'Kanyakumari'],
        'timings': ['06:00', '09:00', '12:00', '15:00', '18:00'],
    },
    {
        'bus_number': '77',
        'route_name': 'Coimbatore - Ooty',
        'stops': ['Coimbatore', 'Mettupalayam', 'Coonoor', 'Ooty'],
        'timings': ['06:00', '08:00', '10:00', '13:00', '16:00'],
    },
    {
        'bus_number': '12E',
        'route_name': 'Chennai - Pondicherry',
        'stops': ['Chennai', 'Chengalpattu', 'Tindivanam', 'Villupuram', 'Pondicherry'],
        'timings': ['06:00', '07:30', '09:00', '11:00', '14:00', '17:00'],
    },
]


class Command(BaseCommand):
    help = 'Seed MongoDB with sample bus route data'

    def handle(self, *args, **kwargs):
        collection = get_routes_collection()
        inserted = 0
        updated = 0

        for route in SAMPLE_ROUTES:
            existing = collection.find_one({'bus_number': route['bus_number']})
            if existing:
                collection.update_one({'bus_number': route['bus_number']}, {'$set': route})
                updated += 1
            else:
                collection.insert_one(route)
                inserted += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Done! Inserted: {inserted}, Updated: {updated} routes.'
            )
        )
