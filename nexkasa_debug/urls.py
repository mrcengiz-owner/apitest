from django.contrib import admin
from django.urls import path
from core.views import debug_connection, diagnostic_dashboard, run_diagnostic_test

urlpatterns = [
    path('admin/', admin.site.urls),
    # The Debug Endpoint (Target)
    path('api/test-connection/', debug_connection, name='debug_connection'),
    
    # The Dashboard UI
    path('diagnostics/', diagnostic_dashboard, name='dashboard'),
    
    # The Backend Runner API (used by Dashboard UI)
    path('api/run-diagnostic/', run_diagnostic_test, name='run_diagnostic'),
]
