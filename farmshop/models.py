from django.db import models
from django.urls import reverse
import uuid, os, PIL
from django.contrib.auth.models import User
from django.utils.text import slugify
from io import BytesIO
from django.core.files.base import ContentFile
from django.forms import ModelForm
from captcha.fields import CaptchaField
from django.core.exceptions import ValidationError
from django.contrib.gis.db import models
from bootstrap_datepicker_plus.widgets import DatePickerInput
from datetime import date
from django.db.models import Count, Sum, IntegerField, Value

def only_int(value): 
    if value.isdigit()==False:
        raise ValidationError('ID contains characters')
    
# Generic class
class GenericMetadata(models.Model):
    generic_id = models.UUIDField(default = uuid.uuid4)
    created = models.DateTimeField(null=True, blank=True)
    changed = models.DateTimeField(verbose_name="Letzte Änderung", null=True, blank=True)
    deleted = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True, blank=True)
    owned_by_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        abstract = True

class PostalAddress(GenericMetadata):
    RLP = "RLP"
    HE = "HE"
    FEDERAL_STATE_CHOICES = ((RLP, "Rheinland-Pfalz"), (HE, "Hessen"),)
    street_name = models.CharField(max_length=300, verbose_name="Strasse und Hausnummer", help_text="Beispiel: 'Musterstraße 10'")
    city_name = models.CharField(max_length=300, verbose_name="Stadt/Ort", help_text="Beispiel: 'Musterdorf'")
    postal_zone = models.CharField(max_length=5, verbose_name="Postleitzahl", help_text="Beispiel: '12345'", validators=[only_int])
    country_subentity = models.CharField(max_length=128,
        choices=FEDERAL_STATE_CHOICES,
        default=RLP, verbose_name="Bundesland")
    country = models.CharField(max_length=128)
    location = models.PointField(null=True, blank=True)

    def __str__(self):
        """Returns a string representation of a postal address."""
        #date = timezone.localtime(self.log_date)
        return f"'{self.street_name}'\n'{self.postal_zone}' '{self.city_name}'\n'{self.country}'"
    
    def get_absolute_url(self):
        return reverse("postaladdress-detail", kwargs={"pk": self.pk})
    

class FarmShop(GenericMetadata):

    def get_upload_path(self, filename):
        name, ext = os.path.splitext(filename)
        return os.path.join('uploads', 'logos' , str(self.generic_id), slugify(name)) + ext
    
    title = models.CharField(max_length=300, verbose_name="Hofladen")
    description = models.CharField(max_length=4096, verbose_name="Beschreibung Hofladen")
    contact_phone = models.CharField(max_length=30, blank=True, null=True, verbose_name="Kontakttelefon für Anfragen")
    contact_email = models.EmailField(blank=True, null=True, verbose_name="E-Mail", help_text="Kontakt E-Mail*")
    impressum = models.TextField(blank=True, null=True, verbose_name="Impressum Hofladen")
    css_style = models.TextField(blank=True, null=True, verbose_name="CSS-Style für Seite")
    farmshop_logo = models.ImageField(blank=True, null = True, upload_to=get_upload_path, verbose_name="Logo", help_text="Graphik mit Logo")
    postal_address = models.ForeignKey(PostalAddress, on_delete=models.CASCADE, verbose_name="Postalische Adresse", help_text="BT-50 - BT-55", null=True, blank=True)

    # https://forum.djangoproject.com/t/django-filefield-resize-image-before-save-to-s3botostorage/7595/2
    # https://dev.to/doridoro/in-django-model-save-an-image-with-pillow-pil-library-5hbo
    # https://stackoverflow.com/questions/9166400/convert-rgba-png-to-rgb-with-pil
    def save(self, *args, **kwargs):
        if self.farmshop_logo:
            try:
                img = PIL.Image.open(self.farmshop_logo)
                img.verify()
                # reopen because img.verify() moves pointer to the end of the file
                img = PIL.Image.open(self.farmshop_logo)

                # convert png to RGB
                if img.mode in ("RGBA", "LA", "P"):
                    background = PIL.Image.new('RGBA', img.size, (255, 255, 255))
                    alpha_composite = PIL.Image.alpha_composite(background, img)
                    img = alpha_composite.convert("RGB")

                # Calculate new dimensions to maintain aspect ratio with a width of 800
                new_width = 800
                original_width, original_height = img.size
                new_height = int((new_width / original_width) * original_height)

                # Resize the image
                img = img.resize((new_width, new_height), PIL.Image.LANCZOS)

                # Prepare the image for saving
                temp_img = BytesIO()
                # Save the image as JPEG
                img.save(temp_img, format="JPEG", quality=70, optimize=True)
                temp_img.seek(0)

                # Change file extension to .jpg
                original_name, _ = self.farmshop_logo.name.lower().split(".")
                print(original_name)
                img = f"{original_name}.jpg"

                # Save the BytesIO object to the ImageField with the new filename
                self.farmshop_logo.save(img, ContentFile(temp_img.read()), save=False)

            except (IOError, SyntaxError) as e:
                raise ValueError(f"The uploaded file is not a valid image. -- {e}")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title}"


