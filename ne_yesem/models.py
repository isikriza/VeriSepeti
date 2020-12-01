from django.db import models


class Restoran(models.Model):
    name = models.CharField(max_length=128)
    il = models.CharField(max_length=128)
    hiz = models.FloatField()
    lezzet = models.FloatField()
    servis = models.FloatField()
    acilis_zamani = models.TimeField()
    kapanis_zamani = models.TimeField()
    haftaici = models.BooleanField(default=True)
    haftasonu = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Semt(models.Model):
    restoran = models.ForeignKey(Restoran, on_delete=models.CASCADE)
    semt_mahalle_adi = models.CharField(max_length=128)
    minimum_tutar = models.FloatField()


class Menu(models.Model):
    restoran = models.ForeignKey(Restoran, on_delete=models.CASCADE)
    yemek = models.CharField(max_length=128)
    fiyat = models.FloatField()


class Yorum(models.Model):
    restoran = models.ForeignKey(Restoran, on_delete=models.CASCADE)
    yorum_hiz = models.FloatField()
    yorum_lezzet = models.FloatField()
    yorum_servis = models.FloatField()
    yorum_date = models.DateTimeField()
    yorum_icerik = models.TextField()
