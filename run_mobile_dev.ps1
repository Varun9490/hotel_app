# Mobile Development Server Script
Write-Host "Starting Django development server for mobile access..."
Write-Host "Make sure your mobile device is on the same network as your computer."
Write-Host "Access the server from your mobile device using: http://192.168.1.4:8000"
Write-Host ""

Set-Location "c:\Users\varun\Desktop\Victoireus internship\hotel_project"
.venv\Scripts\Activate.ps1
python manage.py runserver 0.0.0.0:8000