class FarmShopMetadata(GenericMetadata):
    farmshop = models.ForeignKey(FarmShop, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        abstract = True


class FarmShopInfo(FarmShopMetadata):

    def get_upload_path(self, filename):
        name, ext = os.path.splitext(filename)
        return os.path.join('uploads', 'farmshopinfo_image' , str(self.generic_id), slugify(name)) + ext

    title = models.CharField(max_length=300, verbose_name="Titel")
    description= models.CharField(max_length=4096, verbose_name="Beschreibung", null=True, blank=True)
    image = models.ImageField(blank=True, null = True, upload_to=get_upload_path, verbose_name="Bild", help_text="Beispielbild")
    
    def save(self, *args, **kwargs):
        if self.image:
            try:
                img = PIL.Image.open(self.image)
                img.verify()
                # reopen because img.verify() moves pointer to the end of the file
                img = PIL.Image.open(self.image)

                # convert png to RGB
                if img.mode in ("RGBA", "LA", "P"):
                    background = PIL.Image.new('RGBA', img.size, (255, 255, 255))
                    alpha_composite = PIL.Image.alpha_composite(background, img)
                    img = alpha_composite.convert("RGB")

                # Calculate new dimensions to maintain aspect ratio with a width of 800
                new_width = 800
                original_width, original_height = img.size
                new_height = int((new_width / original_width) * original_height)

                # Resize the image
                img = img.resize((new_width, new_height), PIL.Image.LANCZOS)

                # Prepare the image for saving
                temp_img = BytesIO()
                # Save the image as JPEG
                img.save(temp_img, format="JPEG", quality=70, optimize=True)
                temp_img.seek(0)

                # Change file extension to .jpg
                original_name, _ = self.image.name.lower().split(".")
                print(original_name)
                img = f"{original_name}.jpg"

                # Save the BytesIO object to the ImageField with the new filename
                self.image.save(img, ContentFile(temp_img.read()), save=False)

            except (IOError, SyntaxError) as e:
                raise ValueError(f"The uploaded file is not a valid image. -- {e}")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.description}"


