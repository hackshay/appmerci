# Fichier : quizz/management/commands/import_questions.py
import csv
from django.core.management.base import BaseCommand
from quizz.models import Question, Choice

class Command(BaseCommand):
    help = 'Import questions and choices from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **options):
        with open(options['csv_file'], mode='r') as file:
            reader = csv.reader(file)
            next(reader, None)  # sauter les en-têtes du fichier CSV

            for row in reader:
                question_text = row[0]
                correct_answer = row[5]  # La bonne réponse est dans la 6ème colonne

                # Création de la question
                question, created = Question.objects.get_or_create(text=question_text, answer=correct_answer)

                if created:
                    self.stdout.write(self.style.SUCCESS(f"Added question: {question_text}"))

                # Création des choix de réponse
                for i in range(1, 5):  # Les colonnes 1 à 4 contiennent les choix
                    choice_text = row[i]
                    is_correct = (choice_text == correct_answer)  # Vérifier si le choix est la bonne réponse

                    choice, created = Choice.objects.get_or_create(
                        question=question,
                        choice_text=choice_text,
                        is_correct=is_correct
                    )

                    if created:
                        self.stdout.write(self.style.SUCCESS(f"  - Added choice: {choice_text}"))
