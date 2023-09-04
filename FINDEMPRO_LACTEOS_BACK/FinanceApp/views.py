# views.py 

from .models import Supporter, Expense
from django.shortcuts import render

def financial_dashboard(request):
    supporters = Supporter.objects.all()
    expenses = Expense.objects.filter(date__year=2023)
    
    total_support = sum(s.amount for s in supporters)
    total_expense = sum(e.amount for e in expenses)

    context = {
        'supporters': supporters,
        'expenses': expenses,
        'total_support': total_support,
        'total_expense': total_expense
    }

    return render(request, 'financial/dashboard.html', context)