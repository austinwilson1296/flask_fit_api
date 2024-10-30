from flask import Blueprint, request, render_template, render_template_string
import random
from sqlalchemy import func
from models import db, Exercise, ExerciseCategory

# Define the blueprint
workout_gen = Blueprint('workout_gen', __name__)

@workout_gen.route('/<string:level>/<string:group>', methods=['GET'])
def randomize(level, group):
    # Query for a random exercise based on level and group
    exercise = db.session.query(Exercise).join(ExerciseCategory).filter(
        (ExerciseCategory.name == group) | (ExerciseCategory.subcategory == group)
    ).order_by(func.random()).first()

    # Return the exercise name if found, otherwise a default message
    if exercise:
        return exercise.name
    else:
        return "No exercises found"


#Route to add randomized items to list

@workout_gen.route('/add-to-list', methods=['POST'])
def add_to_list():
    # Retrieve the exercise name sent by HTMX
    exercise = request.form.get('generated-exercise', "No exercise generated")

    # Render and return the exercise wrapped in an <li> element to append to the workout list
    return render_template_string(
        '<li>{{ exercise }}</li>',
        exercise=exercise
    )


#Render partial templates for selection of workout level/type...


@workout_gen.route('/experience-level/<string:level>', methods=['GET'])
def experience_level(level):
    # Set up template path based on the level
    upper_level = level.title()
    template_name = f'partials/modals/experience_level_{level}.html'
    context = {'level': upper_level}
    
    # Render the specified template for experience level
    return render_template(template_name, **context)


@workout_gen.route('/get_selection', methods=['POST'])
def selection():
    # Extract form data
    level = request.form.get('experience_level')    
    workout_type = request.form.get('workout_type')
    warm_up = request.form.get('warm_up') == 'on'
    
    # Render the next partial template based on the submitted data
    # For example, replace 'workout_template' with your actual template name
    return render_template(f'partials/wtemps/{workout_type}.html', level=level, workout_type=workout_type, warm_up=warm_up)


    

    



