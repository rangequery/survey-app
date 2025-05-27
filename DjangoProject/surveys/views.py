from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseRedirect, JsonResponse
from django.views import View
import logging

from .models import Survey, Answer, SurveyShare, Response, Question, QuestionOption
from .utils import export_survey_to_csv, export_survey_to_excel
from .forms import SurveyForm, QuestionForm, QuestionOptionFormSet, SurveyFilterForm

logger = logging.getLogger(__name__)

class SurveyListView(LoginRequiredMixin, ListView):
    """Vue pour afficher la liste des enquêtes"""
    model = Survey
    template_name = 'surveys/survey_list.html'
    context_object_name = 'surveys'
    
    def get_queryset(self):
        """
        Retourne les enquêtes créées par l'utilisateur connecté
        et celles qui ont été partagées avec lui.
        """
        # Filtrage initial
        queryset = Survey.objects.all()
        
        # Appliquer les filtres si présents
        filter_form = SurveyFilterForm(self.request.GET)
        if filter_form.is_valid():
            status = filter_form.cleaned_data.get('status')
            creator = filter_form.cleaned_data.get('creator')
            
            # Filtrer par statut
            if status == 'active':
                now = timezone.now()
                queryset = queryset.filter(
                    Q(start_date__lte=now) & 
                    (Q(end_date__isnull=True) | Q(end_date__gte=now))
                )
            elif status == 'upcoming':
                queryset = queryset.filter(start_date__gt=timezone.now())
            elif status == 'closed':
                queryset = queryset.filter(end_date__lt=timezone.now())
            
            # Filtrer par créateur
            if creator == 'mine':
                queryset = queryset.filter(creator=self.request.user)
            elif creator == 'shared':
                shared_ids = SurveyShare.objects.filter(
                    shared_with=self.request.user,
                    accepted=True
                ).values_list('survey_id', flat=True)
                queryset = queryset.filter(id__in=shared_ids)
        
        # Si aucun filtre n'est appliqué, montrer toutes les enquêtes de l'utilisateur et partagées
        else:
            # Enquêtes créées par l'utilisateur
            user_surveys = Survey.objects.filter(creator=self.request.user)
            
            # Enquêtes partagées avec l'utilisateur
            shared_surveys_ids = SurveyShare.objects.filter(
                shared_with=self.request.user,
                accepted=True
            ).values_list('survey_id', flat=True)
            
            shared_surveys = Survey.objects.filter(id__in=shared_surveys_ids)
            
            # Combiner les deux querysets
            queryset = (user_surveys | shared_surveys).distinct()
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Ajouter le formulaire de filtre
        context['filter_form'] = SurveyFilterForm(self.request.GET)
        
        # Ajouter les partages en attente
        context['pending_shares'] = SurveyShare.objects.filter(
            shared_with=self.request.user,
            accepted=False
        )
        
        surveys = context['surveys']
        total_responses = sum(s.responses.filter(is_complete=True).count() for s in surveys)
        active_surveys = sum(1 for s in surveys if s.is_active)
        closed_surveys = sum(1 for s in surveys if not s.is_active)
        context['total_responses'] = total_responses
        context['active_surveys'] = active_surveys
        context['closed_surveys'] = closed_surveys

        # Calculate average completion rate for all surveys
        completion_rates = []
        survey_completion_percentages = {}
        for s in surveys:
            total = s.responses.count()
            complete = s.responses.filter(is_complete=True).count()
            if total > 0:
                percent = int(round(complete / total * 100))
                completion_rates.append(complete / total)
            else:
                percent = 0
            survey_completion_percentages[s.id] = percent
        if completion_rates:
            avg_completion = int(round(sum(completion_rates) / len(completion_rates) * 100))
        else:
            avg_completion = 0
        context['completion_percentage'] = avg_completion
        context['survey_completion_percentages'] = survey_completion_percentages

        return context

