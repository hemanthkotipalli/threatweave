---
title: "CERT-In Advisory: Smishing Campaigns Exploiting Parcel Delivery and Address Verification"
source_type: "CERT-In"
category: "smishing"
original_reference: "Paraphrased from CERT-In advisory on logistics impersonation smishing."
---

# CERT-In Advisory: Smishing Campaigns Exploiting Parcel Delivery and Address Verification

## Threat Summary
Scammers are executing smishing attacks impersonating postal and courier logistics services, including India Post, FedEx, Blue Dart, and DHL. Victims receive alerts claiming their parcel cannot be delivered due to missing house numbers or incorrect postal codes.

## Attack Mechanics & Indicators
1. **Suspicious Shortened URLs**: SMS contains links using URL shorteners (bit.ly, tinyurl) or obscure subdomains pointing to phishing landing pages.
2. **Micro-Payment Trap**: Victims are instructed to pay a nominal re-delivery fee of INR 5 or INR 25 to update their address.
3. **Card Detail Harvesting**: The payment gateway on the fake portal captures full credit/debit card numbers, expiration dates, and CVVs, followed by unauthorized large-value debits.
4. **Relevant Threat Indicators**: `suspicious_url_path`, `urgency_language`, `credential_request`, `lookalike_domain`.

## Recommended Safeguards
Track consignments strictly through official courier tracking portals entered manually in your browser. Disregard SMS requests asking for payment to rectify delivery details.
