import os, time
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect
from farmshop.forms import RegistrationForm
from django.contrib.auth import authenticate, login
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.timezone import datetime
from datetime import date
from django.urls import reverse_lazy
from farmshop.models import FarmShop, ProductGroup, Product, Warehouse, FarmShopInfo, FarmShopNews
from farmshop.models import Package, Inventory, Order, Customer, PostalAddress
from farmshop.models import OrderForm, CustomerOrderConfirmForm, PreOrder, PreOrderForm#, PreOrderPackages
#from leaflet.admin import LeafletGeoAdminMixin
from leaflet.forms.widgets import LeafletWidget
from bootstrap_datepicker_plus.widgets import DatePickerInput
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.db.models import Count, Sum, IntegerField, Value
from django.db.models.functions import Cast, Coalesce
from django.db.models import Subquery, OuterRef, F, Q
#from .forms import OrderLineFormSet
from django.forms import modelform_factory, Textarea
from .forms import *
from captcha.fields import CaptchaField
import json
from django.core.serializers import serialize
from django.contrib.gis.db.models import PointField
from django.core.mail import send_mail

from django_tables2 import SingleTableView
from .tables import OrderTable

#from queryset_sequence import QuerySetSequence
"""
First view function for singlepage app
"""
def dashboard(request, pk):
    time.sleep(0.5)
    if request.htmx:
        template_name = "singlepage/components/dashboard.html"
    else:
        template_name = "singlepage/components/dashboard_full.html"
    return render(request, template_name, {'pk': pk})

def dashboard2(request, pk):
    time.sleep(0.5)
    if request.htmx:
        template_name = "singlepage/components/dashboard2.html"
    else:
        template_name = "singlepage/components/dashboard_full2.html"
    return render(request, template_name, {'pk': pk})

""" 
Function based view for creating order based on two models (customer and order)
The order form includes a captcha field and is defined in models.py whereas customer form is created by a factory
"""
def hofladen_order_create(request, shopid):
    farmshop = FarmShop.objects.get(pk=shopid)
    CustomerForm = modelform_factory(Customer, fields=["name", "first_name", "email"])
    if request.method == 'POST':
        customer_form = CustomerForm(request.POST, prefix='customer')
        order_form = OrderForm(request.POST, prefix='order')
        if customer_form.is_valid() and order_form.is_valid():
            # pre save customer model
            customer = customer_form.save(commit=False)
            # add metadata 
            customer.created = datetime.now()
            # set farmshop
            farmshop = FarmShop.objects.get(pk=shopid)
            customer.farmshop = farmshop
            customer.save()
            # pre save order model
            order = order_form.save(commit=False)
            order.customer = customer
            order.farmshop = farmshop
            # add metadata 
            order.created = datetime.now()
            order.changed = datetime.now()
            order.save()
            # save id of created order to session 
            request.session["order_id"] = str(order.generic_id)
            return redirect("hofladen-orderform-configure", shopid=shopid, generic_id=order.generic_id)
        else:
            print("form invalid")
    else:
        customer_form = CustomerForm(prefix='customer')
        order_form = OrderForm(prefix='order')
    return render(request, "farmshop/guest/guest_order_create.html", {'form1': customer_form, 'form2': order_form, 'farmshop': farmshop})

def hofladen_order_update(request, shopid, generic_id):
    farmshop = FarmShop.objects.get(pk=shopid)
    CustomerForm = modelform_factory(Customer, fields=["name", "first_name", "email"])
    OrderForm = modelform_factory(Order, fields=["notice", "target_date"], widgets={"target_date": DatePickerInput()})
    order = Order.objects.get(generic_id=generic_id)

    if request.method == 'POST':
        customer_form = CustomerForm(request.POST, prefix='customer', instance=order.customer)
        order_form = OrderForm(request.POST, prefix='order', instance=order)
        if customer_form.is_valid() and order_form.is_valid():
            # pre save customer model
            customer = customer_form.save(commit=False)
            # add metadata 
            customer.changed = datetime.now()
            # set farmshop
            farmshop = FarmShop.objects.get(pk=shopid)
            customer.farmshop = farmshop
            customer.save()
            # pre save order model
            order = order_form.save(commit=False)
            order.customer = customer
            order.farmshop = farmshop
            # add metadata 
            order.changed = datetime.now()
            order.save()
            return redirect("hofladen-orderform-configure", shopid=shopid, generic_id=order.generic_id)
        else:
            print("form invalid")
    else:
        # instantiate from existing order
        #order = Order.objects.get(generic_id=generic_id)
        # orderlines get lost?
        order_form = OrderForm(instance=order, prefix='order')
        customer_form = CustomerForm(instance=order.customer, prefix='customer')
    return render(request, "farmshop/guest/guest_order_update.html", {'form1': customer_form, 'form2': order_form, "farmshop": farmshop})

def hofladen_order_delete(request, shopid, generic_id):
    farmshop = FarmShop.objects.get(pk=shopid)
    context = {
        "farmshop": farmshop,
        "order": generic_id,
    }
    order = Order.objects.get(generic_id=generic_id)
    if request.method =="POST":
        order.delete()
        # delete order_id from session
        del request.session["order_id"]
        return redirect("hofladen-detail", pk=shopid)
    return render(request, "farmshop/guest/guest_order_confirm_delete.html", context)

# after confirmation, the order cannot be edited any longer
def hofladen_order_confirm(request, shopid, generic_id):
    farmshop = FarmShop.objects.get(pk=shopid)
    context = {
        "farmshop": farmshop,
        "order": generic_id,
    }
    order = Order.objects.get(generic_id=generic_id)
    #print(order.orderline_set.count)
    if request.method =="POST":
        order.confirmed = True
        order.changed = datetime.now()
        order.save()
        return redirect("hofladen-orderform-configure", shopid=shopid, generic_id=order.generic_id)
    return render(request, "farmshop/guest/guest_order_confirm_confirm.html", context)

# after confirmation, the order cannot be edited any longer
def hofladen_order_authenticate(request, shopid, generic_id):
    order = Order.objects.get(generic_id=generic_id)
    farmshop = FarmShop.objects.get(pk=shopid)
    customer_order_confirm_form = CustomerOrderConfirmForm(request.POST)
    context = {
        "farmshop": farmshop,
        "order": generic_id,
        "form": customer_order_confirm_form
    }
    if request.method =="POST":
        if customer_order_confirm_form.is_valid():
            if order.customer.email == customer_order_confirm_form.cleaned_data['email']:
                #print("email matches!")
                #create new sessionid cookie and store uuid to order_id 
                request.session['order_id'] = str(order.generic_id)
                return redirect("hofladen-orderform-configure", shopid=shopid, generic_id=order.generic_id)
            else:
                messages.error(request, 'Die angegebene E-Mail wurde nicht für die Bestellung verwendet!')
                # new form
                #customer_order_confirm_form = CustomerOrderConfirmForm(request.POST)
                #context["form"] = customer_order_confirm_form
                #raise customer_order_confirm_form.ValidationError('Die angegebene E-Mail wurde nicht für die Bestellung verwendet!')
                render(request, "farmshop/guest/guest_order_detail_control.html", context)
                #return render(request, "farmshop/guest/guest_order_detail_control_false.html", context)
    return render(request, "farmshop/guest/guest_order_detail_control.html", context)

