let analysisResults = [];
let currentPage = 1;
let itemsPerPage = 10;
let totalPages = 1;

// Comprehensive KSA Educational Policy Database (Policy-Driven)
const KSA_POLICY_DATABASE = {
    'Religious Compliance': {
        severity: 'High',
        description: 'Ensure content aligns with Islamic values. Prohibit promotion of other religions or blasphemy.',
        indicators: ['christianity', 'church', 'bible', 'idol', 'cross', 'atheism', 'mass'],
        action: 'Remove immediately - Not allowed in KSA schools'
    },
    'Political Neutrality': {
        severity: 'High',
        description: 'Materials must remain politically neutral. Prohibit protests, regime change, or political activism.',
        indicators: ['democracy', 'protest', 'revolution', 'election', 'opposition', 'israel'],
        action: 'Review and remove - Political content not appropriate'
    },
    'Public Safety & Morality': {
        severity: 'High',
        description: 'Prohibit depictions of violence, weapons, terrorism, or illegal substances (alcohol/drugs).',
        indicators: ['gun', 'bomb', 'terrorism', 'alcohol', 'drug', 'murder', 'violence'],
        action: 'Remove immediately - Inappropriate for educational content'
    },
    'Social & Cultural Values': {
        severity: 'High',
        description: 'Respect KSA social norms. Prohibit sexual content or promotion of Western celebrations.',
        indicators: ['sex', 'lgbt', 'dating', 'boyfriend', 'christmas', 'halloween', 'pork'],
        action: 'Remove immediately - Violates KSA social/cultural standards'
    },
    'Scientific Integrity': {
        severity: 'Medium',
        description: 'Present scientific theories according to KSA curriculum guidelines.',
        indicators: ['evolution', 'darwin', 'natural selection'],
        action: 'Review - Ensure alignment with KSA curriculum guidelines'
    },
    'Professional Language': {
        severity: 'Medium',
        description: 'Maintain high language standards. Prohibit profanity or derogatory stereotypes.',
        indicators: ['stupid', 'idiot', 'damn', 'racism', 'stereotype'],
        action: 'Review - Inappropriate language for educational materials'
    }
};

// Update analysis logic to use Policy Indicators and Semantic Descriptions
function analyzeTextAgainstPolicies(text, pageNum) {
    const results = [];
    const lowerText = text.toLowerCase();
    
    Object.keys(KSA_POLICY_DATABASE).forEach(policyName => {
        const policy = KSA_POLICY_DATABASE[policyName];
        
        policy.indicators.forEach(indicator => {
            const lowerIndicator = indicator.toLowerCase();
            if (lowerText.includes(lowerIndicator)) {
                const pattern = new RegExp(`\\b${escapeRegex(lowerIndicator)}\\b`, 'gi');
                const matches = [...text.matchAll(pattern)];
                
                matches.forEach(match => {
                    const start = Math.max(0, match.index - 200);
                    const end = Math.min(text.length, match.index + match[0].length + 200);
                    let context = text.substring(start, end).replace(/\s+/g, ' ').trim();
                    
                    const confidence = calculatePolicyConfidence(context, policyName);
                    
                    if (confidence >= 40) {
                        results.push({
                            Page: pageNum,
                            Keyword: match[0],
                            Category: policyName,
                            Severity: policy.severity,
                            Confidence: confidence,
                            Detail: `Policy Violation: ${policy.description}`,
                            Action: policy.action,
                            Context: context,
                            Status: 'Pending', // Audit Layer Status
                            AuditComment: ''
                        });
                    }
                });
            }
        });
    });
    
    return results;
}

function calculatePolicyConfidence(context, policyName) {
    const policy = KSA_POLICY_DATABASE[policyName];
    const lowerContext = context.toLowerCase();
    let confidence = 50;
    
    // Semantic boost from description terms
    const descTerms = policy.description.toLowerCase().split(/\W+/);
    descTerms.forEach(term => {
        if (term.length > 4 && lowerContext.includes(term)) confidence += 5;
    });
    
    // Reductions
    const educationalPhrases = ['history of', 'study of', 'learn about', 'academic'];
    if (educationalPhrases.some(p => lowerContext.includes(p))) confidence -= 30;
    
    const negativeIndicators = ['not allowed', 'prohibited', 'forbidden'];
    if (negativeIndicators.some(p => lowerContext.includes(p))) confidence -= 40;
    
    return Math.min(100, Math.max(0, confidence));
}

