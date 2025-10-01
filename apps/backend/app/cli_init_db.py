from .database import engine
from .models import Base

Base.metadata.create_all(bind=engine)
print("Created tables (if missing).")