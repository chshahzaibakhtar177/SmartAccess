from django.core.management.base import BaseCommand
from datetime import timedelta
from transportation.models import Bus, Route


class Command(BaseCommand):
    help = 'Seeds the database with sample buses and routes for transportation module'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting transportation data seeding...'))

        # Create Routes first
        routes_data = [
            {
                'route_name': 'Route A - City Center',
                'start_location': 'University Main Gate',
                'end_location': 'City Center Plaza',
                'total_distance': 12.5,
                'estimated_time': timedelta(hours=0, minutes=35),
                'status': 'active'
            },
            {
                'route_name': 'Route B - North Campus',
                'start_location': 'University Main Gate',
                'end_location': 'North Campus Station',
                'total_distance': 8.3,
                'estimated_time': timedelta(hours=0, minutes=25),
                'status': 'active'
            },
            {
                'route_name': 'Route C - South District',
                'start_location': 'University Main Gate',
                'end_location': 'South District Terminal',
                'total_distance': 15.7,
                'estimated_time': timedelta(hours=0, minutes=45),
                'status': 'active'
            },
            {
                'route_name': 'Route D - East Valley',
                'start_location': 'University Main Gate',
                'end_location': 'East Valley Mall',
                'total_distance': 10.2,
                'estimated_time': timedelta(hours=0, minutes=30),
                'status': 'active'
            },
            {
                'route_name': 'Route E - West Park',
                'start_location': 'University Main Gate',
                'end_location': 'West Park Residences',
                'total_distance': 6.8,
                'estimated_time': timedelta(hours=0, minutes=20),
                'status': 'active'
            },
            {
                'route_name': 'Route F - Airport Express',
                'start_location': 'University Main Gate',
                'end_location': 'International Airport',
                'total_distance': 25.0,
                'estimated_time': timedelta(hours=1, minutes=0),
                'status': 'inactive'
            },
        ]

        routes = {}
        for route_data in routes_data:
            route, created = Route.objects.get_or_create(
                route_name=route_data['route_name'],
                defaults=route_data
            )
            routes[route_data['route_name']] = route
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created route: {route.route_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'- Route already exists: {route.route_name}'))

        # Create Buses
        buses_data = [
            {
                'bus_number': 'BUS-001',
                'driver_name': 'Muhammad Ali',
                'driver_contact': '+92-300-1234567',
                'capacity': 45,
                'route_name': 'Route A - City Center',
                'is_active': True
            },
            {
                'bus_number': 'BUS-002',
                'driver_name': 'Ahmed Hassan',
                'driver_contact': '+92-300-2345678',
                'capacity': 40,
                'route_name': 'Route B - North Campus',
                'is_active': True
            },
            {
                'bus_number': 'BUS-003',
                'driver_name': 'Fatima Zahra',
                'driver_contact': '+92-300-3456789',
                'capacity': 50,
                'route_name': 'Route A - City Center',
                'is_active': True
            },
            {
                'bus_number': 'BUS-004',
                'driver_name': 'Usman Khan',
                'driver_contact': '+92-300-4567890',
                'capacity': 38,
                'route_name': 'Route C - South District',
                'is_active': True
            },
            {
                'bus_number': 'BUS-005',
                'driver_name': 'Ayesha Siddiqui',
                'driver_contact': '+92-300-5678901',
                'capacity': 42,
                'route_name': 'Route D - East Valley',
                'is_active': True
            },
            {
                'bus_number': 'BUS-006',
                'driver_name': 'Bilal Ahmed',
                'driver_contact': '+92-300-6789012',
                'capacity': 35,
                'route_name': 'Route E - West Park',
                'is_active': True
            },
            {
                'bus_number': 'BUS-007',
                'driver_name': 'Zainab Ali',
                'driver_contact': '+92-300-7890123',
                'capacity': 45,
                'route_name': 'Route B - North Campus',
                'is_active': True
            },
            {
                'bus_number': 'BUS-008',
                'driver_name': 'Hassan Raza',
                'driver_contact': '+92-300-8901234',
                'capacity': 48,
                'route_name': 'Route C - South District',
                'is_active': True
            },
            {
                'bus_number': 'BUS-009',
                'driver_name': 'Mariam Noor',
                'driver_contact': '+92-300-9012345',
                'capacity': 40,
                'route_name': 'Route A - City Center',
                'is_active': False
            },
            {
                'bus_number': 'BUS-010',
                'driver_name': 'Kamran Shahid',
                'driver_contact': '+92-300-0123456',
                'capacity': 55,
                'route_name': 'Route F - Airport Express',
                'is_active': False
            },
        ]

        for bus_data in buses_data:
            route_name = bus_data.pop('route_name')
            route = routes[route_name]
            bus, created = Bus.objects.get_or_create(
                bus_number=bus_data['bus_number'],
                defaults={**bus_data, 'route': route}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created bus: {bus.bus_number} - {bus.driver_name} on {route.route_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'- Bus already exists: {bus.bus_number}'))

        # Summary
        total_routes = Route.objects.count()
        active_routes = Route.objects.filter(status='active').count()
        total_buses = Bus.objects.count()
        active_buses = Bus.objects.filter(is_active=True).count()

        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('Transportation Data Seeding Complete!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.SUCCESS(f'Total Routes: {total_routes} ({active_routes} active)'))
        self.stdout.write(self.style.SUCCESS(f'Total Buses: {total_buses} ({active_buses} active)'))
        self.stdout.write(self.style.SUCCESS('='*50 + '\n'))
