"""
Example views showing how to use the Twilio service
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .twilio_service import twilio_service

def home(request):
    """
    Home page view
    """
    return render(request, 'base.html')

def feedback_form(request):
    """
    Feedback form view
    """
    return render(request, 'feedback_form.html')

def submit_feedback(request):
    """
    Submit feedback view
    """
    return JsonResponse({'success': True})

@login_required
def twilio_demo(request):
    """
    Twilio demo page view
    """
    return render(request, 'dashboard/twilio_demo.html')

@login_required
@require_http_methods(["POST"])
def send_whatsapp_notification(request):
    """
    Example view to send a WhatsApp notification using Twilio
    """
    try:
        # Get data from request
        recipient_number = request.POST.get('recipient_number')
        message_body = request.POST.get('message_body')
        
        # Validate inputs
        if not recipient_number or not message_body:
            return JsonResponse({
                'success': False,
                'error': 'Recipient number and message body are required'
            }, status=400)
        
        # Send WhatsApp message
        result = twilio_service.send_text_message(recipient_number, message_body)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': 'WhatsApp message sent successfully',
                'message_id': result['message_id']
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result['error']
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to send WhatsApp message: {str(e)}'
        }, status=500)

# Example of sending a templated message
@login_required
@require_http_methods(["POST"])
def send_templated_whatsapp(request):
    """
    Example view to send a templated WhatsApp message using Twilio
    """
    try:
        # Get data from request
        recipient_number = request.POST.get('recipient_number')
        content_sid = request.POST.get('content_sid')
        content_variables = request.POST.get('content_variables')
        
        # Validate inputs
        if not recipient_number or not content_sid:
            return JsonResponse({
                'success': False,
                'error': 'Recipient number and content SID are required'
            }, status=400)
        
        # Send templated WhatsApp message
        result = twilio_service.send_template_message(
            to_number=recipient_number,
            content_sid=content_sid,
            content_variables=content_variables
        )
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': 'Templated WhatsApp message sent successfully',
                'message_id': result['message_id']
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result['error']
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to send templated WhatsApp message: {str(e)}'
        }, status=500)