// Enhanced text extraction function
function extractTextFromPage(textContent) {
    // Method 1: Simple join
    let text = textContent.items.map(item => item.str).join(' ');
    
    // Method 2: Preserve line breaks for better context
    let textWithBreaks = '';
    let lastY = null;
    
    textContent.items.forEach((item, index) => {
        const currentY = item.transform ? item.transform[5] : null;
        
        // Add space or newline based on position
        if (index > 0) {
            if (lastY !== null && currentY !== null && Math.abs(currentY - lastY) > 5) {
                textWithBreaks += '\n';
            } else {
                textWithBreaks += ' ';
            }
        }
        
        textWithBreaks += item.str;
        lastY = currentY;
    });
    
    // Use both methods and combine
    return {
        simple: text,
        structured: textWithBreaks,
        combined: text + ' ' + textWithBreaks
    };
}



// Check for false positives (educational context)
function checkFalsePositive(context, keyword) {
    const lowerContext = context.toLowerCase();
    
    // Educational contexts that might be acceptable
    const educationalPhrases = [
        'history of', 'study of', 'learn about', 'educational', 'academic',
        'textbook', 'curriculum', 'lesson', 'chapter', 'subject',
        'ancient', 'historical', 'cultural study', 'comparative religion',
        'world religions', 'religious studies', 'social studies'
    ];
    
    // Check if context suggests educational purpose
    const hasEducationalContext = educationalPhrases.some(phrase => 
        lowerContext.includes(phrase)
    );
    
    // For certain categories, even educational context might be problematic
    const alwaysProblematic = ['sexual', 'porn', 'violence', 'terrorism', 'drug', 'alcohol'];
    const isAlwaysProblematic = alwaysProblematic.some(term => keyword.includes(term));
    
    if (isAlwaysProblematic) {
        return false; // Always flag these
    }
    
    // For others, educational context might be acceptable
    return hasEducationalContext;
}

// Update file name display
document.getElementById('pdfFile').addEventListener('change', function(e) {
    const fileName = e.target.files[0] ? e.target.files[0].name : 'No file selected';
    document.getElementById('fileName').textContent = fileName;
});

let allAnalysisResults = []; // Store unfiltered results
let filteredResults = []; // Store currently filtered results
let totalPagesInPdf = 0; // Total pages in PDF (from backend)

// Backend API: direct endpoint for Vercel deployment
const API_BASE = '';

