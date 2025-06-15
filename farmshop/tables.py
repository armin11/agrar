import django_tables2 as tables
from .models import Order
from django_tables2.utils import A

class OrderTable(tables.Table):

    #amount =  tables.Column(verbose_name="Anzahl", accessor="orderline_set.all.aggregate('amount')")
    sum_amount = tables.Column(verbose_name="Anzahl")
    #confirmed = tables.Column(verbose_name="Bestätigt")
    #cancelled = tables.Column(verbose_name="Storniert")
    edit = tables.LinkColumn('preorder-order-update', text='Bearbeiten', args=[A('farmshop.id'), A('preorder.id'), A('pk')], \
                         orderable=False, empty_values=())
    delete = tables.LinkColumn('preorder-order-delete', text='Löschen', args=[A('farmshop.id'), A('preorder.id'), A('pk')], \
                         orderable=False, empty_values=())

    """
    def render_amount(self):
        return "13"

    """
    class Meta:
        model = Order
        template_name = "django_tables2/bootstrap.html"
        fields = ("id", "changed", "sum_amount", "confirmed", "cancelled", "picked_up", "customer.first_name", "customer.name", "customer.phone", "customer.email", "target_date", "notice", "edit", "delete")