def hofladen_order_cancel(request, shopid, generic_id):
    farmshop = FarmShop.objects.get(pk=shopid)
    context = {
        "farmshop": farmshop,
        "order": generic_id,
    }
    order = Order.objects.get(generic_id=generic_id)
    if request.method =="POST":
        order.cancelled = True
        order.created = datetime.now()
        order.save()
        # delete order_id from session
        print("order_id aus session löschen")
        messages.error(request, 'Ihre Bestellung mit der Nummer ' + str(order.id) + ' wurde endgültig storniert! Sie können eine neue Bestellung anlegen.')
        #sessionid löschen
        del request.session["order_id"]
        return redirect("hofladen-detail", pk=shopid)
    
    return render(request, "farmshop/guest/guest_order_cancel_confirm.html", context)

"""
Function based view that allows the configuration of the previausly created order.
Products may be added and deleted. Also the order can manipulated till the order will be
confirmed. After that, it only can be cancelled fully. The view is generated by a given generic_id.
This id should only be known by the  customer who crested the order.  
"""
def hofladen_order_configure(request, shopid, generic_id):
    order = Order.objects.get(generic_id=generic_id)
    farmshop = order.farmshop
    context = {
        'order': order,
        'farmshop': farmshop,
    }
    # check if generic_id is in session - else return form with email and captcha
    if 'order_id' not in request.session:
        print("requested order not in session")
        return redirect("hofladen-orderform-authenticate", shopid=shopid, generic_id=generic_id)
        #return render(request, "farmshop/guest/guest_order_detail_control.html", context)
    else:
        if request.session['order_id'] != str(generic_id):
            print("session order_id not identical to requested order")
            return redirect("hofladen-orderform-authenticate", shopid=shopid, generic_id=generic_id)
            #return render(request, "farmshop/guest/guest_order_detail_control.html", context)
        
    return render(request, "farmshop/guest/guest_order_detail.html", context)

"""
Function based view to add some orderline from the list of available packages.
After select some package, the maximum available amount of packages will be calculated and
given a spart of the url to have an adopted predefined form - buid with modelform_factory.
"""
def hofladen_order_append_orderline(request, shopid, generic_id, package_id, max_amount):
    order = Order.objects.get(generic_id=generic_id)
    package = Package.objects.get(pk=package_id)
    farmshop = FarmShop.objects.get(pk=shopid)
    OrderLineForm = modelform_factory(OrderLine, fields=["amount"],
                                      widgets={'amount': forms.NumberInput(attrs={'min':0, 'max':max_amount, 'value':0,'type':'number'}),
                                               }
                                      )
    if request.method == 'POST':
        orderline_form = OrderLineForm(request.POST)
        if orderline_form.is_valid():
            #farmshop = FarmShop.objects.get(pk=shopid)
            orderline = orderline_form.save(commit=False)
            orderline.farmshop = farmshop
            orderline.order = order
            orderline.package = package
            # check if orderline with same package already exists
            # if so, only update the amount
            existing_orderline_qs = OrderLine.objects.filter(farmshop=farmshop, order=order, package=package)
            if existing_orderline_qs:
                print("order with this package already exists - only add amount to existing order!")
                print(existing_orderline_qs.count())
                print(existing_orderline_qs)
                if existing_orderline_qs.count() == 1:
                    existing_orderline = existing_orderline_qs.get()
                    existing_orderline.amount = existing_orderline.amount + orderline.amount
                    existing_orderline.save()
                    print("updated existing orderline")
                    return redirect("hofladen-orderform-configure", shopid=shopid, generic_id=generic_id)
            else:
                print("created new orderline")
                orderline.save()
            return redirect("hofladen-orderform-configure", shopid=shopid, generic_id=generic_id)
        else:
            print("form invalid")

    else:
        orderline_form = OrderLineForm(initial={'order': Order.objects.get(generic_id=generic_id), 'package': Package.objects.get(pk=package_id)})
    return render(request, "farmshop/guest/guest_orderline_create.html", { "form": orderline_form , "order": order, "package": package, "farmshop": farmshop})   

def order_delete_orderline(request, shopid, order_id, orderline_id):
    orderline = OrderLine.objects.get(generic_id=orderline_id)
    context = {
        "orderline": orderline
    }
    if request.method =="POST":
        orderline.delete()
        return redirect("orderform-configure", shopid=shopid, generic_id=order_id)
    return render(request, "farmshop/guest/guest_orderline_confirm_delete.html", context)

def hofladen_order_delete_orderline(request, shopid, order_id, orderline_id):
    orderline = OrderLine.objects.get(generic_id=orderline_id)
    farmshop = orderline.farmshop
    context = {
        "orderline": orderline,
        "farmshop": farmshop
    }
    if request.method =="POST":
        orderline.delete()
        return redirect("hofladen-orderform-configure", shopid=shopid, generic_id=order_id)
    return render(request, "farmshop/guest/guest_orderline_confirm_delete.html", context)

"""
Functions to handle preorders - maybe easier to select the package directly and create the form on the fly!
"""
def hofladen_preorder_create(request, shopid, preorder_id):
    farmshop = FarmShop.objects.get(pk=shopid)

    #package = Package.objects.get(pk=package_id)

    CustomerForm = modelform_factory(Customer, fields=["name", "first_name", "email"])
    # get list of preorderable packages for choosing the preorder relation - there should only one !
    preorderable_packages = PreOrder.objects.filter(generic_id=preorder_id, start_date__lte = date.today(), end_date__gte = date.today()).prefetch_related("package")
    preorder = preorderable_packages[:1].get()
    package_id = preorder.package_id
    

    package = Package.objects.get(pk=package_id)
    #print(len(preorderable_packages.get()))
    #preorder = preorderable_packages.values()
    #package = preorder.package.first()
    max_amount = package.available_for_preorder - package.preordered# - preorderable_packages.get().max_packages - confirmed_orders["orderline__amount__sum"]
    OrderLineForm = modelform_factory(OrderLine, fields=["amount"],
                                      widgets={'amount': forms.NumberInput(attrs={'min':1, 'max':max_amount,'type':'number'}),
                                               }
                                      )
    #OrderLineForm.use_required_attribute = False
    # set mandatory field target_date for order to 0000-01-01
    if request.method == 'POST':
        customer_form = CustomerForm(request.POST, prefix='customer')
        order_form = PreOrderForm(request.POST, prefix='order')
        orderline_form = OrderLineForm(request.POST, prefix='orderline')
        # add package formfields
        if customer_form.is_valid() and order_form.is_valid() and orderline_form.is_valid():
            # pre save customer model
            customer = customer_form.save(commit=False)
            # add metadata 
            customer.created = datetime.now()
            # set farmshop
            farmshop = FarmShop.objects.get(pk=shopid)
            customer.farmshop = farmshop
            customer.save()
            # pre save order model
            order = order_form.save(commit=False)
            order.target_date = "2000-01-01"
            order.customer = customer
            order.farmshop = farmshop
            # add metadata 
            order.created = datetime.now()
            order.changed = datetime.now()
            #print("test")
            #print(len(preorderable_packages.get()))
            order.preorder = preorderable_packages.get()
            order.confirmed = True # directly confirmed?
            order.save()
            # save orderline
            orderline = orderline_form.save(commit=False)
            orderline.farmshop = farmshop
            orderline.order = order
            orderline.package = package
            # add metadata 
            orderline.created = datetime.now()
            orderline.changed = datetime.now()
            orderline.save()
            # send mail with link to perorder - to allow cancelling the preorder later
            
            preorder_url = reverse("hofladen-preorder-configure", args=[farmshop.id, order.generic_id])
            
            # Build complete URLs
            preorder_link = f"{preorder_url}"
            send_mail(
                "Ihre Vorbestellung bei " + str(farmshop.title),
                "Hier der Link: " + request.scheme + "://" + request.get_host() + preorder_link,
                "from@example.com",
                ["to@example.com"],
                fail_silently=False,
            )
            # save id of created order to session 
            request.session["preorder_id"] = str(order.generic_id)
            return redirect("hofladen-preorder-configure", shopid=shopid, generic_id=order.generic_id)
        else:
            print("form invalid")
    else:
        customer_form = CustomerForm(prefix='customer')
        order_form = PreOrderForm(prefix='order')
        #orderline_form = OrderLineForm(request.POST, prefix='orderline')
        orderline_form = OrderLineForm( initial={'package': Package.objects.get(pk=package_id)}, prefix='orderline')
    return render(request, "farmshop/guest/guest_preorder_create.html", {'form1': customer_form, 'form2': order_form, 'form3': orderline_form, 'farmshop': farmshop, 'package': package })

