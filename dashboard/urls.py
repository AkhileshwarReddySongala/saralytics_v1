# dashboard/urls.py

from django.urls import path
from . import views  # Import the views from the current directory

urlpatterns = [
    # This maps the main URL (the "root") to the 'home' function in views.py
    path('', views.home, name='home'),
    
    # These are your API endpoints for the charts
    path('api/sales_over_time/', views.sales_over_time_api, name='api-sales-over-time'),
    path('api/sales_by_item/', views.sales_by_item_api, name='api-sales-by-item'),
    path('api/quantity_by_size/', views.quantity_by_size_api, name='api-quantity-by-size'),
    path('api/agent_chat/', views.manager_agent_api, name='api-agent-chat'), 
]