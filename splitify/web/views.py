from django.shortcuts import render,redirect
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView, FormView
from django.urls import reverse_lazy
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from .models import ProcessedResult  # Vous pouvez définir ce modèle pour enregistrer les résultats traités
from .forms import FormulaireTelechargement
import os
import shutil
from django.http import HttpResponse, FileResponse
import subprocess
import threading
from django.views import View
# Page d'accueil
class HomeView(TemplateView):
    template_name = 'home.html'

# Page de téléchargement
class UploadView(FormView):
    template_name = 'upload.html'
    form_class = FormulaireTelechargement
    success_url = reverse_lazy('process')  # Redirige vers la page de traitement après l'upload

    def post(self, request, *args, **kwargs):
        form = FormulaireTelechargement(request.POST, request.FILES)
        if form.is_valid():
            fichier = request.FILES['fichier']
            fs = FileSystemStorage(location=settings.MEDIA_ROOT)

            # Définir le nouveau nom de fichier
            extension = fichier.name.split('.')[-1]  # Récupère l'extension du fichier original
            nouveau_nom = f"input.{extension}"       # Renomme le fichier en "input.<extension>"
            chemin_complet = os.path.join(settings.MEDIA_ROOT, nouveau_nom)

            # Supprimer le fichier existant s'il y en a un avec le même nom
            if os.path.exists(chemin_complet):
                os.remove(chemin_complet)

            # Sauvegarder le fichier avec le nouveau nom
            nom_fichier = fs.save(nouveau_nom, fichier)
            url_fichier = fs.url(nom_fichier)
            return redirect('process')
        
    
        
    def form_valid(self, form):
        # Sauvegarder le fichier téléchargé et l'envoyer pour traitement
        file = form.cleaned_data['file']
        # Traitement du fichier, enregistrez-le ou effectuez une action spécifique
        return super().form_valid(form)

# Page de traitement
class ProcessingView(TemplateView):
    template_name = 'processing.html'
    processing_complete = False  # Variable de classe pour stocker l'état

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        media_path = settings.MEDIA_ROOT
        if os.path.exists(os.path.join(media_path,"input.mp3")):
            context["original"] = settings.MEDIA_ROOT+"/input.mp3"
        # Ajoutez ici le code pour effectuer un traitement (par exemple, traitement de l'image)
        context['status'] = 'Processing...'  # Affichage de l'état
        return context
    
    def execute_demucs(self,file):
        # Exécution du code Demucs en tâche de fond
        subprocess.run(['python3', '-m', 'demucs',
            '--mp3', '--two-stems=vocals', file])
        self.processing_complete = True
        
            
    def post(self, request, *args, **kwargs):
        input_file = os.path.join(settings.MEDIA_ROOT, "input.mp3")
        # Déclencher l'exécution de Demucs de manière asynchrone
        threading.Thread(target=self.execute_demucs(input_file)).start()
        return JsonResponse({'status': 'Processing started...'})

    
# Page des résultats
class ResultView(TemplateView):
    template_name = 'result.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        audios={}
        source_path = settings.SEPARATED_ROOT+"/htdemucs/input"
        if os.path.exists(source_path):
            files_names = [f for f in os.listdir(source_path) if f.endswith('.mp3')]
            for f in files_names:
                result = self.move_file_to_media(source_path, f)
                print(result)
            
            
        
        # Charger tous les fichiers MP3 depuis le dossier media
        media_path = settings.MEDIA_ROOT
        mp3_files = [f for f in os.listdir(media_path) if f.endswith('.mp3')]

        if os.path.exists(os.path.join(media_path,"input.mp3")):
            audios["original"] = settings.MEDIA_ROOT+"/input.mp3"
            for f in mp3_files:
                audios[f.split(".")[0]] = os.path.join(media_path,f)

        # Passer les chemins relatifs des fichiers MP3 à la vue
        context = audios
        
        return context
    def move_file_to_media(self,source_path, file_name):
        # Le chemin absolu du dossier media
        media_directory = settings.MEDIA_ROOT
        
        # Construire le chemin de destination dans le dossier media
        destination_path = media_directory
        print(os.path.join(source_path, file_name))
        # Vérifier si le fichier source existe
        if os.path.exists(os.path.join(source_path, file_name)):
            # Si le fichier de destination existe déjà, on le supprime
            if os.path.exists(os.path.join(destination_path, file_name)):
                os.remove(os.path.join(destination_path, file_name))
            
            # Déplacer le fichier vers le dossier media
            shutil.move(os.path.join(source_path, file_name), destination_path)
            return f"Le fichier a été déplacé et remplacé vers {destination_path}"
        else:
            return "Le fichier source n'existe pas."



def download_file(request, filename):
    # Construire le chemin absolu du fichier
    file_path = os.path.join(settings.MEDIA_ROOT, filename)
    
    # Vérifier si le fichier existe
    if os.path.exists(file_path):
        # Utiliser FileResponse sans ouvrir le fichier explicitement
        response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)
        return response
    else:
        return HttpResponse("Le fichier demandé n'existe pas.", status=404)

