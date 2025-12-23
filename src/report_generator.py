"""
Report Generator for LLMSmartSec.

This module generates PDF audit reports from the audit results.
"""

import os
from datetime import datetime
from typing import Dict, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY


class ReportGenerator:
    """Generates PDF audit reports from LLMSmartSec results."""

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the report generator.

        Args:
            output_dir: Directory for output files. Defaults to ../Results/
        """
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(__file__), "..", "Results")
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        # Set up styles
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()

    def _create_custom_styles(self):
        """Create custom paragraph styles for the report."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1a365d')
        ))

        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#2c5282')
        ))

        # Subsection style
        self.styles.add(ParagraphStyle(
            name='SubSection',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.HexColor('#4a5568')
        ))

        # Body text style
        self.styles.add(ParagraphStyle(
            name='BodyText',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY,
            spaceAfter=8
        ))

        # Code style
        self.styles.add(ParagraphStyle(
            name='Code',
            parent=self.styles['Code'],
            fontSize=8,
            leading=10,
            backColor=colors.HexColor('#f7fafc'),
            borderColor=colors.HexColor('#e2e8f0'),
            borderWidth=1,
            borderPadding=5
        ))

        # Finding styles by severity
        for severity, color in [
            ('Critical', '#c53030'),
            ('High', '#dd6b20'),
            ('Medium', '#d69e2e'),
            ('Low', '#38a169'),
            ('Info', '#3182ce')
        ]:
            self.styles.add(ParagraphStyle(
                name=f'Finding{severity}',
                parent=self.styles['Normal'],
                fontSize=10,
                leftIndent=10,
                textColor=colors.HexColor(color),
                spaceBefore=5,
                spaceAfter=5
            ))

    def generate_pdf(self, audit_results: Dict, filename: Optional[str] = None) -> str:
        """
        Generate a PDF report from audit results.

        Args:
            audit_results: Dictionary containing the audit results
            filename: Output filename. Auto-generated if not provided.

        Returns:
            Path to the generated PDF file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            address = audit_results.get("contract_address", "unknown")[:10]
            filename = f"audit_report_{address}_{timestamp}.pdf"

        filepath = os.path.join(self.output_dir, filename)

        # Create document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Build content
        story = []

        # Title page
        story.extend(self._create_title_page(audit_results))
        story.append(PageBreak())

        # Table of contents placeholder
        story.append(Paragraph("Table of Contents", self.styles['SectionHeader']))
        story.append(Spacer(1, 20))
        toc_items = [
            "1. Executive Summary",
            "2. Contract Overview",
            "3. Developer Analysis",
            "4. Security Vulnerabilities",
            "5. Auditor Assessment",
            "6. Recommendations",
            "7. Conclusion"
        ]
        for item in toc_items:
            story.append(Paragraph(item, self.styles['BodyText']))
        story.append(PageBreak())

        # Executive Summary
        story.extend(self._create_executive_summary(audit_results))
        story.append(PageBreak())

        # Developer Analysis
        story.extend(self._create_section(
            "Developer Analysis (LLMDev)",
            audit_results.get("perspectives", {}).get("developer", "No analysis available")
        ))
        story.append(PageBreak())

        # Security Vulnerabilities
        story.extend(self._create_section(
            "Security Vulnerabilities (LLMeHack)",
            audit_results.get("perspectives", {}).get("ethical_hacker", "No analysis available")
        ))
        story.append(PageBreak())

        # Auditor Assessment
        story.extend(self._create_section(
            "Auditor Assessment (LLMAudit)",
            audit_results.get("perspectives", {}).get("auditor", "No analysis available")
        ))
        story.append(PageBreak())

        # Final Report
        story.extend(self._create_section(
            "Consolidated Report",
            audit_results.get("final_report", "No report generated")
        ))

        # Disclaimer
        story.append(PageBreak())
        story.extend(self._create_disclaimer())

        # Build PDF
        doc.build(story)

        print(f"Report generated: {filepath}")
        return filepath

    def _create_title_page(self, audit_results: Dict) -> list:
        """Create the title page elements."""
        elements = []

        elements.append(Spacer(1, 2*inch))

        # Title
        elements.append(Paragraph(
            "Smart Contract Security Audit Report",
            self.styles['ReportTitle']
        ))

        elements.append(Spacer(1, 0.5*inch))

        # Subtitle
        elements.append(Paragraph(
            "Generated by LLMSmartSec",
            ParagraphStyle(
                'Subtitle',
                parent=self.styles['Normal'],
                fontSize=14,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#4a5568')
            )
        ))

        elements.append(Spacer(1, inch))

        # Contract info table
        contract_address = audit_results.get("contract_address", "Unknown")
        timestamp = audit_results.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        info_data = [
            ["Contract Address:", contract_address],
            ["Audit Date:", timestamp],
            ["Report Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        ]

        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2c5282')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))

        elements.append(info_table)

        return elements

    def _create_executive_summary(self, audit_results: Dict) -> list:
        """Create the executive summary section."""
        elements = []

        elements.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        elements.append(Spacer(1, 10))

        # Summary text
        summary_text = """
        This report presents the findings of an AI-powered security audit conducted on the
        specified smart contract. The audit was performed using LLMSmartSec, which analyzes
        contracts from three distinct perspectives: Developer (LLMDev), Ethical Hacker (LLMeHack),
        and Professional Auditor (LLMAudit).
        """
        elements.append(Paragraph(summary_text.strip(), self.styles['BodyText']))

        elements.append(Spacer(1, 15))

        # Methodology
        elements.append(Paragraph("Methodology", self.styles['SubSection']))
        methodology = [
            "Line-by-line code analysis from a developer perspective",
            "Adversarial vulnerability scanning from an ethical hacker perspective",
            "Comprehensive audit assessment from a professional auditor perspective",
            "Pattern matching against known vulnerability database",
            "Consolidated report generation with prioritized recommendations"
        ]
        for item in methodology:
            elements.append(Paragraph(f"• {item}", self.styles['BodyText']))

        return elements

    def _create_section(self, title: str, content: str) -> list:
        """Create a content section."""
        elements = []

        elements.append(Paragraph(title, self.styles['SectionHeader']))
        elements.append(Spacer(1, 10))

        # Split content into paragraphs
        paragraphs = content.split('\n\n') if content else ["No content available"]

        for para in paragraphs:
            if para.strip():
                # Check if it looks like a header
                if para.strip().startswith('#'):
                    # Remove markdown headers
                    clean_text = para.strip().lstrip('#').strip()
                    elements.append(Paragraph(clean_text, self.styles['SubSection']))
                elif para.strip().startswith('- ') or para.strip().startswith('* '):
                    # Handle bullet points
                    items = para.strip().split('\n')
                    for item in items:
                        clean_item = item.lstrip('-* ').strip()
                        if clean_item:
                            elements.append(Paragraph(f"• {clean_item}", self.styles['BodyText']))
                else:
                    # Regular paragraph
                    # Escape special characters for ReportLab
                    safe_text = para.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    try:
                        elements.append(Paragraph(safe_text, self.styles['BodyText']))
                    except:
                        # If paragraph fails, add as plain text
                        elements.append(Paragraph(para[:500] + "...", self.styles['BodyText']))

                elements.append(Spacer(1, 5))

        return elements

    def _create_disclaimer(self) -> list:
        """Create the disclaimer section."""
        elements = []

        elements.append(Paragraph("Disclaimer", self.styles['SectionHeader']))
        elements.append(Spacer(1, 10))

        disclaimer_text = """
        This audit report is generated by an AI-powered system (LLMSmartSec) and should be
        considered as a supplementary tool for security assessment. While the system employs
        advanced language models to analyze smart contracts from multiple perspectives, it
        may not identify all potential vulnerabilities or security issues.

        This report does not constitute financial, legal, or investment advice. The findings
        and recommendations should be reviewed by qualified security professionals before
        making any decisions regarding the smart contract.

        The authors and developers of LLMSmartSec are not liable for any losses or damages
        resulting from the use of this report or the audited smart contract.

        Always conduct thorough manual reviews and consider engaging professional auditors
        for critical smart contract deployments.
        """

        for para in disclaimer_text.strip().split('\n\n'):
            if para.strip():
                elements.append(Paragraph(para.strip(), self.styles['BodyText']))
                elements.append(Spacer(1, 8))

        return elements


def main():
    """Example usage of ReportGenerator."""
    # Sample audit results
    sample_results = {
        "contract_address": "0x1234567890abcdef",
        "timestamp": "2024-01-15 10:30:00",
        "perspectives": {
            "developer": """
