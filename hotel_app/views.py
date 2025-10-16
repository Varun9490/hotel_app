from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from .models import Guest, Review
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
import json

def home(request):
    """Home page view"""
    return render(request, 'home.html')

def feedback_form(request):
    """Display the feedback form"""
    return render(request, 'feedback_form.html')

@csrf_exempt
def submit_feedback(request):
    """Handle feedback submission"""
    if request.method == 'POST':
        try:
            # Parse JSON data from request body
            data = json.loads(request.body)
            
            # Extract guest information
            guest_name = data.get('guest_name', '')
            room_number = data.get('room_number', '')
            email = data.get('email', '')
            phone = data.get('phone', '')
            
            # Extract feedback data
            overall_rating = data.get('overall_rating', 0)
            cleanliness_rating = data.get('cleanliness_rating', 0)
            staff_rating = data.get('staff_rating', 0)
            recommend = data.get('recommend', '')
            comments = data.get('comments', '')
            
            # Create or get guest
            guest = None
            if guest_name or room_number:
                # Try to find existing guest
                try:
                    if room_number:
                        guest = Guest.objects.get(room_number=room_number)
                    else:
                        guest = Guest.objects.get(full_name=guest_name)
                except Guest.DoesNotExist:
                    # Create new guest
                    guest = Guest.objects.create(
                        full_name=guest_name,
                        room_number=room_number,
                        email=email,
                        phone=phone
                    )
            
            # Create review
            # Format all ratings into the comment field
            full_comment = comments
            if full_comment:
                full_comment += "\n\n"
            else:
                full_comment = ""
            
            full_comment += f"Overall Rating: {overall_rating}/5\n"
            full_comment += f"Cleanliness Rating: {cleanliness_rating}/5\n"
            full_comment += f"Staff Service Rating: {staff_rating}/5\n"
            full_comment += f"Recommendation: {recommend}"
            
            review = Review.objects.create(
                guest=guest,
                rating=overall_rating,
                comment=full_comment
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Thank you for your feedback!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'There was an error submitting your feedback. Please try again.'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)

def signup_view(request):
    """Handle user signup"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard:main')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})