"""
Function based view that allows the configuration of the previausly created preorder.
Products may be added and deleted. Also the order can manipulated till the order will be
confirmed. After that, it only can be cancelled fully. The view is generated by a given generic_id.
This id should only be known by the customer who crested the order - it have to be confirmed with the email address of the customer.  
"""
def hofladen_preorder_configure(request, shopid, generic_id):
    order = Order.objects.get(generic_id=generic_id)
    farmshop = order.farmshop
    context = {
        'order': order,
        'farmshop': farmshop,
    }
    # check if generic_id is in session - else return form with email and captcha
    if 'preorder_id' not in request.session:
        print("requested preorder not in session")
        return redirect("hofladen-preorder-authenticate", shopid=shopid, generic_id=generic_id)
        #return render(request, "farmshop/guest/guest_order_detail_control.html", context)
    else:
        if request.session['preorder_id'] != str(generic_id):
            print("session preorder_id not identical to requested preorder")
            return redirect("hofladen-preorder-authenticate", shopid=shopid, generic_id=generic_id)
            #return render(request, "farmshop/guest/guest_order_detail_control.html", context)
        
    return render(request, "farmshop/guest/guest_preorder_detail.html", context)

# after confirmation, the order cannot be edited any longer
def hofladen_preorder_authenticate(request, shopid, generic_id):
    order = Order.objects.get(generic_id=generic_id)
    farmshop = FarmShop.objects.get(pk=shopid)
    customer_order_confirm_form = CustomerOrderConfirmForm(request.POST)
    context = {
        "farmshop": farmshop,
        "order": generic_id,
        "form": customer_order_confirm_form
    }
    if request.method =="POST":
        if customer_order_confirm_form.is_valid():
            if order.customer.email == customer_order_confirm_form.cleaned_data['email']:
                #create new sessionid cookie and store uuid to order_id 
                request.session['preorder_id'] = str(order.generic_id)
                return redirect("hofladen-preorder-configure", shopid=shopid, generic_id=order.generic_id)
            else:
                messages.error(request, 'Die angegebene E-Mail wurde nicht für die Bestellung verwendet!')
                # new form
                #customer_order_confirm_form = CustomerOrderConfirmForm(request.POST)
                #context["form"] = customer_order_confirm_form
                #raise customer_order_confirm_form.ValidationError('Die angegebene E-Mail wurde nicht für die Bestellung verwendet!')
                render(request, "farmshop/guest/guest_preorder_detail_control.html", context)
                #return render(request, "farmshop/guest/guest_order_detail_control_false.html", context)
    return render(request, "farmshop/guest/guest_preorder_detail_control.html", context)

# after confirmation, the order cannot be edited any longer
def hofladen_preorder_confirm(request, shopid, generic_id):
    farmshop = FarmShop.objects.get(pk=shopid)
    context = {
        "farmshop": farmshop,
        "order": generic_id,
    }
    order = Order.objects.get(generic_id=generic_id)
    #print(order.orderline_set.count)
    if request.method =="POST":
        order.confirmed = True
        order.changed = datetime.now()
        order.save()
        # send mail with link to perorder - to allow cancelling the preorder later
        send_mail(
            "Ihre Vorbestellung bei " + str(farmshop.title),
            "Hier der Link: " + request.build_absolute_uri(),
            "from@example.com",
            ["to@example.com"],
            fail_silently=False,
        )
        return redirect("hofladen-preorder-configure", shopid=shopid, generic_id=order.generic_id)
    return render(request, "farmshop/guest/guest_preorder_confirm_confirm.html", context)

def hofladen_preorder_delete(request, shopid, generic_id):
    farmshop = FarmShop.objects.get(pk=shopid)
    context = {
        "farmshop": farmshop,
        "order": generic_id,
    }
    order = Order.objects.get(generic_id=generic_id)
    if request.method =="POST":
        order.delete()
        # delete order_id from session
        del request.session["preorder_id"]
        return redirect("hofladen-detail", pk=shopid)
    return render(request, "farmshop/guest/guest_preorder_confirm_delete.html", context)

def hofladen_preorder_cancel(request, shopid, generic_id):
    farmshop = FarmShop.objects.get(pk=shopid)
    context = {
        "farmshop": farmshop,
        "order": generic_id,
    }
    order = Order.objects.get(generic_id=generic_id)
    if request.method =="POST":
        order.cancelled = True
        order.created = datetime.now()
        order.save()
        # delete order_id from session
        print("preorder_id aus session löschen")
        messages.error(request, 'Ihre Vorbestellung mit der Nummer ' + str(order.id) + ' wurde endgültig storniert! Sie können eine neue Vorbestellung anlegen.')
        #sessionid löschen
        del request.session["preorder_id"]
        return redirect("hofladen-detail", pk=shopid)
    
    return render(request, "farmshop/guest/guest_preorder_cancel_confirm.html", context)

def farmshop_preorder_package_create():
    pass

def farmshop_preorder_package_update():
    pass

def farmshop_preorder_package_delete():
    pass

# Create your views here.
def home(request):
    my_shops = FarmShop.objects.filter(owned_by_user=request.user)
    context = { 'my_farmshops': my_shops, }
    return render(request, "farmshop/home.html", context)

