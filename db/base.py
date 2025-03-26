# This file is for alembic

# Import all the models, so that Base has them before being
# imported by Alembic

from .database import Base
from api.v1.summarization.model import TextData



