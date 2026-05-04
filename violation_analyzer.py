import PyPDF2
import pandas as pd
import re
from collections import defaultdict
import os

class ViolationAnalyzer:
    def __init__(self, excel_file):
        """
        Initialize the ViolationAnalyzer with violations from an Excel file.
        Expected Excel format: Columns should include 'Category' and 'Keywords' at minimum.
        """
        self.violations = self._load_violations(excel_file)
    
    def _load_violations(self, excel_file):
        """Load violations from Excel file into a dictionary."""
        try:
            df = pd.read_excel(excel_file)
            # Convert to list of dictionaries for easier processing
            return df.to_dict('records')
        except Exception as e:
            print(f"Error loading Excel file: {e}")
            return []
    
    def analyze_pdf(self, pdf_path):
        """Analyze PDF for violations and return findings."""
        if not self.violations:
            return []
        
        findings = []
        
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                for page_num in range(len(reader.pages)):
                    text = reader.pages[page_num].extract_text()
                    
                    for violation in self.violations:
                        # Check if this violation has keywords to search for
                        if 'Keywords' in violation and pd.notna(violation['Keywords']):
                            keywords = [k.strip() for k in str(violation['Keywords']).split(',') if k.strip()]
                            
                            for keyword in keywords:
                                # Create a case-insensitive regex pattern that matches whole words only
                                pattern = r'(?<!\w)' + re.escape(keyword.lower()) + r'(?!\w)'
                                matches = re.findall(pattern, text.lower())
                                
                                if matches:
                                    # Get context (50 chars before and after the first match)
                                    for match in re.finditer(pattern, text.lower()):
                                        start = max(0, match.start() - 50)
                                        end = min(len(text), match.end() + 50)
                                        context = text[start:end].replace('\n', ' ').strip()
                                        
                                        findings.append({
                                            'Page': page_num + 1,
                                            'Category': violation.get('Category', 'Uncategorized'),
                                            'Sub-Category': violation.get('Sub-Category', ''),
                                            'Violation': violation.get('Violation', ''),
                                            'Keyword': keyword,
                                            'Context': f"...{context}...",
                                            'Severity': violation.get('Severity', 'Medium'),
                                            'Action': violation.get('Action', 'Review')
                                        })
                    
                    # Show progress
                    if (page_num + 1) % 10 == 0:
                        print(f"Processed page {page_num + 1}...")
                        
        except Exception as e:
            print(f"Error analyzing PDF: {e}")
            
        return findings

def save_to_excel(findings, output_file):
    """Save findings to an Excel file."""
    if not findings:
        print("No violations found.")
        return
    
    # Convert to DataFrame for easier Excel export
    df = pd.DataFrame(findings)
    
    # Reorder columns for better readability
    columns = ['Page', 'Category', 'Sub-Category', 'Violation', 'Keyword', 'Severity', 'Action', 'Context']
    df = df[[col for col in columns if col in df.columns]]
    
    # Save to Excel
    try:
        df.to_excel(output_file, index=False)
        print(f"\nAnalysis complete. Results saved to: {output_file}")
    except Exception as e:
        print(f"Error saving results: {e}")

def main():
    # File paths - update these as needed
    excel_file = r"c:\Users\CPT\Downloads\bookss\Violations Terminology.xlsx"
    pdf_file = r"c:\Users\CPT\Downloads\bookss\9781663672995.pdf"
    output_file = r"c:\Users\CPT\Downloads\bookss\violation_report.xlsx"
    
    print("Starting violation analysis...")
    print(f"PDF: {pdf_file}")
    print(f"Violations file: {excel_file}")
    
    # Initialize analyzer and process the PDF
    analyzer = ViolationAnalyzer(excel_file)
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
