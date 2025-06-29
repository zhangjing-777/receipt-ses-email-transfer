import os
import asyncio
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
from ses_eml_save.insert_data import ReceiptDataPreparer
from ses_eml_save.eml_parser import load_s3, mail_parser
from ses_eml_save.ocr import ocr_attachment, extract_fields_from_ocr
from ses_eml_save.attachment_upload import upload_attachments_to_storage
from ses_eml_save.string_to_image_upload import render_html_string_to_image_and_upload
from ses_eml_save.link_upload import extract_pdf_invoice_urls, upload_invoice_pdf_to_supabase


load_dotenv()

url: str = os.getenv("SUPABASE_URL") or ""
key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or ""
supabase: Client = create_client(url, key)


logger = logging.getLogger(__name__)


async def upload_to_supabase(bucket, key, user_id):
    logger.info(f"Starting upload_to_supabase for user_id: {user_id}, bucket: {bucket}, key: {key}")
    
    try:
        logger.info("Loading email from S3...")
        eml_bytes = load_s3(bucket, key)
        logger.info(f"Successfully loaded email from S3, size: {len(eml_bytes)} bytes")
        
        logger.info("Parsing email content...")
        raw_attachments = mail_parser(eml_bytes)
        logger.info("Email parsing completed")
        
        html_str = raw_attachments['body']
        subject = raw_attachments['subject']
        attachments = raw_attachments['attachments']
        
        logger.info(f"Email subject: {subject}")
        logger.info(f"Found {len(attachments)} attachments")
        logger.info(f"HTML body length: {len(html_str)} characters")
        
        # 处理附件或链接
        if len(attachments) > 0:
            logger.info("Processing email attachments...")
            public_urls = upload_attachments_to_storage(attachments)
            logger.info(f"Successfully uploaded {len(public_urls)} attachments to storage")
        else:
            logger.info("No attachments found, checking for PDF invoice links...")
            urls = extract_pdf_invoice_urls(html_str)
            if len(urls) > 0:
                logger.info(f"Found {len(urls)} PDF invoice links, downloading and uploading...")
                public_urls = upload_invoice_pdf_to_supabase(urls, subject)
                logger.info(f"Successfully processed {len(public_urls)} PDF invoice links")
            else:
                logger.info("No PDF links found, converting HTML body to image...")
                public_urls = await render_html_string_to_image_and_upload(html_str, subject)
                logger.info("Successfully converted HTML body to image and uploaded")
        
        logger.info(f"Total files to process: {len(public_urls)}")
        
        # 处理每个文件的OCR和数据提取
        successes = []
        failures = []
        
        for i, (filename, public_url) in enumerate(public_urls.items(), 1):
            logger.info(f"Processing file {i}/{len(public_urls)}: {filename}")
            try:
                logger.info(f"Starting OCR for {filename}...")
                ocr = ocr_attachment(public_url)
                logger.info(f"OCR completed for {filename}, text length: {len(ocr)} characters")
                
                logger.info(f"Extracting fields from OCR for {filename}...")
                fields = extract_fields_from_ocr(ocr)
                logger.info(f"Field extraction completed for {filename}")

                logger.info(f"Preparing data for {filename}...")
                preparer = ReceiptDataPreparer(user_id, fields, raw_attachments, public_url, ocr)
                receipt_row = preparer.build_receipt_data()
                eml_row = preparer.build_eml_data(bucket+'/'+key)
                logger.info(f"Data preparation completed for {filename}")

                logger.info(f"Inserting receipt_items_cleaned for {filename}...")
                supabase.table("receipt_items_cleaned").insert(receipt_row).execute()
                logger.info(f"Inserting ses_eml_info for {filename}...")
                supabase.table("ses_eml_info").insert(eml_row).execute()
                logger.info(f"Successfully inserted data for {filename}")

                successes.append(filename)
                logger.info(f"File {filename} processed successfully")
                
            except Exception as e:
                error_msg = f"{filename} - Error: {str(e)}"
                logger.exception(f"Failed to process file {i}/{len(public_urls)}: {error_msg}")
                failures.append(error_msg)
        
        # 生成状态报告
        total_files = len(successes) + len(failures)
        success_count = len(successes)
        failure_count = len(failures)
        
        status = f"""You uploaded a total of {total_files} files: {success_count} succeeded--{successes}, {failure_count} failed--{failures}."""
        
        logger.info(f"Processing summary - Total: {total_files}, Success: {success_count}, Failed: {failure_count}")
        
        # 保存上传结果
        try:
            logger.info("Saving upload result to database...")
            supabase.table("receipt_items_upload_result").insert({"upload_result": status, "user_id": user_id}).execute()
            logger.info("Successfully saved upload result to database")
        except Exception as e:
            logger.exception(f"Failed to save upload result to database: {str(e)}")
        
        logger.info(f"upload_to_supabase completed successfully. Final status: {status}")
        return status
        
    except Exception as e:
        logger.exception(f"Critical error in upload_to_supabase for user_id {user_id}: {str(e)}")
        raise