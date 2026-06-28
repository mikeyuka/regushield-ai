from celery import Celery
from app.config import settings
from app.scraper import scan_subreddits
from app.notifications import send_webhook_notification

celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(name="app.worker.test_celery_task")
def test_celery_task(word: str) -> str:
    return f"ReguShield AI received: {word}"

@celery_app.task(name="app.worker.scheduled_reddit_scrape")
def scheduled_reddit_scrape(limit: int = 10):
    """
    Asynchronous Celery task that scans subreddits for compliance and brand
    protection panic posts and returns the matching results metadata.
    """
    logger_celery = celery_app.log.get_default_logger()
    logger_celery.info(f"Starting scheduled Reddit compliance scrape with limit={limit}...")
    results = scan_subreddits(limit=limit)
    logger_celery.info(f"Finished scraping. Found {len(results)} matching posts.")
    
    # Send webhook notification for each matching post
    for post in results:
        try:
            logger_celery.info(f"Sending webhook notification for post: {post.get('title')}")
            send_webhook_notification(post)
        except Exception as e:
            logger_celery.error(f"Error sending webhook notification for post: {e}", exc_info=True)
            
    return results


@celery_app.task(name="app.worker.process_document_verification")
def process_document_verification(document_id: str) -> dict:
    """
    Background Celery task that retrieves a SupplierDocument record,
    updates its status to PROCESSING, parses the compliance document,
    saves raw text and extracted metadata, and evaluates validation status.
    """
    import os
    import uuid
    from app.database import SessionLocal
    from app.models import SupplierDocument, DocValidationStatus
    from app.parser import parse_compliance_document, extract_text

    logger_celery = celery_app.log.get_default_logger()
    logger_celery.info(f"Starting process_document_verification for ID: {document_id}")

    db = SessionLocal()
    try:
        # Resolve document_id to UUID
        try:
            doc_uuid = uuid.UUID(document_id)
        except ValueError:
            doc_uuid = document_id

        doc = db.query(SupplierDocument).filter(SupplierDocument.id == doc_uuid).first()
        if not doc:
            logger_celery.error(f"SupplierDocument with ID {document_id} not found.")
            return {"status": "FAILED", "error": "Document not found"}

        # Update its status to PROCESSING
        doc.status = DocValidationStatus.PROCESSING
        db.commit()

        # Helper to resolve physical path on disk
        def resolve_physical_path(file_url: str) -> str:
            if os.path.exists(file_url):
                return file_url
            
            if file_url.startswith("/static/"):
                filename = file_url[len("/static/"):]
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                path = os.path.join(base_dir, "uploads", filename)
                if os.path.exists(path):
                    return path

            filename = os.path.basename(file_url)
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            path = os.path.join(base_dir, "uploads", filename)
            if os.path.exists(path):
                return path

            return file_url

        physical_path = resolve_physical_path(doc.file_url)
        logger_celery.info(f"Resolved physical path: {physical_path}")

        # Extract raw text and parse compliance document
        raw_text = extract_text(physical_path)
        parsed_data = parse_compliance_document(physical_path, doc.doc_type.value)

        # Save outputs
        doc.raw_ocr_text = raw_text
        doc.extracted_metadata = parsed_data

        # Evaluate status
        is_accredited = parsed_data.get("is_accredited", False)
        doc_status = parsed_data.get("declaration_of_conformity_status", "INVALID")
        hazards = parsed_data.get("hazards_identified", [])
        
        # Define high-risk hazards
        HIGH_RISK_HAZARDS = {"phthalates", "lead", "cadmium", "toxic", "heavy metals", "flammable"}
        high_risk_flagged = any(h.lower() in HIGH_RISK_HAZARDS for h in hazards)

        if is_accredited and doc_status == "VALID" and not high_risk_flagged:
            doc.status = DocValidationStatus.VALIDATED
        else:
            doc.status = DocValidationStatus.REJECTED

        db.commit()

        # Check if all documents for the compliance request are validated/rejected
        comp_req = doc.compliance_request
        if comp_req:
            from app.models import ComplianceStatus
            all_docs = comp_req.supplier_documents
            all_processed = all(
                d.status in (DocValidationStatus.VALIDATED, DocValidationStatus.REJECTED)
                for d in all_docs
            )
            
            if all_processed:
                logger_celery.info(f"All documents for ComplianceRequest {comp_req.id} are processed. Triggering compilation...")
                comp_req.status = ComplianceStatus.COMPILING
                db.commit()
                
                # Fetch product information
                product = comp_req.product
                product_data = {
                    "sku": product.sku,
                    "name": product.name,
                    "category": product.category,
                    "destination_market": product.destination_market
                }
                
                # Format validation results
                validation_results = []
                for d in all_docs:
                    validation_results.append({
                        "file_name": d.file_name,
                        "doc_type": d.doc_type.value,
                        "status": d.status.value,
                        "extracted_metadata": d.extracted_metadata or {}
                    })
                
                # Compile PDF blueprint
                from app.pdf_generator import compile_pdf_blueprint
                output_filename = f"blueprint_{comp_req.id}.pdf"
                
                try:
                    static_url = compile_pdf_blueprint(
                        product_data=product_data,
                        validation_results=validation_results,
                        output_filename=output_filename
                    )
                    
                    comp_req.generated_pdf_url = static_url
                    comp_req.status = ComplianceStatus.COMPLETED
                    db.commit()
                    logger_celery.info(f"Compliance blueprint compilation completed successfully: {static_url}")
                except Exception as comp_err:
                    logger_celery.error(f"Error compiling compliance blueprint: {comp_err}", exc_info=True)
                    comp_req.status = ComplianceStatus.FAILED
                    comp_req.failed_reason = str(comp_err)
                    db.commit()

        logger_celery.info(f"Finished process_document_verification. Status: {doc.status}")
        return {
            "status": doc.status.value,
            "document_id": document_id,
            "extracted_metadata": parsed_data
        }

    except Exception as e:
        logger_celery.error(f"Error processing document verification: {e}", exc_info=True)
        try:
            doc.status = DocValidationStatus.REJECTED
            doc.error_log = str(e)
            db.commit()
        except Exception:
            pass
        return {"status": "FAILED", "error": str(e)}
    finally:
        db.close()


