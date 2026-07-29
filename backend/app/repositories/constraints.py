"""
GLPO Backend - Constraint Repositories (Time & Resource)
"""
from app.models import ProjectCalendar, Resource
from app.repositories.base import BaseRepository
from app.schemas import ConstraintTimeBase, ConstraintResourceBase

class ConstraintTimeRepository(BaseRepository[ProjectCalendar, ConstraintTimeBase, ConstraintTimeBase]):
    pass

class ConstraintResourceRepository(BaseRepository[Resource, ConstraintResourceBase, ConstraintResourceBase]):
    pass

time_repo = ConstraintTimeRepository(ProjectCalendar)
resource_repo = ConstraintResourceRepository(Resource)
