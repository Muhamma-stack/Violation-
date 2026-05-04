import PyPDF2
import pandas as pd
import re
import os
from collections import defaultdict
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import CellIsRule
from datetime import datetime

class ExcelBasedAnalyzer:
    def __init__(self, excel_file):
        """
        Initialize with the path to the Excel file containing violations.
        Expected Excel format should have columns: 'Category', 'Sub-Category', 'Violation', 'Keywords'
        """
        # Define severity and action mappings similar to content_analyzer.py
        self.severity_mapping = {
            'Religious Content': 'Critical',
            'Violence and Weapons': 'Critical',
            'Gender and Identity': 'Critical',
            'Political Content': 'Major',
            'Alcohol and Drugs': 'Critical',
            'Cultural Inappropriateness': 'Major',
            'Profanity and Offensive Language': 'Moderate',
            'Sensitive Topics': 'Critical'
        }
        
        self.action_mapping = {
            'Religious Content': 'Review for religious sensitivity',
            'Violence and Weapons': 'Review content',
            'Gender and Identity': 'Review content',
            'Political Content': 'Review for political sensitivity',
            'Alcohol and Drugs': 'Review content',
            'Cultural Inappropriateness': 'Review for cultural sensitivity',
            'Profanity and Offensive Language': 'Review for inappropriate language',
            'Sensitive Topics': 'Review sensitive content'
        }
        
        self.categories = self._load_categories(excel_file)
    
    def _load_categories(self, excel_file):
        """Load categories and their keywords from Excel file."""
        try:
            print(f"\nLoading Excel file: {excel_file}")
            
            # Read the Excel file and print sheet names
            xls = pd.ExcelFile(excel_file)
            print(f"Available sheets: {xls.sheet_names}")
            
            # Read the first sheet
            df = pd.read_excel(excel_file, sheet_name=0)
            
            # Clean column names by removing extra spaces and making them lowercase
            df.columns = df.columns.str.strip().str.lower()
            
            print("\nFirst few rows of the Excel file:")
            print(df.head())
            
            print("\nColumns in the Excel file:")
            print(df.columns.tolist())
            
            # Initialize categories dictionary
            categories = {}
            
            # Map the Excel columns to our expected format
            # Using 'Contextual Flag' as the category and 'Word / Concept' as keywords
            for index, row in df.iterrows():
                try:
                    # Get the word/concept (this will be our keyword)
                    word_concept = str(row.get('word / concept', '')).strip()
                    if not word_concept or pd.isna(word_concept):
                        continue
                        
                    # Get the category from 'Contextual Flag' or use a default
                    category = str(row.get('contextual flag', 'Uncategorized')).strip()
                    if not category or pd.isna(category):
                        category = 'Uncategorized'
                    
                    # Get examples for context (optional)
                    examples = str(row.get('examples and phrases', '')).strip()
                    
                    # Clean up the word/concept to extract individual keywords
                    # Split by commas, slashes, or other common separators
                    keywords = []
                    for part in re.split(r'[,/]', word_concept):
                        part = part.strip()
                        if part and part.lower() not in ['and', 'or', 'the']:
                            keywords.append(part)
                    
                    # If no valid keywords found, skip this row
                    if not keywords:
                        continue
                    
                    # Add to categories
                    if category not in categories:
                        categories[category] = {}
                    
                    # Use a default subcategory since the file doesn't have explicit ones
                    subcategory = 'General'
                    if subcategory not in categories[category]:
                        categories[category][subcategory] = []
                    
                    # Add each keyword as a separate violation for better tracking
                    for keyword in keywords:
                        # Map category to severity and action based on content_analyzer.py
                        if any(term in category.lower() for term in ['religious', 'islam', 'christian', 'jewish', 'buddhis', 'hindu', 'sikh']):
                            severity = 'Critical'
                            action = 'Review for religious sensitivity'
                            details = 'Religious content must align with Islamic values'
                        elif any(term in category.lower() for term in ['violence', 'weapon', 'terror', 'blood', 'military', 'horror']):
                            severity = 'Critical'
                            action = 'Review content'
                            details = 'Violent content may require review or redaction'
                        elif any(term in category.lower() for term in ['gender', 'identity', 'lgbtq', 'feminism', 'sexuality']):
                            severity = 'Critical'
                            action = 'Review content'
                            details = 'Content related to gender and identity may require review'
                        elif any(term in category.lower() for term in ['politic', 'government', 'rebellion', 'protest', 'strike']):
                            severity = 'Major'
                            action = 'Review for political sensitivity'
                            details = 'Political content may require review for bias or sensitivity'
                        elif any(term in category.lower() for term in ['alcohol', 'drug', 'wine', 'beer', 'whiskey', 'vodka']):
                            severity = 'Critical'
                            action = 'Review content'
                            details = 'Content may require review or redaction'
                        elif any(term in category.lower() for term in ['cultural', 'tradition', 'custom']):
                            severity = 'Major'
                            action = 'Review for cultural sensitivity'
                            details = 'Cultural content may require review for appropriateness'
                        elif any(term in category.lower() for term in ['profanity', 'offensive', 'curse', 'swear']):
                            severity = 'Moderate'
                            action = 'Review for inappropriate language'
                            details = 'Content may contain offensive language that requires review'
                        else:
                            severity = 'Moderate'
                            action = 'Review content'
                            details = f'Content related to {category} may require review'
                        
                        categories[category][subcategory].append({
                            'violation': f"Found '{keyword}' which relates to: {category}",
                            'keywords': [keyword],
                            'severity': severity,
                            'action': action,
                            'details': details,
                            'examples': examples
                        })
                    
                except Exception as row_error:
                    print(f"\nError processing row {index + 2}: {row_error}")
                    print(f"Row data: {row.to_dict() if hasattr(row, 'to_dict') else row}")
            
            # Print summary of loaded categories and keywords
            print("\nSuccessfully loaded categories:")
            total_keywords = 0
            for cat, subcats in categories.items():
                cat_count = sum(len(violations) for violations in subcats.values())
                print(f"- {cat} ({cat_count} violations)")
                for subcat, violations in subcats.items():
                    print(f"  - {subcat}: {len(violations)} violations")
                    total_keywords += len(violations)
            
            print(f"\nTotal keywords loaded: {total_keywords}")
            
            if not categories:
                print("\nWARNING: No valid categories or keywords were loaded from the Excel file.")
                print("Please check that the Excel file has the correct format with at least a 'Word / Concept' column.")
            
            return categories
            
        except Exception as e:
            import traceback
            print(f"\nError loading Excel file: {e}")
            print("Detailed error:")
            traceback.print_exc()
            return {}
    
    def analyze_pdf(self, pdf_path):
        """Analyze PDF for violations and return findings."""
        if not self.categories:
            print("No categories or keywords loaded from Excel file.")
            return []
        
        findings = []
        total_matches = 0
        
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                total_pages = len(reader.pages)
                print(f"\nAnalyzing PDF: {pdf_path}")
                print(f"Total pages to process: {total_pages}")
                
                for page_num in range(total_pages):
                    text = reader.pages[page_num].extract_text()
                    text_lower = text.lower()
                    page_matches = 0
                    
                    # Search for each category and subcategory
                    for category, subcategories in self.categories.items():
                        for subcategory, violations in subcategories.items():
                            for violation in violations:
                                for keyword in violation['keywords']:
                                    # Skip empty keywords
                                    if not keyword or not keyword.strip():
                                        continue
                                        
                                    # Create a case-insensitive regex pattern that matches whole words only
                                    try:
                                        pattern = r'(?<!\w)' + re.escape(keyword.lower()) + r'(?!\w)'
                                        matches = list(re.finditer(pattern, text_lower))
                                        
                                        if matches:
                                            # Get all matches for this keyword
                                            for match in matches:
                                                # Get the actual matched word from original text (preserving case)
                                                start_pos, end_pos = match.span()
                                                matched_word = text[start_pos:end_pos]
                                                
                                                # Get context (50 chars before and after)
                                                start = max(0, start_pos - 50)
                                                end = min(len(text), end_pos + 50)
                                                context = text[start:end].replace('\n', ' ').strip()
                                                
                                                findings.append({
                                                    'Page': page_num + 1,
                                                    'Keyword': matched_word,
                                                    'Severity': violation.get('severity', 'High'),
                                                    'Details': violation.get('details', f"Content related to {category} may require review"),
                                                    'Action': violation.get('action', 'Review content'),
                                                    'Context': f"...{context}..."
                                                })
                                                
                                            page_matches += len(matches)
                                            total_matches += len(matches)
                                            
                                    except re.error as e:
                                        print(f"Regex error for keyword '{keyword}': {e}")
                                        continue
                    
                    # Show progress
                    if (page_num + 1) % 10 == 0 or (page_num + 1) == total_pages:
                        print(f"Processed page {page_num + 1}/{total_pages} - Found {page_matches} matches on this page")
                
                print(f"\nAnalysis complete. Total matches found: {total_matches}")
                        
        except Exception as e:
            print(f"\nError analyzing PDF: {e}")
            import traceback
            traceback.print_exc()
            
        return findings