class SurveyDetailView(LoginRequiredMixin, DetailView):
    """Vue pour afficher les détails d'une enquête"""
    model = Survey
    template_name = 'surveys/survey_detail.html'
    context_object_name = 'survey'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        survey = self.object
        
        # Vérifier si l'utilisateur a la permission de voir cette enquête
        can_edit = survey.creator == self.request.user
        can_view_results = survey.creator == self.request.user
        can_delete = survey.creator == self.request.user
        
        # Vérifier les permissions via partage
        if not (can_edit and can_view_results and can_delete):
            try:
                share = SurveyShare.objects.get(
                    survey=survey,
                    shared_with=self.request.user,
                    accepted=True
                )
                can_edit = can_edit or share.can_edit
                can_view_results = can_view_results or share.can_view_results
                can_delete = can_delete or share.can_delete
            except SurveyShare.DoesNotExist:
                pass
        
        context['can_edit'] = can_edit
        context['can_view_results'] = can_view_results
        context['can_delete'] = can_delete
        context['questions'] = survey.get_questions()
        context['response_count'] = survey.responses.filter(is_complete=True).count()

        # Add more statistics for the detail page
        complete_responses = survey.responses.filter(is_complete=True).count()
        total_responses = survey.responses.count()
        completion_rate = int((complete_responses / total_responses * 100) if total_responses > 0 else 0)
        # Calculate average completion time using completion_time field
        completed_responses = survey.responses.filter(is_complete=True, completion_time__isnull=False)
        avg_completion_time = None
        if completed_responses.exists():
            durations = completed_responses.values_list('completion_time', flat=True)
            total_duration = sum([d.total_seconds() for d in durations if d], 0)
            avg_seconds = total_duration / len(durations)
            import datetime
            avg_completion_time = str(datetime.timedelta(seconds=int(avg_seconds)))
        context['statistics'] = {
            'complete_responses': complete_responses,
            'completion_rate': completion_rate,
            'average_completion_time': avg_completion_time,
        }
        return context

class SurveyCreateView(LoginRequiredMixin, CreateView):
    """Vue pour créer une nouvelle enquête"""
    model = Survey
    form_class = SurveyForm
    template_name = 'surveys/survey_form.html'
    
    def form_valid(self, form):
        form.instance.creator = self.request.user
        self.object = form.save()
        messages.success(self.request, _("Survey created successfully"))
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse('surveys:detail', kwargs={'pk': self.object.pk})

class SurveyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Vue pour mettre à jour une enquête existante"""
    model = Survey
    form_class = SurveyForm
    template_name = 'surveys/survey_form.html'
    
    def test_func(self):
        """Vérifie si l'utilisateur a la permission de modifier cette enquête"""
        survey = self.get_object()
        
        # L'utilisateur est le créateur
        if survey.creator == self.request.user:
            return True
        
        # L'utilisateur a une permission de partage avec droit d'édition
        try:
            share = SurveyShare.objects.get(
                survey=survey,
                shared_with=self.request.user,
                can_edit=True,
                accepted=True
            )
            return True
        except SurveyShare.DoesNotExist:
            return False
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, _("Survey updated successfully"))
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse('surveys:detail', kwargs={'pk': self.object.pk})

class SurveyDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Vue pour supprimer une enquête"""
    model = Survey
    template_name = 'surveys/survey_confirm_delete.html'
    success_url = reverse_lazy('surveys:list')
    
    def test_func(self):
        """Vérifie si l'utilisateur a la permission de supprimer cette enquête"""
        survey = self.get_object()
        
        # L'utilisateur est le créateur
        if survey.creator == self.request.user:
            return True
        
        # L'utilisateur a une permission de partage avec droit de suppression
        try:
            share = SurveyShare.objects.get(
                survey=survey,
                shared_with=self.request.user,
                can_delete=True,
                accepted=True
            )
            return True
        except SurveyShare.DoesNotExist:
            return False
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _("Survey deleted successfully"))
        return super().delete(request, *args, **kwargs)

