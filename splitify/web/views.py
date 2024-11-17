from django.shortcuts import render,redirect
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView, FormView
from django.urls import reverse_lazy
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from .models import ProcessedResult  # Vous pouvez définir ce modèle pour enregistrer les résultats traités
import os
from django.contrib import messages
import yt_dlp
from urllib.error import HTTPError
import shutil
from django.http import HttpResponse, FileResponse
import subprocess
import threading
from django.views import View
from django.urls import reverse_lazy
from pytube import YouTube
from .forms import FormulaireTelechargement, FormulaireYouTube
# Page d'accueil
class HomeView(TemplateView):
    template_name = 'home.html'

# Page de téléchargement
# class UploadView(FormView):
#     template_name = 'upload.html'
#     form_class = FormulaireTelechargement
#     success_url = reverse_lazy('process')  # Redirige vers la page de traitement après l'upload

#     def post(self, request, *args, **kwargs):
#         form = FormulaireTelechargement(request.POST, request.FILES)
#         if form.is_valid():
#             fichier = request.FILES['fichier']
#             fs = FileSystemStorage(location=settings.MEDIA_ROOT)

#             # Définir le nouveau nom de fichier
#             extension = fichier.name.split('.')[-1]  # Récupère l'extension du fichier original
#             nouveau_nom = f"input.{extension}"       # Renomme le fichier en "input.<extension>"
#             chemin_complet = os.path.join(settings.MEDIA_ROOT, nouveau_nom)

#             # Supprimer le fichier existant s'il y en a un avec le même nom
#             if os.path.exists(chemin_complet):
#                 os.remove(chemin_complet)

#             # Sauvegarder le fichier avec le nouveau nom
#             nom_fichier = fs.save(nouveau_nom, fichier)
#             url_fichier = fs.url(nom_fichier)
#             return redirect('process')
        
    
        
#     def form_valid(self, form):
#         # Sauvegarder le fichier téléchargé et l'envoyer pour traitement
#         file = form.cleaned_data['file']
#         # Traitement du fichier, enregistrez-le ou effectuez une action spécifique
#         return super().form_valid(form)


class UploadView(FormView):
    template_name = 'upload.html'
    form_class = FormulaireTelechargement  # Utilisez un formulaire initial
    success_url = reverse_lazy('process')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['youtube_form'] = FormulaireYouTube()
        return context

    def post(self, request, *args, **kwargs):
        audio_form = FormulaireTelechargement(request.POST, request.FILES)
        youtube_form = FormulaireYouTube(request.POST)

        # Traitement si un fichier audio est envoyé
        if audio_form.is_valid() and 'fichier' in request.FILES:
            fichier = request.FILES['fichier']
            fs = FileSystemStorage(location=settings.MEDIA_ROOT)

            # Définir le nom de fichier
            extension = fichier.name.split('.')[-1]
            nouveau_nom = f"input.{extension}"
            chemin_complet = os.path.join(settings.MEDIA_ROOT, nouveau_nom)

            # Supprimer le fichier existant
            if os.path.exists(chemin_complet):
                os.remove(chemin_complet)

            # Sauvegarder le fichier
            fs.save(nouveau_nom, fichier)
            return redirect('process')

        # Traitement si un lien YouTube est envoyé
        elif youtube_form.is_valid() and youtube_form.cleaned_data['url']:

            yt_url = youtube_form.cleaned_data['url']
        
            # Validation de l'URL
            if not yt_url.startswith("https://www.youtube.com/") and not yt_url.startswith("https://youtu.be/"):
                messages.error(request, "URL non valide. Fournissez une URL YouTube valide.")
                return redirect('upload')

            try:
                # Télécharger l'audio avec yt-dlp
                info = download_audio_with_ytdlp(yt_url)

                # Indiquer que le téléchargement a réussi
                messages.success(request, f"L'audio de {info['title']} a été téléchargé avec succès.")
                return redirect('process')

            except yt_dlp.utils.DownloadError as e:
                messages.error(request, f"Erreur lors du téléchargement : {str(e)}")
            except Exception as e:
                messages.error(request, f"Une erreur est survenue : {str(e)}")


            # try:
            #     yt_url = youtube_form.cleaned_data['url'].split('?')[0]  # Nettoyer l'URL
            #     yt = YouTube(yt_url)
            #     entry = YouTube(yt_url).title
            #     print(f"\nVideo found: {entry}\n")
            #     audio_download = yt.streams.get_audio_only()
                
            #     print(f"Downloading Video...")
            #     # video = yt.streams.filter(only_audio=True).first()
                
            #     print("bon")
            #     if not audio_download:
            #         raise ValueError("Aucun flux audio disponible pour cette vidéo.")

            #     destination = settings.MEDIA_ROOT
            #     # out_file = video.download(output_path=destination)
            #     out_file = audio_download.download(filename="input.mp3")
            #     base, ext = os.path.splitext(out_file)
            #     new_file = os.path.join(destination, 'input.mp3')
            #     os.rename(out_file, new_file)
            #     return redirect('process')

            # except HTTPError as e:
            #     print(f"Erreur HTTP avec YouTube : {e}")
            #     messages.error(request, "Impossible de se connecter à YouTube. Vérifiez l'URL.")

            # except Exception as e:
            #     print(f"Erreur inattendue : {e}")
            #     messages.error(request, "Une erreur est survenue lors du téléchargement de la vidéo.")

            # return redirect('upload')

        return self.form_invalid(audio_form)
        
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
            '--mp3', '--two-stems=vocals', file, '-o', 'media'])
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
        source_path = settings.MEDIA_ROOT+"/htdemucs/input"
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



def download_audio_with_ytdlp(url):
    """
    Télécharge l'audio de la vidéo YouTube en utilisant yt-dlp avec cookies.
    """
    destination = settings.MEDIA_ROOT  # Dossier où stocker le fichier téléchargé
    output_template = os.path.join(destination, 'input.%(ext)s')
    cookies_path = os.path.join(settings.BASE_DIR, 'config', 'cookies.txt')  # Chemin des cookies

    # Configuration yt-dlp
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,  # Nom du fichier de sortie
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'cookiefile': cookies_path,  # Charger les cookies pour l'authentification
        'quiet': False,  # Afficher les logs pour déboguer
        'noplaylist': True,  # Ne pas télécharger de playlists
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)  # Téléchargement
        return info  # Retourne les informations de la vidéo