class FarmShopNews(FarmShopMetadata):

    def get_upload_path(self, filename):
        name, ext = os.path.splitext(filename)
        return os.path.join('uploads', 'farmshopnews_image' , str(self.generic_id), slugify(name)) + ext

    title = models.CharField(max_length=300, verbose_name="Titel")
    description= models.CharField(max_length=4096, verbose_name="Beschreibung", null=True, blank=True)
    image = models.ImageField(blank=True, null = True, upload_to=get_upload_path, verbose_name="Bild", help_text="Beispielbild")
    publication_date = models.DateField(verbose_name="Publikationsdatum", null=True, blank=True)
    url = models.URLField(verbose_name="Link", null=True, blank=True)
    #test = models.CharField(max_length=300, verbose_name="test", null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.image:
            try:
                img = PIL.Image.open(self.image)
                img.verify()
                # reopen because img.verify() moves pointer to the end of the file
                img = PIL.Image.open(self.image)

                # convert png to RGB
                if img.mode in ("RGBA", "LA", "P"):
                    background = PIL.Image.new('RGBA', img.size, (255, 255, 255))
                    alpha_composite = PIL.Image.alpha_composite(background, img)
                    img = alpha_composite.convert("RGB")

                # Calculate new dimensions to maintain aspect ratio with a width of 800
                new_width = 800
                original_width, original_height = img.size
                new_height = int((new_width / original_width) * original_height)

                # Resize the image
                img = img.resize((new_width, new_height), PIL.Image.LANCZOS)

                # Prepare the image for saving
                temp_img = BytesIO()
                # Save the image as JPEG
                img.save(temp_img, format="JPEG", quality=70, optimize=True)
                temp_img.seek(0)

                # Change file extension to .jpg
                original_name, _ = self.image.name.lower().split(".")
                print(original_name)
                img = f"{original_name}.jpg"

                # Save the BytesIO object to the ImageField with the new filename
                self.image.save(img, ContentFile(temp_img.read()), save=False)

            except (IOError, SyntaxError) as e:
                raise ValueError(f"The uploaded file is not a valid image. -- {e}")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.description}"


class ProductGroup(FarmShopMetadata):

    def get_upload_path(self, filename):
        name, ext = os.path.splitext(filename)
        return os.path.join('uploads', 'productgroup_image' , str(self.generic_id), slugify(name)) + ext

    title = models.CharField(max_length=300, verbose_name="Produktgruppe")
    description= models.CharField(max_length=4096, verbose_name="Produktgruppenbeschreibung", null=True, blank=True)
    image = models.ImageField(blank=True, null = True, upload_to=get_upload_path, verbose_name="Bild", help_text="Beispielbild")
    
    def save(self, *args, **kwargs):
        if self.image:
            try:
                img = PIL.Image.open(self.image)
                img.verify()
                # reopen because img.verify() moves pointer to the end of the file
                img = PIL.Image.open(self.image)

                # convert png to RGB
                if img.mode in ("RGBA", "LA", "P"):
                    background = PIL.Image.new('RGBA', img.size, (255, 255, 255))
                    alpha_composite = PIL.Image.alpha_composite(background, img)
                    img = alpha_composite.convert("RGB")

                # Calculate new dimensions to maintain aspect ratio with a width of 800
                new_width = 800
                original_width, original_height = img.size
                new_height = int((new_width / original_width) * original_height)

                # Resize the image
                img = img.resize((new_width, new_height), PIL.Image.LANCZOS)

                # Prepare the image for saving
                temp_img = BytesIO()
                # Save the image as JPEG
                img.save(temp_img, format="JPEG", quality=70, optimize=True)
                temp_img.seek(0)

                # Change file extension to .jpg
                original_name, _ = self.image.name.lower().split(".")
                print(original_name)
                img = f"{original_name}.jpg"

                # Save the BytesIO object to the ImageField with the new filename
                self.image.save(img, ContentFile(temp_img.read()), save=False)

            except (IOError, SyntaxError) as e:
                raise ValueError(f"The uploaded file is not a valid image. -- {e}")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.description}"
    