class TakeSurveyView(View):
    """Vue pour répondre à une enquête"""
    template_name = 'surveys/take_survey.html'
    
    def get(self, request, pk):
        logger.info(f"[TakeSurveyView][GET] User: {request.user} - Survey PK: {pk}")
        try:
            survey = get_object_or_404(Survey, pk=pk)
        except Exception as e:
            messages.error(request, _(f"Erreur lors de la récupération du sondage: {e}"))
            return redirect('surveys:list')
        
        # Vérifier si l'enquête est active
        now = timezone.now()
        if survey.start_date and survey.start_date > now:
            messages.error(request, _("This survey is not open yet."))
            return redirect('surveys:list')
        
        if survey.end_date and survey.end_date < now:
            messages.error(request, _("This survey is closed."))
            return redirect('surveys:list')
        
        # Vérifier si le nombre maximal de réponses est atteint
        if survey.max_responses and survey.responses.filter(is_complete=True).count() >= survey.max_responses:
            messages.error(request, _("This survey has reached its maximum number of responses."))
            return redirect('surveys:list')
        
        # Vérifier si l'utilisateur est authentifié (si requis)
        if not survey.allow_anonymous and not request.user.is_authenticated:
            messages.error(request, _("You need to be logged in to take this survey."))
            return redirect('login')  # Assurez-vous d'avoir une vue de connexion configurée
        
        # Créer ou récupérer une réponse en cours
        response = None
        if request.user.is_authenticated:
            # Vérifier si l'utilisateur a déjà une réponse en cours pour cette enquête
            response = Response.objects.filter(
                survey=survey,
                respondent=request.user,  # Utilisez respondent au lieu de user
                is_complete=False
            ).first()

        # Créer une nouvelle réponse si nécessaire
        if not response:
            response = Response.objects.create(
                survey=survey,
                respondent=request.user if request.user.is_authenticated else None,  # Utilisez respondent au lieu de user
            )
        
        # Obtenir les questions à afficher
        questions = survey.get_questions()
        if survey.randomize_questions:
            questions = list(questions)
            from random import shuffle
            shuffle(questions)
        
        # Gérer l'affichage d'une question à la fois si configuré
        if survey.one_question_per_page:
            # Obtenir le numéro de la question actuelle (par défaut, la première)
            current_question_index = int(request.GET.get('question', 0))
            
            # S'assurer que l'index est valide
            if current_question_index >= len(questions):
                current_question_index = 0
            
            # Obtenir la question actuelle
            if questions:
                current_question = questions[current_question_index]
                progress = (current_question_index / len(questions)) * 100 if len(questions) > 0 else 0
                
                return render(request, self.template_name, {
                    'survey': survey,
                    'question': current_question,
                    'response': response,
                    'current_index': current_question_index,
                    'total_questions': len(questions),
                    'progress': progress,
                    'show_progress': survey.show_progress,
                    'is_first': current_question_index == 0,
                    'is_last': current_question_index == len(questions) - 1
                })
            else:
                messages.error(request, _("This survey has no questions."))
                return redirect('surveys:list')
        else:
            # Afficher toutes les questions sur une seule page
            return render(request, self.template_name, {
                'survey': survey,
                'questions': questions,
                'response': response,
                'show_progress': False
            })
    
    def post(self, request, pk):
        logger.info(f"[TakeSurveyView][POST] User: {request.user} - Survey PK: {pk}")
        try:
            survey = get_object_or_404(Survey, pk=pk)
        except Exception as e:
            messages.error(request, _(f"Erreur lors de la récupération du sondage: {e}"))
            return redirect('surveys:list')
        
        # Vérifier si l'enquête est active (même vérifications que dans get())
        
        # Récupérer ou créer la réponse
        response_id = request.POST.get('response_id')
        
        if response_id:
            response = get_object_or_404(Response, pk=response_id, survey=survey)
        else:
            response = Response.objects.create(
                survey=survey,
                respondent=request.user if request.user.is_authenticated and not survey.allow_anonymous else None,
                is_complete=False
            )
        
        # Traiter les réponses soumises
        if survey.one_question_per_page:
            # Traiter une seule question
            question_id = request.POST.get('question_id')
            if question_id:
                question = get_object_or_404(Question, pk=question_id, survey=survey)
                self._process_question_answer(question, request.POST, response)
                
                # Déterminer la question suivante
                current_index = int(request.POST.get('current_index', 0))
                questions = list(survey.get_questions())
                
                if survey.randomize_questions:
                    # Si les questions sont randomisées, nous devons conserver l'ordre dans la session
                    if 'survey_questions_order' not in request.session:
                        request.session['survey_questions_order'] = [q.id for q in questions]
                    
                    question_ids = request.session['survey_questions_order']
                    questions = [get_object_or_404(Question, pk=qid) for qid in question_ids]
                
                # Vérifier si c'est la dernière question
                if current_index >= len(questions) - 1:
                    # Compléter la réponse
                    response.is_complete = True
                    response.completed_at = timezone.now()
                    response.save()
                    
                    messages.success(request, survey.success_message or _("Thank you for completing the survey!"))
                    
                    # Rediriger si configuré
                    if survey.redirect_url:
                        return redirect(survey.redirect_url)
                    
                    return redirect('surveys:list')
                else:
                    # Passer à la question suivante
                    next_index = current_index + 1
                    return redirect(reverse('surveys:take_survey', kwargs={'pk': survey.pk}) + f'?question={next_index}')
        else:
            # Traiter toutes les questions
            questions = survey.get_questions()
            
            for question in questions:
                self._process_question_answer(question, request.POST, response)
            
            # Compléter la réponse
            response.is_complete = True
            response.completed_at = timezone.now()
            response.save()
            
            messages.success(request, survey.success_message or _("Thank you for completing the survey!"))
            
            # Rediriger si configuré
            if survey.redirect_url:
                return redirect(survey.redirect_url)
            
            return redirect('surveys:list')
        
        
    
    def _process_question_answer(self, question, post_data, response):
        """
        Traite la réponse à une question et la sauvegarde
        """
        # Supprimer toute réponse existante pour cette question
        Answer.objects.filter(question=question, response=response).delete()
        
        # Créer une nouvelle réponse en fonction du type de question
        question_key = f'question_{question.id}'
        
        if hasattr(question.question_type, 'has_options') and question.question_type.has_options:
            # Questions à choix (unique ou multiple)
            if question.question_type.name in ['radio', 'dropdown']:  # Choix unique
                option_id = post_data.get(question_key)
                if option_id:
                    answer = Answer.objects.create(
                        question=question,
                        response=response
                    )
                    option = QuestionOption.objects.get(pk=option_id)
                    answer.selected_options.add(option)
            elif question.question_type.name in ['checkbox', 'multiple_select']:  # Choix multiple
                option_ids = post_data.getlist(question_key)
                if option_ids:
                    answer = Answer.objects.create(
                        question=question,
                        response=response
                    )
                    for option_id in option_ids:
                        option = QuestionOption.objects.get(pk=option_id)
                        answer.selected_options.add(option)
        else:
            # Questions textuelles
            text_value = post_data.get(question_key, '').strip()
            if text_value:
                Answer.objects.create(
                    question=question,
                    response=response,
                    text_answer=text_value
                )

class QuestionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Vue pour créer une nouvelle question"""
    model = Question
    form_class = QuestionForm
    template_name = 'surveys/question_form.html'
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.survey = get_object_or_404(Survey, pk=kwargs.get('survey_pk'))
    
    def test_func(self):
        """Vérifie si l'utilisateur a la permission de modifier l'enquête"""
        survey = self.survey
        
        # L'utilisateur est le créateur
        if survey.creator == self.request.user:
            return True
        
        # L'utilisateur a une permission de partage avec droit d'édition
        try:
            share = SurveyShare.objects.get(
                survey=survey,
                shared_with=self.request.user,
                can_edit=True,
                accepted=True
            )
            return True
        except SurveyShare.DoesNotExist:
            return False
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['survey'] = self.survey
        return kwargs
    
    def form_valid(self, form):
        form.instance.survey = self.survey
        self.object = form.save()
        
        # Gestion des options si applicable
        if hasattr(self.object.question_type, 'has_options') and self.object.question_type.has_options:
            option_formset = QuestionOptionFormSet(self.request.POST, instance=self.object)
            if option_formset.is_valid():
                option_formset.save()
        
        messages.success(self.request, _("Question added successfully"))
        return HttpResponseRedirect(self.get_success_url())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['survey'] = self.survey
        
        # Ajouter le formset pour les options
        if self.request.POST:
            context['option_formset'] = QuestionOptionFormSet(self.request.POST)
        else:
            context['option_formset'] = QuestionOptionFormSet()
        
        return context
    
    def get_success_url(self):
        return reverse('surveys:detail', kwargs={'pk': self.survey.pk})

class QuestionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Vue pour mettre à jour une question existante"""
    model = Question
    form_class = QuestionForm
    template_name = 'surveys/question_form.html'
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.question = get_object_or_404(Question, pk=kwargs.get('pk'))
        self.survey = self.question.survey
    
    def test_func(self):
        """Vérifie si l'utilisateur a la permission de modifier l'enquête"""
        survey = self.survey
        
        # L'utilisateur est le créateur
        if survey.creator == self.request.user:
            return True
        
        # L'utilisateur a une permission de partage avec droit d'édition
        try:
            share = SurveyShare.objects.get(
                survey=survey,
                shared_with=self.request.user,
                can_edit=True,
                accepted=True
            )
            return True
        except SurveyShare.DoesNotExist:
            return False
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['survey'] = self.survey
        return kwargs
    
    def form_valid(self, form):
        self.object = form.save()
        
        # Gestion des options si applicable
        if hasattr(self.object.question_type, 'has_options') and self.object.question_type.has_options:
            option_formset = QuestionOptionFormSet(self.request.POST, instance=self.object)
            if option_formset.is_valid():
                option_formset.save()
        
        messages.success(self.request, _("Question updated successfully"))
        return HttpResponseRedirect(self.get_success_url())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['survey'] = self.survey
        
        # Ajouter le formset pour les options
        if self.request.POST:
            context['option_formset'] = QuestionOptionFormSet(self.request.POST, instance=self.object)
        else:
            context['option_formset'] = QuestionOptionFormSet(instance=self.object)
        
        return context
    
    def get_success_url(self):
        return reverse('surveys:detail', kwargs={'pk': self.survey.pk})

