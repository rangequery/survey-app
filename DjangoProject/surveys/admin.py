from django.contrib import admin
from .models import (
    Survey, Question, QuestionType, QuestionOption, 
    Response, Answer, SurveyShare, SurveyStatistics
)

class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 1

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'survey', 'question_type', 'required', 'order')
    list_filter = ('survey', 'question_type', 'required')
    search_fields = ('text',)
    inlines = [QuestionOptionInline]

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    show_change_link = True

class SurveyAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'created_at', 'is_public', 'is_active', 'response_count')
    list_filter = ('is_public', 'creator')
    search_fields = ('title', 'description')
    inlines = [QuestionInline]
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ('question', 'data')
    can_delete = False

class ResponseAdmin(admin.ModelAdmin):
    list_display = ('survey', 'respondent', 'created_at', 'is_complete', 'completion_time')
    list_filter = ('survey', 'is_complete')
    date_hierarchy = 'created_at'
    readonly_fields = ('survey', 'respondent', 'ip_address', 'user_agent', 'completion_time')
    inlines = [AnswerInline]

class SurveyShareAdmin(admin.ModelAdmin):
    list_display = ('survey', 'shared_by', 'shared_with', 'can_edit', 'can_view_results', 'accepted')
    list_filter = ('can_edit', 'can_view_results', 'accepted')

class QuestionTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'has_options', 'has_multiple_answers', 'template_name')

admin.site.register(Survey, SurveyAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(QuestionType, QuestionTypeAdmin)
admin.site.register(Response, ResponseAdmin)
admin.site.register(SurveyShare, SurveyShareAdmin)
admin.site.register(SurveyStatistics)