import os
import uuid
import requests
import logging
from io import BytesIO
from typing import List
from datetime import datetime
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from supabase import create_client, Client

load_dotenv()

# 设置日志
logger = logging.getLogger(__name__)

# Supabase config
SUPABASE_URL = os.getenv("SUPABASE_URL") or ""
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or ""
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def extract_pdf_invoice_urls(html: str) -> list[str]:
    logger.info("Extracting PDF invoice URLs from HTML content")
    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all("a", string=lambda text: text and "Download PDF invoice" in text)
    urls = [link["href"] for link in links if link.has_attr("href")]
    logger.info(f"Found {len(urls)} PDF invoice URLs")
    return urls

def upload_invoice_pdf_to_supabase(pdf_urls: List[str], user_id:str, show: str) -> dict:
    logger.info(f"Starting PDF upload process for {len(pdf_urls)} URLs with show: {show}")
    public_urls = {}
    
    for i, pdf_url in enumerate(pdf_urls, 1):
        logger.info(f"Processing PDF {i}/{len(pdf_urls)}: {pdf_url}")
        
        try:
            # 下载 PDF 到内存
            logger.info(f"Downloading PDF from: {pdf_url}")
            response = requests.get(pdf_url)
            if response.status_code != 200:
                error_msg = f"下载 PDF 失败: {response.status_code}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            logger.info(f"PDF downloaded successfully, size: {len(response.content)} bytes")

            id = str(uuid.uuid4())[:8]
            filename = f"users/{user_id}/{datetime.utcnow().date().isoformat()}/eml_att_{datetime.utcnow().timestamp()}_{id}.pdf"
            logger.info(f"Generated storage filename: {filename}")

            # 上传到 Supabase Storage
            logger.info(f"Uploading PDF to Supabase Storage: {filename}")
            file = BytesIO(response.content).getvalue()
            supabase.storage.from_(SUPABASE_BUCKET).upload(file=file, path=filename, file_options={"content-type": "application/pdf"})
            logger.info(f"PDF uploaded successfully to Supabase")

            # 获取 Public URL
            signed_url_result = supabase.storage.from_(SUPABASE_BUCKET).create_signed_url(filename, expires_in=86400)
            public_url = signed_url_result["signedURL"]
            # public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(filename).rstrip('?')
            # public_urls[f"{show}_{id}"] = public_url
            # logger.info(f"Generated public URL: {public_urls}")
            public_urls[f"{show}_{id}"] = [public_url,filename]
            
        except Exception as e:
            logger.exception(f"Failed to process PDF {i}: {pdf_url} - Error: {str(e)}")
            raise
    
    logger.info(f"PDF upload process completed. Total files uploaded: {len(public_urls)}")
    return public_urls
