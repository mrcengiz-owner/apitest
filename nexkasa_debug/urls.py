from django.contrib import admin
from django.urls import path
from core.views import (
    debug_connection, diagnostic_dashboard, run_diagnostic_test, 
    mock_get_account, mock_create_transaction, mock_withdraw_request,
    CustomLoginView
)
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Auth
    path('', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    
    # Dashboard & Runner
    path('diagnostics/', diagnostic_dashboard, name='dashboard'),
    path('api/run-diagnostic/', run_diagnostic_test, name='run_diagnostic'),

    # Target Endpoints (Mock & Debug)
    path('api/test-connection/', debug_connection, name='debug_connection'),
    
    # Support both slash and no-slash for robustness
    path('api/get-eligible-account', mock_get_account, name='mock_get_account'),
    path('api/get-eligible-account/', mock_get_account, name='mock_get_account_slash'),
    
    path('api/create-transaction', mock_create_transaction, name='mock_create_transaction'),
    path('api/create-transaction/', mock_create_transaction, name='mock_create_transaction_slash'),
    
    path('api/public/withdraw-request', mock_withdraw_request, name='mock_withdraw_request'),
    path('api/public/withdraw-request/', mock_withdraw_request, name='mock_withdraw_request_slash'),
]
