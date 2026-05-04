import PyPDF2
import re
import csv
from collections import defaultdict
import os

class ContentAnalyzer:
    def __init__(self):
        # Only these keywords (no extras)
        self.categories = {
            'Religious Content': {
                'keywords': ['god', 'resurrection', 'demons', 'church', 'jesus', 'cross', 'bible', 'missionary', 'mass', 'synagogue', 'religion', 'hell'],
                'severity': 'Critical',
                'action': 'Review for religious sensitivity',
                'details': 'Religious content must align with Islamic values'
            },
            'Violence and Weapons': {
                'keywords': ['terror', 'blood', 'violence', 'military', 'horror', 'cutting'],
                'severity': 'Critical',
                'action': 'Review content',
                'details': 'Violent content may require review or redaction'
            },
            'Gender and Identity': {
                'keywords': ['men', 'coming out', 'sex', 'boyfriend', 'feminism'],
                'severity': 'Critical',
                'action': 'Review content',
                'details': 'Content related to gender and identity may require review'
            },
            'Political Content': {
                'keywords': ['republic', 'revolution', 'strike', 'rebellion', 'protest', 'press', 'democracy', 'demonstration', 'communist', 'freedom of speech', 'expression', 'political rights'],
                'severity': 'Major',
                'action': 'Review for political sensitivity',
                'details': 'Political content may require review for bias or sensitivity'
            },
            'Alcohol and Drugs': {
                'keywords': ['wine'],
                'severity': 'Critical',
                'action': 'Review content',
                'details': 'Alcohol content may require review or redaction'
            },
            'Cultural Inappropriateness': {
                'keywords': ['culture', 'pigs', 'primitive', 'halloween', 'music', 'bacon', 'dancing', 'easter', 'savage'],
                'severity': 'Major',
                'action': 'Review for cultural sensitivity',
                'details': 'Cultural content may require review for appropriateness'
            },
            'Profanity and Offensive Language': {
                'keywords': ['insults', 'damn'],
                'severity': 'Moderate',
                'action': 'Review for inappropriate language',
                'details': 'Content may contain offensive language that requires review'
            },
            'Sensitive Topics': {
                'keywords': ['stereotypes', 'affair'],
                'severity': 'Critical',
                'action': 'Review sensitive content',
                'details': 'Content may contain sensitive topics that require review'
            }
        }

    def analyze_text(self, text, page_num):
        """Analyze text for sensitive content and return findings"""
        findings = []
        
        # Convert text to lowercase for case-insensitive matching
        text_lower = text.lower()
        
        for category, data in self.categories.items():
            for keyword in data['keywords']:
                # Create a pattern that matches the exact word (case-insensitive)
                pattern = r'(?<![\w-])' + re.escape(keyword.lower()) + r'(?![\w-])'
                
                # Find all exact matches
                for match in re.finditer(pattern, text_lower):
                    # Get the actual matched word from original text (preserving case)
                    start_pos, end_pos = match.span()
                    matched_word = text[start_pos:end_pos]
                    
                    # Get context (50 characters before and after)
                    start = max(0, start_pos - 50)
                    end = min(len(text), end_pos + 50)
                    context = text[start:end].replace('\n', ' ').strip()
                    
                    findings.append({
                        'Page': page_num,
                        'Keyword': matched_word,  # Use the actual matched word
                        'Severity': data['severity'],
                        'Details': data['details'],
                        'Action': data['action'],
                        'Context': f"...{context}..."
                    })
        return findings

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF with page numbers"""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page_num in range(len(reader.pages)):
            text = reader.pages[page_num].extract_text()
            yield page_num + 1, text  # +1 because page numbers start at 1

def save_to_csv(findings, output_file):
    """Save findings to a CSV file, grouped by keyword"""
    if not findings:
        print("No sensitive content found.")
        return
    
    # Group findings by keyword
    keyword_groups = {}
    for finding in findings:
        keyword = finding['Keyword'].lower()
        if keyword not in keyword_groups:
            keyword_groups[keyword] = []
        keyword_groups[keyword].append(finding)
    
    # Sort keywords alphabetically
    sorted_keywords = sorted(keyword_groups.keys())
    
    # Write to CSV with the desired column structure
    fieldnames = ['Page', 'Keyword', 'Severity', 'Detail', 'Action']
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Write all entries for each keyword, one after another
        for keyword in sorted_keywords:
            for finding in keyword_groups[keyword]:
                # Map the finding to the new column structure
                row = {
                    'Page': finding['Page'],
                    'Keyword': finding['Keyword'],
                    'Severity': finding['Severity'],
                    'Detail': finding['Details'],  # Using Details as Detail
                    'Action': finding['Action']
                }
                writer.writerow(row)
    
    print(f"\nAnalysis complete. Results saved to: {output_file}")
    print("Columns in the report: Page, Keyword, Severity, Detail, Action")

def main():
    # File paths
    pdf_path = r"c:\Users\CPT\Downloads\bookss\9781663693419.pdf"
    output_file = r"c:\Users\CPT\Downloads\bookss\content_review_report.csv"
    
    print("Starting content analysis...")
    print(f"PDF: {pdf_path}")
    
    analyzer = ContentAnalyzer()
    all_findings = []
    
    # Process each page
    for page_num, text in extract_text_from_pdf(pdf_path):
        findings = analyzer.analyze_text(text, page_num)
        all_findings.extend(findings)
        
        # Show progress
        if page_num % 10 == 0:
            print(f"Processed page {page_num}...")
    
    # Save results
    save_to_csv(all_findings, output_file)
    
    # Try to open the results file
    try:
        os.startfile(output_file)
    except:
        print(f"Could not open the file automatically. Please open it manually: {output_file}")

if __name__ == "__main__":
    main()
