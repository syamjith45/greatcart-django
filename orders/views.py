from django.shortcuts import render,redirect
from django.http import HttpResponse
from cart.models import CartItem
from .forms import OrderForm
import datetime
# from .models import Order,Payment
import razorpay
from greenkart.settings import RAZORPAY_KEY_ID,RAZORPAY_KEY_SECRET
client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# views.py
import json
from .utils import generate_order_number
from django.http import JsonResponse, HttpResponse
from .models import Order, Payment





from django.http import HttpResponse
from django.shortcuts import render
from django.http import Http404
from .models import Order, Payment

def payments(request):
    # Check if the request is AJAX and if it's a POST request
    if request.method == 'POST':
        # Extract data from the POST request
        order_number = request.POST.get('order_number')
        transaction_id = request.POST.get('transaction_id')
        payment_method = request.POST.get('payment_method')
        status = request.POST.get('status')

        # Retrieve the order or raise a 404 exception if not found
        order = Order.objects.get(user=request.user, is_ordered=False, order_number=order_number)
        payment = Payment(
            user=request.user,
            payment_id=transaction_id,
            payment_method=payment_method,
            amount_paid=order.order_total,
            status=status
        )
        payment.save()

        # Update the order model
        order.payment = payment
        order.is_ordered = True
        order.save()

        # Render an HTML page after a successful payment
        return render(request, 'orders/payments.html')


def place_order(request, total=0, quantity=0):
    current_user = request.user

    #if the cart count is lessthan or equal to 0, then redirect back to shop

    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <=0:
        return redirect('store')



    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2 * total)/100
    grand_total = total + tax

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Store all the billing information inside Order table
            order = Order()
            order.user = current_user
            order.first_name = form.cleaned_data['first_name']
            order.last_name = form.cleaned_data['last_name']
            order.phone = form.cleaned_data['phone']
            order.email = form.cleaned_data['email']
            order.address_line_1 = form.cleaned_data['address_line_1']
            order.address_line_2 = form.cleaned_data['address_line_2']
            order.country = form.cleaned_data['country']
            order.state = form.cleaned_data['state']
            order.city = form.cleaned_data['city']
            order.order_note = form.cleaned_data['order_note']
            order.order_total = grand_total
            order.tax = tax
            order.ip = request.META.get('REMOTE_ADDR')
            order.save()
            # Generate order number
            order.order_number = generate_order_number(order.id)
            order.save()
            DATA = {
                "amount": float(order.order_total)*100,
                "currency": "INR",
                "receipt": "receipt#1"+ order.order_number,
                "notes": {
                    "key1": "value3",
                    "key2": "value2"
                }
            }
            rzp_order=client.order.create(data=DATA)
            rzp_order_id=rzp_order['id']
            print(rzp_order)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
                'rzp_order_id':rzp_order_id,
                'RAZORPAY_KEY_ID':RAZORPAY_KEY_ID,
                'rzp_amount': float(order.order_total)*100,
            }
            return render(request, 'orders/payments.html', context)

    else:
        return redirect('checkout')