def save_to_excel(findings, output_file):
    """Save findings to an Excel file with Page, Keyword, Severity, Detail, and Action columns."""
    if not findings:
        print("No violations found in the document.")
        return
    
    try:
        # Group findings by keyword for better organization
        keyword_groups = {}
        for finding in findings:
            keyword = finding['Keyword'].lower()
            if keyword not in keyword_groups:
                keyword_groups[keyword] = []
            keyword_groups[keyword].append(finding)
        
        # Sort keywords alphabetically
        sorted_keywords = sorted(keyword_groups.keys())
        
        # Define the required columns in the desired order
        columns = ['Page', 'Keyword', 'Severity', 'Detail', 'Action']
        
        # Prepare data for DataFrame
        data = []
        for keyword in sorted_keywords:
            for finding in keyword_groups[keyword]:
                data.append({
                    'Page': finding['Page'],
                    'Keyword': finding['Keyword'],
                    'Severity': finding.get('severity', finding.get('Severity', 'Moderate')),
                    'Detail': finding.get('details', finding.get('Details', '')),
                    'Action': finding.get('action', finding.get('Action', 'Review content'))
                })
        
        # Create DataFrame
        result_df = pd.DataFrame(data)
        
        # Ensure all required columns exist
        required_columns = ['Page', 'Keyword', 'Severity', 'Detail', 'Action']
        for col in required_columns:
            if col not in result_df.columns:
                result_df[col] = ''
        
        # Create a Pandas Excel writer using openpyxl as the engine
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Write the DataFrame to the Excel file
            result_df.to_excel(writer, index=False, sheet_name='Violations')
            
            # Get the workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets['Violations']
            
            # Set column widths (in character units)
            column_widths = {
                'A': 8,    # Page
                'B': 25,   # Keyword
                'C': 12,   # Severity
                'D': 60,   # Detail
                'E': 30    # Action
            }
            
            # Apply column widths
            for col_letter, width in column_widths.items():
                worksheet.column_dimensions[col_letter].width = width
            
            # Style the header row with blue background and white text
            header_font = Font(bold=True, color='FFFFFF')
            header_fill = PatternFill(start_color='4F81BD', end_color='4F81BD', fill_type='solid')
            
            for cell in worksheet[1]:  # First row is the header
                cell.font = header_font
                cell.fill = header_fill
            
            # Add autofilter to the header row
            worksheet.auto_filter.ref = f"A1:{get_column_letter(len(columns))}{len(result_df)+1}"
            
            # Freeze the header row
            worksheet.freeze_panes = 'A2'
            
            # Auto-adjust row heights for wrapped text
            for row in worksheet.iter_rows():
                for cell in row:
                    cell.alignment = Alignment(wrap_text=True, vertical='top')
            
            # Save the workbook
            workbook.save(output_file)
        
        print(f"\nAnalysis complete. Results saved to: {output_file}")
        
        # Try to open the Excel file
        try:
            os.startfile(output_file)
        except:
            print(f"Could not open the file automatically. Please open it manually: {output_file}")
            
    except Exception as e:
        print(f"\nError saving results: {e}")
        import traceback
        traceback.print_exc()

def main():
    # File paths - update these as needed
    excel_file = r"c:\Users\CPT\Downloads\bookss\Violations Terminology.xlsx"
    pdf_file = r"c:\Users\CPT\Downloads\bookss\9781663673152.pdf"
    output_file = r"c:\Users\CPT\Downloads\bookss\violation_analysis_report.xlsx"
    
    print("Starting Excel-based violation analysis...")
    print(f"PDF: {pdf_file}")
    print(f"Violations file: {excel_file}")
    
    # Initialize analyzer and process the PDF
    analyzer = ExcelBasedAnalyzer(excel_file)
    findings = analyzer.analyze_pdf(pdf_file)
    
    # Save results
    save_to_excel(findings, output_file)
    
    # Try to open the results file
    try:
        os.startfile(output_file)
    except:
        print(f"Could not open the file automatically. Please open it manually: {output_file}")

if __name__ == "__main__":
    main()