async function analyzePDF() {
    const fileInput = document.getElementById('pdfFile');
    if (!fileInput.files[0]) {
        alert('Please select a PDF file');
        return;
    }
    const file = fileInput.files[0];

    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('results').classList.add('hidden');
    const loadingText = document.querySelector('#loading p');
    loadingText.textContent = 'Uploading to backend... AI SAMRAT is analyzing your PDF.';

    try {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(API_BASE + '/analyze', {
            method: 'POST',
            body: formData,
            signal: AbortSignal.timeout(900000) // 15 minute timeout for large files
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(err.detail || 'Backend error');
        }

        const data = await response.json();
        totalPagesInPdf = data.total_pages || 0;
        allAnalysisResults = (data.findings || []).map(f => ({
            ...f,
            Status: 'Pending',
            AuditComment: ''
        }));
        allAnalysisResults.sort((a, b) => {
            const severityOrder = { 'High': 1, 'Medium': 2, 'Low': 3 };
            return (severityOrder[a.Severity] || 99) - (severityOrder[b.Severity] || 99);
        });
        filteredResults = [...allAnalysisResults];
        displayResults();
    } catch (error) {
        console.error('Error:', error);
        alert('Error: ' + error.message + '\n\nMake sure the backend is running:\npython ai_samrat_analyzer.py server');
    } finally {
        document.getElementById('loading').classList.add('hidden');
    }
}

function deduplicateFindings(findings) {
    const seen = new Set();
    return findings.filter(f => {
        const key = `${f.Page}-${f.Keyword.toLowerCase()}-${f.Category}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
    });
}

function applyFilters() {
    const severity = document.getElementById('severityFilter').value;
    const category = document.getElementById('categoryFilter').value;
    
    filteredResults = allAnalysisResults.filter(r => {
        const sevMatch = severity === 'All' || r.Severity === severity;
        const catMatch = category === 'All' || r.Category === category;
        return sevMatch && catMatch;
    });
    
    currentPage = 1;
    updatePagination();
    renderCurrentPage();
    updateStats();
}

function displayResults() {
    const resultsBody = document.getElementById('resultsBody');
    resultsBody.innerHTML = '';
    
    if (allAnalysisResults.length === 0) {
        resultsBody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 40px; color: #28a745; font-weight: bold;">✅ No inappropriate content found! PDF is compliant.</td></tr>';
        document.getElementById('totalMatches').textContent = '0';
        document.getElementById('pagesAnalyzed').textContent = totalPagesInPdf || '0';
        const pwi = document.getElementById('pagesWithIssues'); if (pwi) pwi.textContent = '0';
        const crit = document.getElementById('criticalCount'); if (crit) crit.textContent = '0';
        const maj = document.getElementById('majorCount'); if (maj) maj.textContent = '0';
        const min = document.getElementById('minorCount'); if (min) min.textContent = '0';
        const avg = document.getElementById('avgConfidence'); if (avg) avg.textContent = '-';
        document.getElementById('complianceStatus').textContent = '✅ COMPLIANT';
        document.getElementById('complianceStatus').className = 'compliance-badge compliance-compliant';
        document.getElementById('paginationContainer').classList.add('hidden');
    } else {
        updateStats();
        updatePagination();
        renderCurrentPage();
    }
    
    document.getElementById('results').classList.remove('hidden');
}

function updateStats() {
    const uniquePages = new Set(filteredResults.map(r => r.Page));
    const criticalCount = filteredResults.filter(r => r.Severity === 'High').length;
    const majorCount = filteredResults.filter(r => r.Severity === 'Medium').length;
    const minorCount = filteredResults.filter(r => r.Severity === 'Low').length;
    
    document.getElementById('totalMatches').textContent = filteredResults.length;
    document.getElementById('pagesAnalyzed').textContent = totalPagesInPdf > 0 ? totalPagesInPdf : uniquePages.size;
    const pwiEl = document.getElementById('pagesWithIssues'); if (pwiEl) pwiEl.textContent = uniquePages.size;
    document.getElementById('criticalCount').textContent = criticalCount;
    document.getElementById('majorCount').textContent = majorCount;
    document.getElementById('minorCount').textContent = minorCount;
    const confidences = filteredResults.map(r => r.Confidence).filter(c => c != null && !isNaN(c));
    const avgConf = confidences.length ? Math.round(confidences.reduce((a, b) => a + b, 0) / confidences.length) : 0;
    const avgEl = document.getElementById('avgConfidence'); if (avgEl) avgEl.textContent = avgConf + '%';
    
    // Update compliance badge
    const badge = document.getElementById('complianceStatus');
    if (criticalCount > 0) {
        badge.textContent = '❌ NOT COMPLIANT';
        badge.className = 'compliance-badge compliance-noncompliant';
    } else if (majorCount > 0) {
        badge.textContent = '⚠️ NEEDS REVIEW';
        badge.className = 'compliance-badge compliance-review';
    } else {
        badge.textContent = '✅ MOSTLY COMPLIANT';
        badge.className = 'compliance-badge compliance-mostly';
    }
}

function renderCurrentPage() {
    const resultsBody = document.getElementById('resultsBody');
    resultsBody.innerHTML = '';
    
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, filteredResults.length);
    const currentPageResults = filteredResults.slice(startIndex, endIndex);
    
    if (currentPageResults.length === 0) {
        resultsBody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 40px;">No results to display</td></tr>';
        return;
    }
    
    currentPageResults.forEach((result, index) => {
        const globalIndex = allAnalysisResults.indexOf(result);
        const row = document.createElement('tr');
        const statusClass = result.Status === 'Accepted' ? 'status-accepted' : 
                           result.Status === 'Rejected' ? 'status-rejected' : 'status-pending';

        row.innerHTML = `
            <td>${result.Page}</td>
            <td><strong>${result.Category}</strong></td>
            <td><strong>${result.Keyword}</strong></td>
            <td><span class="severity-badge severity-${result.Severity.toLowerCase()}">${result.Severity}</span></td>
            <td title="${result.Detail}">${result.Detail.length > 40 ? result.Detail.substring(0, 40) + '...' : result.Detail}</td>
            <td>${result.Action}</td>
            <td><span class="status-badge ${statusClass}">${result.Status}</span></td>
            <td>
                <input type="text" class="comment-input" placeholder="Add comment..." 
                       value="${result.AuditComment || ''}" 
                       onchange="updateAuditComment(${globalIndex}, this.value)">
            </td>
            <td>
                <div class="audit-actions">
                    <button class="btn-approve" onclick="auditFinding(${globalIndex}, 'Accepted')">✅</button>
                    <button class="btn-reject" onclick="auditFinding(${globalIndex}, 'Rejected')">❌</button>
                </div>
            </td>
        `;
        resultsBody.appendChild(row);
    });
}

function auditFinding(index, status) {
    allAnalysisResults[index].Status = status;
    renderCurrentPage();
    updateStats();
}

function updateAuditComment(index, comment) {
    allAnalysisResults[index].AuditComment = comment;
}

function updatePagination() {
    totalPages = Math.ceil(filteredResults.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage + 1;
    const endIndex = Math.min(currentPage * itemsPerPage, filteredResults.length);
    document.getElementById('paginationInfo').textContent = 
        `Showing ${startIndex} - ${endIndex} of ${filteredResults.length} results`;
    
    document.getElementById('firstPageBtn').disabled = currentPage === 1;
    document.getElementById('prevPageBtn').disabled = currentPage === 1;
    document.getElementById('nextPageBtn').disabled = currentPage === totalPages;
    document.getElementById('lastPageBtn').disabled = currentPage === totalPages;
    
    const pageNumbers = document.getElementById('pageNumbers');
    pageNumbers.innerHTML = '';
    
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
    
    if (endPage - startPage < maxVisiblePages - 1) {
        startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }
    
    if (startPage > 1) {
        const ellipsis = document.createElement('span');
        ellipsis.className = 'page-ellipsis';
        ellipsis.textContent = '...';
        pageNumbers.appendChild(ellipsis);
    }
    
    for (let i = startPage; i <= endPage; i++) {
        const pageBtn = document.createElement('button');
        pageBtn.className = 'page-number-btn';
        if (i === currentPage) {
            pageBtn.classList.add('active');
        }
        pageBtn.textContent = i;
        pageBtn.onclick = () => goToPage(i);
        pageNumbers.appendChild(pageBtn);
    }
    
    if (endPage < totalPages) {
        const ellipsis = document.createElement('span');
        ellipsis.className = 'page-ellipsis';
        ellipsis.textContent = '...';
        pageNumbers.appendChild(ellipsis);
    }
    
    if (filteredResults.length > 0) {
        document.getElementById('paginationContainer').classList.remove('hidden');
    } else {
        document.getElementById('paginationContainer').classList.add('hidden');
    }
}

function goToPage(page) {
    if (page >= 1 && page <= totalPages) {
        currentPage = page;
        renderCurrentPage();
        updatePagination();
        // Scroll to top of table
        document.getElementById('resultsTable').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function previousPage() {
    if (currentPage > 1) {
        goToPage(currentPage - 1);
    }
}

function nextPage() {
    if (currentPage < totalPages) {
        goToPage(currentPage + 1);
    }
}

function goToLastPage() {
    goToPage(totalPages);
}

function changePageSize() {
    const pageSizeSelect = document.getElementById('pageSize');
    itemsPerPage = parseInt(pageSizeSelect.value);
    currentPage = 1;
    updatePagination();
    renderCurrentPage();
}

function downloadExcel() {
    if (allAnalysisResults.length === 0) {
        alert('No results to download');
        return;
    }
    
    // Prepare data for Excel following the Mandatory Schema: Page | Category | Keyword | Severity | Detail | Action + Status + Comment
    const excelData = allAnalysisResults.map(result => ({
        Page: result.Page,
        Category: result.Category || 'N/A',
        Keyword: result.Keyword,
        Severity: result.Severity,
        Detail: result.Detail,
        Action: result.Action,
        Status: result.Status,
        'Reviewer Comment': result.AuditComment || '',
        Confidence: `${result.Confidence}%`
    }));
    
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.json_to_sheet(excelData);
    
    ws['!cols'] = [
        { wch: 8 },  // Page
        { wch: 25 }, // Category
        { wch: 20 }, // Keyword
        { wch: 12 }, // Severity
        { wch: 50 }, // Detail
        { wch: 40 }, // Action
        { wch: 15 }, // Status
        { wch: 30 }, // Comment
        { wch: 12 }  // Confidence
    ];
    
    XLSX.utils.book_append_sheet(wb, ws, 'KSA Audited Report');
    const fileName = `KSA_Audit_Report_${new Date().toISOString().split('T')[0]}.xlsx`;
    XLSX.writeFile(wb, fileName);
}

// Add some CSS for severity badges (inline style would be better, but adding via JS)
const style = document.createElement('style');
style.textContent = `
    .severity-badge {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: 600;
        display: inline-block;
    }
    .severity-critical {
        background-color: #ff4444;
        color: white;
    }
    .severity-major {
        background-color: #ff8800;
        color: white;
    }
    .severity-minor {
        background-color: #44aaff;
        color: white;
    }
    .confidence-badge {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: 600;
        display: inline-block;
    }
    .confidence-high {
        background-color: #4caf50;
        color: white;
    }
    .confidence-medium {
        background-color: #ff9800;
        color: white;
    }
    .status-badge {
        padding: 4px 10px;
        border-radius: 15px;
        font-size: 0.8em;
        font-weight: bold;
    }
    .status-pending { background-color: #f0f0f0; color: #666; }
    .status-accepted { background-color: #d4edda; color: #155724; }
    .status-rejected { background-color: #f8d7da; color: #721c24; }
    
    .audit-actions {
        display: flex;
        gap: 5px;
    }
    .audit-actions button {
        border: none;
        background: white;
        cursor: pointer;
        padding: 5px;
        border-radius: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .audit-actions button:hover {
        background: #f8f9fa;
    }
`;
document.head.appendChild(style);

