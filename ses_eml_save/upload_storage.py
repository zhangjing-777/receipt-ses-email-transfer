import os
import base64
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
from ses_eml_save.util import make_safe_storage_path
import logging

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL") or ""
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or ""
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


logger = logging.getLogger(__name__)

def upload_attachments_to_storage(att, bucket="lazy-receipt"):
    """ for att in raw_attachments['attachments'] """
    try:
        filename = att["filename"]
        safe_filename = make_safe_storage_path(filename)
        binary = att["binary"]
        if isinstance(binary, str):
            binary_data = base64.b64decode(binary)
        else:
            binary_data = binary  # 已经是 bytes

        date_url = datetime.utcnow().date().isoformat()
        timestamp = datetime.utcnow().isoformat()
        storage_path = f"{date_url}/{timestamp}_{safe_filename}"

        logger.info(f"Uploading {filename} to storage at {storage_path}")
        # 上传到 Supabase Storage
        supabase.storage.from_(bucket).upload(
            path=storage_path,
            file=binary_data,
            file_options={"content-type": att.get("content_type", "application/octet-stream")}
        )

        # 获取公开 URL
        public_url = supabase.storage.from_(bucket).get_public_url(storage_path).rstrip('?')
        logger.info(f"Upload successful. Public URL: {public_url}")
        return public_url
    except Exception as e:
        logger.exception(f"Failed to upload attachment: {att.get('filename', 'unknown')} - Error: {str(e)}")
        raise
