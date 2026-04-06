from django.urls import path
from . import views

urlpatterns = [
    path('pay/<int:billing_id>/', views.create_payment, name='create_payment'),
    path('vnpay-return/', views.vnpay_return, name='vnpay_return'),
    path('sepay/webhook/', views.sepay_webhook, name='sepay_webhook'),
    path('status/<int:billing_id>/', views.payment_status, name='payment_status'),
    path('history/', views.payment_history, name='payment_history'),
]
