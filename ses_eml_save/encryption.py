import os
import base64
import logging
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# 获取加密密钥，如果不存在则生成新的
ENCRYPTION_KEY = base64.b64decode(os.getenv("ENCRYPTION_KEY"))
if not ENCRYPTION_KEY:
    # 生成新密钥并提示用户保存到环境变量
    new_key = Fernet.generate_key().decode()
    logger.warning(f"No ENCRYPTION_KEY found. Generated new key: {new_key}")
    logger.warning("Please add this key to your .env file: ENCRYPTION_KEY=" + new_key)
    ENCRYPTION_KEY = new_key

fernet = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)

# 需要加密的敏感字段
SENSITIVE_FIELDS = {
    'receipt_items_en': ['buyer', 'seller', 'address', 'file_url','invoice_number','original_info','ocr'],
    'ses_eml_info_en': ['from', 'to', 's3_eml_url','buyer', 'seller']
}

def encrypt_value(value):
    """加密单个值"""
    if value is None or value == "":
        return value
    
    try:
        if isinstance(value, (int, float)):
            value = str(value)
        encrypted = fernet.encrypt(value.encode('utf-8'))
        return base64.b64encode(encrypted).decode('utf-8')
    except Exception as e:
        logger.error(f"Encryption failed for value: {str(e)}")
        return value

def decrypt_value(encrypted_value):
    """解密单个值"""
    if encrypted_value is None or encrypted_value == "":
        return encrypted_value
    
    try:
        encrypted_bytes = base64.b64decode(encrypted_value.encode('utf-8'))
        decrypted = fernet.decrypt(encrypted_bytes)
        return decrypted.decode('utf-8')
    except Exception as e:
        logger.error(f"Decryption failed for value: {str(e)}")
        return encrypted_value

def encrypt_data(table_name, data_dict):
    """对指定表的敏感字段进行加密"""
    if table_name not in SENSITIVE_FIELDS:
        return data_dict
    
    encrypted_data = data_dict.copy()
    sensitive_fields = SENSITIVE_FIELDS[table_name]
    
    for field in sensitive_fields:
        if field in encrypted_data and encrypted_data[field]:
            encrypted_data[field] = encrypt_value(encrypted_data[field])
    
    logger.info(f"Encrypted {len(sensitive_fields)} sensitive fields for table {table_name}")
    return encrypted_data

def decrypt_data(table_name, data_dict):
    """对指定表的敏感字段进行解密"""
    if table_name not in SENSITIVE_FIELDS:
        return data_dict
    
    decrypted_data = data_dict.copy()
    sensitive_fields = SENSITIVE_FIELDS[table_name]
    
    for field in sensitive_fields:
        if field in decrypted_data and decrypted_data[field]:
            decrypted_data[field] = decrypt_value(decrypted_data[field])
    
    logger.info(f"Decrypted {len(sensitive_fields)} sensitive fields for table {table_name}")
    return decrypted_data