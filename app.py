import json
import requests
from fastapi import FastAPI, Request, HTTPException
from ses_eml_save.main import upload_to_supabase
import logging
from datetime import datetime
import os

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

app = FastAPI()

@app.get("/health")
async def health_check():
    """健康检查接口"""
    logger.info("Health check requested")
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# 自动从 SNS 拉取 S3 并转发给supabase
@app.post("/webhook/ses-email-transfer")
async def ses_email_transfer(request: Request):
    logger.info("Received webhook request")
    
    try:
        payload = await request.json()
        logger.info(f"Webhook payload type: {payload.get('Type', 'Unknown')}")
    except Exception as e:
        logger.exception(f"Failed to parse request JSON: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # 1. 订阅确认逻辑（只处理一次）
    if payload.get("Type") == "SubscriptionConfirmation":
        logger.info("Processing SNS subscription confirmation")
        subscribe_url = payload.get("SubscribeURL")
        if subscribe_url:
            logger.info(f"🔔 SNS 订阅确认中: {subscribe_url}")
            try:
                response = requests.get(subscribe_url, timeout=10)
                response.raise_for_status()
                logger.info("SNS subscription confirmed successfully")
                return {"message": "Subscription confirmed", "status": "success"}
            except Exception as e:
                logger.exception(f"Subscription failed: {str(e)}")
                return {"error": f"Subscription failed: {str(e)}", "status": "error"}

    # 2. 正常邮件通知
    if payload.get("Type") == "Notification":
        logger.info("Processing SNS notification")
        try:
            message = json.loads(payload["Message"])
            logger.info("Successfully parsed SNS message")
        except Exception as e:
            logger.exception(f"Failed to parse SNS message: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid SNS message format")

        try:
            s3_bucket = message["bucket"]
            s3_key = message["key"]
            user_id = message.get("user_id", "unknown")
            logger.info(f"Extracted S3 info - Bucket: {s3_bucket}, Key: {s3_key}")
        except KeyError as e:
            logger.exception(f"Missing required fields in SNS message: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Missing required field: {str(e)}")

        try:
            logger.info(f"Starting upload process for bucket: {s3_bucket}, key: {s3_key}")
            result = upload_to_supabase(s3_bucket, s3_key, user_id)
            logger.info(f"Upload process completed: {result}")
            return {"message": "Email processed successfully", "result": result, "status": "success"}
        except Exception as e:
            logger.exception(f"Upload process failed: {str(e)}")
            return {"error": f"Upload process failed: {str(e)}", "status": "error"}

    logger.warning(f"Unhandled payload type: {payload.get('Type', 'Unknown')}")
    return {"message": "No action taken", "status": "ignored"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.exception(f"Unhandled exception occurred: {str(exc)}")
    return {"error": "Internal server error", "status": "error"}
