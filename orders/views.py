from django.shortcuts import render,redirect
from django.http import HttpResponse
from cart.models import CartItem
from store.models import Product
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
from .models import Order, Payment,OrderProduct
from django.http import Http404
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

def payments(request):
    if request.method == 'POST':
        # Extract data from the POST request
        order_number = request.POST.get('order_number')
        transaction_id = request.POST.get('transaction_id')
        payment_method = request.POST.get('payment_method')
        status = request.POST.get('status')

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
        cart_items = CartItem.objects.filter(user=request.user)

        for item in cart_items:
            orderproduct = OrderProduct()
            orderproduct.order_id = order.id
            orderproduct.payment = payment
            orderproduct.user_id = request.user.id
            orderproduct.product_id = item.product_id
            orderproduct.quantity = item.quantity
            orderproduct.product_price = item.product.price
            orderproduct.ordered = True
            orderproduct.save()

            cart_item = CartItem.objects.get(id=item.id)
            product_variation = cart_item.variations.all()
            orderproduct = OrderProduct.objects.get(id=orderproduct.id)
            orderproduct.variations.set(product_variation)
            orderproduct.save()
            # Reduce the quantity of the sold products
            product = Product.objects.get(id=item.product_id)
            product.stock -= item.quantity
            product.save()

            #clear cart_item

            CartItem.objects.filter(user=request.user).delete()


    # Send order recieved email to customer
            mail_subject = 'Thank you for your order!'
            message = render_to_string('orders/order_recieved_email.html', {
                'user': request.user,
                'order': order,
            })
            to_email = request.user.email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()


        # RETURN BACK TO AJAX WITH THE STATUS SUCCESS OR FAILURE
            response = {
                'order_number': order_number,
                'transaction_id': transaction_id,
            }
            return JsonResponse(response)
        return HttpResponse('Payments view')



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

def order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = 0
        for i in ordered_products:
            subtotal += i.product_price * i.quantity

        payment = Payment.objects.get(payment_id=transID)

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
        }
        return render(request, 'orders/order_complete.html', context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')
