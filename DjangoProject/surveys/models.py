from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.urls import reverse
from django.core.exceptions import ValidationError
import uuid
import json
import re

class TimeStampedModel(models.Model):
    """Base model with created and modified timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class QuestionType(models.Model):
    """Model representing different types of questions"""
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    has_options = models.BooleanField(default=False)
    has_multiple_answers = models.BooleanField(default=False)
    template_name = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return self.name

    @classmethod
    def get_default_types(cls):
        """Create default question types if they don't exist"""
        defaults = [
            {
                'name': 'text',
                'description': 'Short text answer',
                'has_options': False,
                'has_multiple_answers': False,
                'template_name': 'questions/text.html'
            },
            {
                'name': 'textarea',
                'description': 'Long text answer',
                'has_options': False,
                'has_multiple_answers': False,
                'template_name': 'questions/textarea.html'
            },
            {
                'name': 'radio',
                'description': 'Single choice from multiple options',
                'has_options': True,
                'has_multiple_answers': False,
                'template_name': 'questions/radio.html'
            },
            {
                'name': 'checkbox',
                'description': 'Multiple choices from multiple options',
                'has_options': True,
                'has_multiple_answers': True,
                'template_name': 'questions/checkbox.html'
            },
            {
                'name': 'dropdown',
                'description': 'Single choice from dropdown',
                'has_options': True,
                'has_multiple_answers': False,
                'template_name': 'questions/dropdown.html'
            },
            {
                'name': 'rating',
                'description': 'Rating on a scale',
                'has_options': True,
                'has_multiple_answers': False,
                'template_name': 'questions/rating.html'
            },
            {
                'name': 'date',
                'description': 'Date selection',
                'has_options': False,
                'has_multiple_answers': False,
                'template_name': 'questions/date.html'
            },
        ]
        
        for default in defaults:
            cls.objects.get_or_create(name=default['name'], defaults=default)

