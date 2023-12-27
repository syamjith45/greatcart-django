from django.shortcuts import render,redirect
from django.http import HttpResponse
from cart.models import CartItem
from .forms import OrderForm
import datetime
from .models import Order
import razorpay
from greenkart.settings import RAZORPAY_KEY_ID,RAZORPAY_KEY_SECRET
client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

def payments(request):
    return render(request,'orders/payments.html')

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
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()
            # Generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr,mt,dt)
            current_date = d.strftime("%Y%m%d") #20210305
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)

            DATA = {
                "amount": float(data.order_total)*100,
                "currency": "INR",
                "receipt": "receipt#1"+ data.order_number,
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
                'rzp_amount': float(data.order_total)*100,
            }
            return render(request, 'orders/payments.html', context)

    else:
        return redirect('checkout')
