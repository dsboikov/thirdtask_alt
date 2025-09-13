from __future__ import annotations
from django import forms


class CheckoutForm(forms.Form):
    shipping_address = forms.CharField(widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}))
    payment_method = forms.ChoiceField(choices=[("mock", "Оплата при получении")],
                                       widget=forms.Select(attrs={"class": "form-select"}))
