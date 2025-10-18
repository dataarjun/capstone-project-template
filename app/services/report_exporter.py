"""
Report Exporter Service

This service provides multi-format export capabilities for AML investigation reports,
including JSON, CSV, Markdown, and PDF formats with SAR compliance features.
"""

import json
import csv
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import pandas as pd

# PDF generation
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak
from reportlab.platypus.tableofcontents import TableOfContents

# Markdown generation
import markdown
from markdown.extensions import tables, codehilite

from app.core.logger import get_logger
from app.models.aml_models import ReportDoc, InvestigationSummary, BatchProcessingResult

logger = get_logger(__name__)


class ReportExporter:
    """
    Multi-format report exporter for AML investigations
    """
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # PDF styles
        self.styles = getSampleStyleSheet()
        self._setup_pdf_styles()
    
    def _setup_pdf_styles(self):
        """Setup custom PDF styles"""
        
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.darkred,
            alignment=1  # Center
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue,
            borderWidth=1,
            borderColor=colors.grey,
            borderPadding=5
        ))
        
        # Risk indicator style
        self.styles.add(ParagraphStyle(
            name='RiskIndicator',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            textColor=colors.darkred,
            borderWidth=1,
            borderColor=colors.red,
            borderPadding=3
        ))
    
    async def export_json(self, data: List[Dict[str, Any]], 
                         filename: Optional[str] = None) -> str:
        """
        Export data to JSON format
        
        Args:
            data: List of investigation results or single result
            filename: Optional custom filename
            
        Returns:
            Path to exported file
        """
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"aml_report_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str, ensure_ascii=False)
            
            logger.info(f"JSON report exported: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to export JSON report: {str(e)}")
            raise
    
    async def export_csv(self, data: List[Dict[str, Any]], 
                        filename: Optional[str] = None) -> str:
        """
        Export data to CSV format for Excel analysis
        
        Args:
            data: List of investigation results
            filename: Optional custom filename
            
        Returns:
            Path to exported file
        """
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"aml_report_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        try:
            # Flatten nested data for CSV
            flattened_data = []
            for item in data:
                flat_item = self._flatten_dict(item)
                flattened_data.append(flat_item)
            
            if flattened_data:
                df = pd.DataFrame(flattened_data)
                df.to_csv(filepath, index=False, encoding='utf-8')
            
            logger.info(f"CSV report exported: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to export CSV report: {str(e)}")
            raise
    
    async def export_markdown(self, data: List[Dict[str, Any]], 
                            filename: Optional[str] = None) -> str:
        """
        Export data to Markdown format for documentation
        
        Args:
            data: List of investigation results
            filename: Optional custom filename
            
        Returns:
            Path to exported file
        """
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"aml_report_{timestamp}.md"
        
        filepath = self.output_dir / filename
        
        try:
            markdown_content = self._generate_markdown_report(data)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            logger.info(f"Markdown report exported: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to export Markdown report: {str(e)}")
            raise
    
    async def export_pdf(self, data: List[Dict[str, Any]], 
                        filename: Optional[str] = None,
                        sar_format: bool = True) -> str:
        """
        Export data to PDF format for compliance/regulatory submission
        
        Args:
            data: List of investigation results
            filename: Optional custom filename
            sar_format: Use SAR-compliant format
            
        Returns:
            Path to exported file
        """
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"aml_report_{timestamp}.pdf"
        
        filepath = self.output_dir / filename
        
        try:
            doc = SimpleDocTemplate(str(filepath), pagesize=A4, topMargin=1*inch)
            story = []
            
            if sar_format:
                story = self._generate_sar_pdf(data, story)
            else:
                story = self._generate_standard_pdf(data, story)
            
            doc.build(story)
            
            logger.info(f"PDF report exported: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to export PDF report: {str(e)}")
            raise
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """Flatten nested dictionary for CSV export"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Convert list to string for CSV
                items.append((new_key, str(v)))
            else:
                items.append((new_key, v))
        return dict(items)
    
    def _generate_markdown_report(self, data: List[Dict[str, Any]]) -> str:
        """Generate Markdown report content"""
        
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        content = f"""# AML Investigation Report

**Generated:** {timestamp}  
**Total Cases:** {len(data)}

## Executive Summary

"""
        
        if data:
            # Calculate summary statistics
            escalated_cases = sum(1 for item in data if item.get('risk_level') in ['High', 'Critical'])
            sar_cases = sum(1 for item in data if item.get('reporting_status') == 'SAR_FILED')
            
            content += f"""
- **Escalated Cases:** {escalated_cases}/{len(data)} ({escalated_cases/len(data)*100:.1f}%)
- **SAR Filed:** {sar_cases}
- **Average Risk Score:** {sum(item.get('risk_score', 0) for item in data) / len(data):.1f}

