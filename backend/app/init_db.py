import sys
import os

# Add the backend directory to sys.path so app is importable
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from app.database import Base, engine
# Import all models to ensure they are registered on the Base metadata
from app.models import Product, ComplianceRequest, SupplierDocument, AuditLogPlaceholder

def init_db():
    print("Initializing database and compiling models...")
    Base.metadata.create_all(bind=engine)
    print("All tables compiled and created successfully in SQLite database.")

if __name__ == "__main__":
    init_db()