class Survey(TimeStampedModel):
    """Model representing a survey"""
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_surveys')
    is_public = models.BooleanField(default=True)
    allow_anonymous = models.BooleanField(default=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    access_code = models.CharField(max_length=20, blank=True, null=True)
    max_responses = models.PositiveIntegerField(null=True, blank=True)
    
    # Advanced features
    theme = models.JSONField(default=dict, blank=True)
    success_message = models.TextField(blank=True, default=_("Thank you for completing this survey!"))
    redirect_url = models.URLField(blank=True, null=True)
    show_progress = models.BooleanField(default=True)
    randomize_questions = models.BooleanField(default=False)
    one_question_per_page = models.BooleanField(default=False)
    allow_save_and_continue = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = _("Survey")
        verbose_name_plural = _("Surveys")
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('survey:detail', kwargs={'pk': self.pk})
    
    def is_active(self):
        now = timezone.now()
        if self.end_date and now > self.end_date:
            return False
        if now < self.start_date:
            return False
        if self.max_responses and self.response_count >= self.max_responses:
            return False
        return True
    
    @property
    def response_count(self):
        return self.responses.count()
    
    @property
    def completion_rate(self):
        """Calculate the completion rate of the survey"""
        total = self.responses.count()
        if total == 0:
            return 0
        completed = self.responses.filter(is_complete=True).count()
        return int((completed / total) * 100)
    
    def get_questions(self):
        """Get questions in the correct order"""
        questions = self.questions.all()
        if self.randomize_questions:
            return questions.order_by('?')
        return questions.order_by('order')
    
    def clean(self):
        """Validate survey data"""
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError(_("End date cannot be before start date"))

class Question(TimeStampedModel):
    """Model representing a question in a survey"""
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    help_text = models.TextField(blank=True)
    question_type = models.ForeignKey(QuestionType, on_delete=models.PROTECT)
    order = models.PositiveIntegerField(default=0)
    required = models.BooleanField(default=True)
    
    # Advanced features
    validation_regex = models.CharField(max_length=500, blank=True)
    validation_message = models.CharField(max_length=255, blank=True)
    min_value = models.IntegerField(null=True, blank=True)
    max_value = models.IntegerField(null=True, blank=True)
    conditional_logic = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.text[:50]
    
    def get_options(self):
        """Get options in the correct order"""
        return self.options.order_by('order')
    
    def validate_answer(self, answer_data):
        """Validate an answer against this question's rules"""
        if self.required and not answer_data:
            return False, _("This question is required")
        
        if self.question_type.has_options:
            # For option-based questions
            if self.question_type.has_multiple_answers:
                # Multiple selection
                if not isinstance(answer_data, list):
                    return False, _("Invalid answer format")
                
                valid_options = set(self.options.values_list('id', flat=True))
                for option_id in answer_data:
                    if option_id not in valid_options:
                        return False, _("Invalid option selected")
            else:
                # Single selection
                if not self.options.filter(id=answer_data).exists():
                    return False, _("Invalid option selected")
        else:
            # For text-based questions
            if self.validation_regex and not re.match(self.validation_regex, answer_data):
                return False, self.validation_message or _("Answer format is invalid")
            
            if self.min_value is not None and float(answer_data) < self.min_value:
                return False, _("Value must be at least {}").format(self.min_value)
                
            if self.max_value is not None and float(answer_data) > self.max_value:
                return False, _("Value must be at most {}").format(self.max_value)
        
        return True, ""

class QuestionOption(TimeStampedModel):
    """Model representing an option for a question"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)
    is_default = models.BooleanField(default=False)
    
    # Advanced features
    image = models.ImageField(upload_to='option_images/', blank=True, null=True)
    extra_info = models.TextField(blank=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.text

class Response(TimeStampedModel):
    """Model representing a response to a survey"""
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='responses')
    respondent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='survey_responses')
    is_complete = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    completion_time = models.DurationField(null=True, blank=True)
    
    # For partial responses
    resume_token = models.UUIDField(default=uuid.uuid4, editable=False)
    last_page = models.PositiveIntegerField(default=1)
    
    class Meta:
        verbose_name = _("Response")
        verbose_name_plural = _("Responses")
    
    def __str__(self):
        return f"Response to {self.survey.title} ({self.created_at})"
    
    def get_answers(self):
        """Get all answers for this response"""
        return self.answers.all()
    
    def set_answer(self, question, answer_data):
        """Set or update an answer for a question"""
        # Validate the answer
        is_valid, message = question.validate_answer(answer_data)
        if not is_valid:
            raise ValidationError(message)
        
        # Create or update the answer
        answer, created = Answer.objects.update_or_create(
            response=self,
            question=question,
            defaults={'data': json.dumps(answer_data) if isinstance(answer_data, (dict, list)) else answer_data}
        )
        
        # Handle options for option-based questions
        if question.question_type.has_options:
            # Clear existing options
            answer.selected_options.clear()
            
            # Add new options
            if question.question_type.has_multiple_answers:
                # Multiple selection
                for option_id in answer_data:
                    option = QuestionOption.objects.get(id=option_id, question=question)
                    answer.selected_options.add(option)
            else:
                # Single selection
                option = QuestionOption.objects.get(id=answer_data, question=question)
                answer.selected_options.add(option)
        
        return answer

class Answer(TimeStampedModel):
    """Model representing an answer to a question"""
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    data = models.TextField(blank=True)
    selected_options = models.ManyToManyField(QuestionOption, blank=True, related_name='answers')
    
    class Meta:
        unique_together = ('response', 'question')
    
    def __str__(self):
        return f"Answer to {self.question.text[:30]}"
    
    @property
    def value(self):
        """Return the answer value in the appropriate format"""
        if self.question.question_type.has_options:
            if self.question.question_type.has_multiple_answers:
                return list(self.selected_options.values('id', 'text'))
            else:
                option = self.selected_options.first()
                return option.id if option else None
        else:
            try:
                return json.loads(self.data)
            except (json.JSONDecodeError, TypeError):
                return self.data

class SurveyShare(TimeStampedModel):
    """Model for sharing surveys with other users"""
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='shares')
    shared_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_surveys')
    shared_with = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_surveys')
    can_edit = models.BooleanField(default=False)
    can_view_results = models.BooleanField(default=True)
    can_delete = models.BooleanField(default=False)
    message = models.TextField(blank=True)
    accepted = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('survey', 'shared_with')
    
    def __str__(self):
        return f"{self.survey.title} shared with {self.shared_with.username}"

class SurveyStatistics(TimeStampedModel):
    """Model for storing pre-calculated survey statistics"""
    survey = models.OneToOneField(Survey, on_delete=models.CASCADE, related_name='statistics')
    total_responses = models.PositiveIntegerField(default=0)
    complete_responses = models.PositiveIntegerField(default=0)
    average_completion_time = models.DurationField(null=True, blank=True)
    question_stats = models.JSONField(default=dict)
    
    def __str__(self):
        return f"Statistics for {self.survey.title}"
    
    def update(self):
        """Update the statistics"""
        responses = self.survey.responses.all()
        self.total_responses = responses.count()
        self.complete_responses = responses.filter(is_complete=True).count()
        
        # Calculate average completion time
        complete_times = [r.completion_time for r in responses if r.completion_time]
        if complete_times:
            total_seconds = sum(t.total_seconds() for t in complete_times)
            self.average_completion_time = timezone.timedelta(seconds=total_seconds / len(complete_times))
        
        # Calculate per-question statistics
        question_stats = {}
        for question in self.survey.questions.all():
            answers = Answer.objects.filter(question=question, response__survey=self.survey)
            
            if question.question_type.has_options:
                # For option-based questions, count selections
                option_counts = {}
                for option in question.options.all():
                    count = option.answers.filter(response__survey=self.survey).count()
                    option_counts[str(option.id)] = {
                        'text': option.text,
                        'count': count,
                        'percentage': round((count / max(1, answers.count())) * 100, 1)
                    }
                
                question_stats[str(question.id)] = {
                    'text': question.text,
                    'type': question.question_type.name,
                    'answer_count': answers.count(),
                    'options': option_counts
                }
            else:
                # For text-based questions, provide basic stats
                question_stats[str(question.id)] = {
                    'text': question.text,
                    'type': question.question_type.name,
                    'answer_count': answers.count()
                }
        
        self.question_stats = question_stats
        self.save()