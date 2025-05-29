from sqlalchemy import create_engine, Column, String, Boolean, Float, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Create base class for declarative models
Base = declarative_base()

class Doctor(Base):
    """SQLAlchemy model for doctor information"""
    
    __tablename__ = 'doctors'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    specialty = Column(String, nullable=True)
    profile_url = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    location = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    has_multiple_locations = Column(Boolean, default=False)
    is_employed_provider = Column(Boolean, default=False)
    is_accepting_new_patients = Column(Boolean, default=False)
    rating = Column(Float, default=0)
    rating_count = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<Doctor(name='{self.name}', specialty='{self.specialty}')>"

# Default PostgreSQL connection string based on docker-compose.yml
DEFAULT_DB_URI = "postgresql://postgres:postgres@localhost:5432/andalusia_doctors"

# Database setup function
def init_db(db_uri=DEFAULT_DB_URI):
    """Initialize the database connection and create tables if they don't exist"""
    engine = create_engine(db_uri)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

# Create a session factory to get a new session when needed
def get_session(db_uri=DEFAULT_DB_URI):
    """Get a new session for database operations"""
    engine = create_engine(db_uri)
    Session = sessionmaker(bind=engine)
    return Session()

def save_doctor(doctor_data, db_uri=DEFAULT_DB_URI):
    """
    Save a doctor to the database.
    
    Args:
        doctor_data (dict): Dictionary containing doctor information
        db_uri (str): Database connection string
    
    Returns:
        int: The ID of the saved doctor
    """
    session = get_session(db_uri)
    
    # Check if doctor with same profile_url already exists
    existing = None
    if 'profile_url' in doctor_data and doctor_data['profile_url']:
        existing = session.query(Doctor).filter_by(profile_url=doctor_data['profile_url']).first()
    
    if existing:
        # Update existing doctor
        for key, value in doctor_data.items():
            if hasattr(existing, key):
                setattr(existing, key, value)
        doctor = existing
    else:
        # Create new doctor
        doctor = Doctor(**doctor_data)
        session.add(doctor)
    
    session.commit()
    doctor_id = doctor.id
    session.close()
    
    return doctor_id

def get_all_doctors(db_uri=DEFAULT_DB_URI):
    """
    Retrieve all doctors from the database.
    
    Args:
        db_uri (str): Database connection string
    
    Returns:
        list: List of Doctor objects
    """
    session = get_session(db_uri)
    doctors = session.query(Doctor).all()
    session.close()
    return doctors

def get_doctor_by_id(doctor_id, db_uri=DEFAULT_DB_URI):
    """
    Retrieve a doctor by ID.
    
    Args:
        doctor_id (int): The ID of the doctor to retrieve
        db_uri (str): Database connection string
    
    Returns:
        Doctor: Doctor object if found, None otherwise
    """
    session = get_session(db_uri)
    doctor = session.query(Doctor).filter_by(id=doctor_id).first()
    session.close()
    return doctor

