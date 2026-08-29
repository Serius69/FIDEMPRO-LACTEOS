from django.contrib import admin

from .models import (
    Organization,
    OrganizationMembership,
    ResourceUsage,
    Subscription,
    UsageEvent,
)

admin.site.register(Organization)
admin.site.register(OrganizationMembership)
admin.site.register(Subscription)
admin.site.register(UsageEvent)
admin.site.register(ResourceUsage)
