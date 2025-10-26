from django.core.management.base import BaseCommand
from library.models import BookCategory

class Command(BaseCommand):
    help = 'Create default book categories for the library system'

    def handle(self, *args, **options):
        # Default book categories with appropriate colors
        default_categories = [
            {
                'name': 'Fiction',
                'description': 'Novels, short stories, and other fictional works',
                'color': '#e74c3c'  # Red
            },
            {
                'name': 'Non-Fiction',
                'description': 'Biographies, memoirs, and factual books',
                'color': '#3498db'  # Blue
            },
            {
                'name': 'Science & Technology',
                'description': 'Computer science, engineering, physics, chemistry, and technology books',
                'color': '#9b59b6'  # Purple
            },
            {
                'name': 'Mathematics',
                'description': 'Pure mathematics, applied mathematics, and statistics',
                'color': '#f39c12'  # Orange
            },
            {
                'name': 'Business & Economics',
                'description': 'Management, finance, economics, and entrepreneurship',
                'color': '#27ae60'  # Green
            },
            {
                'name': 'Literature & Language',
                'description': 'Classical literature, poetry, linguistics, and language studies',
                'color': '#8e44ad'  # Dark Purple
            },
            {
                'name': 'History & Politics',
                'description': 'Historical accounts, political science, and social studies',
                'color': '#34495e'  # Dark Gray
            },
            {
                'name': 'Education & Teaching',
                'description': 'Educational theory, teaching methods, and academic resources',
                'color': '#16a085'  # Teal
            },
            {
                'name': 'Health & Medicine',
                'description': 'Medical textbooks, health guides, and wellness resources',
                'color': '#e67e22'  # Dark Orange
            },
            {
                'name': 'Reference & Research',
                'description': 'Dictionaries, encyclopedias, research methodologies, and reference materials',
                'color': '#95a5a6'  # Gray
            }
        ]

        created_count = 0
        for category_data in default_categories:
            category, created = BookCategory.objects.get_or_create(
                name=category_data['name'],
                defaults={
                    'description': category_data['description'],
                    'color': category_data['color']
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created book category: {category.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Book category already exists: {category.name}')
                )

        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {created_count} book categories!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('All book categories already exist in the database.')
            )