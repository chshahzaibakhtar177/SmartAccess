from django.contrib import admin
from .models import Student, Fine, EntryLog

admin.site.register(Student)
admin.site.register(Fine)
admin.site.register(EntryLog)

admin.site.site_header = "SmartAccess Admin"
admin.site.site_title = "SmartAccess Admin Portal"
admin.site.index_title = "Welcome to SmartAccess Admin Portal"

