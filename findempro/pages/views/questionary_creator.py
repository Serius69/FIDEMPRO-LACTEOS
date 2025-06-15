"""
views/questionary_creator.py - Creación de preguntas y respuestas
"""
import logging

from questionary.models import Questionary, Question
from variable.models import Variable

logger = logging.getLogger(__name__)


def create_and_save_questions(questionary: Questionary) -> None:
    """
    Crear preguntas para un cuestionario
    """
    try:
        from questionary.data.questionary_test_data import question_data
        
        created_questions = []
        
        for data in question_data:
            if not all([data.get('question'), data.get('type'), data.get('initials_variable')]):
                logger.warning(f"Skipping question with incomplete data: {data}")
                continue
                
            try:
                variable = Variable.objects.get(
                    initials=data['initials_variable'],
                    fk_product=questionary.fk_product
                )
            except Variable.DoesNotExist:
                logger.error(
                    f"Variable with initials '{data['initials_variable']}' not found "
                    f"for product {questionary.fk_product.id}"
                )
                continue
            except Variable.MultipleObjectsReturned:
                variable = Variable.objects.filter(
                    initials=data['initials_variable'],
                    fk_product=questionary.fk_product
                ).first()

            # Solo agregar possible_answers si el tipo no es 1 (respuesta abierta)
            possible_answers = data.get('possible_answers') if data['type'] != 1 else None
                
            question = Question.objects.create(
                question=data['question'],
                type=data['type'],
                fk_questionary=questionary,
                fk_variable=variable,
                possible_answers=possible_answers,
                is_active=True
            )
            created_questions.append(question)
            
        logger.info(f"{len(created_questions)} questions created for questionary {questionary.id}")
            
    except Exception as e:
        logger.error(f"Error creating questions for questionary {questionary.id}: {str(e)}")
        raise