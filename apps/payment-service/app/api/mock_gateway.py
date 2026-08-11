import os
from fastapi import APIRouter, Depends, BackgroundTasks, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.payment_service import PaymentService

router = APIRouter()

current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(os.path.dirname(current_dir), "templates")
templates = Jinja2Templates(directory=templates_dir)

@router.get("/mock-gateway/pay", response_class=HTMLResponse)
async def get_mock_payment_page(request: Request, txn_id: str, db: AsyncSession = Depends(get_db)):
    txn = await PaymentService.get_mock_payment_details(db, txn_id)
    return templates.TemplateResponse(
        "payment.html",
        {
            "request": request,
            "txn_id": str(txn.id),
            "gateway": txn.gateway,
            "amount": float(txn.amount)
        }
    )

@router.post("/mock-gateway/pay")
async def post_mock_payment_process(
    txn_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    return await PaymentService.process_mock_payment(db, txn_id, background_tasks)