class Product(FarmShopMetadata):
 
    def get_upload_path(self, filename):
        name, ext = os.path.splitext(filename)
        return os.path.join('uploads', 'product_image' , str(self.generic_id), slugify(name)) + ext


    title = models.CharField(max_length=300, verbose_name="Produktbezeichnung")
    description = models.CharField(max_length=4096, verbose_name="Produktbeschreibung")
    tax_percent = models.DecimalField(decimal_places=2, max_digits=4, verbose_name="Steuersatz")
    product_group = models.ForeignKey(ProductGroup, on_delete=models.CASCADE, verbose_name="Herkunft", help_text="Herkunft")
    image = models.ImageField(blank=True, null = True, upload_to=get_upload_path, verbose_name="Bild", help_text="Beispielbild")

    def save(self, *args, **kwargs):
        if self.image:
            try:
                img = PIL.Image.open(self.image)
                img.verify()
                # reopen because img.verify() moves pointer to the end of the file
                img = PIL.Image.open(self.image)

                # convert png to RGB
                if img.mode in ("RGBA", "LA", "P"):
                    background = PIL.Image.new('RGBA', img.size, (255, 255, 255))
                    alpha_composite = PIL.Image.alpha_composite(background, img)
                    img = alpha_composite.convert("RGB")

                # Calculate new dimensions to maintain aspect ratio with a width of 800
                new_width = 800
                original_width, original_height = img.size
                new_height = int((new_width / original_width) * original_height)

                # Resize the image
                img = img.resize((new_width, new_height), PIL.Image.LANCZOS)

                # Prepare the image for saving
                temp_img = BytesIO()
                # Save the image as JPEG
                img.save(temp_img, format="JPEG", quality=70, optimize=True)
                temp_img.seek(0)

                # Change file extension to .jpg
                original_name, _ = self.image.name.lower().split(".")
                print(original_name)
                img = f"{original_name}.jpg"

                # Save the BytesIO object to the ImageField with the new filename
                self.image.save(img, ContentFile(temp_img.read()), save=False)

            except (IOError, SyntaxError) as e:
                raise ValueError(f"The uploaded file is not a valid image. -- {e}")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} / {self.product_group}"
    

class Package(FarmShopMetadata):

    def get_upload_path(self, filename):
        name, ext = os.path.splitext(filename)
        return os.path.join('uploads', 'package_image' , str(self.generic_id), slugify(name)) + ext

    class UnitChoices(models.TextChoices):
        KGM = "KGM", "Kilogramm"
        H87 = "H87", "Stück"
        C62 = "C62", "ein"
        MTK = "MTK", "Quadratmeter"
        LM = "LM", "Laufende Meter"

    title = models.CharField(max_length=300, verbose_name="Bezeichnung Packung/Paket")
    description = models.CharField(max_length=4096, verbose_name="Beschreibung Packung/Paket")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Produkt", help_text="Hilfe zum Produkt", null=True)
    unit = models.CharField(max_length=5, choices=UnitChoices.choices, verbose_name="Einheit", help_text="")

    unit_is_approximate = False
    units = models.IntegerField(verbose_name="Einheiten", null=True)
    # tax_percent = models.DecimalField(decimal_places=2, max_digits=4, verbose_name="Steuersatz")
    # product_group = models.ForeignKey(ProductGroup, on_delete=models.CASCADE, verbose_name="Herkunft", help_text="Herkunft")
    # 
    price = models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Packungspreis", null=True)
    orderable = models.BooleanField(verbose_name="Bestellbar", help_text="Packung ist bestellbar")
    #shop_quota = models.IntegerField(verbose_name="Online Kontingent", help_text="Maximal online bestellbare Menge", default=0)
    image = models.ImageField(blank=True, null = True, upload_to=get_upload_path, verbose_name="Bild", help_text="Beispielbild")

    """
    Amount of packages for which a current preorder option is given thru preorder/preorderpackages
    """
    @property
    def available_for_preorder(self):
        preorderable_packages = PreOrder.objects.filter(start_date__lte = date.today(), end_date__gte = date.today()).filter(package=self.id).aggregate(sum_packages=Sum('max_packages'))
        if preorderable_packages["sum_packages"]:
            return preorderable_packages["sum_packages"]
        else:
            return 0

    """
    Amount of packages which are actually preordered via a given preorder/preorderpackages combination
    """
    @property
    def preordered(self):
        already_preordered_packages = OrderLine.objects.filter(package=self.id).prefetch_related('order', 'order__preorder').filter(order__confirmed=True, order__cancelled=False, order__preorder__start_date__lte = date.today(), order__preorder__end_date__gte = date.today()).aggregate(sum_amount=Sum('amount'))
        if already_preordered_packages["sum_amount"]:
            return already_preordered_packages["sum_amount"]
        else:
            return 0
        
    @property
    def preordered_percentage(self):
        if self.available_for_preorder == 0:
            return 0
        
        return round((self.preordered / self.available_for_preorder) * 100)

    def save(self, *args, **kwargs):
        if self.image:
            try:
                img = PIL.Image.open(self.image)
                img.verify()
                # reopen because img.verify() moves pointer to the end of the file
                img = PIL.Image.open(self.image)

                # convert png to RGB
                if img.mode in ("RGBA", "LA", "P"):
                    background = PIL.Image.new('RGBA', img.size, (255, 255, 255))
                    alpha_composite = PIL.Image.alpha_composite(background, img)
                    img = alpha_composite.convert("RGB")

                # Calculate new dimensions to maintain aspect ratio with a width of 800
                new_width = 800
                original_width, original_height = img.size
                new_height = int((new_width / original_width) * original_height)

                # Resize the image
                img = img.resize((new_width, new_height), PIL.Image.LANCZOS)

                # Prepare the image for saving
                temp_img = BytesIO()
                # Save the image as JPEG
                img.save(temp_img, format="JPEG", quality=70, optimize=True)
                temp_img.seek(0)

                # Change file extension to .jpg
                original_name, _ = self.image.name.lower().split(".")
                print(original_name)
                img = f"{original_name}.jpg"

                # Save the BytesIO object to the ImageField with the new filename
                self.image.save(img, ContentFile(temp_img.read()), save=False)

            except (IOError, SyntaxError) as e:
                raise ValueError(f"The uploaded file is not a valid image. -- {e}")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.product})"
    
