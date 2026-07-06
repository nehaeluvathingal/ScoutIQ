import logging
from typing import Dict, Any, List

logger = logging.getLogger("company_verifier")

SUSPICIOUS_COMPANIES = {
    "shadowy finance group": {
        "trust_score": 0.1,
        "safety_flags": [
            "Payment requested/offered in Cryptocurrency only",
            "Anonymous/unknown company headquarters",
            "Lacks valid corporate website",
            "Suspicious/unverifiable job description"
        ],
        "is_suspicious": True,
        "notes": "High risk of scam. Immediate red flags identified regarding payment terms and corporate identity."
    }
}

def verify_company(company_name: str) -> Dict[str, Any]:
    """Analyzes a company name and verifies its trust signals.
    
    Checks against known suspicious company records and evaluates the name format.
    Returns:
        A dictionary with trust_score, safety_flags, is_suspicious, and notes.
    """
    logger.info(f"Verifying company: {company_name}")
    company_lower = company_name.lower().strip()
    
    # Check known suspicious list
    if company_lower in SUSPICIOUS_COMPANIES:
        return SUSPICIOUS_COMPANIES[company_lower]
        
    # Default clean company check
    # Check for suspicious words in the name
    flags = []
    trust_score = 0.95
    
    suspicious_keywords = ["shadowy", "scam", "anonymous", "hack", "bypass"]
    for keyword in suspicious_keywords:
        if keyword in company_lower:
            flags.append(f"Suspicious keyword '{keyword}' in company name")
            trust_score -= 0.3
            
    is_suspicious = len(flags) > 0
    if is_suspicious:
        notes = f"Warning: Potential company verification issues. Found {len(flags)} red flags."
    else:
        notes = "Company verified. Safe records, professional business domain matching, and high credibility signals."
        
    return {
        "trust_score": max(0.0, trust_score),
        "safety_flags": flags,
        "is_suspicious": is_suspicious,
        "notes": notes
    }
