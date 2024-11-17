# myapp/forms.py
from django import forms

class UploadForm(forms.Form):
    file = forms.FileField()
class FormulaireTelechargement(forms.Form):
    fichier = forms.FileField(label="Sélectionnez un fichier")

class FormulaireYouTube(forms.Form):
    url = forms.URLField(
        required=False,
        label="Entrez un lien YouTube",
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://youtube.com/...'})
    )