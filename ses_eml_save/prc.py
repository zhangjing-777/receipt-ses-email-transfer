import os
from typing import Optional, List, Dict, Any, Union
from datetime import date, datetime
from decimal import Decimal
from fastapi import HTTPException
from supabase import create_client, Client
from postgrest import APIError
from uuid import UUID



# 初始化 Supabase（管理端使用 Service Role
SUPABASE_URL = os.environ["SUPABASE_URL"]
SERVICE_KEY  = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
ENC_KEY      = os.environ["ENC_KEY"]
HMAC_KEY     = os.environ["HMAC_KEY"]

supa: Client = create_client(SUPABASE_URL, SERVICE_KEY)

def _jsonify(v):
    if v is None:
        return None
    if isinstance(v, UUID):
        return str(v)
    if isinstance(v, (date, datetime)):
        # PostgREST 接受 ISO8601 字符串
        return v.isoformat()
    if isinstance(v, Decimal):
        # 建议转成字符串，避免精度丢失
        return str(v)
    return v

def rpc(schema: str, fn: str, params: Dict[str, Any]) -> Any:
    """统一的 RPC 调用，先把参数转换为可 JSON 序列化类型。"""
    safe_params = {k: _jsonify(v) for k, v in params.items() if v is not None}
    try:
        res = (
            supa.postgrest
            .schema(schema)
            .rpc(fn, safe_params)
            .execute()
        )
        return res.data
    except APIError as e:
        # 交给路由层转成 HTTP 错误
        raise HTTPException(status_code=500, detail={
            "code": e.code, "message": e.message, "details": e.details
        })

def get_ses_eml_info(user_id: str) -> List[Dict[str, Any]]:
    data = rpc(
        "api",
        "get_ses_eml_info",
        {"enc_key": ENC_KEY, "hmac_key": HMAC_KEY, "p_user_id": str(user_id)}
    )
    return data or []

def update_ses_eml_info(
    id: str,
    user_id: str,
    from_email: Optional[str] = None,
    to_email: Optional[str] = None,
    s3_eml_url: Optional[str] = None,
    buyer: Optional[str] = None,
    seller: Optional[str] = None,
    invoice_date: Optional[Union[str, date, datetime]] = None,
    create_time: Optional[Union[str, datetime]] = None
) -> Dict[str, Any]:
    payload = {
    "p_enc_key": ENC_KEY,
    "p_hmac_key": HMAC_KEY,
    "p_id": str(id),
    "p_user_id": str(user_id),
    "p_from": from_email,       # None -> 不改
    "p_to": to_email,           # None -> 不改
    "p_buyer": buyer,
    "p_seller": seller,
    "p_s3_eml_url": s3_eml_url,
    "p_invoice_date": invoice_date,  # None -> 不改
    "p_create_time":create_time
}
    data = rpc("api", "update_ses_eml_info", payload)
    if not data:
        raise HTTPException(status_code=404, detail="Record not found")
    return data[0]

def insert_ses_eml_info(
    id: str,
    user_id: str,
    from_email: Optional[str] = None,
    to_email: Optional[str] = None,
    s3_eml_url: Optional[str] = None,
    buyer: Optional[str] = None,
    seller: Optional[str] = None,
    invoice_date: Optional[Union[str, date, datetime]] = None,
    create_time: Optional[Union[str, datetime]] = None
) -> Dict[str, Any]:
    payload = {
    "p_enc_key": ENC_KEY,
    "p_hmac_key": HMAC_KEY,
    "p_id": str(id),
    "p_user_id": str(user_id),
    "p_from": from_email,       # None -> 不改
    "p_to": to_email,           # None -> 不改
    "p_buyer": buyer,
    "p_seller": seller,
    "p_s3_eml_url": s3_eml_url,
    "p_invoice_date": invoice_date,  # None -> 不改
    "p_create_time":create_time
}
    data = rpc("api", "insert_ses_eml_info", payload)
    if not data:
        raise HTTPException(status_code=404, detail="Record not found")
    return data[0]



def get_receipt_items_cleaned_for_user(user_id: str) -> List[Dict[str, Any]]:
    data = rpc(
        "api",
        "get_receipt_items_cleaned_for_user",
        {"p_enc_key": ENC_KEY, "p_hmac_key": HMAC_KEY, "p_user_id": str(user_id)}
    )
    return data or []

def update_receipt_item_cleaned(
    id: str,
    user_id: str,
    buyer: Optional[str] = None,
    seller: Optional[str] = None,
    invoice_number: Optional[str] = None,
    address: Optional[str] = None,
    file_url: Optional[str] = None,
    original_info: Optional[str] = None,
    ocr: Optional[str] = None,
    invoice_date: Optional[Union[str, date, datetime]] = None,
    category: Optional[str] = None,
    invoice_total: Optional[Union[Decimal, float, str]] = None,
    currency: Optional[str] = None,
    hash_id: Optional[str] = None,
    create_time: Optional[Union[str, datetime]] = None
) -> Dict[str, Any]:
    payload = {
        "p_enc_key": ENC_KEY,
        "p_hmac_key": HMAC_KEY,
        "p_id": str(id),                
        "p_user_id": str(user_id),

        "p_buyer": buyer,
        "p_seller": seller,
        "p_invoice_number": invoice_number,
        "p_address": address,
        "p_file_url": file_url,
        "p_original_info": original_info,
        "p_ocr": ocr,

        "p_invoice_date": invoice_date,
        "p_category": category,
        "p_invoice_total": invoice_total,
        "p_currency": currency,
        "p_hash_id": hash_id,
        "p_create_time":  create_time            
    }
    data = rpc("api", "update_receipt_item_cleaned", payload)
    if not data:
        raise HTTPException(status_code=404, detail="Record not found")
    return data[0]

def insert_receipt_item_cleaned(
    id: str,
    user_id: str,
    buyer: Optional[str] = None,
    seller: Optional[str] = None,
    invoice_number: Optional[str] = None,
    address: Optional[str] = None,
    file_url: Optional[str] = None,
    original_info: Optional[str] = None,
    ocr: Optional[str] = None,
    invoice_date: Optional[Union[str, date, datetime]] = None,
    category: Optional[str] = None,
    invoice_total: Optional[Union[Decimal, float, str]] = None,
    currency: Optional[str] = None,
    hash_id: Optional[str] = None,
    create_time: Optional[Union[str, datetime]] = None
) -> Dict[str, Any]:
    payload = {
        "p_enc_key": ENC_KEY,
        "p_hmac_key": HMAC_KEY,
        "p_id": str(id),                
        "p_user_id": str(user_id),

        "p_buyer": buyer,
        "p_seller": seller,
        "p_invoice_number": invoice_number,
        "p_address": address,
        "p_file_url": file_url,
        "p_original_info": original_info,
        "p_ocr": ocr,

        "p_invoice_date": invoice_date,
        "p_category": category,
        "p_invoice_total": invoice_total,
        "p_currency": currency,
        "p_hash_id": hash_id,
        "p_create_time":  create_time            
    }
    data = rpc("api", "insert_receipt_item_cleaned", payload)
    if not data:
        raise HTTPException(status_code=404, detail="Record not found")
    return data[0]