## Code Review Summary

The contract implements a basic token with transfer functionality.

### Observations:
- Standard ERC20 implementation
- Uses SafeMath for arithmetic operations
- Proper access control with Ownable pattern

### Recommendations:
- Consider adding events for all state changes
- Implement EIP-2612 permit functionality
            """,
            "ethical_hacker": """
## Vulnerability Assessment

### Critical Findings:
None identified.

### High Severity:
1. **Potential Reentrancy** - The withdraw function makes external calls before updating state.

### Medium Severity:
1. **Centralization Risk** - Owner has significant control over contract functions.

### Low Severity:
1. **Missing Input Validation** - Some functions don't validate zero addresses.
            """,
            "auditor": """
## Audit Summary

The contract has been reviewed for common vulnerabilities and best practices.

### Overall Assessment: MEDIUM RISK

The contract implements basic functionality correctly but has some areas for improvement,
particularly around external call handling and input validation.

### Key Findings:
1. Reentrancy vulnerability in withdraw function (High)
2. Missing zero-address checks (Low)
3. No emergency pause functionality (Medium)

### Recommendations:
1. Implement checks-effects-interactions pattern
2. Add input validation for all external functions
3. Consider adding pausable functionality
            """
        },
        "final_report": """
# Final Consolidated Report

## Executive Summary
The smart contract audit revealed several findings that should be addressed before deployment.

## Risk Rating: MEDIUM

## Priority Actions:
1. Fix the reentrancy vulnerability in the withdraw function
2. Add comprehensive input validation
3. Implement emergency pause mechanism

## Conclusion
The contract requires modifications before it can be considered production-ready.
        """
    }

    # Generate report
    generator = ReportGenerator()
    pdf_path = generator.generate_pdf(sample_results, "sample_audit_report.pdf")
    print(f"Sample report generated at: {pdf_path}")


if __name__ == "__main__":
    main()
