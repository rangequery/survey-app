# surveys/apps.py
from django.apps import AppConfig

class SurveysConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'surveys'
    
    def ready(self):
        # Modifié pour éviter l'erreur de table inexistante
        try:
            # Vérifier si la table existe avant d'appeler get_default_types
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SHOW TABLES LIKE 'surveys_questiontype'")
                if cursor.fetchone():
                    from .models import QuestionType
                    QuestionType.get_default_types()
        except Exception as e:
            # Gérer silencieusement l'erreur pendant l'initialisation
            print(f"Erreur lors de l'initialisation des types de questions: {e}")