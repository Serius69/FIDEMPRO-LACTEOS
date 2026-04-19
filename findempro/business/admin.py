from django.contrib import admin
from .models import Business, CompanyProfile

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_type_display', 'industry_sector', 'location', 'owner_name', 'is_active', 'date_created']
    list_filter = ['type', 'industry_sector', 'is_active']
    search_fields = ['name', 'location', 'fk_user__username']
    readonly_fields = ['date_created', 'last_updated', 'industry_sector']
    ordering = ['-date_created']


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ['fk_business', 'demand_pattern', 'distribution_preference',
                    'monte_carlo_iterations', 'confidence_level', 'min_profit_margin_pct']
    list_filter = ['demand_pattern', 'distribution_preference']
    search_fields = ['fk_business__name']
    readonly_fields = ['date_created', 'last_updated']