---
title: "CERT-In Advisory: Distribution of Malicious APKs Under Guise of Income Tax Refunds"
source_type: "CERT-In"
category: "malware"
original_reference: "Paraphrased from CERT-In technical alert regarding trojanized Android applications targeting tax filers."
---

# CERT-In Advisory: Distribution of Malicious APKs Under Guise of Income Tax Refunds

## Threat Summary
A malicious Android application (APK) distribution campaign has been observed impersonating the Income Tax Department of India. Scammers transmit SMS notifications stating that an income tax refund of a specific amount (e.g., INR 15,490) has been approved and requires immediate confirmation.

## Attack Mechanics & Indicators
1. **Urgent Refund Notification**: Unsolicited SMS prompts user to claim an expiring refund immediately by tapping an embedded short link.
2. **Direct APK Sideloading**: The link prompts the user to download an untrusted APK (e.g., 'ITR_Refund_v2.apk') rather than using the official Google Play Store.
3. **Permission Abuse**: Once installed, the app requests extensive device permissions, including READ_SMS and RECEIVE_SMS, allowing it to intercept banking OTPs.
4. **Relevant Threat Indicators**: `credential_request`, `urgency_language`, `suspicious_url_path`, `advance_fee_lure`.

## Recommended Safeguards
The Income Tax Department never distributes refunds through APK downloads or asks for bank passwords via mobile apps outside the official incometax.gov.in portal.
