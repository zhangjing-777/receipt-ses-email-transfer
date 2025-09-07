import os
import logging
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from fastapi import FastAPI, Request, Query, Path, Body
from pydantic import BaseModel, Field
from ses_eml_save.main import upload_to_supabase
from ses_eml_save.prc import get_ses_eml_info, update_ses_eml_info, get_receipt_items_cleaned_for_user, update_receipt_item_cleaned



# 创建logs目录
os.makedirs('logs', exist_ok=True)

# 配置日志格式和存储
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(f'logs/app_{datetime.now().strftime("%Y%m%d")}.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Encrypted Data API")

@app.get("/health")
async def health_check():
    """健康检查接口"""
    logger.info("Health check requested")
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# 拉取 S3 并转发给supabase
@app.post("/webhook/ses-email-transfer")
async def ses_email_transfer(bucket, key, user_id):
    logger.info("Received webhook request")
    bucket = str(bucket)
    key = str(key)
    user_id = str(user_id)
    try:
        logger.info(f"Starting upload process for bucket: {bucket}, key: {key}, user_id: {user_id}")
        result = await upload_to_supabase(bucket, key, user_id)
        logger.info(f"Upload process completed: {result}")
        return {"message": "Email processed successfully", "result": result, "status": "success"}
    except Exception as e:
        logger.exception(f"Upload process failed: {str(e)}")
        return {"error": f"Upload process failed: {str(e)}", "status": "error"}
    
class SesEmlInfoUpdate(BaseModel):
    """更新 ses_eml_info 用（不传=不改）"""
    from_email: Optional[str] = Field(default=None, description="不改就别传或传 null", examples=[None])
    to_email: Optional[str]   = Field(default=None, description="不改就别传或传 null", examples=[None])
    s3_eml_url: Optional[str] = Field(default=None, description="不改就别传或传 null", examples=[None])
    buyer: Optional[str] = Field(default=None, description="不改就别传或传 null", examples=[None])
    seller: Optional[str] = Field(default=None, description="不改就别传或传 null", examples=[None])
    invoice_date: Optional[Union[str, date, datetime]] = Field(default=None, description="不改就别传或传 null", examples=[None])
    create_time: Optional[Union[str, datetime]] = Field(default=None, description="不改就别传或传 null", examples=[None])


class ReceiptItemCleanedUpdate(BaseModel):
    """更新 receipt_items_cleaned 用（不传=不改）"""
    buyer: Optional[str] = Field(default=None, description="不改就别传或传 null", examples=[None])
    seller: Optional[str] = Field(default=None, description="不改就别传或传 null", examples=[None])
    invoice_number: Optional[str] = Field(default=None, description="不改就别传或传 null", examples=[None])
    address: Optional[str] = Field(default=None, description="不改就别传或传 null", examples=[None])
    file_url: Optional[str] = Field(default=None, description="不改就别传或传 null", examples=[None])
    original_info: Optional[str] = Field(default=None, description="不改就别传或传 null", examples=[None])
    ocr: Optional[str] = Field(default=None, description="不改就别传或传 null", examples=[None])

    invoice_date: Optional[Union[str, date, datetime]] = Field(default=None, description="不改就别传或传 null", examples=[None])
    category: Optional[str] = Field(default=None, description="不改就别传或传 null", examples=[None])
    invoice_total: Optional[Union[Decimal, float, str]] = Field(default=None, description="不改就别传或传 null", examples=[None])
    currency: Optional[str] = Field(default=None, description="不改就别传或传 null", examples=[None])
    hash_id: Optional[str] = Field(default=None, description="不改就别传或传 null", examples=[None])
    create_time: Optional[Union[str, datetime]] = Field(default=None, description="不改就别传或传 null", examples=[None])


# -----------------------------
# ses_eml_info - GET / PATCH
# -----------------------------

@app.get(
    "/ses-eml-info/{user_id}",
    summary="获取用户的 ses_eml_info（已解密）",
    response_model=List[Dict[str, Any]],
)
def api_get_ses_eml_info(user_id: UUID = Path(..., description="用户 UUID")):
    return get_ses_eml_info(str(user_id))


@app.patch(
    "/ses-eml-info/{record_id}",
    summary="更新 ses_eml_info（仅更新传入字段）并返回已解密数据",
    response_model=Dict[str, Any],
)
def api_update_ses_eml_info(
    record_id: UUID = Path(..., description="记录 UUID"),
    user_id:   UUID = Query(..., description="用户 UUID（不可更改，用于保护）"),
    body: SesEmlInfoUpdate = Body(
        default_factory=SesEmlInfoUpdate,   # <-- 关键：默认就是 {}
        examples={"empty": {"summary": "不改任何字段", "value": {}}}
    ),
):
    changes = body.model_dump(exclude_unset=True, exclude_none=True)
    if not changes:
        return {"message": "No changes"}
    return update_ses_eml_info(id=record_id, user_id=user_id, **changes)


# ------------------------------------
# receipt_items_cleaned - GET / PATCH
# ------------------------------------

@app.get(
    "/receipt-items-cleaned/{user_id}",
    summary="获取用户的 receipt_items_cleaned（已解密）",
    response_model=List[Dict[str, Any]],
)
def api_get_receipt_items_cleaned(user_id: UUID = Path(..., description="用户 UUID")):
    return get_receipt_items_cleaned_for_user(str(user_id))

@app.patch(
    "/receipt-items-cleaned/{record_id}",
    summary="更新 receipt_items_cleaned（仅更新传入字段）并返回已解密数据",
    response_model=Dict[str, Any],
)
def api_update_receipt_item_cleaned(
    record_id: UUID = Path(..., description="记录 UUID"),
    user_id:   UUID = Query(..., description="用户 UUID（不可更改，用于保护）"),
    body: ReceiptItemCleanedUpdate = Body(
        default_factory=ReceiptItemCleanedUpdate,   # <-- 关键：默认就是 {}
        examples={"empty": {"summary": "不改任何字段", "value": {}}}
    ),
):
    changes = body.model_dump(exclude_unset=True, exclude_none=True)
    if not changes:
        return {"message": "No changes"}
    return update_receipt_item_cleaned(id=record_id, user_id=user_id, **changes)



@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.exception(f"Unhandled exception occurred: {str(exc)}")
    return {"error": "Internal server error", "status": "error"}
