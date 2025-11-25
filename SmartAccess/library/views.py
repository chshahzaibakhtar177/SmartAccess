from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from datetime import timedelta
import json

from .models import Book, BookCategory, BookBorrow, BookReservation
from students.models import Student
from .forms import BookForm, BookSearchForm, BookCategoryForm
from authentication.decorators import teacher_required, student_required


# ============ TEACHER VIEWS ============

@login_required
@teacher_required
def library_dashboard(request):
    """Library dashboard for teachers with statistics"""
    total_books = Book.objects.count()
    available_books = Book.objects.filter(status='available').count()
    borrowed_books = BookBorrow.objects.filter(status__in=['active', 'overdue']).count()
    overdue_books = BookBorrow.objects.filter(status='overdue').count()
    
    # Recent borrows
    recent_borrows = BookBorrow.objects.select_related(
        'book', 'student', 'student__user'
    ).order_by('-borrow_date')[:10]
    
    # Books running low (only 1 or 2 copies available)
    low_stock_books = Book.objects.values('title', 'author', 'isbn').annotate(
        available_count=Count('id', filter=Q(status='available'))
    ).filter(available_count__lte=2, available_count__gt=0).order_by('available_count')[:5]
    
    # Most borrowed books this month
    this_month = timezone.now().date().replace(day=1)
    popular_books = BookBorrow.objects.filter(
        borrow_date__date__gte=this_month
    ).values('book__title', 'book__author', 'book__id').annotate(
        borrow_count=Count('id')
    ).order_by('-borrow_count')[:5]
    
    context = {
        'total_books': total_books,
        'available_books': available_books,
        'borrowed_books': borrowed_books,
        'overdue_books': overdue_books,
        'recent_borrowings': recent_borrows,
        'low_stock_books': low_stock_books,
        'popular_books': popular_books,
    }
    return render(request, 'library/dashboard.html', context)


@login_required
def book_list(request):
    """Book list view with search and filters"""
    form = BookSearchForm(request.GET or None)
    books = Book.objects.select_related('category').all()
    
    # Get all categories for filter dropdown
    categories = BookCategory.objects.all()
    
    # Get search parameters
    search_query = request.GET.get('search_query', '')
    selected_category = request.GET.get('category', '')
    selected_status = request.GET.get('status', '')
    
    # Apply search filters
    if form.is_valid():
        search_query = form.cleaned_data.get('search_query')
        category = form.cleaned_data.get('category')
        status = form.cleaned_data.get('status')
        
        if search_query:
            books = books.filter(
                Q(title__icontains=search_query) |
                Q(author__icontains=search_query) |
                Q(isbn__icontains=search_query) |
                Q(publisher__icontains=search_query)
            )
        
        if category:
            books = books.filter(category=category)
        
        if status:
            books = books.filter(status=status)
    
    # Pagination
    paginator = Paginator(books, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'books': page_obj,  # Changed from page_obj to books
        'page_obj': page_obj,
        'form': form,
        'categories': categories,
        'total_books': books.count(),
        'search_query': search_query,
        'selected_category': selected_category,
        'selected_status': selected_status,
    }
    return render(request, 'library/book_list.html', context)


@login_required
def book_detail(request, pk):
    """Book detail view"""
    book = get_object_or_404(Book.objects.select_related('category'), pk=pk)
    
    # Get current borrow (who has it now)
    current_borrow = BookBorrow.objects.filter(
        book=book,
        status__in=['active', 'overdue']
    ).select_related('student', 'student__user').first()
    
    # Get borrow history
    borrowing_history = BookBorrow.objects.filter(
        book=book
    ).select_related('student', 'student__user').order_by('-borrow_date')[:5]
    
    # Related books from same category
    related_books = Book.objects.filter(
        category=book.category
    ).exclude(id=book.id)[:4]
    
    # Check if current user (if student) has borrowed this book
    user_active_borrow = None
    user_reservation = None
    can_borrow = False
    can_reserve = False
    
    if hasattr(request.user, 'student_profile'):
        student = request.user.student_profile
        user_active_borrow = BookBorrow.objects.filter(
            book=book,
            student=student,
            status__in=['active', 'overdue']
        ).first()
        
        user_reservation = BookReservation.objects.filter(
            book=book,
            student=student,
            status='pending'
        ).first()
        
        # Check if student can borrow
        active_borrows = BookBorrow.objects.filter(
            student=student,
            status__in=['active', 'overdue']
        ).count()
        can_borrow = active_borrows < 5 and book.is_available and not user_active_borrow
        
        # Can reserve if book is not available and no active reservation
        can_reserve = not book.is_available and not user_reservation and not user_active_borrow
    
    context = {
        'book': book,
        'current_borrow': current_borrow,
        'borrowing_history': borrowing_history,
        'related_books': related_books,
        'user_active_borrow': user_active_borrow,
        'user_reservation': user_reservation,
        'can_borrow': can_borrow,
        'can_reserve': can_reserve,
    }
    return render(request, 'library/book_detail.html', context)


