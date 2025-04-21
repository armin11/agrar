from django.contrib import admin

# Register your models here.
from farmshop.models import FarmShop, Product, ProductGroup, Order, OrderLine
from farmshop.models import PreOrder #, PreOrderPackages
from farmshop.models import Customer, Inventory, Warehouse, Package, PostalAddress
from leaflet.admin import LeafletGeoAdmin

class OrderInLineAdmin(admin.TabularInline):
    model = OrderLine


class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderInLineAdmin]


# Register your models here.
admin.site.register(FarmShop)
admin.site.register(Product)
admin.site.register(ProductGroup)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderLine)
admin.site.register(Customer)
admin.site.register(Inventory)
admin.site.register(Warehouse)
admin.site.register(Package)
admin.site.register(PreOrder)
#admin.site.register(PreOrderPackages)
admin.site.register(PostalAddress, LeafletGeoAdmin)

