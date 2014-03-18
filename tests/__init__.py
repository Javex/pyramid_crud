from pyramid_crud import forms

normal_forms = [
    forms.ModelForm,
]

inline_forms = [
    forms.BaseInLine,
    forms.TabularInLine,
]

all_forms = normal_forms + inline_forms