@login_required
def survey_results(request, pk):
    logger.info(f"[survey_results] User: {request.user} - Survey PK: {pk}")
    try:
        survey = get_object_or_404(Survey, pk=pk)
    except Exception as e:
        messages.error(request, _(f"Erreur lors de la récupération du sondage: {e}"))
        return redirect('surveys:list')
    
    # Check if user has permission to view results
    if survey.creator != request.user:
        # Check if user has permission via share
        try:
            share = SurveyShare.objects.get(
                survey=survey,
                shared_with=request.user,
                can_view_results=True,
                accepted=True
            )
        except SurveyShare.DoesNotExist:
            messages.error(request, _("You don't have permission to view the results of this survey"))
            return redirect('surveys:detail', pk=survey.pk)
    
    # Get questions
    questions = survey.get_questions()
    
    # Apply date filters if provided
    date_filter = request.GET.get('date_filter', 'all')
    start_date = None
    end_date = None
    
    if date_filter == 'today':
        start_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = timezone.now()
    elif date_filter == 'yesterday':
        start_date = (timezone.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
    elif date_filter == 'this_week':
        # Get the start of the week (Monday)
        today = timezone.now()
        start_date = (today - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = timezone.now()
    elif date_filter == 'last_week':
        today = timezone.now()
        start_date = (today - timedelta(days=today.weekday() + 7)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=7)
    elif date_filter == 'this_month':
        start_date = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = timezone.now()
    elif date_filter == 'last_month':
        today = timezone.now()
        if today.month == 1:
            last_month = 12
            last_month_year = today.year - 1
        else:
            last_month = today.month - 1
            last_month_year = today.year
        start_date = timezone.datetime(last_month_year, last_month, 1, 0, 0, 0)
        if last_month == 12:
            end_date = timezone.datetime(last_month_year + 1, 1, 1, 0, 0, 0)
        else:
            end_date = timezone.datetime(last_month_year, last_month + 1, 1, 0, 0, 0)
    elif date_filter == 'custom':
        # Parse custom date range
        try:
            start_date_str = request.GET.get('start_date')
            end_date_str = request.GET.get('end_date')
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').replace(tzinfo=timezone.get_current_timezone())
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=timezone.get_current_timezone())
        except ValueError:
            messages.error(request, _("Invalid date format. Please use YYYY-MM-DD."))
    
    # Filter responses based on date range
    responses = survey.responses.filter(is_complete=True)
    if start_date:
        responses = responses.filter(created_at__gte=start_date)
    if end_date:
        responses = responses.filter(created_at__lte=end_date)
    
    # Calculate statistics
    total_responses = responses.count()
    complete_responses = responses.filter(is_complete=True).count()
    completion_rate = int((complete_responses / total_responses * 100) if total_responses > 0 else 0)
    
    # Calculate answer counts for each option
    for question in questions:
        if hasattr(question.question_type, 'has_options') and question.question_type.has_options:
            options = question.get_options()
            for option in options:
                option.answer_count = Answer.objects.filter(
                    question=question,
                    response__in=responses,
                    selected_options=option
                ).count()
    
    # Get response trend data (responses per day for the last 30 days)
    end_date_trend = timezone.now()
    start_date_trend = end_date_trend - timedelta(days=30)
    trend_data = []
    
    current_date = start_date_trend
    while current_date <= end_date_trend:
        next_date = current_date + timedelta(days=1)
        count = responses.filter(created_at__gte=current_date, created_at__lt=next_date).count()
        trend_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'count': count
        })
        current_date = next_date
    
    # Get cross-tabulation data if requested
    cross_tab_data = None
    question1_id = request.GET.get('question1')
    question2_id = request.GET.get('question2')
    
    if question1_id and question2_id and question1_id != question2_id:
        try:
            question1 = survey.questions.get(id=question1_id)
            question2 = survey.questions.get(id=question2_id)
            
            # Only support cross-tabulation for questions with options
            if (hasattr(question1.question_type, 'has_options') and question1.question_type.has_options and
                hasattr(question2.question_type, 'has_options') and question2.question_type.has_options):
                
                options1 = question1.get_options()
                options2 = question2.get_options()
                
                cross_tab_data = {
                    'question1': question1,
                    'question2': question2,
                    'options1': options1,
                    'options2': options2,
                    'data': []
                }
                
                # Calculate counts for each combination
                for option1 in options1:
                    row_data = []
                    for option2 in options2:
                        # Find responses that selected both options
                        count = Response.objects.filter(
                            survey=survey,
                            is_complete=True
                        ).filter(
                            # Utiliser Q objects pour éviter les conflits sur answers__question
                            Q(answers__question=question1, answers__selected_options=option1) &
                            Q(answers__question=question2, answers__selected_options=option2)
                        ).distinct().count()
                        row_data.append(count)
                    cross_tab_data['data'].append(row_data)
        except (Survey.DoesNotExist, ValueError):
            messages.error(request, _("Invalid questions selected for cross-tabulation."))
    
    return render(request, 'surveys/survey_results.html', {
        'survey': survey,
        'questions': questions,
        'total_responses': total_responses,
        'complete_responses': complete_responses,
        'completion_rate': completion_rate,
        'date_filter': date_filter,
        'start_date': start_date.strftime('%Y-%m-%d') if start_date else '',
        'end_date': end_date.strftime('%Y-%m-%d') if end_date else '',
        'trend_data': trend_data,
        'cross_tab_data': cross_tab_data
    })

