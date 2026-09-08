---
title: "CERT-In Advisory: Large-Scale Phishing Campaigns Impersonating Major Banking Portals"
source_type: "CERT-In"
category: "phishing"
original_reference: "Paraphrased from CERT-In advisory on high-volume SMS and email phishing impersonating commercial banks."
---

# CERT-In Advisory: Large-Scale Phishing Campaigns Impersonating Major Banking Portals

## Threat Summary
CERT-In has observed widespread phishing campaigns targeting customers of major Indian public and private sector banks. Attackers use smishing (SMS phishing) and WhatsApp messages alleging that the customer's bank account has been suspended or that an unauthorized transaction was detected.

## Attack Mechanics & Indicators
1. **Urgency Language**: Messages use coercive language such as 'Immediate Action Required', 'Your account will be blocked within 24 hours', or 'Unauthorized debit of INR 45,000 detected'.
2. **Deceptive URLs**: The communication contains embedded links directing victims to typosquatted, lookalike banking portals hosted on suspicious domains (e.g. sbi-kyc-verify.live, hdfc-netbanking-alert.com).
3. **Credential Harvesting**: Victims are prompted to input sensitive banking credentials, including customer ID, login password, debit card number, ATM PIN, and subsequent One-Time Passwords (OTPs).
4. **Relevant Threat Indicators**: `credential_request`, `urgency_language`, `lookalike_domain`, `suspicious_url_path`.

## Recommended Safeguards
Users should never click on links received via unsolicited SMS or messaging apps. Verify account status exclusively via official banking applications or through verified helpline numbers printed on physical bank cards.
