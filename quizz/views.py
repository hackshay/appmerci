from django.shortcuts import render, redirect, get_object_or_404
from random import choice
from .models import Question, Choice, Player, Animator, GameSession
from .forms import PlayerForm
from django.views.decorators.csrf import csrf_exempt
import random
import json
import uuid
from django.http import JsonResponse, HttpResponseBadRequest

# Vue pour afficher le quiz

@csrf_exempt  # Notez que désactiver CSRF n'est pas recommandé, mais cela semble être votre configuration actuelle.
def home(request):
    # Récupérer la clé de session de jeu depuis la session du navigateur
    game_session_key = request.session.get('game_session_key')

    # Si aucune session de jeu n'est en cours, redirigez peut-être l'utilisateur ou gérez ce scénario.
    if game_session_key is None:
        # Gérer l'absence de session de jeu (par exemple, rediriger vers la page de démarrage)
        return redirect('start_session')  # Remplacez par votre propre logique si nécessaire

    # Récupérer l'objet GameSession en utilisant la clé de session de jeu.
    try:
        game_session = GameSession.objects.get(session_key=game_session_key)
    except GameSession.DoesNotExist:
        # Gérer le cas où la session de jeu n'existe pas.
        # Peut-être rediriger vers la page de démarrage ou afficher un message d'erreur.
        return redirect('start_session')  # Remplacez par votre propre logique si nécessaire

    # Récupérer tous les joueurs appartenant à cette session de jeu.
    players = Player.objects.filter(game_session=game_session)

    # Logique existante pour gérer les requêtes POST
    if request.method == 'POST':
        try:
            content = json.loads(request.body)

            # Si c'est une requête pour sélectionner un animateur
            if 'action' in content and content['action'] == 'select_animator':
                # Assurez-vous de filtrer les joueurs par game_session ici aussi
                players = list(players)  # déjà filtré pour la session actuelle au-dessus
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
            # Si ce n'est pas une requête JSON, alors c'est un POST de formulaire standard
            form = PlayerForm(request.POST)
            if form.is_valid():
                new_player = form.save(commit=False)
                new_player.game_session = game_session  # Assurez-vous que le joueur est lié à la session de jeu
                new_player.save()
                return redirect('home')  # Ceci redirige vers la vue 'home'

    # Si ce n'est pas une requête POST, ou si le formulaire n'est pas valide, affichez la page normalement avec les joueurs de la session actuelle
    form = PlayerForm()  # un nouveau formulaire vide pour la présentation
    context = {
        'form': form,
        'players': players,  # joueurs déjà filtrés pour la session actuelle
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
    # Récupérer la clé de session de jeu depuis la session du navigateur
    game_session_key = request.session.get('game_session_key')

    # Si aucune session de jeu n'est en cours, vous pourriez rediriger l'utilisateur ou gérer cela autrement
    if game_session_key is None:
        # Gérer l'absence de session de jeu (par exemple, rediriger vers la page de démarrage)
        return redirect('start_session')  # Remplacez par votre propre logique si nécessaire

    # Récupérer l'objet GameSession en utilisant la clé de session de jeu.
    try:
        game_session = GameSession.objects.get(session_key=game_session_key)
    except GameSession.DoesNotExist:
        # Gérer le cas où la session de jeu n'existe pas.
        return redirect('start_session')  # Remplacez par votre propre logique si nécessaire

    # Récupérer tous les joueurs appartenant à cette session de jeu.
    players = Player.objects.filter(game_session=game_session)

    questions = Question.objects.all()

    if not questions:
        return render(request, 'quiz/no_questions.html')  # ou toute autre gestion en cas d'absence de questions

    question = random.choice(questions)
    choices = question.choice_set.all()

    correct_choice = None
    for choice in choices:
        if choice.is_correct:
            correct_choice = choice
            break

    if request.method == 'POST':
        player_id = request.POST.get('player_id')
        if player_id:
            selected_player = get_object_or_404(Player, pk=player_id)
            selected_player.score += 1  # Incrémenter le score
            selected_player.save()
            return redirect('quizz')  # Assurez-vous que c'est le nom correct dans vos URL patterns

    context = {
        'question': question,
        'choices': choices,
        'correct_choice': correct_choice,  # Si vous souhaitez afficher ou utiliser le choix correct dans le template
        'players': players,  # Joueurs spécifiques à la session actuelle
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
    game_session_key=request.session.get('game_session_key')

    if game_session_key is None:
        return redirect('start_session')
    try:
        game_session=GameSession.objects.get(session_key=game_session_key)
    except GameSession.DoesNotExist:
        return redirect('start_session')
    # Récupérer tous les joueurs et leurs scores
    players = Player.objects.filter(game_session=game_session).order_by('-score')

    # Préparer les données pour l'affichage
    context = {
        'players': players,
    }
    
    # Afficher la page de fin de quiz avec les scores
    return render(request, 'quiz/end_quiz.html', context)

def start_session(request):
    if request.method == 'POST':  # supposer que la demande de démarrage de session est un POST
        new_game = GameSession()
        new_game.save()

        # Vous pouvez également ajouter l'animateur à la session ici si nécessaire
        print("New GameSession created with session_key:", new_game.session_key)
        # Rediriger l'utilisateur vers la page du jeu avec la clé de session

        # Convertir l'UUID en chaîne avant de le stocker
        session_key_str = str(new_game.session_key)  # Assurez-vous que session_key est l'UUID
        request.session['game_session_key'] = session_key_str
        # ou stocker la clé de session dans la session du navigateur.
        return redirect('home')  # remplacez 'game_view' par le nom de la vue de votre jeu

    # Si la méthode est GET, nous affichons simplement la page avec le formulaire de démarrage
    return render(request, 'quiz/start_session.html')