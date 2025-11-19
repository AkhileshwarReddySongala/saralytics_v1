
from django.contrib import admin
from django.urls import path, include  # Make sure 'include' is imported

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # This is the most important line.
    # It tells Django that for the root URL (''), it should look for
    # instructions in the 'dashboard/urls.py' file.
    path('', include('dashboard.urls')),
]