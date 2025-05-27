from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Survey, Answer, SurveyShare, Response, Question, QuestionOption

class SurveyForm(forms.ModelForm):
    class Meta:
        model = Survey
        fields = [
            'title', 'description', 'is_public', 'allow_anonymous',
            'start_date', 'end_date', 'access_code', 'max_responses',
            'theme', 'success_message', 'redirect_url', 'show_progress',
            'randomize_questions', 'one_question_per_page', 'allow_save_and_continue'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'required': False, 'class': 'form-control'}),
            'access_code': forms.TextInput(attrs={'class': 'form-control'}),
            'max_responses': forms.NumberInput(attrs={'class': 'form-control'}),
            'theme': forms.TextInput(attrs={'class': 'form-control'}), # Will be replaced with a color picker in JS
            'success_message': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'redirect_url': forms.URLInput(attrs={'class': 'form-control'}),
            'show_progress': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'randomize_questions': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'one_question_per_page': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_save_and_continue': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = [
            'text', 'help_text', 'question_type', 'required',
            'validation_regex', 'validation_message', 'min_value', 'max_value',
            'conditional_logic'
        ]
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'help_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            'required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'validation_regex': forms.TextInput(attrs={'class': 'form-control'}),
            'validation_message': forms.TextInput(attrs={'class': 'form-control'}),
            'min_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'conditional_logic': forms.HiddenInput(),
        }
    
    def __init__(self, *args, survey=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.survey = survey

# Form for question options
class QuestionOptionForm(forms.ModelForm):
    class Meta:
        model = QuestionOption
        fields = ('text', 'order', 'is_default', 'image', 'extra_info')
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'extra_info': forms.TextInput(attrs={'class': 'form-control'}),
        }

# Mise à jour du formset avec le formulaire modifié
QuestionOptionFormSet = forms.inlineformset_factory(
    Question,
    QuestionOption,
    form=QuestionOptionForm,
    extra=3,
    can_delete=True
)

class SurveyShareForm(forms.ModelForm):
    class Meta:
        model = SurveyShare
        fields = ['shared_with', 'can_edit', 'can_view_results', 'can_delete', 'message']
        widgets = {
            'shared_with': forms.Select(attrs={'class': 'form-select'}),
            'can_edit': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_view_results': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_delete': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class SurveyFilterForm(forms.Form):
    STATUS_CHOICES = (
        ('', _('All')),
        ('active', _('Active')),
        ('upcoming', _('Upcoming')),
        ('closed', _('Closed')),
    )
    
    CREATOR_CHOICES = (
        ('', _('All')),
        ('mine', _('Created by me')),
        ('shared', _('Shared with me')),
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES, 
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    creator = forms.ChoiceField(
        choices=CREATOR_CHOICES, 
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )