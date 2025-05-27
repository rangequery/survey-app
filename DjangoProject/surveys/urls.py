from django.urls import path
from . import views

app_name = 'surveys'

urlpatterns = [
    # Vos URLs existantes
    path('', views.SurveyListView.as_view(), name='list'),
    path('create/', views.SurveyCreateView.as_view(), name='create_survey'),
    path('<int:pk>/', views.SurveyDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.SurveyUpdateView.as_view(), name='edit_survey'),
    path('<int:pk>/delete/', views.SurveyDeleteView.as_view(), name='delete_survey'),
    path('<int:pk>/take/', views.TakeSurveyView.as_view(), name='take_survey'),
    path('<int:pk>/submit/', views.submit_survey, name='submit_survey'),
    path('<int:survey_pk>/add-question/', views.QuestionCreateView.as_view(), name='add_question'),
    
    # Nouvelles URLs pour les résultats et l'exportation
    path('<int:pk>/results/', views.survey_results, name='results'),
    path('<int:pk>/export/csv/', views.export_survey_csv, name='export_csv'),
    path('<int:pk>/export/excel/', views.export_survey_excel, name='export_excel'),
    path('<int:pk>/completed/', views.survey_completed, name='survey_completed'),
    path('<int:pk>/save-progress/', views.save_progress, name='save_progress'),
]