# function based view for getting all orderable packages - information come from three models
def orderable_packages(request, shopid):
    # get all packages from shop
    farmshop = FarmShop.objects.get(pk=shopid)
    packages = Package.objects.filter(farmshop=farmshop)
    # extend packages with number of already ordered packages
    packages_ordered_amount = Package.objects.filter(farmshop=farmshop).annotate(
        sum_online_quota=Subquery(Inventory.objects.filter(package=OuterRef('pk')).filter(package__orderable=True, farmshop=farmshop).values('package').annotate(sum_online_quota=Sum('online_quota')).values('sum_online_quota')), 
        sum_ordered=Subquery(OrderLine.objects.filter(package=OuterRef('pk')).filter(package__orderable=True, farmshop=farmshop).values('package').annotate(sum_ordered=Sum('amount')).values('sum_ordered'))
        )
    packages_ordered_amount = packages_ordered_amount.filter(Q(sum_ordered=None) | Q(sum_online_quota__gt=F("sum_ordered")))#.filter(sum_online_quota__gt=F("sum_ordered"))
    context = {
        'package': packages_ordered_amount,
        'farmshop': farmshop,
    }
    #print(str(len(packages)))
    return render(request, "farmshop/backend/orderable_package_list.html", context)

"""
Function based view to show a list of available products for the shop. 
"""
def hofladen_available_package_list(request, shopid, generic_id):
    # get all packages from shop
    farmshop = FarmShop.objects.get(pk=shopid)
    packages = Package.objects.filter(farmshop=farmshop)
    # extend packages with number of already ordered packages
    packages_ordered_amount = Package.objects.filter(farmshop=farmshop).annotate(
        sum_online_quota=Coalesce(Subquery(Inventory.objects.filter(package=OuterRef('pk')).filter(package__orderable=True, farmshop=farmshop).values('package').annotate(sum_online_quota=Sum('online_quota')).values('sum_online_quota')), Value(0)), 
        sum_ordered=Coalesce(Subquery(OrderLine.objects.filter(order__cancelled=False, package=OuterRef('pk')).filter(package__orderable=True, farmshop=farmshop).values('package').annotate(sum_ordered=Sum('amount')).values('sum_ordered')), Value(0))
        ).annotate(available=F('sum_online_quota') - F('sum_ordered'))
    packages_ordered_amount = packages_ordered_amount.filter(Q(sum_ordered=None) | Q(sum_online_quota__gt=F("sum_ordered")))
    print(packages_ordered_amount)
    
    context = {
        'farmshop': farmshop,
        'package': packages_ordered_amount,
        'generic_id': generic_id,
    }
    #print(str(len(packages)))
    return render(request, "farmshop/frontend/hofladen_available_package_list.html", context)

"""
Function based view to show a list of available products for the shop. 
"""
def available_package_list(request, shopid, generic_id):
    # get all packages from shop
    farmshop = FarmShop.objects.get(pk=shopid)
    packages = Package.objects.filter(farmshop=farmshop)
    # extend packages with number of already ordered packages
    packages_ordered_amount = Package.objects.filter(farmshop=farmshop).annotate(
        sum_online_quota=Coalesce(Subquery(Inventory.objects.filter(package=OuterRef('pk')).filter(package__orderable=True, farmshop=farmshop).values('package').annotate(sum_online_quota=Sum('online_quota')).values('sum_online_quota')), Value(0)), 
        sum_ordered=Coalesce(Subquery(OrderLine.objects.filter(package=OuterRef('pk')).filter(package__orderable=True, farmshop=farmshop).values('package').annotate(sum_ordered=Sum('amount')).values('sum_ordered')), Value(0))
        ).annotate(available=F('sum_online_quota') - F('sum_ordered'))
    packages_ordered_amount = packages_ordered_amount.filter(Q(sum_ordered=None) | Q(sum_online_quota__gt=F("sum_ordered")))
    context = {
        'farmshop': farmshop,
        'package': packages_ordered_amount,
        'generic_id': generic_id,
    }
    #print(str(len(packages)))
    return render(request, "farmshop/available_package_list.html", context)

# Registration
def register(request):
    if request.method != 'POST':
        form = RegistrationForm()
    else:
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            #
            user = form.save()
            login(request, user)
            #
            return redirect('home')
        else:
            print('form is invalid')
    context = {'form': form}

    return render(request, 'registration/register.html', context)

@login_required
def get_farmshop_logo(request, pk):
    try:
        farmshop = FarmShop.objects.get(owned_by_user=request.user, pk=pk)
    except FarmShop.DoesNotExist:
        farmshop = None
    if farmshop.farmshop_logo:
        if os.path.exists(farmshop.farmshop_logo.file.name):
            response = FileResponse(farmshop.farmshop_logo)
            return response
        else:
           return HttpResponse("File not found", status=404) 
    else:
        return HttpResponse("Object not found", status=404)


