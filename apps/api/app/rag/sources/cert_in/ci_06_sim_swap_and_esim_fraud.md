---
title: "CERT-In Advisory: Social Engineering Tactics in eSIM and SIM Swap Hijacking"
source_type: "CERT-In"
category: "social_engineering"
original_reference: "Paraphrased from CERT-In awareness bulletin on telecom identity theft and SIM swap fraud."
---

# CERT-In Advisory: Social Engineering Tactics in eSIM and SIM Swap Hijacking

## Threat Summary
Targeted attacks involving fraudulent SIM swap and unauthorized eSIM profile transfers are increasing. Attackers seek to hijack phone numbers to bypass two-factor authentication (2FA) mechanisms protecting banking and email accounts.

## Attack Mechanics & Indicators
1. **Telecom Executive Impersonation**: Scammers call victims claiming to be customer care representatives offering 5G upgrades or SIM KYC validation.
2. **eSIM QR Forwarding Lure**: Victims are persuaded to send an SMS request for eSIM conversion and forward the received QR code or confirmation code to the attacker.
3. **Loss of Cellular Connectivity**: Once the attacker activates the eSIM, the victim's physical SIM loses network reception, allowing the scammer to intercept all incoming OTPs.
4. **Relevant Threat Indicators**: `credential_request`, `urgency_language`, `vishing_script_pattern`.

## Recommended Safeguards
Never forward eSIM activation QR codes, emails, or telecom SMS confirmation codes to any third party. If your phone suddenly loses signal unexpectedly, report immediately to your telecom service provider.
