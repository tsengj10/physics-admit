from django.contrib import admin
from admissions.models import *

# Register your models here.

class OverallStateAdmin(admin.ModelAdmin):
  readonly_fields=('time', )

class CommentAdmin(admin.ModelAdmin):
  readonly_fields=('time', 'commenter', )

class OfferAdmin(admin.ModelAdmin):
  readonly_fields=('time', )

admin.site.register(OverallState, OverallStateAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Offer, OfferAdmin)
admin.site.register(CandidateInfo)
admin.site.register(College)
admin.site.register(PhysicsSchoolType)
admin.site.register(QualificationType)
admin.site.register(Candidate)
admin.site.register(Qualification)
admin.site.register(School)
