import uuid
import hashlib
from datetime import datetime
from typing import Dict, Any
from ses_eml_save.util import clean_and_parse_json
import logging



logger = logging.getLogger(__name__)


class ReceiptDataPreparer:
    def __init__(self, user_id, fields: str, raw_attachments: Dict[str, Any], public_url: str, ocr: str):
        self.fields = fields
        self.raw_attachments = raw_attachments
        self.public_url = public_url
        self.ocr = ocr

        # 共享 ID，确保 receipt 和 eml 绑定
        self.record_id = str(uuid.uuid4())

        # 用户名 = 邮箱前缀
        self.user_id = user_id

        # 解析字段
        self.items = self.parse_fields()

    def parse_fields(self) -> Dict[str, Any]:
        """清洗字段并返回 dict"""
        logger.info("Parsing and cleaning fields for receipt data.")
        try:
            items = clean_and_parse_json(self.fields)
        except Exception as e:
            logger.exception(f"Failed to parse fields: {str(e)}")
            raise ValueError(f"Failed to parse fields: {e}")

        # 生成 hash_id，防重复
        hash_input = "|".join([
            str(self.user_id),
            str(items.get("invoice_total", "")),
            str(items.get("buyer", "")),
            str(items.get("seller", "")),
            str(items.get("invoice_date", "")),
            str(items.get("invoice_number", ""))
        ])

        items["hash_id"] = hashlib.md5(hash_input.encode()).hexdigest()
        logger.info(f"Generated hash_id for receipt: {items['hash_id']}")
        return items

    def build_receipt_data(self) -> Dict[str, Any]:
        logger.info("Building receipt data dictionary.")
        try:
            data = {
                "id": self.record_id,
                "user_id": self.user_id,
                "file_url": self.public_url,
                "original_info": self.raw_attachments.get("body", ""),
                "ocr": self.ocr,
                "create_time": datetime.utcnow().isoformat(),
                **self.items  # 合并提取字段
            }
            logger.info("Receipt data built successfully.")
            return data
        except Exception as e:
            logger.exception(f"Failed to build receipt data: {str(e)}")
            raise

    def build_eml_data(self, s3_eml_url: str) -> Dict[str, Any]:
        logger.info("Building EML data dictionary.")
        try:
            data = {
                "id": self.record_id,
                "user_id": self.user_id,
                "from": self.raw_attachments.get("from_email", ""),
                "to": self.raw_attachments.get("to_email", ""),
                "s3_eml_url": s3_eml_url,
                "buyer": self.items.get("buyer", ""),
                "seller": self.items.get("seller", ""),
                "invoice_date": self.items.get("invoice_date", ""),
                "create_time": datetime.utcnow().isoformat()
            }
            logger.info("EML data built successfully.")
            return data
        except Exception as e:
            logger.exception(f"Failed to build EML data: {str(e)}")
            raise
