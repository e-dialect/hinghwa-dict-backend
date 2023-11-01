from django.db import models


class Person(models.Model):
    name = models.CharField(blank=True, verbose_name="身份", max_length=100)


class Relation(models.Model):
    from_person = models.ForeignKey(Person, on_delete=models.CASCADE, verbose_name="本人")
    to_person = models.ForeignKey(Person, on_delete=models.CASCADE, verbose_name="他人")