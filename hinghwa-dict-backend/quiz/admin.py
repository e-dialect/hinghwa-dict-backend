from django.contrib import admin
from .models import Quiz


# Register your models here.


class QuizAdmin(admin.ModelAdmin):
    list_display = ["id", "question", "answer"]
    list_filter = []
    search_fields = ["id", "question"]
    ordering = ["id"]
    list_per_page = 50


admin.site.register(Quiz, QuizAdmin)
