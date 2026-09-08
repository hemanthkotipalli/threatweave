---
title: "CERT-In Advisory: Deceptive Typosquatted Domains Exploiting Public Welfare Schemes"
source_type: "CERT-In"
category: "phishing"
original_reference: "Paraphrased from CERT-In security bulletin on fraudulent domains mimicking government welfare portals."
---

# CERT-In Advisory: Deceptive Typosquatted Domains Exploiting Public Welfare Schemes

## Threat Summary
Malicious actors have registered numerous lookalike and typosquatted domains impersonating official Indian government welfare and direct benefit transfer (DBT) portals, such as PM-Kisan, PM Awas Yojana, and digital scholarship funds.

## Attack Mechanics & Indicators
1. **Deceptive TLDs and Subdomains**: Attackers utilize non-governmental top-level domains such as .top, .online, .info, or .club, embedding official acronyms (e.g., pm-kisan-registration.top).
2. **Official Brand Impersonation**: Portals copy government emblems, photographs of dignitaries, and official color schemes to project legitimacy.
3. **Data Harvesting & Advance Fees**: Visitors are coerced into submitting Aadhaar numbers, bank account numbers, and paying a 'nominal application verification fee'.
4. **Relevant Threat Indicators**: `lookalike_domain`, `brand_impersonation`, `credential_request`, `advance_fee_lure`.

## Recommended Safeguards
Citizens must verify that official Indian government websites end strictly in the `.gov.in` or `.nic.in` domain hierarchy before entering personal or financial details.
