"""
GLPO Backend - Constraint Repositories (Time & Resource)
"""
from app.models import ProjectConstraintTime, ProjectConstraintResource
from app.repositories.base import BaseRepository
from app.schemas import ConstraintTimeBase, ConstraintResourceBase

class ConstraintTimeRepository(BaseRepository[ProjectConstraintTime, ConstraintTimeBase, ConstraintTimeBase]):
    pass

class ConstraintResourceRepository(BaseRepository[ProjectConstraintResource, ConstraintResourceBase, ConstraintResourceBase]):
    pass

time_repo = ConstraintTimeRepository(ProjectConstraintTime)
resource_repo = ConstraintResourceRepository(ProjectConstraintResource)
