from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
from models.mall_product import MallProduct
from models.mall_order import MallOrder
from models.user_points import UserPoints
from models.points_logs import PointsLog

router = APIRouter(prefix="/mall", tags=["mall"])


@router.get("/products")
def list_products(db: Session = Depends(get_db)):
    return db.query(MallProduct).filter(MallProduct.status == 1).all()


@router.post("/exchange/{product_id}")
def exchange_product(product_id: int,
                     db: Session = Depends(get_db),
                     current_user=Depends(get_current_user)):

    product = db.query(MallProduct).filter(MallProduct.id == product_id).first()

    if not product or product.status != 1:
        raise HTTPException(status_code=404, detail="商品不存在")

    if product.stock <= 0:
        raise HTTPException(status_code=400, detail="库存不足")

    account = db.query(UserPoints).filter(UserPoints.user_id == current_user.id).first()

    if not account or account.balance < product.points_price:
        raise HTTPException(status_code=400, detail="积分不足")

    account.balance -= product.points_price
    product.stock -= 1

    order = MallOrder(
        user_id=current_user.id,
        product_id=product.id,
        points_cost=product.points_price
    )

    log = PointsLog(
        user_id=current_user.id,
        change_amount=-product.points_price,
        type="product_exchange",
        description=f"兑换商品 {product.name}"
    )

    db.add(order)
    db.add(log)
    db.commit()

    return {"message": "兑换成功"}