# My default view classes
class MyCreateView(LoginRequiredMixin, CreateView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['my_farmshops'] = FarmShop.objects.filter(owned_by_user=self.request.user)
        return context
    
    def form_valid(self, form):
        form.instance.created = datetime.now()
        form.instance.changed = datetime.now()
        form.instance.owned_by_user = self.request.user
        return super().form_valid(form)


class MyListView(LoginRequiredMixin, ListView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['my_farmshops'] = FarmShop.objects.filter(owned_by_user=self.request.user)
        return context

    def get_queryset(self):
        return self.model.objects.filter(
            owned_by_user=self.request.user
        ).order_by('-created')


class MyUpdateView(LoginRequiredMixin, UpdateView):
     
    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['my_farmshops'] = FarmShop.objects.filter(owned_by_user=self.request.user)
        return context

    def form_valid(self, form):
        if form.instance.owned_by_user == self.request.user:
            form.instance.changed = datetime.now()
            return super().form_valid(form)
        else:
            return HttpResponse("Object not owned by logged in user!", status=401)


class MyDeleteView(LoginRequiredMixin, DeleteView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['my_farmshops'] = FarmShop.objects.filter(owned_by_user=self.request.user)
        return context

    def form_valid(self, form):
        object = self.get_object()
        if object.owned_by_user == self.request.user:
            return super().form_valid(form)
        else:
            return HttpResponse("Object not owned by logged in user!", status=401)
        

class MyDetailView(LoginRequiredMixin, DetailView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['my_farmshops'] = FarmShop.objects.filter(owned_by_user=self.request.user)
        return context

    def get_queryset(self):
        return self.model.objects.filter(
            owned_by_user=self.request.user
        ).order_by('-created')

    def form_valid(self, form):
        object = self.get_object()
        if object.owned_by_user == self.request.user:
            return super().form_valid(form)
        else:
            return HttpResponse("Object not owned by logged in user!", status=401)

class PostalAddressCreateView(MyCreateView):
    #template_name = "xrechnung_light/postaladdress_form.html"
    model = PostalAddress
    fields = ["street_name", "postal_zone", "city_name", "country_subentity", "location"]
    success_url = reverse_lazy("postaladdress-list")   
    def form_valid(self, form):
        form.instance.country = 'DE'
        return super().form_valid(form)


class PostalAddressDetailView(DetailView):
    model = PostalAddress
    context_object_name = "postaladdress"
    def get_object(self):
        obj = super().get_object()
        # Record the last accessed date
        #obj.last_accessed = timezone.now()
        #obj.save()
        return obj
    #fields = ["party_name"]


class PostalAddressUpdateView(MyUpdateView):
    model = PostalAddress
    fields = ["street_name", "postal_zone", "city_name", "country_subentity", "location"]
    success_url = reverse_lazy("postaladdress-list") 

    def get_form(self, form_class=None):
        form = super().get_form(form_class=None)
        form.fields['location'].widget = LeafletWidget()
        return form


class PostalAddressDeleteView(MyDeleteView):
    model = PostalAddress
    success_url = reverse_lazy("postaladdress-list")


class PostalAddressListView(MyListView):
    """Renders the postal addresses, with a list of all postal addresses"""
    model = PostalAddress


class HofladenListView(ListView):
    model = FarmShop

    def get_queryset(self):
        return self.model.objects.filter(
            active=True
        ).order_by('id') #.prefetch_related('party_postal_address')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        print(context)
        locations1 = context["farmshop_list"].select_related("postal_address").annotate(location=Cast("postal_address__location", output_field=PointField()))


        #locations = context["farmshop_list"].select_related("postal_address")
        #locations2 = QuerySetSequence(locations)
        locations = PostalAddress.objects.all()

        print(locations.query)
        #locations = locations.objects.all()
        #print(locations.query)
        context["markers"] = json.loads(
            serialize("geojson", locations, geometry_field='location')
        )
        return context


class HofladenDetailView(ListView):
    model = FarmShop

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['farmshop'] = FarmShop.objects.get(pk=self.kwargs['pk'])
        return context


class HofladenProductGroupView(ListView):
    model = FarmShop

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['farmshop'] = FarmShop.objects.get(pk=self.kwargs['pk'])
        return context
    
    """def get_queryset(self):
        return self.model.objects.filter(
            active=True
        ).order_by('id') #.prefetch_related('party_postal_address')
    """

class HofladenProductGroupProductView(ListView):
    model = FarmShop

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        farmshop = FarmShop.objects.get(pk=self.kwargs['shopid'])
        context['farmshop'] = farmshop
        products = Product.objects.filter(farmshop=farmshop, product_group=self.kwargs['pk'])
        context['products'] = products
        return context

class HofladenProductGroupProductPackageView(ListView):
    model = FarmShop

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        farmshop = FarmShop.objects.get(pk=self.kwargs['shopid'])
        context['farmshop'] = farmshop
        products = Product.objects.filter(farmshop=farmshop, product_group=self.kwargs['pk'])
        context['products'] = products
        packages = Package.objects.filter(farmshop=farmshop, product=self.kwargs['pk'])
        context['packages'] = packages
        return context


class HofladenPackageView(ListView):
    model = FarmShop

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['farmshop'] = FarmShop.objects.get(pk=self.kwargs['pk'])
        return context
    

class HofladenPackagePreorderView_old(ListView):
    model = FarmShop

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        farmshop = FarmShop.objects.get(pk=self.kwargs['pk'])
        context['farmshop'] = farmshop
        # add counter for maximum orderable packages 
        preorderable_packages = PreOrder.objects.filter(farmshop=farmshop).filter(start_date__lte = date.today(), end_date__gte = date.today())
        # do it another way !
        # a preorder is currently only available for one package
        # the filter to ge the currently ordered packages for this preorder can be get by aggregate
        # 
        #  
        
        preorderable_package_id_list = preorderable_packages.values_list('package', flat=True)
        packages = Package.objects.filter(id__in = preorderable_package_id_list).prefetch_related('preorder_set').annotate(max_orderable_packages = Sum('preorder__max_packages'))
        print(packages.all())
        # already ordered packages for actual preorders
        already_preordered_packages = OrderLine.objects.filter(package__in = preorderable_package_id_list).prefetch_related('order').filter(order__confirmed=True, order__cancelled=False).select_related('preorder').filter(order__preorder__start_date__lte = date.today(), order__preorder__end_date__gte = date.today()).values('package_id').annotate(total=Sum('amount'))
        context['packages'] = packages
        context['already_preordered_packages'] = already_preordered_packages
        return context
    

class HofladenPackagePreorderView(ListView):
    model = FarmShop

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        farmshop = FarmShop.objects.get(pk=self.kwargs['pk'])
        context['farmshop'] = farmshop
        # add counter for maximum orderable packages 
        preorderable_packages = PreOrder.objects.filter(farmshop=farmshop).filter(start_date__lte = date.today(), end_date__gte = date.today()).prefetch_related('package', )
        context['object_list'] = preorderable_packages
        
        return context
        # do it another way !
        # a preorder is currently only available for one package
        # the filter to ge the currently ordered packages for this preorder can be get by aggregate
        # 
        #  
        
        preorderable_package_id_list = preorderable_packages.values_list('package', flat=True)
        packages = Package.objects.filter(id__in = preorderable_package_id_list).prefetch_related('preorder_set').annotate(max_orderable_packages = Sum('preorder__max_packages'))
        #print(packages.all())
        # already ordered packages for actual preorders
        already_preordered_packages = OrderLine.objects.filter(package__in = preorderable_package_id_list).prefetch_related('order').filter(order__confirmed=True, order__cancelled=False).select_related('preorder').filter(order__preorder__start_date__lte = date.today(), order__preorder__end_date__gte = date.today()).values('package_id').annotate(total=Sum('amount'))
        context['packages'] = packages
        context['already_preordered_packages'] = already_preordered_packages
        return context   


class HofladenProductView(ListView):
    model = FarmShop

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['farmshop'] = FarmShop.objects.get(pk=self.kwargs['pk'])
        return context
    

class HofladenNewsView(ListView):
    model = FarmShop

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['farmshop'] = FarmShop.objects.get(pk=self.kwargs['pk'])
        context['news'] = FarmShopNews.objects.filter(farmshop=context['farmshop']).order_by('-publication_date')
        return context
    
    
class FarmShopListView(MyListView):
    model = FarmShop

    def get_queryset(self):
        return self.model.objects.filter(
            owned_by_user=self.request.user
        ).order_by('-created') #.prefetch_related('party_postal_address')
    

class FarmShopCreateView(MyCreateView):
    model = FarmShop
    fields = ["title", "description", "farmshop_logo", "contact_phone", "impressum", "postal_address"]
    success_url = reverse_lazy("farmshop-list")   

    def get_form(self, form_class=None):
        form = super().get_form(form_class=None)
        #form.fields['party_postal_address'].queryset = form.fields['party_postal_address'].queryset.filter(owned_by_user=self.request.user.id)
        return form


class FarmShopUpdateView(MyUpdateView):
    model = FarmShop

    fields = ["title", "description", "farmshop_logo", "contact_phone", "impressum", "postal_address"]
    success_url = reverse_lazy("farmshop-list") 

    def get_form(self, form_class=None):
        form = super().get_form(form_class=None)
        #form.fields['party_postal_address'].queryset = form.fields['party_postal_address'].queryset.filter(owned_by_user=self.request.user.id)
        return form 
    

class FarmShopDeleteView(MyDeleteView):
    model = FarmShop
    success_url = reverse_lazy("farmshop-list")


class FarmShopDetailView(MyDetailView):
    model = FarmShop
    success_url = reverse_lazy("farmshop-detail")


# define classes for objects, that are specific for one farmshop
# 
#  
class MyFarmShopCreateView(MyCreateView):

    def form_valid(self, form):
        # check if farmshop is owned by actual user
        
        farmshop = FarmShop.objects.get(pk=self.kwargs['shopid'])
        if farmshop.owned_by_user == self.request.user:
            form.instance.farmshop = farmshop
        else:
            return HttpResponse("Shop not owned by logged in user!", status=401)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['farmshop'] = FarmShop.objects.get(pk=self.kwargs['shopid'])
        return context
    
    def get_form_kwargs(self):
        form = super().get_form_kwargs()
        form['initial'].update({'farmshop': FarmShop.objects.get(pk=self.kwargs['shopid'])})
        return form
    

class MyFarmShopListView(MyListView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['farmshop'] = FarmShop.objects.get(pk=self.kwargs['shopid'])
        return context
    
    # Overwrite querset to apply filter to actual shop
    def get_queryset(self, **kwargs):
        queryset = super().get_queryset()
        return queryset.filter(farmshop=self.kwargs['shopid'])
    

class MyFarmShopUpdateView(MyUpdateView):

    def form_valid(self, form):
        # check if farmshop is owned by actual user
        
        farmshop = FarmShop.objects.get(pk=self.kwargs['shopid'])
        if farmshop.owned_by_user == self.request.user:
            form.instance.farmshop = farmshop
        else:
            return HttpResponse("Shop not owned by logged in user!", status=401)
        return super().form_valid(form)


class MyFarmShopDeleteView(MyDeleteView):

    def form_valid(self, form):
        # check if farmshop is owned by actual user
        
        farmshop = FarmShop.objects.get(pk=self.kwargs['shopid'])
        if farmshop.owned_by_user != self.request.user:
            return HttpResponse("Shop not owned by logged in user!", status=401)
        else:
            return super().form_valid(form)
    
"""
Special classes for resources that are owned by a farmshop and only the owner of the farmshop should be able
to access and change them - the owner of the resource itself is not relevant
"""
class MyOwnFarmShopCreateView(CreateView):

    def form_valid(self, form):
        # check if farmshop is owned by actual user
        
        farmshop = FarmShop.objects.get(pk=self.kwargs['shopid'])
        if farmshop.owned_by_user == self.request.user:
            form.instance.farmshop = farmshop
            form.instance.created = datetime.now()
            form.instance.changed = datetime.now()
            form.instance.owned_by_user = self.request.user
        else:
            return HttpResponse("Shop not owned by logged in user!", status=401)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['farmshop'] = FarmShop.objects.get(pk=self.kwargs['shopid'])
        context['my_farmshops'] = FarmShop.objects.filter(owned_by_user=self.request.user)
        return context
    
    def get_form_kwargs(self):
        form = super().get_form_kwargs()
        form['initial'].update({'farmshop': FarmShop.objects.get(pk=self.kwargs['shopid'])})
        return form
    

class MyOwnFarmShopListView(ListView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['farmshop'] = FarmShop.objects.get(pk=self.kwargs['shopid'])
        context['my_farmshops'] = FarmShop.objects.filter(owned_by_user=self.request.user)
        return context
    
    # Overwrite querset to apply filter to actual shop
    def get_queryset(self, **kwargs):
        queryset = super().get_queryset()
        return queryset.filter(farmshop=self.kwargs['shopid'])
    

class MyOwnFarmShopUpdateView(UpdateView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['farmshop'] = FarmShop.objects.get(pk=self.kwargs['shopid'])
        context['my_farmshops'] = FarmShop.objects.filter(owned_by_user=self.request.user)
        return context

    def form_valid(self, form):
        # check if farmshop is owned by actual user
        
        farmshop = FarmShop.objects.get(pk=self.kwargs['shopid'])
        if farmshop.owned_by_user == self.request.user:
            form.instance.farmshop = farmshop
            form.instance.changed = datetime.now()
            form.instance.owned_by_user = self.request.user
        else:
            return HttpResponse("Shop not owned by logged in user!", status=401)
        return super().form_valid(form)


class MyOwnFarmShopDeleteView(DeleteView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['farmshop'] = FarmShop.objects.get(pk=self.kwargs['shopid'])
        context['my_farmshops'] = FarmShop.objects.filter(owned_by_user=self.request.user)
        return context

    def form_valid(self, form):
        # check if farmshop is owned by actual user
        
        farmshop = FarmShop.objects.get(pk=self.kwargs['shopid'])
        if farmshop.owned_by_user != self.request.user:
            return HttpResponse("Shop not owned by logged in user!", status=401)
        else:
            return super().form_valid(form)

"""ProductGroup"""
class ProductGroupCreateView(MyFarmShopCreateView):
    model = ProductGroup
    fields = ["title", "description", "image"]
    
    def get_success_url(self):
        return reverse_lazy("productgroup-list", kwargs={'shopid': self.kwargs['shopid']})    
    

class ProductGroupListView(MyFarmShopListView):
    model = ProductGroup
    # database table names differ from object names
    context_object_name = 'productgroup_list'


class ProductGroupUpdateView(MyFarmShopUpdateView):
    model = ProductGroup

    fields = ["title", "description", "image"]

    def get_success_url(self):
        return reverse_lazy("productgroup-list", kwargs={'shopid': self.kwargs['shopid']}) 
    

class ProductGroupDeleteView(MyFarmShopDeleteView):
    model = ProductGroup

    def get_success_url(self):
        return reverse_lazy("productgroup-list", kwargs={'shopid': self.kwargs['shopid']}) 


"""FarmShopInfo"""
class FarmShopInfoCreateView(MyFarmShopCreateView):
    model = FarmShopInfo
    fields = ["title", "description", "image"]
    
    def get_success_url(self):
        return reverse_lazy("farmshopinfo-list", kwargs={'shopid': self.kwargs['shopid']})    
    

class FarmShopInfoListView(MyFarmShopListView):
    model = FarmShopInfo
    # database table names differ from object names
    context_object_name = 'farmshopinfo_list'


class FarmShopInfoUpdateView(MyFarmShopUpdateView):
    model = FarmShopInfo

    fields = ["title", "description", "image"]

    def get_success_url(self):
        return reverse_lazy("farmshopinfo-list", kwargs={'shopid': self.kwargs['shopid']}) 
    

class FarmShopInfoDeleteView(MyFarmShopDeleteView):
    model = FarmShopInfo

    def get_success_url(self):
        return reverse_lazy("farmshopinfo-list", kwargs={'shopid': self.kwargs['shopid']}) 


"""FarmShopNews"""
class FarmShopNewsCreateView(MyFarmShopCreateView):
    model = FarmShopNews
    fields = ["publication_date", "title", "description", "image", "url"]

    def get_form(self, form_class=None):
        form = super().get_form(form_class=None)
        form.fields['publication_date'].widget = DatePickerInput()
        return form
    
    def get_success_url(self):
        return reverse_lazy("farmshopnews-list", kwargs={'shopid': self.kwargs['shopid']})    
    

class FarmShopNewsListView(MyFarmShopListView):
    model = FarmShopNews
    # database table names differ from object names
    context_object_name = 'farmshopnews_list'


class FarmShopNewsUpdateView(MyFarmShopUpdateView):
    model = FarmShopNews

    fields = ["publication_date", "title", "description", "image", "url"]

    def get_form(self, form_class=None):
        form = super().get_form(form_class=None)
        form.fields['publication_date'].widget = DatePickerInput()
        return form
    
    def get_success_url(self):
        return reverse_lazy("farmshopnews-list", kwargs={'shopid': self.kwargs['shopid']}) 
    

class FarmShopNewsDeleteView(MyFarmShopDeleteView):
    model = FarmShopNews

    def get_success_url(self):
        return reverse_lazy("farmshopnews-list", kwargs={'shopid': self.kwargs['shopid']}) 


"""Product"""
class ProductCreateView(MyFarmShopCreateView):
    model = Product
    fields = ["title", "description", "tax_percent", "product_group", "image"]

    def get_form(self, form_class=None):
        form = super().get_form(form_class=None)
        form.fields['product_group'].queryset = form.fields['product_group'].queryset.filter(farmshop=self.kwargs['shopid'])
        return form 

    def get_success_url(self):
        return reverse_lazy("product-list", kwargs={'shopid': self.kwargs['shopid']})    
    

class ProductListView(MyFarmShopListView):
    model = Product
    # database table names differ from object names
    context_object_name = 'product_list'
    

class ProductUpdateView(MyFarmShopUpdateView):
    model = Product

    fields = ["title", "description", "tax_percent", "product_group", "image"]

    def get_form(self, form_class=None):
        form = super().get_form(form_class=None)
        form.fields['product_group'].queryset = form.fields['product_group'].queryset.filter(farmshop=self.kwargs['shopid'])
        return form 

    def get_success_url(self):
        return reverse_lazy("product-list", kwargs={'shopid': self.kwargs['shopid']}) 
    

class ProductDeleteView(MyFarmShopDeleteView):
    model = Product

    def get_success_url(self):
        return reverse_lazy("product-list", kwargs={'shopid': self.kwargs['shopid']}) 


"""Warehouse"""
class WarehouseCreateView(MyFarmShopCreateView):
    model = Warehouse
    fields = ["title", "description"]

    def get_success_url(self):
        return reverse_lazy("warehouse-list", kwargs={'shopid': self.kwargs['shopid']})    
    

class WarehouseListView(MyFarmShopListView):
    model = Warehouse
    # database table names differ from object names
    context_object_name = 'warehouse_list'
    

class WarehouseUpdateView(MyFarmShopUpdateView):
    model = Warehouse

    fields = ["title", "description"]

    def get_success_url(self):
        return reverse_lazy("warehouse-list", kwargs={'shopid': self.kwargs['shopid']}) 
    

class WarehouseDeleteView(MyFarmShopDeleteView):
    model = Warehouse

    def get_success_url(self):
        return reverse_lazy("warehouse-list", kwargs={'shopid': self.kwargs['shopid']}) 
    

"""Package"""
class PackageCreateView(MyFarmShopCreateView):
    model = Package
    fields = ["title", "description", "product", "units", "unit", "price", "orderable", "image"]

    def get_form(self, form_class=None):
        form = super().get_form(form_class=None)
        form.fields['product'].queryset = form.fields['product'].queryset.filter(farmshop=self.kwargs['shopid'])
        return form 

    def get_success_url(self):
        return reverse_lazy("package-list", kwargs={'shopid': self.kwargs['shopid']})    
    

class PackageListView(MyFarmShopListView):
    model = Package
    # database table names differ from object names
    context_object_name = 'package_list'
    

class PackageUpdateView(MyFarmShopUpdateView):
    model = Package

    fields = ["title", "description", "product", "units", "unit", "price", "orderable", "image"]

    def get_form(self, form_class=None):
        form = super().get_form(form_class=None)
        form.fields['product'].queryset = form.fields['product'].queryset.filter(farmshop=self.kwargs['shopid'])
        return form 
    
    def get_success_url(self):
        return reverse_lazy("package-list", kwargs={'shopid': self.kwargs['shopid']}) 
    

class PackageDeleteView(MyFarmShopDeleteView):
    model = Package

    def get_success_url(self):
        return reverse_lazy("package-list", kwargs={'shopid': self.kwargs['shopid']}) 


"""Inventory"""
class InventoryCreateView(MyFarmShopCreateView):
    model = Inventory
    fields = ["package", "warehouse", "units", "online_quota", "production_date", "expiry_date", ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class=None)
        form.fields['package'].queryset = form.fields['package'].queryset.filter(farmshop=self.kwargs['shopid'])
        form.fields['warehouse'].queryset = form.fields['warehouse'].queryset.filter(farmshop=self.kwargs['shopid'])
        return form 

    def get_success_url(self):
        return reverse_lazy("package-list", kwargs={'shopid': self.kwargs['shopid']})    
    

class InventoryListView(MyFarmShopListView):
    model = Inventory
    # database table names differ from object names
    #context_object_name = 'inventory_list'
    

class InventoryUpdateView(MyFarmShopUpdateView):
    model = Inventory

    fields = ["package", "warehouse", "units", "online_quota", "production_date", "expiry_date", ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class=None)
        form.fields['package'].queryset = form.fields['package'].queryset.filter(farmshop=self.kwargs['shopid'])
        form.fields['warehouse'].queryset = form.fields['warehouse'].queryset.filter(farmshop=self.kwargs['shopid'])
        return form 
    
    def get_success_url(self):
        return reverse_lazy("inventory-list", kwargs={'shopid': self.kwargs['shopid']}) 
    

class InventoryDeleteView(MyFarmShopDeleteView):
    model = Inventory

    def get_success_url(self):
        return reverse_lazy("inventory-list", kwargs={'shopid': self.kwargs['shopid']}) 


"""PreOrder"""
class PreOrderCreateView(MyFarmShopCreateView):
    model = PreOrder
    fields = ["package", "max_packages", "notice", "start_date", "end_date", ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class=None)
        #form.fields['package'].queryset = form.fields['package'].queryset.filter(farmshop=self.kwargs['shopid'])
        #form.fields['warehouse'].queryset = form.fields['warehouse'].queryset.filter(farmshop=self.kwargs['shopid'])
        return form 

    def get_success_url(self):
        return reverse_lazy("preorder-list", kwargs={'shopid': self.kwargs['shopid']})    
    

class PreOrderListView(MyFarmShopListView):
    model = PreOrder
    """
    def get_queryset(self, **kwargs):
        return super().get_queryset(**kwargs).select_related('order_set').all()
    """
    # database table names differ from object names
    #context_object_name = 'PreOrder_list'

    
class PreOrderDetailView(SingleTableView):
    model = PreOrder
    table_class = OrderTable
    """
    def get_queryset(self, **kwargs):
        #print(self.kwargs['pk'])
        return Order.objects.filter(preorder=self.kwargs['pk'])
        #return Order.objects.all()
    """

    #add table 
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['farmshop'] = FarmShop.objects.get(pk=self.kwargs['shopid'])
        context['my_farmshops'] = FarmShop.objects.filter(owned_by_user=self.request.user)
        context['preorder'] = PreOrder.objects.get(id=self.kwargs['pk'])
        already_ordered = Order.objects.filter(preorder=self.kwargs['pk'], confirmed=True, cancelled=False).annotate(sum_amount=Sum('orderline__amount')).aggregate(Sum('sum_amount'))
        context['already_ordered'] = already_ordered['sum_amount__sum']
        return context
    
    def get_queryset(self):
        return Order.objects.filter(preorder=self.kwargs['pk']).annotate(sum_amount=Sum('orderline__amount'))
        #return Order.objects.filter(preorder=self.kwargs['pk'], confirmed=True, cancelled=False).annotate(sum_amount=Sum('orderline__amount'))
    

class PreOrderUpdateView(MyFarmShopUpdateView):
    model = PreOrder

    fields = fields = ["notice", "start_date", "end_date", "package", "max_packages"]

    def get_form(self, form_class=None):
        form = super().get_form(form_class=None)
        #form.fields['package'].queryset = form.fields['package'].queryset.filter(farmshop=self.kwargs['shopid'])
        #form.fields['warehouse'].queryset = form.fields['warehouse'].queryset.filter(farmshop=self.kwargs['shopid'])
        return form 
    
    def get_success_url(self):
        return reverse_lazy("preorder-list", kwargs={'shopid': self.kwargs['shopid']}) 
    

class PreOrderDeleteView(MyFarmShopDeleteView):
    model = PreOrder

    def get_success_url(self):
        return reverse_lazy("preorder-list", kwargs={'shopid': self.kwargs['shopid']}) 


"""Order"""
class OrderCreateView(MyOwnFarmShopCreateView):
    model = Order
    fields = ["target_date", "notice"]

    def get_form(self, form_class=None):
        form = super().get_form(form_class=None)
        #form.fields['package'].queryset = form.fields['package'].queryset.filter(farmshop=self.kwargs['shopid'])
        #form.fields['warehouse'].queryset = form.fields['warehouse'].queryset.filter(farmshop=self.kwargs['shopid'])
        return form 

    def get_success_url(self):
        return reverse_lazy("order-list", kwargs={'shopid': self.kwargs['shopid']})    
    
"""New view with inlined orderlines - not yet ready"""
# https://dev.to/zxenia/django-inline-formsets-with-class-based-views-and-crispy-forms-14o6
class OrderCreateView2(MyFarmShopCreateView):
    model = Order
    template_name = 'farmshop/order_create2.html'
    form_class = OrderLineForm
    success_url = None

    def get_context_data(self, **kwargs):
        context = super(OrderCreateView2, self).get_context_data(**kwargs)
        if self.request.POST:
            # all vars not only titles
            context['orderlines'] = OrderLineFormSet(self.request.POST)
        else:
            context['orderlines'] = OrderLineFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        orderlines = context['orderlines']
        with transaction.atomic():
            #form.instance.owned_by_user = self.request.user
            self.object = form.save()
            if orderlines.is_valid():
                orderlines.instance = self.object
                orderlines.save()
        return super(OrderCreateView2, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy('order-list', kwargs={'pk': self.object.pk})



class OrderListView(MyOwnFarmShopListView):
    model = Order
    """
    Used for administration of all orders - therefor only the id of the shop is used as filter. 
    The filter for the user is not needed!
    """
    """
    def get_queryset(self, **kwargs):
        return self.model.objects.filter(
            farmshop=self.kwargs['shopid']
        ).order_by('id') #.prefetch_related('party_postal_address')
    """
    # database table names differ from object names
    #context_object_name = 'order_list'
    

class OrderUpdateView(MyOwnFarmShopUpdateView):
    model = Order

    fields = ["target_date", "notice"]

    def get_form(self, form_class=None):
        form = super().get_form(form_class=None)
        #form.fields['package'].queryset = form.fields['package'].queryset.filter(farmshop=self.kwargs['shopid'])
        #form.fields['warehouse'].queryset = form.fields['warehouse'].queryset.filter(farmshop=self.kwargs['shopid'])
        return form 
    
    def get_success_url(self):
        return reverse_lazy("order-list", kwargs={'shopid': self.kwargs['shopid']}) 
    

class OrderDeleteView(MyOwnFarmShopDeleteView):
    model = Order

    def get_success_url(self):
        return reverse_lazy("order-list", kwargs={'shopid': self.kwargs['shopid']}) 


"""
PreOrder managemet for backend
"""
class PreOrderOrderCreateView(MyOwnFarmShopCreateView):
    model = Order
    fields = ["target_date", "notice"]

    def get_form(self, form_class=None):
        form = super().get_form(form_class=None)
        #form.fields['package'].queryset = form.fields['package'].queryset.filter(farmshop=self.kwargs['shopid'])
        #form.fields['warehouse'].queryset = form.fields['warehouse'].queryset.filter(farmshop=self.kwargs['shopid'])
        return form 

    def get_success_url(self):
        return reverse_lazy("preorder-detail", kwargs={'shopid': self.kwargs['shopid'], 'pk': self.kwargs['preorderid']})    
    

class PreOrderOrderListView(MyOwnFarmShopListView):
    model = Order
    """
    Used for administration of all orders - therefor only the id of the shop is used as filter. 
    The filter for the user is not needed!
    """
    """
    def get_queryset(self, **kwargs):
        return self.model.objects.filter(
            farmshop=self.kwargs['shopid']
        ).order_by('id') #.prefetch_related('party_postal_address')
    """
    # database table names differ from object names
    #context_object_name = 'order_list'
    

class PreOrderOrderUpdateView(MyOwnFarmShopUpdateView):
    model = Order

    fields = ["target_date", "notice"]

    def get_form(self, form_class=None):
        form = super().get_form(form_class=None)
        #form.fields['package'].queryset = form.fields['package'].queryset.filter(farmshop=self.kwargs['shopid'])
        #form.fields['warehouse'].queryset = form.fields['warehouse'].queryset.filter(farmshop=self.kwargs['shopid'])
        return form 
    
    def get_success_url(self):
        return reverse_lazy("preorder-detail", kwargs={'shopid': self.kwargs['shopid'], 'pk': self.kwargs['preorderid']}) 
    

class PreOrderOrderDeleteView(MyOwnFarmShopDeleteView):
    model = Order

    def get_success_url(self):
        return reverse_lazy("preorder-detail", kwargs={'shopid': self.kwargs['shopid'], 'pk': self.kwargs['preorderid']}) 