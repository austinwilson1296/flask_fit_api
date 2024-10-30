from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import DeclarativeBase
from flask_sqlalchemy import SQLAlchemy



class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)

class ExerciseCategory(db.Model):
    __tablename__ = 'exercise_category'  # Specify the table name

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # Define the primary key
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # Unique name with a max length
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # Unique category with a max length
    subcategory: Mapped[str] = mapped_column(String(50), nullable=True)  # Nullable subcategory with a max length

    def __repr__(self):
        return f'<ExerciseCategory id={self.id}, name={self.name}, category={self.category}, subcategory={self.subcategory}>'
    

class Exercise(db.Model):
    __tablename__ = 'exercise'  # Specify the table name

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # Define the primary key
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # Unique name with a max length
    
    # Correct ForeignKey definition; specify the target column explicitly
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('exercise_category.id'), nullable=False)  # Foreign key reference to exercise_category.id

    # Establish a relationship with ExerciseCategory
    category: Mapped[ExerciseCategory] = relationship("ExerciseCategory", backref="exercises")

    def __repr__(self):
        return f'<Exercise id={self.id}, name={self.name}, category_id={self.category_id}>'