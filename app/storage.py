"""SQLite storage for documents and extractions."""
import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.schema import DocumentMetadata, ExtractedData, DocumentResponse

Base = declarative_base()


class Document(Base):
    """SQLAlchemy model for documents table."""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    extraction_mode = Column(String(50), nullable=False)
    status = Column(String(50), default="success")
    error_message = Column(Text, nullable=True)
    extracted_json = Column(Text, nullable=True)


class Storage:
    """Handle document persistence in SQLite and JSON files."""
    
    def __init__(self):
        """Initialize database connection and create tables."""
        # Ensure data directory exists
        db_dir = os.path.dirname(settings.sqlite_db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        # Create engine and session
        self.engine = create_engine(f"sqlite:///{settings.sqlite_db_path}")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def save_document(
        self,
        filename: str,
        extraction_mode: str,
        extracted_data: Optional[ExtractedData] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> DocumentResponse:
        """
        Save a processed document to database and JSON file.
        
        Args:
            filename: Name of the uploaded file
            extraction_mode: Mode used for extraction ("llm" or "rules")
            extracted_data: Extracted structured data
            status: Processing status
            error_message: Error message if processing failed
            
        Returns:
            DocumentResponse with metadata and extracted data
        """
        session = self.SessionLocal()
        
        try:
            # Prepare JSON
            extracted_json = None
            if extracted_data:
                extracted_json = extracted_data.model_dump_json()
            
            # Create database record
            doc = Document(
                filename=filename,
                extraction_mode=extraction_mode,
                status=status,
                error_message=error_message,
                extracted_json=extracted_json
            )
            
            session.add(doc)
            session.commit()
            session.refresh(doc)
            
            # Save JSON to file if successful
            if extracted_data and status == "success":
                self._save_json_file(doc.id, extracted_data)
            
            # Build response
            metadata = DocumentMetadata(
                id=doc.id,
                filename=doc.filename,
                upload_date=doc.upload_date,
                extraction_mode=doc.extraction_mode,
                status=doc.status,
                error_message=doc.error_message
            )
            
            return DocumentResponse(
                metadata=metadata,
                extracted_data=extracted_data
            )
            
        finally:
            session.close()
    
    def get_documents(self, limit: int = 100, offset: int = 0) -> List[DocumentResponse]:
        """
        Retrieve list of processed documents.
        
        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            
        Returns:
            List of DocumentResponse objects
        """
        session = self.SessionLocal()
        
        try:
            docs = session.query(Document).order_by(
                Document.upload_date.desc()
            ).limit(limit).offset(offset).all()
            
            results = []
            for doc in docs:
                metadata = DocumentMetadata(
                    id=doc.id,
                    filename=doc.filename,
                    upload_date=doc.upload_date,
                    extraction_mode=doc.extraction_mode,
                    status=doc.status,
                    error_message=doc.error_message
                )
                
                extracted_data = None
                if doc.extracted_json:
                    try:
                        extracted_data = ExtractedData.model_validate_json(doc.extracted_json)
                    except Exception:
                        pass
                
                results.append(DocumentResponse(
                    metadata=metadata,
                    extracted_data=extracted_data
                ))
            
            return results
            
        finally:
            session.close()
    
    def get_document_by_id(self, doc_id: int) -> Optional[DocumentResponse]:
        """
        Retrieve a specific document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            DocumentResponse or None if not found
        """
        session = self.SessionLocal()
        
        try:
            doc = session.query(Document).filter(Document.id == doc_id).first()
            
            if not doc:
                return None
            
            metadata = DocumentMetadata(
                id=doc.id,
                filename=doc.filename,
                upload_date=doc.upload_date,
                extraction_mode=doc.extraction_mode,
                status=doc.status,
                error_message=doc.error_message
            )
            
            extracted_data = None
            if doc.extracted_json:
                try:
                    extracted_data = ExtractedData.model_validate_json(doc.extracted_json)
                except Exception:
                    pass
            
            return DocumentResponse(
                metadata=metadata,
                extracted_data=extracted_data
            )
            
        finally:
            session.close()
    
    def _save_json_file(self, doc_id: int, extracted_data: ExtractedData):
        """Save extracted data to a JSON file."""
        # Ensure output directory exists
        if not os.path.exists(settings.json_output_dir):
            os.makedirs(settings.json_output_dir, exist_ok=True)
        
        # Generate filename
        filename = f"document_{doc_id}.json"
        filepath = os.path.join(settings.json_output_dir, filename)
        
        # Write JSON
        with open(filepath, "w") as f:
            f.write(extracted_data.model_dump_json(indent=2))


# Singleton instance
storage = Storage()
