---
title: "CERT-In Advisory: Fraudulent Online Task and Part-Time Employment Schemes"
source_type: "CERT-In"
category: "fraud"
original_reference: "Paraphrased from CERT-In advisory on Telegram-based rating and task fraud."
---

# CERT-In Advisory: Fraudulent Online Task and Part-Time Employment Schemes

## Threat Summary
Organized syndicates are recruiting job seekers through WhatsApp, Telegram, and Instagram offering part-time work-from-home opportunities involving liking YouTube videos, rating Google Maps locations, or reviewing hotel listings.

## Attack Mechanics & Indicators
1. **Initial Small Payouts**: Victims receive initial minor payments (INR 200 - 500) to build false confidence and trust.
2. **Advance Investment Demands**: Scammers transition to 'prepaid merchant tasks', demanding upfront deposits of INR 10,000 to INR 1,00,000 to unlock higher commission tiers.
3. **Fabricated Transaction Proof**: Victims are shown fake payment confirmation dashboards and screenshots showing accumulated 'profits' that cannot be withdrawn without further deposits.
4. **Relevant Threat Indicators**: `advance_fee_lure`, `fake_payment_confirmation`, `urgency_language`.

## Recommended Safeguards
Legitimate employers never demand payments or security deposits to allocate work. Cease all communication immediately if an online task requires depositing funds.
