from django import forms
from .models import Restoran
from .models import Semt
from .models import Menu
from .models import Yorum


class RestoranForm(forms.ModelForm):
    class Meta:
        model = Restoran
        fields = ['name', 'il', 'hiz', 'lezzet', 'servis',
                  'acilis_zamani', 'kapanis_zamani', 'haftaici', 'haftasonu']


class SemtForm(forms.ModelForm):
    class Meta:
        model = Semt
        fields = ['semt_mahalle_adi', 'minimum_tutar', 'restoran']


class MenuForm(forms.ModelForm):
    class Meta:
        model = Menu
        fields = ['yemek', 'fiyat', 'restoran']


class YorumForm(forms.ModelForm):
    class Meta:
        model = Yorum
        fields = ['yorum_hiz', 'yorum_lezzet', 'yorum_servis', 'yorum_date',
                  'yorum_icerik', 'restoran']
