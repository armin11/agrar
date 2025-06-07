from django.urls import path, include
from django.contrib.auth import views as auth_views
from farmshop import views
from farmshop.views import FarmShopListView, FarmShopCreateView, FarmShopUpdateView, FarmShopDeleteView, FarmShopDetailView
from farmshop.views import HofladenListView, HofladenDetailView, HofladenProductGroupView, HofladenPackageView, HofladenProductView
from farmshop.views import HofladenProductGroupProductView, HofladenProductGroupProductPackageView
from farmshop.views import HofladenNewsView, HofladenPackagePreorderView
from farmshop.views import ProductGroupListView, ProductGroupCreateView, ProductGroupUpdateView, ProductGroupDeleteView #, ProductGroupDetailView
from farmshop.views import FarmShopInfoListView, FarmShopInfoCreateView, FarmShopInfoUpdateView, FarmShopInfoDeleteView
from farmshop.views import FarmShopNewsListView, FarmShopNewsCreateView, FarmShopNewsUpdateView, FarmShopNewsDeleteView
from farmshop.views import ProductListView, ProductCreateView, ProductUpdateView, ProductDeleteView
from farmshop.views import WarehouseListView, WarehouseCreateView, WarehouseUpdateView, WarehouseDeleteView
from farmshop.views import PackageListView, PackageCreateView, PackageUpdateView, PackageDeleteView
from farmshop.views import InventoryListView, InventoryCreateView, InventoryUpdateView, InventoryDeleteView
from farmshop.views import OrderListView, OrderCreateView, OrderUpdateView, OrderDeleteView
from farmshop.views import PreOrderOrderListView, PreOrderOrderCreateView, PreOrderOrderUpdateView, PreOrderOrderDeleteView
from farmshop.views import PreOrderListView, PreOrderCreateView, PreOrderUpdateView, PreOrderDeleteView, PreOrderDetailView
from farmshop.views import PostalAddressListView, PostalAddressCreateView, PostalAddressUpdateView, PostalAddressDeleteView, PostalAddressDetailView


