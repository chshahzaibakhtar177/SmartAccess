from django.core.management.base import BaseCommand
from events.models import EventCategory


class Command(BaseCommand):
    help = 'Create default event categories'

    def handle(self, *args, **options):
        categories = [
            {
                'name': 'Academic',
                'description': 'Academic events like seminars, workshops, and lectures',
                'color': '#007bff'
            },
            {
                'name': 'Sports',
                'description': 'Sports competitions, tournaments, and fitness events',
                'color': '#28a745'
            },
            {
                'name': 'Cultural',
                'description': 'Cultural events, festivals, and entertainment programs',
                'color': '#dc3545'
            },
            {
                'name': 'Social',
                'description': 'Social gatherings, meetups, and community events',
                'color': '#ffc107'
            },
            {
                'name': 'Career',
                'description': 'Career development, job fairs, and professional networking',
                'color': '#6f42c1'
            },
            {
                'name': 'Technology',
                'description': 'Tech talks, hackathons, and innovation events',
                'color': '#17a2b8'
            },
            {
                'name': 'Health & Wellness',
                'description': 'Health awareness, wellness programs, and medical camps',
                'color': '#20c997'
            },
            {
                'name': 'Alumni',
                'description': 'Alumni reunions, networking events, and alumni activities',
                'color': '#fd7e14'
            }
        ]

        created_count = 0
        for cat_data in categories:
            category, created = EventCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'color': cat_data['color']
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {category.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Category already exists: {category.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully processed {len(categories)} categories. Created {created_count} new categories.')
        )