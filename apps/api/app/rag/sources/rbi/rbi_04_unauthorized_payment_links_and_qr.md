---
title: "RBI Consumer Advisory: Tampered Physical QR Codes and Deceptive Payment Stickers"
source_type: "RBI"
category: "qr_fraud"
original_reference: "Paraphrased from RBI retail payment advisory on physical QR sticker tampering."
---

# RBI Consumer Advisory: Tampered Physical QR Codes and Deceptive Payment Stickers

## Consumer Guidance
The Reserve Bank of India alerts digital payment users and offline merchants against physical tampering of Quick Response (QR) codes at merchant counters and public payment points.

## Tampering Mechanics
1. **Covert Sticker Placement**: Fraudsters paste adhesive QR code stickers directly over the legitimate merchant's Bharat QR or UPI QR display.
2. **Mismatched Payee Details**: When scanned, the QR code resolves to a personal Virtual Payment Address (VPA) belonging to the fraudster rather than the merchant.
3. **Deceptive Deep-Links**: In other variants, QR codes contain encoded URLs directing the customer's phone to a credential-stealing phishing portal.
4. **Relevant Threat Indicators**: `qr_upi_deeplink_suspicious`, `qr_non_url_payload`, `lookalike_domain`.

## Safety Protocol
Customers should always verify that the registered beneficiary name displayed on their UPI app matches the merchant's physical signboard before authorizing payments.