urlpatterns = [
    path("", views.home, name="home"),
    #path("hello/<name>", views.hello_there, name="hello_there"),
    path("accounts/login/", auth_views.LoginView.as_view(next_page="home"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(next_page="home"), name='logout'),
    # https://dev.to/donesrom/how-to-set-up-django-built-in-registration-in-2023-41hg
    path("register/", views.register, name = "register"),

    path("hofladen/", HofladenListView.as_view(template_name="farmshop/frontend/hofladen_list.html"), name="hofladen-list"),
    path("hofladen/map/", HofladenListView.as_view(template_name="farmshop/frontend/hofladen_map.html"), name="hofladen-map"),
  
    path("hofladen/<int:pk>/", HofladenDetailView.as_view(template_name="farmshop/frontend/hofladen_detail.html"), name="hofladen-detail"),
    path("hofladen/<int:pk>/address/", HofladenDetailView.as_view(template_name="farmshop/frontend/hofladen_address.html"), name="hofladen-address"),
    path("hofladen/<int:pk>/productgroup/", HofladenProductGroupView.as_view(template_name="farmshop/frontend/hofladen_productgroup.html"), name="hofladen-productgroup"),
    path("hofladen/<int:pk>/package/", HofladenPackageView.as_view(template_name="farmshop/frontend/hofladen_package.html"), name="hofladen-package"),
    path("hofladen/<int:pk>/product/", HofladenProductView.as_view(template_name="farmshop/frontend/hofladen_product.html"), name="hofladen-product"),
    path("hofladen/<int:pk>/news/", HofladenNewsView.as_view(template_name="farmshop/frontend/hofladen_news.html"), name="hofladen-news"),
    path("hofladen/<int:pk>/impressum/", HofladenDetailView.as_view(template_name="farmshop/frontend/hofladen_impressum.html"), name="hofladen-impressum"),
    path("hofladen/<int:pk>/privacy/", HofladenDetailView.as_view(template_name="farmshop/frontend/hofladen_privacy.html"), name="hofladen-privacy"),

    path("hofladen/<int:shopid>/productgroup/<int:pk>/product/", HofladenProductGroupProductView.as_view(template_name="farmshop/frontend/hofladen_productgroup_product.html"), name="hofladen-productgroup-product"),
    path("hofladen/<int:shopid>/productgroup/<int:groupid>/product/<int:pk>/package/", HofladenProductGroupProductPackageView.as_view(template_name="farmshop/frontend/hofladen_productgroup_product_package.html"), name="hofladen-productgroup-product-package"),

    path("hofladen/<int:shopid>/orderform/create/", views.hofladen_order_create, name="hofladen-orderform-create"),
    path("hofladen/<int:shopid>/orderform/<uuid:generic_id>/", views.hofladen_order_configure, name="hofladen-orderform-configure"),
    
    path("hofladen/<int:shopid>/orderform/<uuid:generic_id>/available_package_list/", views.hofladen_available_package_list, name="hofladen-available-package-list"),
    path("hofladen/<int:shopid>/orderform/<uuid:generic_id>/orderline/create/<int:package_id>/<int:max_amount>/", views.hofladen_order_append_orderline, name="hofladen-order-append-orderline"),
    path("hofladen/<int:shopid>/orderform/<uuid:order_id>/orderline/<uuid:orderline_id>/delete/", views.hofladen_order_delete_orderline, name="hofladen-order-delete-orderline"),

    path("hofladen/<int:shopid>/orderform/<uuid:generic_id>/delete/", views.hofladen_order_delete, name="hofladen-orderform-delete"),
    path("hofladen/<int:shopid>/orderform/<uuid:generic_id>/update/", views.hofladen_order_update, name="hofladen-orderform-update"),
    path("hofladen/<int:shopid>/orderform/<uuid:generic_id>/confirm/", views.hofladen_order_confirm, name="hofladen-orderform-confirm"),
    path("hofladen/<int:shopid>/orderform/<uuid:generic_id>/cancel/", views.hofladen_order_cancel, name="hofladen-orderform-cancel"),
    path("hofladen/<int:shopid>/orderform/<uuid:generic_id>/authenticate/", views.hofladen_order_authenticate, name="hofladen-orderform-authenticate"),

    #path("hofladen/<int:shopid>/preorder/<int:package_id>/create/", views.hofladen_preorder_create, name="hofladen-preorder-create"),
    #path("hofladen/<int:shopid>/preorder/<uuid:generic_id>/update/", views.hofladen_preorder_update, name="hofladen-preorder-update"),

    path("hofladen/<int:shopid>/preorder/<uuid:preorder_id>/append/", views.hofladen_preorder_create, name="hofladen-preorder-append"),

    #path("hofladen/<int:pk>/package-preorder/", HofladenPackagePreorderView.as_view(template_name="farmshop/frontend/hofladen_package_preorder.html"), name="hofladen-package-preorder"),
    
    path("hofladen/<int:pk>/preorder/", HofladenPackagePreorderView.as_view(template_name="farmshop/frontend/hofladen_package_preorder.html"), name="hofladen-package-preorder"),

    path("hofladen/<int:shopid>/preorder/<uuid:generic_id>/", views.hofladen_preorder_configure, name="hofladen-preorder-configure"),
    path("hofladen/<int:shopid>/preorder/<uuid:generic_id>/delete/", views.hofladen_preorder_delete, name="hofladen-preorder-delete"),
    path("hofladen/<int:shopid>/preorder/<uuid:generic_id>/confirm/", views.hofladen_preorder_confirm, name="hofladen-preorder-confirm"),
    path("hofladen/<int:shopid>/preorder/<uuid:generic_id>/cancel/", views.hofladen_preorder_cancel, name="hofladen-preorder-cancel"),
    path("hofladen/<int:shopid>/preorder/<uuid:generic_id>/authenticate/", views.hofladen_order_authenticate, name="hofladen-preorder-authenticate"),

    #path("hofladen/<int:shopid>/orderform/<uuid:order_id>/orderline/<uuid:orderline_id>/delete/", views.hofladen_order_delete_orderline, name="hofladen-order-delete-orderline"),

    path("postaladdress/", PostalAddressListView.as_view(), name="postaladdress-list"),
    path("postaladdress/create/", PostalAddressCreateView.as_view(), name="postaladdress-create"),
    path("postaladdress/<int:pk>/", PostalAddressDetailView.as_view(), name="postaladdress-detail"),
    path("postaladdress/<int:pk>/update/", PostalAddressUpdateView.as_view(), name="postaladdress-update"),
    path("postaladdress/<int:pk>/delete/", PostalAddressDeleteView.as_view(), name="postaladdress-delete"),

    path("farmshop/", FarmShopListView.as_view(template_name="farmshop/backend/farmshop_list.html"), name="farmshop-list"),
    path("farmshop/<int:pk>/", FarmShopDetailView.as_view(template_name="farmshop/backend/farmshop_detail.html"), name="farmshop-detail"),
    path("farmshop/create/", FarmShopCreateView.as_view(template_name="farmshop/backend/farmshop_form.html"), name="farmshop-create"),
    path("farmshop/<int:pk>/update/", FarmShopUpdateView.as_view(template_name="farmshop/backend/farmshop_form.html"), name="farmshop-update"),
    path("farmshop/<int:pk>/delete/", FarmShopDeleteView.as_view(template_name="farmshop/backend/farmshop_confirm_delete.html"), name="farmshop-delete"),
    path("farmshop/<int:pk>/logo/", views.get_farmshop_logo, name="farmshop-logo"),

    #path("farmshop/<int:shop_pk>/productgroup/<int:pk>/", ProductGroupDetailView.as_view(), name="productgroup-detail"),
    path("farmshop/<int:shopid>/productgroup/", ProductGroupListView.as_view(template_name="farmshop/backend/productgroup_list.html"), name="productgroup-list"),
    path("farmshop/<int:shopid>/productgroup/create/", ProductGroupCreateView.as_view(template_name="farmshop/backend/productgroup_form.html"), name="productgroup-create"),
    path("farmshop/<int:shopid>/productgroup/<int:pk>/update/", ProductGroupUpdateView.as_view(template_name="farmshop/backend/productgroup_form.html"), name="productgroup-update"),
    path("farmshop/<int:shopid>/productgroup/<int:pk>/delete/", ProductGroupDeleteView.as_view(template_name="farmshop/backend/productgroup_confirm_delete.html"), name="productgroup-delete"),
    
    path("farmshop/<int:shopid>/info/", FarmShopInfoListView.as_view(template_name="farmshop/backend/farmshopinfo_list.html"), name="farmshopinfo-list"),
    path("farmshop/<int:shopid>/info/create/", FarmShopInfoCreateView.as_view(template_name="farmshop/backend/farmshopinfo_form.html"), name="farmshopinfo-create"),
    path("farmshop/<int:shopid>/info/<int:pk>/update/", FarmShopInfoUpdateView.as_view(template_name="farmshop/backend/farmshopinfo_form.html"), name="farmshopinfo-update"),
    path("farmshop/<int:shopid>/info/<int:pk>/delete/", FarmShopInfoDeleteView.as_view(template_name="farmshop/backend/farmshopinfo_confirm_delete.html"), name="farmshopinfo-delete"),

    path("farmshop/<int:shopid>/news/", FarmShopNewsListView.as_view(template_name="farmshop/backend/farmshopnews_list.html"), name="farmshopnews-list"),
    path("farmshop/<int:shopid>/news/create/", FarmShopNewsCreateView.as_view(template_name="farmshop/backend/farmshopnews_form.html"), name="farmshopnews-create"),
    path("farmshop/<int:shopid>/news/<int:pk>/update/", FarmShopNewsUpdateView.as_view(template_name="farmshop/backend/farmshopnews_form.html"), name="farmshopnews-update"),
    path("farmshop/<int:shopid>/news/<int:pk>/delete/", FarmShopNewsDeleteView.as_view(template_name="farmshop/backend/farmshopnews_confirm_delete.html"), name="farmshopnews-delete"),


    path("farmshop/<int:shopid>/product/", ProductListView.as_view(template_name="farmshop/backend/product_list.html"), name="product-list"),
    path("farmshop/<int:shopid>/product/create/", ProductCreateView.as_view(template_name="farmshop/backend/product_form.html"), name="product-create"),
    path("farmshop/<int:shopid>/product/<int:pk>/update/", ProductUpdateView.as_view(template_name="farmshop/backend/product_form.html"), name="product-update"),
    path("farmshop/<int:shopid>/product/<int:pk>/delete/", ProductDeleteView.as_view(template_name="farmshop/backend/product_confirm_delete.html"), name="product-delete"),

    path("farmshop/<int:shopid>/warehouse/", WarehouseListView.as_view(template_name="farmshop/backend/warehouse_list.html"), name="warehouse-list"),
    path("farmshop/<int:shopid>/warehouse/create/", WarehouseCreateView.as_view(template_name="farmshop/backend/warehouse_form.html"), name="warehouse-create"),
    path("farmshop/<int:shopid>/warehouse/<int:pk>/update/", WarehouseUpdateView.as_view(template_name="farmshop/backend/warehouse_form.html"), name="warehouse-update"),
    path("farmshop/<int:shopid>/warehouse/<int:pk>/delete/", WarehouseDeleteView.as_view(template_name="farmshop/backend/warehouse_confirm_delete.html"), name="warehouse-delete"),

    path("farmshop/<int:shopid>/package/", PackageListView.as_view(template_name="farmshop/backend/package_list.html"), name="package-list"),
    path("farmshop/<int:shopid>/package/create/", PackageCreateView.as_view(template_name="farmshop/backend/package_form.html"), name="package-create"),
    path("farmshop/<int:shopid>/package/<int:pk>/update/", PackageUpdateView.as_view(template_name="farmshop/backend/package_form.html"), name="package-update"),
    path("farmshop/<int:shopid>/package/<int:pk>/delete/", PackageDeleteView.as_view(template_name="farmshop/backend/package_confirm_delete.html"), name="package-delete"),

    path("farmshop/<int:shopid>/inventory/", InventoryListView.as_view(template_name="farmshop/backend/inventory_list.html"), name="inventory-list"),
    path("farmshop/<int:shopid>/inventory/create/", InventoryCreateView.as_view(template_name="farmshop/backend/inventory_form.html"), name="inventory-create"),
    path("farmshop/<int:shopid>/inventory/<int:pk>/update/", InventoryUpdateView.as_view(template_name="farmshop/backend/inventory_form.html"), name="inventory-update"),
    path("farmshop/<int:shopid>/inventory/<int:pk>/delete/", InventoryDeleteView.as_view(template_name="farmshop/backend/inventory_confirm_delete.html"), name="inventory-delete"),

    # my orders
    path("farmshop/<int:shopid>/order/", OrderListView.as_view(template_name="farmshop/backend/order_list.html"), name="order-list"),
    path("farmshop/<int:shopid>/order/create/", OrderCreateView.as_view(template_name="farmshop/backend/order_form.html"), name="order-create"),
    path("farmshop/<int:shopid>/order/<int:pk>/update/", OrderUpdateView.as_view(template_name="farmshop/backend/order_form.html"), name="order-update"),
    path("farmshop/<int:shopid>/order/<int:pk>/delete/", OrderDeleteView.as_view(template_name="farmshop/backend/order_confirm_delete.html"), name="order-delete"),

    # my preorders
    path("farmshop/<int:shopid>/preorder/", PreOrderListView.as_view(template_name="farmshop/backend/preorder_list.html"), name="preorder-list"),
    path("farmshop/<int:shopid>/preorder/create/", PreOrderCreateView.as_view(template_name="farmshop/backend/preorder_form.html"), name="preorder-create"),
    path("farmshop/<int:shopid>/preorder/<int:pk>/update/", PreOrderUpdateView.as_view(template_name="farmshop/backend/preorder_form.html"), name="preorder-update"),
    path("farmshop/<int:shopid>/preorder/<int:pk>/delete/", PreOrderDeleteView.as_view(template_name="farmshop/backend/preorder_confirm_delete.html"), name="preorder-delete"),
    path("farmshop/<int:shopid>/preorder/<int:pk>/", PreOrderDetailView.as_view(template_name="farmshop/backend/preorder_detail.html"), name="preorder-detail"),

    # preorder order backend management
    path("farmshop/<int:shopid>/preorder/<int:preorderid>/order/", PreOrderOrderListView.as_view(template_name="farmshop/backend/order_list.html"), name="preorder-order-list"),
    path("farmshop/<int:shopid>/preorder/<int:preorderid>/order/create/", PreOrderOrderCreateView.as_view(template_name="farmshop/backend/order_form.html"), name="preorder-order-create"),
    path("farmshop/<int:shopid>/preorder/<int:preorderid>/order/<int:pk>/update/", PreOrderOrderUpdateView.as_view(template_name="farmshop/backend/order_form.html"), name="preorder-order-update"),
    path("farmshop/<int:shopid>/preorder/<int:preorderid>/order/<int:pk>/delete/", PreOrderOrderDeleteView.as_view(template_name="farmshop/backend/order_confirm_delete.html"), name="preorder-order-delete"),

    path("farmshop/<int:shopid>/orderable_packages/", views.orderable_packages, name="orderable-packages"),

    path('captcha/', include('captcha.urls')),

    path("farmshop/<int:pk>/singlepage/", views.dashboard, name="dashboard"),   
    path("farmshop/<int:pk>/singlepage/dashboard2", views.dashboard2, name="dashboard2"), 

]
