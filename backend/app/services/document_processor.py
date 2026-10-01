import os
import uuid
import hashlib
import fitz  # PyMuPDF
from typing import List, Tuple, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.database import Document


class DocumentProcessor:
    """Handle PDF document processing and text extraction"""
    
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def validate_file(self, filename: str, file_size: int) -> Tuple[bool, str]:
        """
        Validate uploaded file
        Returns: (is_valid, error_message)
        """
        # Check file extension
        ext = filename.lower().split('.')[-1]
        if ext not in settings.ALLOWED_EXTENSIONS:
            return False, f"File type .{ext} not allowed. Only {settings.ALLOWED_EXTENSIONS} allowed."
        
        # Check file size
        max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_size_bytes:
            return False, f"File size {file_size/1024/1024:.2f}MB exceeds maximum {settings.MAX_FILE_SIZE_MB}MB"
        
        return True, ""
    
    def generate_safe_filename(self, original_filename: str) -> str:
        """Generate a safe unique filename"""
        ext = original_filename.split('.')[-1].lower()
        unique_id = str(uuid.uuid4())
        return f"{unique_id}.{ext}"
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _calculate_image_hash(self, image_bytes: bytes) -> str:
        """Calculate hash of image to detect duplicates"""
        return hashlib.md5(image_bytes).hexdigest()
    
    def save_file(self, file_content: bytes, filename: str) -> str:
        """Save uploaded file to disk"""
        file_path = os.path.join(self.upload_dir, filename)
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Set secure permissions (owner read/write only)
        os.chmod(file_path, 0o600)
        return file_path
    
    def extract_text_from_pdf(self, file_path: str, use_vision: bool = True) -> Tuple[str, int]:
        """Extract text from PDF with smart image filtering"""
        try:
            doc = fitz.open(file_path)
            text_content = ""
            
            # Track processed images
            image_cache: Dict[str, str] = {}
            seen_hashes: Dict[str, int] = {}  # hash -> count
            total_images = 0
            processed_images = 0
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text_content += f"\n--- Page {page_num + 1} ---\n"
                text_content += page.get_text()
                
                if use_vision:
                    image_list = page.get_images()
                    if image_list:
                        total_images += len(image_list)
                        print(f"📸 Found {len(image_list)} image(s) on page {page_num + 1}")
                        
                        for img_index, img in enumerate(image_list):
                            try:
                                xref = img[0]
                                base_image = doc.extract_image(xref)
                                image_bytes = base_image["image"]
                                image_ext = base_image["ext"]
                                
                                # Calculate hash
                                image_hash = self._calculate_image_hash(image_bytes)
                                seen_hashes[image_hash] = seen_hashes.get(image_hash, 0) + 1
                                
                                # Skip if seen more than once (likely decorative)
                                if seen_hashes[image_hash] > 1:
                                    print(f"  ⏭️  Skipped duplicate image {img_index + 1}")
                                    continue
                                
                                # Skip small images (likely logos/icons)
                                if len(image_bytes) < 5000:  # < 5KB
                                    print(f"  ⏭️  Skipped small image {img_index + 1} ({len(image_bytes)} bytes)")
                                    continue
                                
                                # Process unique, substantial image
                                description = self._describe_image_sync(image_bytes, image_ext)
                                text_content += f"\n[IMAGE: {description}]\n"
                                processed_images += 1
                                print(f"  ✅ Processed unique image {img_index + 1}")
                                
                            except Exception as e:
                                print(f"  ⚠️  Error: {str(e)}")
            
            page_count = len(doc)
            doc.close()
            
            # Summary
            skipped = total_images - processed_images
            print(f"📊 Images: {total_images} total, {processed_images} processed, {skipped} skipped")
            if skipped > 0:
                print(f"💰 Saved ~${skipped * 0.03:.2f}")
            
            return text_content, page_count
        
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    def _describe_image_sync(self, image_bytes: bytes, image_format: str) -> str:
        """Synchronous wrapper for Vision API call"""
        import httpx
        import base64
        from app.core.config import settings
        
        if not settings.OPENROUTER_API_KEY:
            return "[Vision API not configured]"
        
        # Encode image to base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        try:
            # Use synchronous httpx client
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": settings.DEFAULT_MODEL,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": "Describe this technical diagram or image in detail. Focus on: 1) Main components and their relationships, 2) Technical specifications visible, 3) Network topology or system architecture if applicable, 4) Any labels, numbers, or measurements shown. Be concise but comprehensive."
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/{image_format};base64,{image_base64}"
                                        }
                                    }
                                ]
                            }
                        ],
                        "max_tokens": 500
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                return data["choices"][0]["message"]["content"]
        
        except Exception as e:
            print(f"    ❌ Vision API Error: {str(e)}")
            return f"[Image description failed]"
    
    def sanitize_text(self, text: str) -> str:
        """
        Sanitize extracted text to prevent prompt injection
        Remove suspicious patterns that could be instructions
        """
        # Remove common injection patterns
        suspicious_patterns = [
            "ignore previous instructions",
            "ignore all previous",
            "disregard previous",
            "new instructions:",
            "system:",
            "assistant:",
        ]
        
        text_lower = text.lower()
        for pattern in suspicious_patterns:
            if pattern in text_lower:
                # Log this as suspicious activity
                print(f"⚠️  Warning: Suspicious pattern detected: {pattern}")
        
        # For now, we'll keep the text but log suspicious patterns
        # In production, you might want to strip or flag these sections
        return text
    
    def create_document_record(
        self,
        db: Session,
        user_id: int,
        original_filename: str,
        safe_filename: str,
        file_path: str,
        file_size: int,
        file_hash: str
    ) -> Document:
        """Create document record in database"""
        document_id = str(uuid.uuid4())
        
        document = Document(
            id=document_id,
            original_filename=original_filename,
            safe_filename=safe_filename,
            file_path=file_path,
            file_size=file_size,
            file_hash=file_hash,
            mime_type="application/pdf",
            status="processing",
            user_id=user_id
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        return document
    
    def update_document_status(
        self,
        db: Session,
        document_id: str,
        status: str,
        page_count: int = None,
        chunk_count: int = None,
        error_message: str = None
    ):
        """Update document processing status"""
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.status = status
            document.page_count = page_count
            document.chunk_count = chunk_count
            document.error_message = error_message
            document.processed_at = datetime.utcnow() if status in ["ready", "failed"] else None
            db.commit()