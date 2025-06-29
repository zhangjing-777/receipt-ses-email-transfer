import os
import base64
import requests
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)



OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("MODEL")
MODEL_FREE = os.getenv("MODEL_FREE")
OPENROUTER_URL = os.getenv("OPENROUTER_URL") or ""

HEADERS = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }


def openrouter_image_ocr(file_url):
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What's in this image?"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": file_url
                    }
                }
            ]
        }
    ]
    
    # 先尝试使用 MODEL_FREE
    payload = {
        "model": MODEL_FREE,
        "messages": messages
    }
    
    try:
        logger.info(f"Trying image OCR with MODEL_FREE: {MODEL_FREE}")
        response = requests.post(OPENROUTER_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        response_data = response.json()
        
        # 记录 token 使用量
        if "usage" in response_data:
            usage = response_data["usage"]
            logger.info(f"Image OCR token usage (MODEL_FREE) - Prompt: {usage.get('prompt_tokens', 'N/A')}, "
                       f"Completion: {usage.get('completion_tokens', 'N/A')}, "
                       f"Total: {usage.get('total_tokens', 'N/A')}")
        else:
            logger.warning("No usage information found in OpenRouter response")
        
        logger.info(f"Image OCR API response (MODEL_FREE): {response.status_code}")
        return response_data["choices"][0]["message"]["content"]
        
    except Exception as e:
        logger.warning(f"MODEL_FREE failed, trying MODEL: {str(e)}")
        
        # 如果 MODEL_FREE 失败，尝试使用 MODEL
        payload["model"] = MODEL
        try:
            logger.info(f"Trying image OCR with MODEL: {MODEL}")
            response = requests.post(OPENROUTER_URL, headers=HEADERS, json=payload)
            response.raise_for_status()
            response_data = response.json()
            
            # 记录 token 使用量
            if "usage" in response_data:
                usage = response_data["usage"]
                logger.info(f"Image OCR token usage (MODEL) - Prompt: {usage.get('prompt_tokens', 'N/A')}, "
                           f"Completion: {usage.get('completion_tokens', 'N/A')}, "
                           f"Total: {usage.get('total_tokens', 'N/A')}")
            else:
                logger.warning("No usage information found in OpenRouter response")
            
            logger.info(f"Image OCR API response (MODEL): {response.status_code}")
            return response_data["choices"][0]["message"]["content"]
            
        except Exception as e2:
            logger.exception(f"Both MODEL_FREE and MODEL failed for image OCR: {str(e2)}")
            raise

def openrouter_pdf_ocr(file_url):
    logger.info(f"Starting PDF OCR for: {file_url}")
    try:
        response = requests.get(file_url)
        response.raise_for_status()
        base64_pdf = base64.b64encode(response.content).decode('utf-8')
        data_url = f"data:application/pdf;base64,{base64_pdf}"
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What are the main points in this document?"
                    },
                    {
                        "type": "file",
                        "file": {
                            "filename": "invoice.pdf",
                            "file_data": data_url
                        }
                    },
                ]
            }
        ]
        plugins = [
            {
                "id": "file-parser",
                "pdf": {
                    "engine": "pdf-text"  
                }
            }
        ]
        
        # 先尝试使用 MODEL_FREE
        payload = {
            "model": MODEL_FREE,
            "messages": messages,
            "plugins": plugins
        }
        
        try:
            logger.info(f"Trying PDF OCR with MODEL_FREE: {MODEL_FREE}")
            response = requests.post(OPENROUTER_URL, headers=HEADERS, json=payload)
            response.raise_for_status()
            response_data = response.json()
            
            # 记录 token 使用量
            if "usage" in response_data:
                usage = response_data["usage"]
                logger.info(f"PDF OCR token usage (MODEL_FREE) - Prompt: {usage.get('prompt_tokens', 'N/A')}, "
                           f"Completion: {usage.get('completion_tokens', 'N/A')}, "
                           f"Total: {usage.get('total_tokens', 'N/A')}")
            else:
                logger.warning("No usage information found in OpenRouter response")
            
            logger.info(f"PDF OCR API response (MODEL_FREE): {response.status_code}")
            return response_data["choices"][0]["message"]["content"]
            
        except Exception as e:
            logger.warning(f"MODEL_FREE failed, trying MODEL: {str(e)}")
            
            # 如果 MODEL_FREE 失败，尝试使用 MODEL
            payload["model"] = MODEL
            try:
                logger.info(f"Trying PDF OCR with MODEL: {MODEL}")
                response = requests.post(OPENROUTER_URL, headers=HEADERS, json=payload)
                response.raise_for_status()
                response_data = response.json()
                
                # 记录 token 使用量
                if "usage" in response_data:
                    usage = response_data["usage"]
                    logger.info(f"PDF OCR token usage (MODEL) - Prompt: {usage.get('prompt_tokens', 'N/A')}, "
                               f"Completion: {usage.get('completion_tokens', 'N/A')}, "
                               f"Total: {usage.get('total_tokens', 'N/A')}")
                else:
                    logger.warning("No usage information found in OpenRouter response")
                
                logger.info(f"PDF OCR API response (MODEL): {response.status_code}")
                return response_data["choices"][0]["message"]["content"]
                
            except Exception as e2:
                logger.exception(f"Both MODEL_FREE and MODEL failed for PDF OCR: {str(e2)}")
                raise
                
    except Exception as e:
        logger.exception(f"PDF OCR failed: {str(e)}")
        raise

