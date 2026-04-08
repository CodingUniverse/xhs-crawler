from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.database import PlatformAccount, AccountStatusEnum
from app.schemas import (
    PlatformAccountCreate,
    PlatformAccountUpdate,
    PlatformAccountResponse,
)

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=list[PlatformAccountResponse])
async def list_accounts(
    platform: str = None,
    status: AccountStatusEnum = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(PlatformAccount)
    if platform:
        query = query.where(PlatformAccount.platform_name == platform)
    if status:
        query = query.where(PlatformAccount.status == status)
    result = await db.execute(query.order_by(PlatformAccount.created_at.desc()))
    return result.scalars().all()


@router.get("/{account_id}", response_model=PlatformAccountResponse)
async def get_account(account_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PlatformAccount).where(PlatformAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.post("", response_model=PlatformAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account: PlatformAccountCreate,
    db: AsyncSession = Depends(get_db),
):
    db_account = PlatformAccount(**account.model_dump())
    db.add(db_account)
    await db.commit()
    await db.refresh(db_account)
    return db_account


@router.patch("/{account_id}", response_model=PlatformAccountResponse)
async def update_account(
    account_id: int,
    account_update: PlatformAccountUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PlatformAccount)
        .where(PlatformAccount.id == account_id)
        .with_for_update()
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    update_data = account_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)
    
    await db.commit()
    await db.refresh(account)
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(account_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PlatformAccount)
        .where(PlatformAccount.id == account_id)
        .with_for_update()
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    await db.delete(account)
    await db.commit()