@login_required
@teacher_required
def add_book(request):
    """Add new book"""
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save()
            messages.success(request, f'Book "{book.title}" added successfully!')
            return redirect('book_detail', pk=book.pk)
    else:
        form = BookForm()
    
    context = {'form': form, 'action': 'Add'}
    return render(request, 'library/book_form.html', context)


@login_required
@teacher_required
def edit_book(request, pk):
    """Edit existing book"""
    book = get_object_or_404(Book, pk=pk)
    
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            book = form.save()
            messages.success(request, f'Book "{book.title}" updated successfully!')
            return redirect('book_detail', pk=book.pk)
    else:
        form = BookForm(instance=book)
    
    context = {'form': form, 'book': book, 'action': 'Edit'}
    return render(request, 'library/book_form.html', context)


@login_required
@teacher_required
def delete_book(request, pk):
    """Delete book"""
    book = get_object_or_404(Book, pk=pk)
    
    # Check if book has active borrows
    active_borrows = BookBorrow.objects.filter(
        book=book,
        status__in=['active', 'overdue']
    ).count()
    
    if active_borrows > 0:
        messages.error(request, f'Cannot delete "{book.title}". It has {active_borrows} active borrow(s).')
        return redirect('book_detail', pk=pk)
    
    book_title = book.title
    book.delete()
    messages.success(request, f'Book "{book_title}" deleted successfully!')
    return redirect('book_list')


# ============ TEACHER BOOK ISSUING ============

@login_required
@teacher_required
def teacher_issue_book(request):
    """Teacher issues book to student - can search or scan NFC"""
    if request.method == 'POST':
        # Check if request is JSON
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                book_id = data.get('book_id')
                student_id = data.get('student_id')
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'message': 'Invalid JSON data'})
        else:
            # Form data
            book_id = request.POST.get('book_id')
            student_id = request.POST.get('student_id')
        
        if not book_id or not student_id:
            return JsonResponse({'success': False, 'message': 'Missing book or student information'})
        
        try:
            book = Book.objects.get(id=book_id)
            student = Student.objects.get(id=student_id)
        except Book.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Book not found'})
        except Student.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Student not found'})
        
        # Validate borrowing
        if not book.is_available:
            return JsonResponse({'success': False, 'message': f'{book.title} is not available'})
        
        # Check if student already has this book
        existing_borrow = BookBorrow.objects.filter(
            book=book,
            student=student,
            status__in=['active', 'overdue']
        ).first()
        
        if existing_borrow:
            return JsonResponse({'success': False, 'message': f'{student.name} already has this book'})
        
        # Check borrow limit
        active_borrows = BookBorrow.objects.filter(
            student=student,
            status__in=['active', 'overdue']
        ).count()
        
        if active_borrows >= student.borrowing_limit:
            return JsonResponse({'success': False, 'message': f'{student.name} has reached borrowing limit ({student.borrowing_limit} books)'})
        
        # Check for unpaid fines
        unpaid_fines = BookBorrow.objects.filter(
            student=student,
            fine_amount__gt=0,
            fine_paid=False
        ).exists()
        
        if unpaid_fines:
            return JsonResponse({'success': False, 'message': f'{student.name} has unpaid fines'})
        
        # Create borrow record with teacher tracking
        due_date = timezone.now().date() + timedelta(days=14)  # 2 weeks
        borrow = BookBorrow.objects.create(
            book=book,
            student=student,
            issued_by=request.user.teacher_profile,
            due_date=due_date,
            checkout_notes=f'Issued by {request.user.get_full_name()}'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'{book.title} issued to {student.name}',
            'student_name': student.name,
            'book_title': book.title,
            'due_date': due_date.strftime('%B %d, %Y')
        })
    
    # GET request - show issue book page
    available_books = Book.objects.filter(status='available').select_related('category').order_by('title')
    recent_issues = BookBorrow.objects.filter(
        issued_by=request.user.teacher_profile
    ).select_related('book', 'student').order_by('-borrow_date')[:10]
    
    context = {
        'available_books': available_books,
        'recent_issues': recent_issues,
    }
    return render(request, 'library/teacher_issue_book.html', context)


