"""Reports endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from pydantic import BaseModel

from app.core.security import get_current_user
from app.db import get_db
from app.db.models import Report, User

router = APIRouter(prefix="/reports", tags=["Reports"])


class ReportResponse(BaseModel):
    id: int
    report_uuid: str
    task_type: str
    title: Optional[str]
    user_input: str
    final_content: str
    agents_used: Optional[list]
    created_at: str


@router.get("", response_model=List[ReportResponse])
async def list_reports(current_user: dict = Depends(get_current_user)):
    async with get_db() as db:
        result = await db.execute(
            select(Report)
            .where(Report.user_id == int(current_user["sub"]))
            .order_by(desc(Report.created_at))
        )
        reports = result.scalars().all()
        return [
            ReportResponse(
                id=r.id,
                report_uuid=str(r.report_uuid),
                task_type=r.task_type,
                title=r.title,
                user_input=r.user_input,
                final_content=r.final_content[:500] + "..." if len(r.final_content) > 500 else r.final_content,
                agents_used=r.agents_used,
                created_at=r.created_at.isoformat()
            )
            for r in reports
        ]


@router.get("/{report_uuid}", response_model=ReportResponse)
async def get_report(report_uuid: str, current_user: dict = Depends(get_current_user)):
    async with get_db() as db:
        from uuid import UUID
        result = await db.execute(
            select(Report).where(Report.report_uuid == UUID(report_uuid), Report.user_id == int(current_user["sub"]))
        )
        report = result.scalar_one_or_none()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        return ReportResponse(
            id=report.id,
            report_uuid=str(report.report_uuid),
            task_type=report.task_type,
            title=report.title,
            user_input=report.user_input,
            final_content=report.final_content,
            agents_used=report.agents_used,
            created_at=report.created_at.isoformat()
        )
