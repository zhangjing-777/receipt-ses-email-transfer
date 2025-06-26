import os
from dotenv import load_dotenv
from supabase import create_client, Client
from ses_eml_save.eml_parser import load_s3, mail_parser
from ses_eml_save.upload_storage import upload_attachments_to_storage
from ses_eml_save.ocr import ocr_attachment, extract_fields_from_ocr
from ses_eml_save.insert_data import ReceiptDataPreparer
import logging
from datetime import datetime


load_dotenv()

url: str = os.getenv("SUPABASE_URL") or ""
key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or ""
supabase: Client = create_client(url, key)


logger = logging.getLogger(__name__)


def upload_to_supabase(bucket, key):
    logger.info(f"Starting upload_to_supabase for bucket={bucket}, key={key}")
    try:
        eml_bytes=load_s3(bucket, key)
        logger.info("Loaded EML from S3.")
    except Exception as e:
        logger.exception(f"Failed to load EML from S3: {str(e)}")
        raise

    try:
        raw_attachments = mail_parser(eml_bytes)
        logger.info("Parsed mail from EML bytes.")
    except Exception as e:
        logger.exception(f"Failed to parse mail from EML bytes: {str(e)}")
        raise

    successes = []
    failures = []

    attachments = raw_attachments['attachments']
    if not isinstance(attachments, list):
        logger.error(f"Expected a list of attachments, got {type(attachments)}. Aborting upload.")
        return "No valid attachments found."
    for att in attachments:
        try:
            logger.info(f"Processing attachment: {att.get('filename', 'unknown')}")
            public_url = upload_attachments_to_storage(att)
            logger.info(f"Uploaded attachment to storage: {public_url}")
            ocr = ocr_attachment(public_url)
            logger.info("Performed OCR on attachment.")
            fields = extract_fields_from_ocr(ocr)
            logger.info("Extracted fields from OCR.")

            preparer = ReceiptDataPreparer(fields, raw_attachments, public_url, ocr)
            receipt_row = preparer.build_receipt_data()
            eml_row = preparer.build_eml_data(bucket+'/'+key)
            supabase.table("receipt_items_cleaned").insert(receipt_row).execute()
            supabase.table("ses_eml_info").insert(eml_row).execute()
            logger.info(f"Inserted data for attachment: {att.get('filename', 'unknown')}")

            successes.append(att.get('filename', 'unknown'))
        except Exception as e:
            error_msg = f"{att.get('filename', 'unknown')} - Error: {str(e)}"
            logger.exception(f"Failed to process attachment: {error_msg}")
            failures.append(error_msg)
        
    status = f"""You uploaded a total of {len(successes)+len(failures)} files:  {len(successes)} succeeded--{successes}, {len(failures)} failed--{failures}."""
    try:
        supabase.table("receipt_items_upload_result").insert({"upload_result":status, "user_id":raw_attachments.get('to_email', '').split("@")[0]}).execute()
        logger.info("Inserted upload result status.")
    except Exception as e:
        logger.exception(f"Failed to insert upload result status: {str(e)}")
    logger.info(f"upload_to_supabase finished. Status: {status}")
    return status