@login_required
def save_progress(request, pk):
    """
    Vue pour sauvegarder les progrès d'une enquête en cours sans la marquer comme complète.
    Utile pour les longues enquêtes où l'utilisateur peut vouloir revenir plus tard.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': _("Only POST requests are allowed.")}, status=400)
    
    survey = get_object_or_404(Survey, pk=pk)
    
    # Vérifier si l'enquête permet de sauvegarder et continuer
    if not survey.allow_save_and_continue:
        return JsonResponse({
            'status': 'error', 
            'message': _("This survey does not allow saving progress.")
        }, status=400)
    
    # Vérifier si l'enquête est active
    now = timezone.now()
    if survey.start_date and survey.start_date > now:
        return JsonResponse({
            'status': 'error', 
            'message': _("This survey is not open yet.")
        }, status=400)
    
    if survey.end_date and survey.end_date < now:
        return JsonResponse({
            'status': 'error', 
            'message': _("This survey is closed.")
        }, status=400)
    
    # Récupérer ou créer la réponse
    response_id = request.POST.get('response_id')
    
    if response_id:
        # Vérifier que la réponse appartient bien à l'utilisateur courant
        response = get_object_or_404(
            Response, 
            pk=response_id, 
            survey=survey,
            respondent=request.user
        )
    else:
        # Créer une nouvelle réponse
        response = Response.objects.create(
            survey=survey,
            respondent=request.user,
            is_complete=False
        )
    
    # Enregistrer les réponses soumises jusqu'à présent
    questions_answered = []
    
    # Récupérer les questions soumises (format: question_123=value)
    for key, value in request.POST.items():
        if key.startswith('question_') and key != 'response_id':
            try:
                question_id = int(key.split('_')[1])
                question = Question.objects.get(id=question_id, survey=survey)
                
                # Supprimer toute réponse existante pour cette question
                Answer.objects.filter(question=question, response=response).delete()
                
                # Si la question a des options (choix unique ou multiple)
                if hasattr(question.question_type, 'has_options') and question.question_type.has_options:
                    if question.question_type.name in ['checkbox', 'multiple_select']:
                        # Pour les choix multiples, la valeur est une liste
                        option_ids = request.POST.getlist(key)
                        if option_ids:
                            answer = Answer.objects.create(
                                question=question,
                                response=response
                            )
                            for option_id in option_ids:
                                option = QuestionOption.objects.get(pk=option_id)
                                answer.selected_options.add(option)
                            questions_answered.append(question_id)
                    else:
                        # Pour un choix unique
                        option_id = value
                        if option_id:
                            answer = Answer.objects.create(
                                question=question,
                                response=response
                            )
                            option = QuestionOption.objects.get(pk=option_id)
                            answer.selected_options.add(option)
                            questions_answered.append(question_id)
                else:
                    # Pour les questions de texte
                    text_value = value.strip()
                    if text_value:
                        Answer.objects.create(
                            question=question,
                            response=response,
                            text_answer=text_value
                        )
                        questions_answered.append(question_id)
            except (ValueError, Question.DoesNotExist, QuestionOption.DoesNotExist):
                # Ignorer les clés qui ne correspondent pas à des questions valides
                pass
    
    # Mettre à jour la date de dernière modification
    response.updated_at = timezone.now()
    response.save()
    
    # Si la requête attend une réponse JSON (AJAX)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': _("Your progress has been saved."),
            'response_id': response.id,
            'questions_answered': questions_answered
        })
    
    # Sinon, rediriger avec un message
    messages.success(request, _("Your progress has been saved. You can continue later."))
    return redirect('surveys:take_survey', pk=survey.pk)

@login_required
def export_survey_csv(request, pk):
    """View for exporting survey results to CSV"""
    survey = get_object_or_404(Survey, pk=pk)
    
    # Check if user has permission to view results
    if survey.creator != request.user:
        # Check if user has permission via share
        try:
            share = SurveyShare.objects.get(
                survey=survey,
                shared_with=request.user,
                can_view_results=True,
                accepted=True
            )
        except SurveyShare.DoesNotExist:
            messages.error(request, _("You don't have permission to export the results of this survey"))
            return redirect('surveys:detail', pk=survey.pk)
    
    # Apply date filters if provided
    date_filter = request.GET.get('date_filter', 'all')
    start_date = None
    end_date = None
    
    # Apply the same date filtering logic as in survey_results
    # (Code omitted for brevity - copy from survey_results)
    
    # Filter responses based on date range
    responses = survey.responses.filter(is_complete=True)
    if start_date:
        responses = responses.filter(created_at__gte=start_date)
    if end_date:
        responses = responses.filter(created_at__lte=end_date)
    
    # Use the utility function to export
    return export_survey_to_csv(survey, responses)

@login_required
def export_survey_excel(request, pk):
    """View for exporting survey results to Excel"""
    survey = get_object_or_404(Survey, pk=pk)
    
    # Check if user has permission to view results
    if survey.creator != request.user:
        # Check if user has permission via share
        try:
            share = SurveyShare.objects.get(
                survey=survey,
                shared_with=request.user,
                can_view_results=True,
                accepted=True
            )
        except SurveyShare.DoesNotExist:
            messages.error(request, _("You don't have permission to export the results of this survey"))
            return redirect('surveys:detail', pk=survey.pk)
    
    # Apply date filters if provided
    date_filter = request.GET.get('date_filter', 'all')
    start_date = None
    end_date = None
    
    # Apply the same date filtering logic as in survey_results
    # (Code omitted for brevity - copy from survey_results)
    
    # Filter responses based on date range
    responses = survey.responses.filter(is_complete=True)
    if start_date:
        responses = responses.filter(created_at__gte=start_date)
    if end_date:
        responses = responses.filter(created_at__lte=end_date)
    
    # Use the utility function to export
    return export_survey_to_excel(survey, responses)

def survey_completed(request, pk):
    """
    Vue pour afficher une page de confirmation après avoir complété une enquête.
    Cette fonction est appelée après la soumission réussie d'une enquête.
    """
    survey = get_object_or_404(Survey, pk=pk)
    
    # Vérifier si l'enquête existe et est active
    now = timezone.now()
    if survey.start_date and survey.start_date > now:
        messages.error(request, _("This survey is not open yet."))
        return redirect('surveys:list')
    
    if survey.end_date and survey.end_date < now:
        messages.error(request, _("This survey is closed."))
        return redirect('surveys:list')
    
    # Vérifier si l'utilisateur a complété l'enquête
    user_completed = False
    
    if request.user.is_authenticated:
        # Pour un utilisateur authentifié, vérifier s'il a une réponse complète
        user_completed = Response.objects.filter(
            survey=survey,
            respondent=request.user,
            is_complete=True
        ).exists()
    else:
        # Pour un utilisateur anonyme, vérifier via la session
        completed_surveys = request.session.get('completed_surveys', [])
        user_completed = str(pk) in completed_surveys
    
    # Si l'utilisateur n'a pas complété l'enquête, rediriger vers la page de l'enquête
    if not user_completed and not survey.allow_anonymous:
        messages.info(request, _("You must complete the survey to see this page."))
        return redirect('surveys:take_survey', pk=survey.pk)

    # Statistiques pour la page de remerciement
    total_responses = survey.responses.count()
    complete_responses = survey.responses.filter(is_complete=True).count()
    completion_rate = int((complete_responses / total_responses * 100) if total_responses > 0 else 0)
    questions_count = survey.get_questions().count()
    
    return render(request, 'surveys/survey_completed.html', {
        'survey': survey,
        'custom_message': survey.success_message,
        'total_responses': total_responses,
        'complete_responses': complete_responses,
        'completion_rate': completion_rate,
        'questions_count': questions_count,
    })

# Ajout de la fonction submit_survey manquante
@login_required
def submit_survey(request, pk):
    """
    Vue pour soumettre les réponses à une enquête
    Cette fonction est une alternative à la méthode post de TakeSurveyView
    """
    survey = get_object_or_404(Survey, pk=pk)
    
    if request.method != 'POST':
        messages.error(request, _("Invalid request method. Please use the survey form."))
        return redirect('surveys:take_survey', pk=survey.pk)
    
    # Vérifier si l'enquête est active
    now = timezone.now()
    if survey.start_date and survey.start_date > now:
        messages.error(request, _("This survey is not open yet."))
        return redirect('surveys:list')
    
    if survey.end_date and survey.end_date < now:
        messages.error(request, _("This survey is closed."))
        return redirect('surveys:list')
    
    # Vérifier si le nombre maximal de réponses est atteint
    if survey.max_responses and survey.responses.filter(is_complete=True).count() >= survey.max_responses:
        messages.error(request, _("This survey has reached its maximum number of responses."))
        return redirect('surveys:list')
    
    # Vérifier le code d'accès si défini
    if survey.access_code and survey.access_code != request.POST.get('access_code'):
        messages.error(request, _("Invalid access code."))
        return redirect('surveys:take_survey', pk=survey.pk)
    
    # Récupérer ou créer la réponse
    response_id = request.POST.get('response_id')
    
    if response_id:
        # Vérifier que la réponse appartient bien à l'utilisateur courant ou est anonyme
        response = get_object_or_404(
            Response, 
            pk=response_id, 
            survey=survey
        )
        # Vérifier que l'utilisateur est autorisé à soumettre cette réponse
        if response.respondent and response.respondent != request.user:
            messages.error(request, _("You are not authorized to submit this response."))
            return redirect('surveys:take_survey', pk=survey.pk)
    else:
        # Créer une nouvelle réponse
        response = Response.objects.create(
            survey=survey,
            respondent=request.user if request.user.is_authenticated and not survey.allow_anonymous else None,
            is_complete=False
        )
    
    # Recueillir les questions et réponses
    questions = survey.get_questions()
    valid_response = True
    error_message = None

    for question in questions:
        is_required = getattr(question, 'required', False)
        question_key = f'question_{question.id}'
        answer_data = None
        # Si la question a des options
        if hasattr(question.question_type, 'has_options') and question.question_type.has_options:
            if question.question_type.name in ['radio', 'dropdown']:
                answer_data = request.POST.get(question_key)
            elif question.question_type.name in ['checkbox', 'multiple_select']:
                answer_data = request.POST.getlist(question_key)
        else:
            answer_data = request.POST.get(question_key, '').strip()

        # Validation obligatoire
        if is_required and (not answer_data or (isinstance(answer_data, list) and not any(answer_data))):
            valid_response = False
            error_message = _("Veuillez répondre à toutes les questions obligatoires.")
            break
        try:
            if answer_data:
                response.set_answer(question, answer_data)
        except Exception as e:
            valid_response = False
            error_message = str(e)
            break

    # Si la réponse est valide, la marquer comme complète
    if valid_response:
        response.is_complete = True
        response.completed_at = timezone.now()
        response.save()
        messages.success(request, survey.success_message or _("Merci d'avoir complété ce sondage !"))
        return redirect('surveys:survey_completed', pk=survey.pk)
    # Sinon, retourner au formulaire avec les réponses déjà saisies
    if error_message:
        messages.error(request, error_message)
    return redirect('surveys:take_survey', pk=survey.pk)