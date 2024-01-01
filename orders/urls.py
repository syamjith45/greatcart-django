from django.urls import path

from .import views

urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
     path('payments/', views.payments, name='payments'),
     path('order_complete/',views.order_complete,name='order_complete')
     # path('store-payment/', views.store_payment, name='store_payment'),
     # path('your-payment-endpoint/', views.handle_payment, name='your_payment_endpoint'),
    # path('handle_payment_success/', views.handle_payment_success, name='handle_payment_success'),
]
