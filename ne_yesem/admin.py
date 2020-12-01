from django.contrib import admin
from .models import Restoran
from .models import Semt
from .models import Menu
from .models import Yorum

admin.site.register(Restoran)
admin.site.register(Semt)
admin.site.register(Menu)
admin.site.register(Yorum)
