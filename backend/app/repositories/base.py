"""
GLPO Backend - Base Repository (Helpers)
Cung cấp các hàm Helper (CRUD cơ bản, Phân trang) để tái sử dụng khi tương tác với Database.
"""
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import Select

from app.db.database import Base
from app.schemas.schemas import PaginatedResponse

# Định nghĩa Type Variables cho Generic Type Hinting
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Lớp Base Repository cung cấp các hàm trợ giúp (Helper) chuẩn tương tác với Database.
    Các lớp Repository cụ thể sẽ kế thừa từ lớp này.

    Attributes:
        model (Type[ModelType]): Lớp SQLAlchemy Model tương ứng (VD: AppProject).
    """

    def __init__(self, model: Type[ModelType]):
        """
        Khởi tạo BaseRepository.

        Args:
            model (Type[ModelType]): Lớp SQLAlchemy Model.
        """
        self.model = model

    async def get_by_id(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        Tìm kiếm một bản ghi dựa trên ID (Khóa chính).

        Args:
            db (AsyncSession): Phiên kết nối DB.
            id (Any): Khóa chính cần tìm.

        Returns:
            Optional[ModelType]: Đối tượng Model nếu tìm thấy, ngược lại là None.
        """
        result = await db.execute(select(self.model).filter(self.model.id == id))
        return result.scalars().first()

    async def get_all(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        Lấy danh sách các bản ghi có giới hạn (skip/limit).

        Args:
            db (AsyncSession): Phiên kết nối DB.
            skip (int): Số lượng bản ghi cần bỏ qua.
            limit (int): Số lượng bản ghi tối đa trả về.

        Returns:
            List[ModelType]: Danh sách đối tượng Model.
        """
        result = await db.execute(select(self.model).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Tạo mới một bản ghi vào Database.

        Args:
            db (AsyncSession): Phiên kết nối DB.
            obj_in (CreateSchemaType): Đối tượng Pydantic Schema chứa dữ liệu đầu vào.

        Returns:
            ModelType: Đối tượng Model vừa được tạo thành công.
        """
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Cập nhật một bản ghi đã tồn tại trong Database.

        Args:
            db (AsyncSession): Phiên kết nối DB.
            db_obj (ModelType): Đối tượng Model gốc lấy từ Database.
            obj_in (Union[UpdateSchemaType, Dict[str, Any]]): Dữ liệu cập nhật.

        Returns:
            ModelType: Đối tượng Model sau khi đã được cập nhật.
        """
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: int) -> Optional[ModelType]:
        """
        Xóa một bản ghi khỏi Database.

        Args:
            db (AsyncSession): Phiên kết nối DB.
            id (int): Khóa chính của bản ghi cần xóa.

        Returns:
            Optional[ModelType]: Đối tượng Model đã bị xóa, hoặc None nếu không tìm thấy.
        """
        obj = await self.get_by_id(db, id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj

    async def paginate(
        self, db: AsyncSession, query: Select, page: int, page_size: int
    ) -> PaginatedResponse:
        """
        Thực hiện phân trang cho một Query bất kỳ.

        Args:
            db (AsyncSession): Phiên kết nối DB.
            query (Select): Câu lệnh truy vấn SQLAlchemy (chưa gọi limit/offset).
            page (int): Số trang hiện tại (>= 1).
            page_size (int): Kích thước một trang (>= 1).

        Returns:
            PaginatedResponse: Object chuẩn phân trang bao gồm total, page, items.
            
        Raises:
            ValueError: Nếu page hoặc page_size < 1.
        """
        if page < 1 or page_size < 1:
            raise ValueError("Page và Page Size phải lớn hơn hoặc bằng 1.")

        # Đếm tổng số bản ghi
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Thực hiện lấy dữ liệu phân trang
        offset = (page - 1) * page_size
        paginated_query = query.offset(offset).limit(page_size)
        result = await db.execute(paginated_query)
        items = list(result.scalars().unique().all())

        return PaginatedResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=items
        )
