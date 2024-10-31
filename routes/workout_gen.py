from flask import Blueprint, request, render_template, jsonify, current_app
from sqlalchemy import func
from typing import List, Optional, Tuple
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



def get_unique_exercise_sequence(
    categories: List[str], 
    exclude_exercise_ids: List[int] = None
) -> Tuple[List[Optional[Exercise]], List[int]]:
    """
    Get a sequence of unique exercises following a specific category order.
    
    Args:
        categories (List[str]): List of category names in desired sequence order
        exclude_exercise_ids (List[int], optional): List of exercise IDs to exclude
        
    Returns:
        Tuple of (List[Optional[Exercise]], List[int]): 
        - Exercises in the specified sequence
        - IDs of selected exercises
    """
    try:
        # If no exclusion list provided, start with an empty list
        exclude_exercise_ids = exclude_exercise_ids or []

        # Create a query to get random exercises for each category
        base_query = (
            db.session.query(
                Exercise.id,
                Exercise.name,
                ExerciseCategory.name.label('category_name'),
                func.row_number().over(
                    partition_by=ExerciseCategory.name,
                    order_by=func.random()
                ).label('rn')
            )
            .join(Exercise.category)
            .filter(ExerciseCategory.name.in_(categories))
        )

        # Add exclusion filter if we have excluded IDs
        if exclude_exercise_ids:
            base_query = base_query.filter(~Exercise.id.in_(exclude_exercise_ids))

        # Convert to CTE
        random_exercises = base_query.cte()

        # Query to get one random exercise per category
        exercise_pool = (
            db.session.query(Exercise)
            .join(random_exercises, Exercise.id == random_exercises.c.id)
            .filter(random_exercises.c.rn == 1)
            .all()
        )

        # Create a mapping of category name to exercise
        exercise_map = {
            ex.category.name: ex for ex in exercise_pool
        }

        # Build the final sequence maintaining the original order
        sequence = [exercise_map.get(category) for category in categories]

        # Collect IDs of exercises in this sequence
        new_excluded_ids = [ex.id for ex in sequence if ex is not None]

        return sequence, new_excluded_ids
        
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Error fetching exercise sequence: {str(e)}")

@workout_gen.route('/get_selection', methods=['POST'])
def selection():
    try:
        # Extract form data
        level = request.form.get('experience_level')    
        workout_type = request.form.get('workout_type')
        warm_up = request.form.get('warm_up') == 'on'
        cool_down = request.form.get('cool_down') == 'on'

        # Define the specific list of subcategories in desired sequence for warmup
        warmup_categories = [
            "Core_hip_legs",
            "Core_spinal",
            "Thoracic_spine_mobility",
            "Core_hip_legs",
            "Core_spinal",
            "Thoracic_spine_mobility",
            "Scapulo_thoracic",
            "Core_hip_legs",
            "Shoulder_scapula",
            "Thoracic_spine_mobility",
            "Core_hip_legs",
            "Shoulder_scapula"
        ]

        # Define cooldown categories (modify as needed)
        cooldown_categories = [
            "Core_hip_legs",
            "Core_spinal",
            "Thoracic_spine_mobility",
            "Core_hip_legs",
            "Core_spinal",
            "Thoracic_spine_mobility",
            "Scapulo_thoracic",
            "Core_hip_legs",
            "Shoulder_scapula",
            "Thoracic_spine_mobility",
            "Core_hip_legs",
            "Shoulder_scapula"
        ]

        # Initialize exercise lists
        warm_ex = []
        cool_ex = []
        excluded_ids = []

        # Get warmup exercises
        if warm_up:
            warm_ex, excluded_ids = get_unique_exercise_sequence(warmup_categories)

            # Get cooldown exercises, excluding warmup exercises
            if cool_down:
                cool_ex, _ = get_unique_exercise_sequence(
                    cooldown_categories, 
                    exclude_exercise_ids=excluded_ids
                )

        return render_template(
            f'partials/wtemps/{workout_type}.html', 
            level=level, 
            workout_type=workout_type, 
            warm_up=warm_up,
            cool_down=cool_down,
            warm_ex=warm_ex,
            cool_ex=cool_ex
        )
    
    except Exception as e:
        current_app.logger.error(f"Error in workout selection: {str(e)}")
        return jsonify({'error': 'Failed to generate workout'}), 500

    



