# Ajoutez ce code à votre fichier utils.py

import csv
from io import StringIO
import xlsxwriter
from io import BytesIO
from django.http import HttpResponse
from django.utils.translation import gettext as _


def export_survey_to_csv(survey, responses):
    """
    Exporte les résultats d'une enquête au format CSV.
    
    Args:
        survey: L'objet Survey à exporter
        responses: QuerySet des réponses à inclure
    
    Returns:
        HttpResponse avec le contenu CSV
    """
    # Créer une réponse HTTP avec le type MIME pour CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{survey.title}_results.csv"'
    
    # Créer le writer CSV
    writer = csv.writer(response)
    
    # Récupérer toutes les questions
    questions = survey.get_questions()
    
    # Écrire l'en-tête
    header = [_('Respondent ID'), _('Date')]
    for question in questions:
        header.append(question.text)
    writer.writerow(header)
    
    # Écrire les données
    for response_obj in responses:
        row = [
            response_obj.id,
            response_obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ]
        
        # Traiter chaque question
        for question in questions:
            # Récupérer la réponse à cette question
            try:
                answer = response_obj.answers.get(question=question)
                
                # Traiter différemment selon le type de question
                if hasattr(question.question_type, 'has_options') and question.question_type.has_options:
                    # Pour les questions à choix unique ou multiple
                    selected_options = answer.selected_options.all()
                    if selected_options:
                        row.append(", ".join([opt.text for opt in selected_options]))
                    else:
                        row.append("")
                else:
                    # Pour les questions de texte
                    row.append(answer.text_answer or "")
            except:
                # Si pas de réponse à cette question
                row.append("")
                
        writer.writerow(row)
    
    return response


def export_survey_to_excel(survey, responses):
    """
    Exporte les résultats d'une enquête au format Excel.
    
    Args:
        survey: L'objet Survey à exporter
        responses: QuerySet des réponses à inclure
    
    Returns:
        HttpResponse avec le contenu Excel
    """
    # Créer un buffer en mémoire
    output = BytesIO()
    
    # Créer un nouveau classeur Excel et ajouter une feuille
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet(_('Results'))
    
    # Ajouter des formats
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#4472C4',
        'color': 'white',
        'border': 1
    })
    
    cell_format = workbook.add_format({
        'border': 1
    })
    
    date_format = workbook.add_format({
        'border': 1,
        'num_format': 'yyyy-mm-dd hh:mm:ss'
    })
    
    # Récupérer toutes les questions
    questions = survey.get_questions()
    
    # Écrire l'en-tête
    headers = [_('Respondent ID'), _('Date')]
    for question in questions:
        headers.append(question.text)
        
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)
    
    # Écrire les données
    for row_idx, response_obj in enumerate(responses, start=1):
        worksheet.write(row_idx, 0, response_obj.id, cell_format)
        worksheet.write_datetime(row_idx, 1, response_obj.created_at, date_format)
        
        # Traiter chaque question
        for col_idx, question in enumerate(questions, start=2):
            # Récupérer la réponse à cette question
            try:
                answer = response_obj.answers.get(question=question)
                
                # Traiter différemment selon le type de question
                if hasattr(question.question_type, 'has_options') and question.question_type.has_options:
                    # Pour les questions à choix unique ou multiple
                    selected_options = answer.selected_options.all()
                    if selected_options:
                        worksheet.write(row_idx, col_idx, ", ".join([opt.text for opt in selected_options]), cell_format)
                    else:
                        worksheet.write(row_idx, col_idx, "", cell_format)
                else:
                    # Pour les questions de texte
                    worksheet.write(row_idx, col_idx, answer.text_answer or "", cell_format)
            except:
                # Si pas de réponse à cette question
                worksheet.write(row_idx, col_idx, "", cell_format)
    
    # Ajuster la largeur des colonnes
    for i, header in enumerate(headers):
        worksheet.set_column(i, i, max(len(header) * 1.2, 15))
    
    # Fermer le workbook
    workbook.close()
    
    # Préparer la réponse HTTP
    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{survey.title}_results.xlsx"'
    
    return response