@login_required
@teacher_required
def teacher_return_book(request):
    """Teacher views all borrowed books and can return them"""
    # Get all active borrows
    active_borrows = BookBorrow.objects.filter(
        status__in=['active', 'overdue']
    ).select_related('book', 'student', 'student__user').order_by('due_date')
    
    # Recent returns
    recent_returns = BookBorrow.objects.filter(
        returned_to=request.user.teacher_profile,
        status='returned'
    ).select_related('book', 'student', 'student__user').order_by('-return_date')[:10]
    
    context = {
        'active_borrows': active_borrows,
        'recent_returns': recent_returns,
    }
    return render(request, 'library/teacher_return_book.html', context)


@login_required
@teacher_required
def process_book_return(request, borrow_id):
    """Process the actual return of a book"""
    if request.method == 'POST':
        borrow = get_object_or_404(BookBorrow, id=borrow_id)
        
        if borrow.status == 'returned':
            return JsonResponse({'success': False, 'message': 'Book already returned'})
        
        # Update borrow record
        borrow.status = 'returned'
        borrow.return_date = timezone.now()
        borrow.returned_to = request.user.teacher_profile
        borrow.return_notes = f'Returned to {request.user.get_full_name()}'
        
        # Calculate final fine if overdue
        if borrow.is_overdue:
            borrow.fine_amount = borrow.calculate_fine()
        
        borrow.save()
        
        return JsonResponse({
            'success': True,
            'message': f'{borrow.book.title} returned successfully',
            'book_title': borrow.book.title,
            'student_name': borrow.student.name,
            'fine_amount': float(borrow.fine_amount) if borrow.fine_amount > 0 else 0
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
@teacher_required  
def search_student_api(request):
    """API to search students by name, roll number, or NFC UID"""
    query = request.GET.get('q', '')
    nfc_uid = request.GET.get('nfc_uid', '')
    
    # Search by NFC UID
    if nfc_uid:
        students = Student.objects.filter(nfc_uid=nfc_uid)
    # Search by name or roll number
    elif len(query) >= 2:
        students = Student.objects.filter(
            Q(name__icontains=query) |
            Q(roll_number__icontains=query)
        )[:10]
    else:
        return JsonResponse({'students': []})
    
    students_data = [{
        'id': s.id,
        'name': s.name,
        'roll_number': s.roll_number,
        'nfc_uid': s.nfc_uid or '',
        'active_borrows': BookBorrow.objects.filter(
            student=s,
            status__in=['active', 'overdue']
        ).count(),
        'borrowing_limit': s.borrowing_limit
    } for s in students]
    
    return JsonResponse({'students': students_data})


@csrf_exempt
def scan_card_for_issue(request):
    """API endpoint to get student details by scanning NFC card for book issuing"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            card_id = data.get('card_id')
            
            if not card_id:
                return JsonResponse({
                    'success': False,
                    'error': 'No card_id provided'
                })
            
            try:
                student = Student.objects.get(nfc_uid=card_id)
                
                # Get active borrows count
                active_borrows = BookBorrow.objects.filter(
                    student=student,
                    status__in=['active', 'overdue']
                ).count()
                
                return JsonResponse({
                    'success': True,
                    'student_id': student.id,
                    'student_name': student.name,
                    'roll_number': student.roll_number,
                    'nfc_uid': student.nfc_uid,
                    'active_borrows': active_borrows,
                    'borrowing_limit': student.borrowing_limit
                })
            except Student.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Card not recognized. Please assign this card to a student first.'
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Only POST method allowed'
    })


# ============ STUDENT BOOK BORROWING ============

@login_required
@student_required
def borrow_book(request, pk):
    """Student borrow book"""
    book = get_object_or_404(Book, pk=pk)
    student = request.user.student_profile
    
    # Validate borrowing
    if not book.is_available:
        messages.error(request, f'"{book.title}" is not available for borrowing.')
        return redirect('book_detail', pk=pk)
    
    # Check if student already has this book
    existing_borrow = BookBorrow.objects.filter(
        book=book,
        student=student,
        status__in=['active', 'overdue']
    ).first()
    
    if existing_borrow:
        messages.error(request, 'You already have this book borrowed.')
        return redirect('book_detail', pk=pk)
    
    # Check borrow limit (max 5 books)
    active_borrows = BookBorrow.objects.filter(
        student=student,
        status__in=['active', 'overdue']
    ).count()
    
    if active_borrows >= 5:
        messages.error(request, 'You have reached the maximum borrow limit (5 books). Please return some books first.')
        return redirect('student_library_dashboard')
    
    # Check for unpaid fines
    unpaid_fines = BookBorrow.objects.filter(
        student=student,
        fine_amount__gt=0,
        fine_paid=False
    ).exists()
    
    if unpaid_fines:
        messages.error(request, 'You have unpaid fines. Please clear them before borrowing more books.')
        return redirect('student_library_dashboard')
    
    # Create borrow record
    due_date = timezone.now().date() + timedelta(days=14)  # 2 weeks
    borrow = BookBorrow.objects.create(
        book=book,
        student=student,
        due_date=due_date
    )
    
    messages.success(request, f'You have successfully borrowed "{book.title}". Please return it by {due_date.strftime("%B %d, %Y")}.')
    return redirect('student_library_dashboard')


@login_required
@student_required
def return_book(request, borrow_id):
    """Student initiates book return (must be processed by teacher)"""
    borrow = get_object_or_404(BookBorrow, id=borrow_id)
    student = request.user.student_profile
    
    if borrow.student != student:
        messages.error(request, "You don't have permission to return this book.")
        return redirect('student_library_dashboard')
    
    if borrow.status not in ['active', 'overdue']:
        messages.error(request, 'This book has already been returned.')
        return redirect('student_library_dashboard')
    
    messages.info(request, f'Please bring "{borrow.book.title}" to the library desk. The teacher will process your return.')
    return redirect('student_library_dashboard')


# ============ BOOK RESERVATIONS ============

@login_required
@student_required
def reserve_book(request, pk):
    """Student reserve book"""
    book = get_object_or_404(Book, pk=pk)
    student = request.user.student_profile
    
    # Check if book is available
    if book.is_available:
        messages.info(request, 'This book is available for borrowing. No need to reserve.')
        return redirect('book_detail', pk=pk)
    
    # Check if already has active reservation
    existing_reservation = BookReservation.objects.filter(
        book=book,
        student=student,
        status='pending'
    ).first()
    
    if existing_reservation:
        messages.error(request, 'You already have a reservation for this book.')
        return redirect('book_detail', pk=pk)
    
    # Create reservation
    expiry_date = timezone.now() + timedelta(days=7)
    reservation = BookReservation.objects.create(
        book=book,
        student=student,
        expiry_date=expiry_date
    )
    
    messages.success(request, f'Book "{book.title}" reserved successfully. You will be notified when it becomes available.')
    return redirect('student_library_dashboard')


@login_required
def cancel_reservation(request, reservation_id):
    """Cancel book reservation"""
    reservation = get_object_or_404(BookReservation, id=reservation_id)
    
    # Check permissions
    if hasattr(request.user, 'student_profile'):
        if reservation.student != request.user.student_profile:
            messages.error(request, "You don't have permission to cancel this reservation.")
            return redirect('book_detail', pk=reservation.book.id)
    
    if reservation.status != 'pending':
        messages.error(request, 'This reservation cannot be cancelled.')
        return redirect('book_detail', pk=reservation.book.id)
    
    book_title = reservation.book.title
    reservation.status = 'cancelled'
    reservation.save()
    
    messages.success(request, f'Reservation for "{book_title}" cancelled successfully.')
    return redirect('student_library_dashboard')


# ============ STUDENT DASHBOARD ============

@login_required
@student_required
def student_library_dashboard(request):
    """Student library dashboard"""
    student = request.user.student_profile
    
    # Active borrows
    active_borrows = BookBorrow.objects.filter(
        student=student,
        status__in=['active', 'overdue']
    ).select_related('book', 'book__category').order_by('due_date')
    
    # Count overdue books
    overdue_count = BookBorrow.objects.filter(
        student=student,
        status='overdue'
    ).count()
    
    # Borrow history
    borrow_history = BookBorrow.objects.filter(
        student=student,
        status='returned'
    ).select_related('book').order_by('-return_date')[:5]
    
    # Active reservations
    active_reservations = BookReservation.objects.filter(
        student=student,
        status='pending'
    ).select_related('book').order_by('reservation_date')
    
    # Statistics
    total_borrowed = BookBorrow.objects.filter(student=student).count()
    total_fines_result = BookBorrow.objects.filter(
        student=student,
        fine_amount__gt=0,
        fine_paid=False
    ).aggregate(total=Sum('fine_amount'))
    total_fines = total_fines_result['total'] or 0
    
    context = {
        'current_borrowings': active_borrows,  # Changed from active_borrows
        'active_borrows': active_borrows,
        'borrowed_count': active_borrows.count(),  # Added
        'overdue_count': overdue_count,  # Added
        'borrow_history': borrow_history,
        'active_reservations': active_reservations,
        'total_borrowed': total_borrowed,
        'total_fines': total_fines,
        'borrow_limit': 5,
        'borrows_left': max(0, 5 - active_borrows.count()),
    }
    return render(request, 'library/student_dashboard.html', context)


# ============ CATEGORY MANAGEMENT ============

@login_required
@teacher_required
def category_list(request):
    """List all book categories"""
    categories = BookCategory.objects.annotate(
        book_count=Count('books')
    ).order_by('name')
    
    context = {
        'categories': categories,
        'total_categories': categories.count(),
    }
    return render(request, 'library/category_list.html', context)


@login_required
@teacher_required
def category_create(request):
    """Create new book category"""
    if request.method == 'POST':
        form = BookCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" created successfully!')
            return redirect('library_category_list')
    else:
        form = BookCategoryForm()
    
    context = {
        'form': form,
        'action': 'Create',
    }
    return render(request, 'library/category_form.html', context)


@login_required
@teacher_required
def category_edit(request, pk):
    """Edit book category"""
    category = get_object_or_404(BookCategory, pk=pk)
    
    if request.method == 'POST':
        form = BookCategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" updated successfully!')
            return redirect('library_category_list')
    else:
        form = BookCategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'action': 'Edit',
    }
    return render(request, 'library/category_form.html', context)


@login_required
@teacher_required
def category_delete(request, pk):
    """Delete book category"""
    category = get_object_or_404(BookCategory, pk=pk)
    books_count = category.books.count()
    
    if books_count > 0:
        messages.error(request, f'Cannot delete category "{category.name}". It has {books_count} book(s).')
        return redirect('library_category_list')
    
    category_name = category.name
    category.delete()
    messages.success(request, f'Category "{category_name}" deleted successfully!')
    return redirect('library_category_list')


# ============ REPORTS ============

@login_required
@teacher_required
def overdue_books_report(request):
    """Generate report of overdue books"""
    overdue_borrows = BookBorrow.objects.filter(
        status='overdue'
    ).select_related('book', 'student', 'student__user').order_by('due_date')
    
    # Pagination
    paginator = Paginator(overdue_borrows, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    total_fines_result = overdue_borrows.aggregate(
        total=Sum('fine_amount')
    )
    total_fines = total_fines_result['total'] or 0
    
    context = {
        'page_obj': page_obj,
        'total_overdue': overdue_borrows.count(),
        'total_fines': total_fines,
    }
    return render(request, 'library/overdue_report.html', context)


# ============ NFC API ============

@csrf_exempt
def book_nfc_checkout_api(request):
    """Book NFC checkout/checkin API"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nfc_uid = data.get('nfc_uid')
            book_nfc_uid = data.get('book_nfc_uid')
            action = data.get('action', 'checkout')  # checkout or checkin
            
            # Find student
            try:
                student = Student.objects.get(nfc_uid=nfc_uid)
            except Student.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Student NFC card not found'
                }, status=404)
            
            # Find book
            try:
                book = Book.objects.get(nfc_tag_uid=book_nfc_uid)
            except Book.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Book NFC tag not found'
                }, status=404)
            
            if action == 'checkout':
                # Check if book is available
                if not book.is_available:
                    return JsonResponse({
                        'success': False,
                        'message': f'Book "{book.title}" is not available'
                    }, status=400)
                
                # Check borrow limit
                active_borrows = BookBorrow.objects.filter(
                    student=student,
                    status__in=['active', 'overdue']
                ).count()
                
                if active_borrows >= 5:
                    return JsonResponse({
                        'success': False,
                        'message': 'Borrow limit reached (5 books)'
                    }, status=400)
                
                # Create borrow
                due_date = timezone.now().date() + timedelta(days=14)
                borrow = BookBorrow.objects.create(
                    book=book,
                    student=student,
                    due_date=due_date,
                    nfc_checkout=True
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f'Book "{book.title}" checked out to {student.user.get_full_name()}',
                    'due_date': due_date.isoformat()
                })
            
            elif action == 'checkin':
                # Find active borrow
                borrow = BookBorrow.objects.filter(
                    book=book,
                    student=student,
                    status__in=['active', 'overdue']
                ).first()
                
                if not borrow:
                    return JsonResponse({
                        'success': False,
                        'message': 'No active borrow found for this book and student'
                    }, status=404)
                
                # Process return
                borrow.return_date = timezone.now()
                borrow.status = 'returned'
                borrow.nfc_checkin = True
                borrow.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Book "{book.title}" returned',
                    'fine_amount': float(borrow.fine_amount)
                })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Only POST method allowed'
    }, status=405)