"""
class PackageContent(GenericMetadata):
    package = models.ForeignKey(Package, on_delete=models.CASCADE, verbose_name="Packung", help_text="Packung")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Artikel", help_text="Artikel")
    unit_type = "objects"
    unit_is_approximate = False
    units = models.IntegerField(verbose_name="Einheiten")
    # tax_percent = models.DecimalField(decimal_places=2, max_digits=4, verbose_name="Steuersatz")
    # product_group = models.ForeignKey(ProductGroup, on_delete=models.CASCADE, verbose_name="Herkunft", help_text="Herkunft")
    # 
    orderable = models.BooleanField(verbose_name="Bestellbar", help_text="Packung ist bestellbar")

    def __str__(self):
        return f"'Inhalt von {self.package.title}'"      
"""


class Warehouse(FarmShopMetadata):
    title = models.CharField(max_length=300, verbose_name="Warenlager")
    description = models.CharField(max_length=4096, verbose_name="Warenlagerbeschreibung")

    def __str__(self):
        return f"{self.title}"
    

class Inventory(FarmShopMetadata):
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='packages', verbose_name="Packung", help_text="Packung")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, verbose_name="Lagerort", help_text="Lagerort")
    units = models.IntegerField(verbose_name="Einheiten")
    online_quota = models.IntegerField(verbose_name="Online Kontingent", help_text="Maximal online bestellbare Menge", default=0)
    production_date = models.DateField(verbose_name="Produktionsdatum", null=True, blank=True)
    expiry_date = models.DateField(verbose_name="Haltbarkeitsdatum", null=True, blank=True)

    @property
    def online_available (self):
        # get all packages in inventories from this farmshop
        # get all already ordered packages
        #  
        pass#return self.number_of_units * self.price_per_unit

    def __str__(self):
        return f"{self.units} Objekte vom Typ '{self.package}' in {self.warehouse.title}"
    

class Customer(FarmShopMetadata):
    name = models.CharField(blank=False, null=False, max_length=300, verbose_name="Name", help_text="Nachname *")
    first_name = models.CharField(blank=True, null=True, max_length=300, verbose_name="Vorname", help_text="Vorname")
    email = models.EmailField(blank=False, null=False, verbose_name="E-Mail", help_text="EMail-Adresse *")
    phone = models.CharField(blank=True, null=True, max_length=300, verbose_name="Telefonnummer", help_text="Telefonnummer")
    newsletter = models.BooleanField(null=True, blank=True)

    def __str__(self):
        return f"'{self.first_name} {self.name}'"


