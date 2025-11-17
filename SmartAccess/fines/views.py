from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

# Import from the modular models
from .models import Fine
from .forms import FineForm
from students.models import Student

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


@csrf_exempt
def scan_card_for_fine(request):
    """API endpoint to get student details by scanning NFC card"""
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
                return JsonResponse({
                    'success': True,
                    'student_id': student.id,
                    'student_name': student.name,
                    'roll_number': student.roll_number,
                    'course': student.course,
                    'department': student.department
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
