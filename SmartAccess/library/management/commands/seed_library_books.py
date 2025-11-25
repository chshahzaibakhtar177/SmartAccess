from django.core.management.base import BaseCommand
from library.models import Book, BookCategory


class Command(BaseCommand):
    help = 'Seeds the database with sample books for the library module'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting library books seeding...'))

        # Ensure categories exist
        categories_data = [
            {'name': 'Computer Science', 'description': 'Programming, algorithms, and computing', 'color': '#007bff'},
            {'name': 'Mathematics', 'description': 'Pure and applied mathematics', 'color': '#28a745'},
            {'name': 'Physics', 'description': 'Classical and modern physics', 'color': '#dc3545'},
            {'name': 'Engineering', 'description': 'Various engineering disciplines', 'color': '#ffc107'},
            {'name': 'Literature', 'description': 'Fiction and non-fiction literature', 'color': '#6f42c1'},
            {'name': 'Business', 'description': 'Management and business studies', 'color': '#fd7e14'},
            {'name': 'Science', 'description': 'General science books', 'color': '#20c997'},
        ]

        categories = {}
        for cat_data in categories_data:
            category, created = BookCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            categories[cat_data['name']] = category
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created category: {category.name}'))

        # Sample books data
        books_data = [
            # Computer Science Books
            {
                'isbn': '9780262033848',
                'title': 'Introduction to Algorithms',
                'author': 'Thomas H. Cormen',
                'publisher': 'MIT Press',
                'publication_year': 2009,
                'edition': '3rd Edition',
                'category': 'Computer Science',
                'pages': 1312,
                'location': 'A-1-CS',
                'price': 89.99,
                'status': 'available'
            },
            {
                'isbn': '9780134685991',
                'title': 'Effective Java',
                'author': 'Joshua Bloch',
                'publisher': 'Addison-Wesley',
                'publication_year': 2018,
                'edition': '3rd Edition',
                'category': 'Computer Science',
                'pages': 416,
                'location': 'A-2-CS',
                'price': 54.99,
                'status': 'available'
            },
            {
                'isbn': '9781449355739',
                'title': 'Learning Python',
                'author': 'Mark Lutz',
                'publisher': "O'Reilly Media",
                'publication_year': 2013,
                'edition': '5th Edition',
                'category': 'Computer Science',
                'pages': 1648,
                'location': 'A-3-CS',
                'price': 64.99,
                'status': 'available'
            },
            {
                'isbn': '9780135957059',
                'title': 'The Pragmatic Programmer',
                'author': 'David Thomas, Andrew Hunt',
                'publisher': 'Addison-Wesley',
                'publication_year': 2019,
                'edition': '2nd Edition',
                'category': 'Computer Science',
                'pages': 352,
                'location': 'A-4-CS',
                'price': 49.99,
                'status': 'available'
            },
            {
                'isbn': '9781492040347',
                'title': 'Designing Data-Intensive Applications',
                'author': 'Martin Kleppmann',
                'publisher': "O'Reilly Media",
                'publication_year': 2017,
                'edition': '1st Edition',
                'category': 'Computer Science',
                'pages': 616,
                'location': 'A-5-CS',
                'price': 59.99,
                'status': 'available'
            },
            
            # Mathematics Books
            {
                'isbn': '9780073383095',
                'title': 'Calculus: Early Transcendentals',
                'author': 'James Stewart',
                'publisher': 'Brooks Cole',
                'publication_year': 2015,
                'edition': '8th Edition',
                'category': 'Mathematics',
                'pages': 1368,
                'location': 'B-1-MATH',
                'price': 94.99,
                'status': 'available'
            },
            {
                'isbn': '9780321964687',
                'title': 'Linear Algebra and Its Applications',
                'author': 'David C. Lay',
                'publisher': 'Pearson',
                'publication_year': 2015,
                'edition': '5th Edition',
                'category': 'Mathematics',
                'pages': 576,
                'location': 'B-2-MATH',
                'price': 79.99,
                'status': 'available'
            },
            {
                'isbn': '9780471317180',
                'title': 'Advanced Engineering Mathematics',
                'author': 'Erwin Kreyszig',
                'publisher': 'Wiley',
                'publication_year': 2011,
                'edition': '10th Edition',
                'category': 'Mathematics',
                'pages': 1264,
                'location': 'B-3-MATH',
                'price': 89.99,
                'status': 'available'
            },
            
            # Physics Books
            {
                'isbn': '9781429244145',
                'title': 'University Physics',
                'author': 'Hugh D. Young, Roger A. Freedman',
                'publisher': 'Pearson',
                'publication_year': 2015,
                'edition': '14th Edition',
                'category': 'Physics',
                'pages': 1632,
                'location': 'C-1-PHYS',
                'price': 99.99,
                'status': 'available'
            },
            {
                'isbn': '9781118230725',
                'title': 'Fundamentals of Physics',
                'author': 'David Halliday, Robert Resnick',
                'publisher': 'Wiley',
                'publication_year': 2013,
                'edition': '10th Edition',
                'category': 'Physics',
                'pages': 1450,
                'location': 'C-2-PHYS',
                'price': 94.99,
                'status': 'available'
            },
            
            # Engineering Books
            {
                'isbn': '9780134444321',
                'title': 'Engineering Mechanics: Statics',
                'author': 'Russell C. Hibbeler',
                'publisher': 'Pearson',
                'publication_year': 2015,
                'edition': '14th Edition',
                'category': 'Engineering',
                'pages': 752,
                'location': 'D-1-ENG',
                'price': 84.99,
                'status': 'available'
            },
            {
                'isbn': '9780134441146',
                'title': 'Electric Circuits',
                'author': 'James W. Nilsson',
                'publisher': 'Pearson',
                'publication_year': 2014,
                'edition': '10th Edition',
                'category': 'Engineering',
                'pages': 896,
                'location': 'D-2-ENG',
                'price': 79.99,
                'status': 'available'
            },
            {
                'isbn': '9780073398112',
                'title': 'Thermodynamics: An Engineering Approach',
                'author': 'Yunus Cengel, Michael Boles',
                'publisher': 'McGraw-Hill',
                'publication_year': 2014,
                'edition': '8th Edition',
                'category': 'Engineering',
                'pages': 1024,
                'location': 'D-3-ENG',
                'price': 89.99,
                'status': 'available'
            },
            
            # Literature Books
            {
                'isbn': '9780141439518',
                'title': 'Pride and Prejudice',
                'author': 'Jane Austen',
                'publisher': 'Penguin Classics',
                'publication_year': 2012,
                'edition': 'Revised Edition',
                'category': 'Literature',
                'pages': 480,
                'location': 'E-1-LIT',
                'price': 14.99,
                'status': 'available'
            },
            {
                'isbn': '9780451524935',
                'title': '1984',
                'author': 'George Orwell',
                'publisher': 'Signet Classic',
                'publication_year': 1950,
                'edition': 'Mass Market',
                'category': 'Literature',
                'pages': 328,
                'location': 'E-2-LIT',
                'price': 12.99,
                'status': 'available'
            },
            {
                'isbn': '9780743273565',
                'title': 'The Great Gatsby',
                'author': 'F. Scott Fitzgerald',
                'publisher': 'Scribner',
                'publication_year': 2004,
                'edition': 'Revised',
                'category': 'Literature',
                'pages': 180,
                'location': 'E-3-LIT',
                'price': 15.99,
                'status': 'available'
            },
            
            # Business Books
            {
                'isbn': '9780735211292',
                'title': 'Atomic Habits',
                'author': 'James Clear',
                'publisher': 'Avery',
                'publication_year': 2018,
                'edition': '1st Edition',
                'category': 'Business',
                'pages': 320,
                'location': 'F-1-BUS',
                'price': 26.99,
                'status': 'available'
            },
            {
                'isbn': '9780307887894',
                'title': 'The Lean Startup',
                'author': 'Eric Ries',
                'publisher': 'Crown Business',
                'publication_year': 2011,
                'edition': '1st Edition',
                'category': 'Business',
                'pages': 336,
                'location': 'F-2-BUS',
                'price': 27.99,
                'status': 'available'
            },
            {
                'isbn': '9781591847786',
                'title': 'Good to Great',
                'author': 'Jim Collins',
                'publisher': 'Harper Business',
                'publication_year': 2001,
                'edition': '1st Edition',
                'category': 'Business',
                'pages': 320,
                'location': 'F-3-BUS',
                'price': 29.99,
                'status': 'available'
            },
            
            # Science Books
            {
                'isbn': '9780393339918',
                'title': 'A Brief History of Time',
                'author': 'Stephen Hawking',
                'publisher': 'Bantam',
                'publication_year': 1998,
                'edition': '10th Anniversary',
                'category': 'Science',
                'pages': 256,
                'location': 'G-1-SCI',
                'price': 18.99,
                'status': 'available'
            },
            {
                'isbn': '9780393316049',
                'title': 'Cosmos',
                'author': 'Carl Sagan',
                'publisher': 'Ballantine Books',
                'publication_year': 2013,
                'edition': 'Reissue',
                'category': 'Science',
                'pages': 396,
                'location': 'G-2-SCI',
                'price': 19.99,
                'status': 'available'
            },
        ]

        # Create books
        books_created = 0
        books_existed = 0
        
        for book_data in books_data:
            category_name = book_data.pop('category')
            book_data['category'] = categories[category_name]
            
            # Check if book exists by ISBN
            if not Book.objects.filter(isbn=book_data['isbn']).exists():
                Book.objects.create(**book_data)
                books_created += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created book: {book_data["title"]}'))
            else:
                books_existed += 1
                self.stdout.write(self.style.WARNING(f'- Book already exists: {book_data["title"]}'))

        # Create some duplicate copies for popular books
        popular_isbns = ['9780262033848', '9781449355739', '9780073383095']
        for isbn in popular_isbns:
            original_book = Book.objects.filter(isbn=isbn, copy_number=1).first()
            if original_book:
                for copy_num in range(2, 4):  # Create copies 2 and 3
                    # Check using both isbn and copy_number
                    existing = Book.objects.filter(isbn=isbn, copy_number=copy_num).exists()
                    if not existing:
                        # Create a new book object without using the unique isbn in create
                        new_book = Book(
                            isbn=original_book.isbn,
                            title=original_book.title,
                            author=original_book.author,
                            publisher=original_book.publisher,
                            publication_year=original_book.publication_year,
                            edition=original_book.edition,
                            category=original_book.category,
                            pages=original_book.pages,
                            location=original_book.location,
                            copy_number=copy_num,
                            status='available',
                            price=original_book.price
                        )
                        new_book.save()
                        books_created += 1
                        self.stdout.write(self.style.SUCCESS(f'✓ Created copy #{copy_num} of: {original_book.title}'))

        # Summary
        total_books = Book.objects.count()
        total_categories = BookCategory.objects.count()
        available_books = Book.objects.filter(status='available').count()

        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('Library Books Seeding Complete!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.SUCCESS(f'Books Created: {books_created}'))
        self.stdout.write(self.style.SUCCESS(f'Books Already Existed: {books_existed}'))
        self.stdout.write(self.style.SUCCESS(f'Total Books: {total_books} ({available_books} available)'))
        self.stdout.write(self.style.SUCCESS(f'Total Categories: {total_categories}'))
        self.stdout.write(self.style.SUCCESS('='*50 + '\n'))