class PreOrder(FarmShopMetadata):
    notice = models.CharField(max_length=4096, verbose_name="Anmerkungen", null=True, blank=True)
    start_date = models.DateField(verbose_name="Startdatum")
    end_date = models.DateField(verbose_name="Enddatum")

    package = models.ForeignKey(Package, on_delete=models.CASCADE, verbose_name="Packung/Paket", null=True, blank=True)
    max_packages = models.IntegerField(verbose_name="Maximal bestellbare Packungen", default=1)
    
    def __str__(self):
        return f"Vorbestellung Nummer {self.id}"
    

class Order(FarmShopMetadata):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="Kunde", help_text="Kunde", null=True, blank=True)
    notice = models.CharField(max_length=4096, verbose_name="Anmerkungen", null=True, blank=True)
    #order_date = models.DateField(verbose_name="Bestelldatum")
    target_date = models.DateField(blank=True, null=True, verbose_name="Abholdatum")
    order_type = "internet"
    confirmed = models.BooleanField(verbose_name="Bestätigt", default=False, help_text="Nach der Bestätigung kann die Bestellung nicht mehr bearbeitet werden. Bitte stornieren Sie sie, wenn sie Fehler enthält.")
    cancelled = models.BooleanField(verbose_name="Storniert", default=False, help_text="Nach der Stornierung kann die Bestellung nicht mehr bearbeitet werden. Die Informationen werden verworfen.")
    # new to allow preorders
    preorder = models.ForeignKey(PreOrder, on_delete=models.CASCADE, verbose_name="Vorbestellung", null=True, blank=True, related_name="orders")
    picked_up = models.BooleanField(verbose_name="Abgeholt", default=False, help_text="Bestellung wurde abgeholt")


    def total_price(self):
        sum = 0.0
        orderlines = OrderLine.objects.filter(order=self.pk)
        for orderline in orderlines:
            sum = sum + float(orderline.amount) * float(orderline.package.price)
        return sum

    def __str__(self):
        return f"Bestellung Nummer {self.id}"
        #return f"'{self.order_date} - Bestellung von {self.customer.first_name} {self.customer.name}'"


class OrderLine(FarmShopMetadata):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name="Bestellung", help_text="Bestellung")
    package = models.ForeignKey(Package, on_delete=models.CASCADE, verbose_name="Packung", help_text="Packung")
    amount = models.IntegerField(verbose_name="Menge")

    
    def total_price(self):
        package = Package.objects.filter(pk=self.package.id).get()
        return float(package.price) * float(self.amount)

    def __str__(self):
        return f"Bestellungsposten Nummer {self.id}"
        #return f"'{self.order_date} - Bestellung von {self.customer.first_name} {self.customer.name}'"
        

"""
class PreOrderPackages(FarmShopMetadata):
    preorder = models.ForeignKey(PreOrder, on_delete=models.CASCADE, verbose_name="Vorbestellung")
    package = models.ForeignKey(Package, on_delete=models.CASCADE, verbose_name="Packung/Paket")
    max_packages = models.IntegerField(verbose_name="Maximale Packungen", default=1)
    
    class Meta:
        unique_together = ('preorder', 'package') # Make sure you dont have duplicate record in the table if so then remove this relation.
"""

class CustomerOrderConfirmForm(ModelForm):
    captcha = CaptchaField()
    class Meta:
        model = Customer
        fields = ['email']
        

class OrderForm(ModelForm):
    captcha = CaptchaField()
    class Meta:
        model = Order
        fields = ['notice', 'target_date']
        widgets={"target_date": DatePickerInput()}


class PreOrderForm(ModelForm):
    captcha = CaptchaField()
    class Meta:
        model = Order
        fields = ['notice']
        #widgets={"target_date": DatePickerInput()}


#https://docs.djangoproject.com/en/4.2/topics/class-based-views/mixins/#using-formmixin-with-detailview