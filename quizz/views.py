from django.shortcuts import render, redirect, get_object_or_404
from random import choice
from .models import Question, Choice, Player, Animator
from .forms import PlayerForm
from django.views.decorators.csrf import csrf_exempt
import random
import json
import uuid
from django.http import JsonResponse, HttpResponseBadRequest

# Vue pour afficher le quiz

@csrf_exempt  # Notez que désactiver CSRF n'est pas recommandé, mais cela semble être votre configuration actuelle.
def home(request):
    players = Player.objects.all()  # Assurez-vous d'importer le modèle Player
    form = PlayerForm()  # Et aussi d'importer PlayerForm

    if request.method == 'POST':
        try:
            content = json.loads(request.body)

            # Si c'est une requête pour sélectionner un animateur
            if 'action' in content and content['action'] == 'select_animator':
                players = list(Player.objects.all())
                if len(players) >= 2:
                    # Sélectionner un joueur au hasard pour devenir animateur
                    player_to_become_animator = random.choice(players)
                    animator_name = player_to_become_animator.name

                    # Créer une nouvelle instance Animator
                    animator = Animator(name=animator_name)
                    animator.save()

                    # Supprimer le joueur de la base de données ou le marquer comme inactif
                    player_to_become_animator.delete()

                    # Retourner une réponse avec le nom de l'animateur
                    return JsonResponse({'animator_name': animator_name})

                else:
                    return HttpResponseBadRequest("Pas assez de joueurs.")

        except json.JSONDecodeError:
            # Si ce n'est pas une requête JSON, alors c'est un POST de formulaire
            form = PlayerForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('home')  # Ceci redirige vers la vue 'home', changer selon votre URL

    # Si ce n'est pas une requête POST ou si rien n'a correspondu, affichez la page normalement.
    context = {
        'form': form,
        'players': Player.objects.all(),  # Ceci récupère tous les joueurs restants
    }
    return render(request, 'quiz/home.html', context)

                    

@csrf_exempt  # Assurez-vous de comprendre les implications en matière de sécurité de l'utilisation de cette exemption
def delete_player(request):
    if request.method == 'POST':
        # Ici, on récupère les données du formulaire, pas du JSON
        player_id = request.POST.get('player_id')
        if player_id:
            try:
                player = Player.objects.get(id=player_id)
                player.delete()
                return JsonResponse({'message': 'Joueur supprimé avec succès'})
            except Player.DoesNotExist:
                return JsonResponse({'error': 'Joueur non trouvé'}, status=404)
        else:
            return JsonResponse({'error': 'No player ID provided'}, status=400)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


def show_question(request):
    players = Player.objects.all()  # Récupère tous les joueurs
    questions = Question.objects.all()

    if not questions:
        # Si aucune question n'est disponible, rediriger ou informer l'utilisateur en conséquence
        return render(request, 'quiz/no_questions.html')  # Assurez-vous de créer ce template.

    # Si nous avons des questions, sélectionnez-en une au hasard
    question = random.choice(questions)
    choices = question.choice_set.all()

    correct_choice = None
    for choice in choices:
        if choice.is_correct:
            correct_choice = choice
            break

    if request.method == 'POST':
        
        # L'animateur a sélectionné le joueur qui a donné la bonne réponse
        player_id = request.POST.get('player_id')  # Obtenir l'ID du joueur sélectionné par l'animateur

        if player_id:  # Assurez-vous qu'un ID de joueur a été reçu
            selected_player = get_object_or_404(Player, pk=player_id)
            selected_player.score += 1  # Augmentation du score car l'animateur a indiqué que ce joueur a bien répondu
            selected_player.save()

            # Après avoir mis à jour le score, vous pouvez rediriger vers la même vue pour charger une nouvelle question
            return redirect('show_question')  # 'show_question' devrait être le nom de cette vue dans vos URL.

    # Si ce n'est pas un POST ou si aucune sélection n'a été faite, affichez simplement la question et les options
    context = {
        'question': question,
        'choices': choices,
        'correct_choice': correct_choice,  # Ajoutez ceci si vous souhaitez l'utiliser dans votre template
        'players': players,
    }
    return render(request, 'quiz/questions.html', context)

def get_random_question(request):
    # Récupère toutes les questions disponibles
    all_questions = Question.objects.all()

    if not all_questions:
        return JsonResponse({'error': 'Pas de questions disponibles'}, status=404)

    # Si nous n'avons pas encore demandé de questions ou si toutes les questions ont été posées,
    # la liste des questions posées dans la session sera vide ou égale à la liste de toutes les questions.
    # Dans ce cas, nous devons réinitialiser la liste des questions posées.
    if not request.session.get('asked_questions') or len(request.session.get('asked_questions', [])) == len(all_questions):
        request.session['asked_questions'] = []

    # Exclure les questions déjà posées
    remaining_questions = all_questions.exclude(id__in=request.session['asked_questions'])

    # S'il ne reste plus de questions, cela signifie que nous avons posé toutes les questions possibles.
    # Dans ce cas, vous pouvez choisir de renvoyer une erreur, réinitialiser la liste, ou (comme dans cet exemple)
    # recommencer depuis le début en posant à nouveau les questions.
    if not remaining_questions:
        remaining_questions = all_questions
        request.session['asked_questions'] = []  # Réinitialisation de la liste des questions posées

    # Choix d'une question aléatoire parmi les questions restantes
    question = random.choice(remaining_questions)

    # Ajouter l'ID de la question actuelle à la liste des questions posées
    asked_questions = request.session['asked_questions']
    asked_questions.append(question.id)
    request.session['asked_questions'] = asked_questions

    # Préparer les choix de réponse
    choices = list(question.choice_set.values('choice_text', 'is_correct'))

    # Renvoyer la question et les choix
    return JsonResponse({
        'question_text': question.text,  # Assurez-vous que 'text' est le bon champ dans votre modèle de Question
        'choices': choices,
    })

@csrf_exempt  # Ajoutez ceci pour exempter votre vue de la vérification CSRF, mais seulement si nécessaire
def update_score(request):
    if request.method == 'POST':
        player_id = request.POST.get('player_id')
        if player_id:
            try:
                player = Player.objects.get(pk=player_id)
                player.score += 1
                player.save()
                return JsonResponse({'success': True})  # ou tout autre réponse que vous jugez appropriée
            except Player.DoesNotExist:
                return JsonResponse({'error': 'Player not found'}, status=404)
    return JsonResponse({'error': 'Bad request'}, status=400)

def end_quiz(request):
    # Récupérer tous les joueurs et leurs scores
    players = Player.objects.all().order_by('-score')

    # Préparer les données pour l'affichage
    context = {
        'players': players,
    }
    
    # Afficher la page de fin de quiz avec les scores
    return render(request, 'quiz/end_quiz.html', context)

def start_session(request):
    request.session.create()
    return render(request, 'quiz/start_session.html')