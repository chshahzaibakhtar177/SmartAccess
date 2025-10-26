from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

# Import from the modular models
from .models import Fine
from .forms import FineForm

# Fines management views - migrated from legacy student app

def add_fine(request):
    """Add fine view - migrated from legacy student app"""
    search_query = request.GET.get('search', '')  # Get search term from URL param

    if request.method == 'POST':
        form = FineForm(request.POST)
        if form.is_valid():
            form.save()
            form = FineForm()
    else:
        form = FineForm()

    # Filter fines based on search query if provided
    if search_query:
        fines = Fine.objects.filter(
            student__name__icontains=search_query
        ) | Fine.objects.filter(
            student__roll_number__icontains=search_query
        )
    else:
        fines = Fine.objects.all()

    return render(request, 'fines/add_fine.html', {'form': form, 'fines': fines, 'search_query': search_query})


def edit_fine(request, fine_id):
    """Edit fine view - migrated from legacy student app"""
    fine = get_object_or_404(Fine, id=fine_id)

    if request.method == 'POST':
        form = FineForm(request.POST, instance=fine)
        if form.is_valid():
            form.save()
            return redirect('add_fine')
    else:
        form = FineForm(instance=fine)

    fines = Fine.objects.select_related('student').all()
    return render(request, 'fines/add_fine.html', {
        'form': form,
        'fines': fines,
        'edit_mode': True,
        'editing_fine': fine,
    })


def delete_fine(request, fine_id):
    """Delete fine view - migrated from legacy student app"""
    fine = get_object_or_404(Fine, id=fine_id)
    fine.delete()
    return redirect('add_fine')


def toggle_fine_payment(request, fine_id):
    """Toggle fine payment view - migrated from legacy student app"""
    fine = get_object_or_404(Fine, id=fine_id)
    fine.is_paid = not fine.is_paid
    fine.save()
    return redirect('add_fine')