"""
        
        content += "## Case Details\n\n"
        
        for i, item in enumerate(data, 1):
            content += f"### Case {i}: {item.get('case_id', 'Unknown')}\n\n"
            
            # Basic information
            content += f"**Risk Level:** {item.get('risk_level', 'Unknown')}  \n"
            content += f"**Risk Score:** {item.get('risk_score', 0)}/100  \n"
            content += f"**Status:** {item.get('reporting_status', 'Unknown')}  \n"
            
            # Transaction details
            transaction = item.get('transaction', {})
            if transaction:
                content += f"**Amount:** ${transaction.get('amount', 0):,.2f}  \n"
                content += f"**Currency:** {transaction.get('currency', 'USD')}  \n"
                content += f"**Type:** {transaction.get('transaction_type', 'Unknown')}  \n"
            
            # Risk factors
            risk_factors = item.get('risk_factors', [])
            if risk_factors:
                content += f"**Risk Factors:** {', '.join(risk_factors[:5])}  \n"
            
            # Alerts
            alerts = item.get('alerts', [])
            if alerts:
                content += f"**Alerts:** {', '.join(alerts)}  \n"
            
            # Approval status
            approval_status = item.get('approval_status')
            if approval_status:
                content += f"**Approval Status:** {approval_status}  \n"
            
            content += "\n---\n\n"
        
        return content
    
    def _generate_sar_pdf(self, data: List[Dict[str, Any]], story: List) -> List:
        """Generate SAR-compliant PDF content"""
        
        # Title page
        story.append(Paragraph("SUSPICIOUS ACTIVITY REPORT", self.styles['CustomTitle']))
        story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}", self.styles['Normal']))
        story.append(Spacer(1, 0.5*inch))
        
        # Executive summary
        story.append(Paragraph("EXECUTIVE SUMMARY", self.styles['SectionHeader']))
        
        if data:
            escalated_cases = sum(1 for item in data if item.get('risk_level') in ['High', 'Critical'])
            sar_cases = sum(1 for item in data if item.get('reporting_status') == 'SAR_FILED')
            avg_risk = sum(item.get('risk_score', 0) for item in data) / len(data)
            
            summary_data = [
                ['Total Cases Investigated', str(len(data))],
                ['High/Critical Risk Cases', str(escalated_cases)],
                ['SAR Filed', str(sar_cases)],
                ['Average Risk Score', f"{avg_risk:.1f}/100"]
            ]
            
            summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Case details
        for i, item in enumerate(data, 1):
            story.append(Paragraph(f"CASE {i}: {item.get('case_id', 'Unknown')}", self.styles['SectionHeader']))
            
            # Case information table
            case_data = [
                ['Field', 'Value'],
                ['Risk Level', item.get('risk_level', 'Unknown')],
                ['Risk Score', f"{item.get('risk_score', 0)}/100"],
                ['Reporting Status', item.get('reporting_status', 'Unknown')],
                ['Approval Status', item.get('approval_status', 'N/A')]
            ]
            
            # Add transaction details
            transaction = item.get('transaction', {})
            if transaction:
                case_data.extend([
                    ['Transaction Amount', f"${transaction.get('amount', 0):,.2f}"],
                    ['Currency', transaction.get('currency', 'USD')],
                    ['Transaction Type', transaction.get('transaction_type', 'Unknown')],
                    ['Customer ID', transaction.get('customer_id', 'Unknown')]
                ])
            
            case_table = Table(case_data, colWidths=[2*inch, 3*inch])
            case_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(case_table)
            
            # Risk factors
            risk_factors = item.get('risk_factors', [])
            if risk_factors:
                story.append(Spacer(1, 0.2*inch))
                story.append(Paragraph("Risk Factors:", self.styles['Heading3']))
                for factor in risk_factors[:10]:  # Limit to top 10
                    story.append(Paragraph(f"• {factor}", self.styles['RiskIndicator']))
            
            # Decision path
            decision_path = item.get('decision_path', [])
            if decision_path:
                story.append(Spacer(1, 0.2*inch))
                story.append(Paragraph("Investigation Path:", self.styles['Heading3']))
                story.append(Paragraph(" → ".join(decision_path), self.styles['Normal']))
            
            story.append(Spacer(1, 0.3*inch))
            
            if i < len(data):
                story.append(PageBreak())
        
        return story
    
    def _generate_standard_pdf(self, data: List[Dict[str, Any]], story: List) -> List:
        """Generate standard PDF content"""
        
        # Title
        story.append(Paragraph("AML Investigation Report", self.styles['CustomTitle']))
        story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}", self.styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Summary table
        if data:
            summary_data = [['Case ID', 'Risk Level', 'Risk Score', 'Status', 'Amount']]
            
            for item in data:
                transaction = item.get('transaction', {})
                summary_data.append([
                    item.get('case_id', 'Unknown'),
                    item.get('risk_level', 'Unknown'),
                    str(item.get('risk_score', 0)),
                    item.get('reporting_status', 'Unknown'),
                    f"${transaction.get('amount', 0):,.2f}"
                ])
            
            summary_table = Table(summary_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1.5*inch, 1*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
        
        return story
    
    async def export_batch_summary(self, summary: BatchProcessingResult, 
                                 format: str = "json") -> str:
        """
        Export batch processing summary
        
        Args:
            summary: BatchProcessingResult object
            format: Export format (json, csv, markdown, pdf)
            
        Returns:
            Path to exported file
        """
        data = [summary.model_dump()]
        
        if format == "json":
            return await self.export_json(data, f"batch_summary_{summary.batch_id}.json")
        elif format == "csv":
            return await self.export_csv(data, f"batch_summary_{summary.batch_id}.csv")
        elif format == "markdown":
            return await self.export_markdown(data, f"batch_summary_{summary.batch_id}.md")
        elif format == "pdf":
            return await self.export_pdf(data, f"batch_summary_{summary.batch_id}.pdf")
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def get_export_history(self) -> List[Dict[str, Any]]:
        """Get list of exported files"""
        files = []
        for file_path in self.output_dir.glob("*"):
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "filename": file_path.name,
                    "path": str(file_path),
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        return sorted(files, key=lambda x: x["modified"], reverse=True)


# Global report exporter instance
report_exporter = ReportExporter()
