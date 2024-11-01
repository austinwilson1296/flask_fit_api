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


@workout_gen.route('/select-category')
def select_category():
    category = request.args.get('category')
    return category or '', 200

@workout_gen.route('/generate-exercise', methods=['POST'])
def generate_exercise():
    category = request.form.get('selected-category-display')
    if category:
        exercise = Exercise.query.filter_by(category=category).order_by(func.random()).first()
        if exercise:
            return jsonify({
                'id': exercise.id,
                'name': exercise.name,
                'description': exercise.description
            })
    return jsonify({'error': 'No exercise found for this category'}), 404


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
    """
    try:
        exclude_exercise_ids = exclude_exercise_ids or []

        # Create a query to get multiple exercises for each category
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

        # Exclude specified exercises
        if exclude_exercise_ids:
            base_query = base_query.filter(~Exercise.id.in_(exclude_exercise_ids))

        random_exercises = base_query.cte()

        # Get all exercises in pool
        exercise_pool = (
            db.session.query(Exercise)
            .join(random_exercises, Exercise.id == random_exercises.c.id)
            .all()
        )

        # Map exercises by category
        exercise_map = {}
        for ex in exercise_pool:
            if ex.category.name not in exercise_map:
                exercise_map[ex.category.name] = []
            exercise_map[ex.category.name].append(ex)

        # Build sequence and exclude IDs list
        sequence = []
        new_excluded_ids = set(exclude_exercise_ids)

        for category in categories:
            available_exercises = [
                ex for ex in exercise_map.get(category, []) if ex.id not in new_excluded_ids
            ]
            if available_exercises:
                selected_exercise = available_exercises[0]  # Pick the first unique exercise
                sequence.append(selected_exercise)
                new_excluded_ids.add(selected_exercise.id)
            else:
                sequence.append(None)  # Handle case if no exercises are available

        return sequence, list(new_excluded_ids)
        
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

    



