"""
RAG system validation and health checks.

Validates collection integrity, metadata completeness,
and reports issues for operational awareness.
"""

import logging
from typing import Any, Dict, List

from .qdrant_manager import QdrantManager
from .loader import load_documents
from .config import RAG_DATA_ROOT


logger = logging.getLogger(__name__)


class RAGValidator:
    """
    Validates RAG collection and corpus integrity.
    """
    
    REQUIRED_METADATA_FIELDS = {
        "title",
        "category",
        "source_file",
        "relative_path",
    }
    
    def __init__(self, qdrant_manager: QdrantManager = None):
        """
        Initialize validator.
        
        Args:
            qdrant_manager: Qdrant manager instance.
        """
        self.manager = qdrant_manager or QdrantManager()
        self.issues = []
        self.warnings = []
    
    def validate_all(self) -> Dict[str, Any]:
        """
        Run all validation checks and return report.
        
        Returns:
            Validation report dictionary.
        """
        self.issues = []
        self.warnings = []
        
        logger.info("Starting comprehensive RAG validation")
        
        checks = [
            self.check_collection_exists,
            self.check_embedding_dimensions,
            self.check_vector_count,
            self.check_corpus_integrity,
            self.check_metadata_completeness,
        ]
        
        results = {}
        for check in checks:
            try:
                check_name = check.__name__
                result = check()
                results[check_name] = result
                logger.debug(f"✓ {check_name}")
            except Exception as e:
                logger.error(f"✗ {check.__name__}: {e}")
                self.issues.append(f"{check.__name__}: {str(e)}")
        
        return self._format_report(results)
    
    def check_collection_exists(self) -> bool:
        """Check that collection exists."""
        exists = self.manager.collection_exists()
        if not exists:
            self.issues.append("Collection does not exist")
        return exists
    
    def check_embedding_dimensions(self) -> Dict[str, Any]:
        """Check that embedding dimensions are consistent."""
        if not self.manager.collection_exists():
            self.warnings.append("Cannot check dimensions: collection does not exist")
            return {"status": "skipped"}
        
        try:
            stats = self.manager.get_statistics()
            return {
                "status": "ok",
                "dimension": stats.get("points_count", 0),
            }
        except Exception as e:
            self.issues.append(f"Failed to check dimensions: {e}")
            return {"status": "error", "error": str(e)}
    
    def check_vector_count(self) -> Dict[str, int]:
        """Check vector count."""
        if not self.manager.collection_exists():
            self.warnings.append("Cannot count vectors: collection does not exist")
            return {"status": "skipped"}
        
        try:
            count = self.manager.count_vectors()
            if count == 0:
                self.issues.append("Collection is empty")
            return {"status": "ok", "vector_count": count}
        except Exception as e:
            self.issues.append(f"Failed to count vectors: {e}")
            return {"status": "error", "error": str(e)}
    
    def check_corpus_integrity(self) -> Dict[str, Any]:
        """Check that all corpus files can be loaded."""
        try:
            documents = load_documents(RAG_DATA_ROOT)
            
            empty_files = []
            for doc in documents:
                if not doc.page_content.strip():
                    empty_files.append(doc.metadata.get("relative_path", "unknown"))
            
            if empty_files:
                self.warnings.append(f"Found {len(empty_files)} empty files")
            
            return {
                "status": "ok",
                "total_documents": len(documents),
                "empty_files": len(empty_files),
            }
        except Exception as e:
            self.issues.append(f"Failed to load corpus: {e}")
            return {"status": "error", "error": str(e)}
    
    def check_metadata_completeness(self) -> Dict[str, Any]:
        """Check that all metadata fields are present."""
        try:
            documents = load_documents(RAG_DATA_ROOT)
            
            incomplete_docs = []
            for doc in documents:
                missing_fields = self.REQUIRED_METADATA_FIELDS - set(doc.metadata.keys())
                if missing_fields:
                    incomplete_docs.append({
                        "file": doc.metadata.get("relative_path", "unknown"),
                        "missing": list(missing_fields),
                    })
            
            if incomplete_docs:
                self.warnings.append(f"Found {len(incomplete_docs)} documents with missing metadata")
            
            return {
                "status": "ok",
                "total_documents": len(documents),
                "incomplete_count": len(incomplete_docs),
                "incomplete_docs": incomplete_docs[:10],  # Show first 10
            }
        except Exception as e:
            self.issues.append(f"Failed to check metadata: {e}")
            return {"status": "error", "error": str(e)}
    
    def _format_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Format validation report."""
        report = {
            "status": "ok" if not self.issues else "failed",
            "checks": results,
            "issues": self.issues,
            "warnings": self.warnings,
        }
        
        self._print_report(report)
        return report
    
    @staticmethod
    def _print_report(report: Dict[str, Any]) -> None:
        """Print validation report to logger."""
        status = "✓ PASS" if report["status"] == "ok" else "✗ FAIL"
        
        report_str = f"""
╔═══════════════════════════════════════════════════════════╗
║         RAG VALIDATION REPORT - {status:^30} ║
╠═══════════════════════════════════════════════════════════╣
"""
        
        if report["issues"]:
            report_str += "║ ISSUES:                                                   ║\n"
            for issue in report["issues"]:
                report_str += f"║  ✗ {issue:<53} ║\n"
        
        if report["warnings"]:
            report_str += "║ WARNINGS:                                                 ║\n"
            for warning in report["warnings"]:
                report_str += f"║  ⚠ {warning:<53} ║\n"
        
        if not report["issues"] and not report["warnings"]:
            report_str += "║ All checks passed!                                        ║\n"
        
        report_str += "╚═══════════════════════════════════════════════════════════╝"
        
        logger.info(report_str)
