import os
import logging
from datetime import datetime
from fastapi import FastAPI, Request
from ses_eml_save.main import upload_to_supabase



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



@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.exception(f"Unhandled exception occurred: {str(exc)}")
    return {"error": "Internal server error", "status": "error"}
