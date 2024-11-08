# myapp/forms.py
from django import forms

class UploadForm(forms.Form):
    file = forms.FileField()
class FormulaireTelechargement(forms.Form):
    fichier = forms.FileField(label="Sélectionnez un fichier")