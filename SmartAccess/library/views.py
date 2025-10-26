from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count
from django.core.paginator import Paginator
from datetime import timedelta
import json

# Import from the modular models
from .models import Book, BookCategory, BookBorrow, BookReservation
from students.models import Student
from .forms import BookForm, BookSearchForm, BookBorrowForm, BookReturnForm, BookReservationForm, BookCategoryForm
from authentication.decorators import teacher_required, student_required

# Library management views - migrated from legacy student app
# Note: Due to time constraints, providing basic structure

@login_required
def library_dashboard(request):
    """Library dashboard - migrated from legacy student app"""
    total_books = Book.objects.count()
    available_books = Book.objects.filter(status='available').count()
    borrowed_books = BookBorrow.objects.filter(return_date__isnull=True).count()
    
    context = {
        'total_books': total_books,
        'available_books': available_books,
        'borrowed_books': borrowed_books,
    }
    return render(request, 'library/dashboard.html', context)


def book_list(request):
    """Book list view - migrated from legacy student app"""
    form = BookSearchForm(request.GET)
    books = Book.objects.all()
    
    # Apply search filters
    if form.is_valid():
        search_query = form.cleaned_data.get('search_query')
        category = form.cleaned_data.get('category')
        
        if search_query:
            books = books.filter(
                Q(title__icontains=search_query) |
                Q(author__icontains=search_query) |
                Q(isbn__icontains=search_query)
            )
        
        if category:
            books = books.filter(category=category)
    
    # Pagination
    paginator = Paginator(books, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'total_books': books.count()
    }
    return render(request, 'library/book_list.html', context)


def book_detail(request, pk):
    """Book detail view - migrated from legacy student app"""
    book = get_object_or_404(Book, pk=pk)
    return render(request, 'library/book_detail.html', {'book': book})


@login_required
@teacher_required
def add_book(request):
    """Add book view - migrated from legacy student app"""
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Book added successfully!')
            return redirect('book_list')
    else:
        form = BookForm()
    return render(request, 'library/book_form.html', {'form': form})


@login_required
@teacher_required
def edit_book(request, pk):
    """Edit book view - migrated from legacy student app"""
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, 'Book updated successfully!')
            return redirect('book_detail', pk=book.pk)
    else:
        form = BookForm(instance=book)
    return render(request, 'library/book_form.html', {'form': form, 'book': book})


@login_required
@teacher_required
def delete_book(request, pk):
    """Delete book view - migrated from legacy student app"""
    book = get_object_or_404(Book, pk=pk)
    book.delete()
    messages.success(request, 'Book deleted successfully!')
    return redirect('book_list')


@login_required
@student_required
def borrow_book(request, pk):
    """Borrow book view - migrated from legacy student app"""
    book = get_object_or_404(Book, pk=pk)
    # Implementation would be migrated here
    return redirect('book_detail', pk=book.pk)


@login_required
@student_required
def return_book(request, borrow_id):
    """Return book view - migrated from legacy student app"""
    borrow = get_object_or_404(BookBorrow, id=borrow_id)
    # Implementation would be migrated here
    return redirect('student_library_dashboard')


@login_required
@student_required
def reserve_book(request, pk):
    """Reserve book view - migrated from legacy student app"""
    book = get_object_or_404(Book, pk=pk)
    # Implementation would be migrated here
    return redirect('book_detail', pk=book.pk)


@login_required
@student_required
def student_library_dashboard(request):
    """Student library dashboard - migrated from legacy student app"""
    # Implementation would be migrated here
    return render(request, 'library/student_dashboard.html')


@csrf_exempt
def book_nfc_checkout_api(request):
    """Book NFC checkout API - migrated from legacy student app"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Implementation would be migrated here
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Only POST method allowed'})


@login_required
def overdue_books_report(request):
    """Generate report of overdue books"""
    thirty_days_ago = timezone.now() - timedelta(days=30)
    overdue_borrows = BookBorrow.objects.filter(
        is_returned=False, 
        borrow_date__lt=thirty_days_ago
    ).select_related('book', 'student')
    
    context = {
        'overdue_borrows': overdue_borrows,
        'total_overdue': overdue_borrows.count()
    }
    return render(request, 'library/overdue_report.html', context)

@login_required
def cancel_reservation(request, reservation_id):
    """Cancel a book reservation"""
    reservation = get_object_or_404(BookReservation, id=reservation_id)
    
    # Check permissions
    try:
        user_student = request.user.student_profile
        if reservation.student != user_student:
            messages.error(request, "You don't have permission to cancel this reservation.")
            return redirect('book_detail', pk=reservation.book.id)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found. Please contact administrator.")
        return redirect('login')
    
    if reservation.student != user_student:
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


# Book Category Management Views
@login_required
@teacher_required
def category_list(request):
    """List all book categories"""
    categories = BookCategory.objects.all().order_by('name')
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
            messages.success(request, f'Book category "{category.name}" created successfully!')
            return redirect('library_category_list')
    else:
        form = BookCategoryForm()
    
    return render(request, 'library/category_form.html', {
        'form': form,
        'title': 'Create Book Category',
        'submit_text': 'Create Category'
    })


@login_required
@teacher_required
def category_edit(request, pk):
    """Edit existing book category"""
    category = get_object_or_404(BookCategory, pk=pk)
    
    if request.method == 'POST':
        form = BookCategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Book category "{category.name}" updated successfully!')
            return redirect('library_category_list')
    else:
        form = BookCategoryForm(instance=category)
    
    return render(request, 'library/category_form.html', {
        'form': form,
        'category': category,
        'title': 'Edit Book Category',
        'submit_text': 'Update Category'
    })


@login_required
@teacher_required
def category_delete(request, pk):
    """Delete book category"""
    category = get_object_or_404(BookCategory, pk=pk)
    
    # Check if category has books
    books_count = category.books.count()
    
    if request.method == 'POST':
        if books_count > 0:
            messages.error(request, f'Cannot delete category "{category.name}" because it has {books_count} book(s) assigned to it.')
        else:
            category_name = category.name
            category.delete()
            messages.success(request, f'Book category "{category_name}" deleted successfully!')
        return redirect('library_category_list')
    
    return render(request, 'library/category_confirm_delete.html', {
        'category': category,
        'books_count': books_count
    })