def ocr_attachment(file_url) -> str:
    logger.info(f"Starting OCR for attachment: {file_url}")
    try:
        if file_url.endswith("pdf"):
            return openrouter_pdf_ocr(file_url)
        else:
            return openrouter_image_ocr(file_url)
    except Exception as e:
        logger.error(f"OCR failed for {file_url}: {str(e)}")
        raise
    

DEEPSEEK_URL = os.getenv("DEEPSEEK_URL") or ""
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

DEEP_HEADERS = {
    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    "Content-Type": "application/json"
}



def extract_fields_from_ocr(text):
    logger.info("Extracting fields from OCR text.")
    prompt = f"""This is the raw text extracted from an invoice using OCR. 
    Please extract the following fields and output them as a JSON object, with strict type and format requirements:

    - invoice_number: string
    - invoice_date: string, must be in "YYYY-MM-DD" format (ISO 8601), e.g. "2025-06-23"
    - buyer (purchaser): string
    - seller (vendor): string
    - invoice_total: number (do not include any currency symbols, commas, or quotes, just the numeric value, e.g. 1234.56)
    - currency: string (e.g. "USD", "CNY")
    - category: string
    - address: string

    Return only the JSON object, no extra explanation.

    Example output:
    {{
      "invoice_number": "INV-20250623-001",
      "invoice_date": "2025-06-23",
      "buyer": "Acme Corp",
      "seller": "Widget Inc",
      "invoice_total": 1234.56,
      "currency": "USD",
      "category": "Office Supplies",
      "address": "123 Main St, Springfield"
    }}

    Invoice text is as follows:
    {text}
    """
    data = {
        "model": "deepseek-chat",  
        "messages": [
            {"role": "system", "content": "You are an AI assistant specialized in extracting structured data."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "stream": False
    }
    try:
        response = requests.post(DEEPSEEK_URL, headers=DEEP_HEADERS, json=data)
        response.raise_for_status()
        response_data = response.json()
        
        # 记录 token 使用量
        if "usage" in response_data:
            usage = response_data["usage"]
            logger.info(f"Deepseek field extraction token usage - Prompt: {usage.get('prompt_tokens', 'N/A')}, "
                       f"Completion: {usage.get('completion_tokens', 'N/A')}, "
                       f"Total: {usage.get('total_tokens', 'N/A')}")
            print(f"Total: {usage.get('total_tokens', 'N/A')}")
        else:
            logger.warning("No usage information found in Deepseek response")
        
        logger.info(f"Deepseek API response: {response.status_code}")
        return response_data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.exception(f"Field extraction from OCR failed: {str(e)}")
        raise


