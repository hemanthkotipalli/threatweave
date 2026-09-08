---
title: "RBI Fraud Advisory: Merchant Exploitation via Fabricated UPI Payment Screenshots"
source_type: "RBI"
category: "payment_fraud"
original_reference: "Paraphrased from RBI merchant security guidance regarding spoofed payment confirmation apps."
---

# RBI Fraud Advisory: Merchant Exploitation via Fabricated UPI Payment Screenshots

## Regulatory Advisory
The Reserve Bank of India has issued security advisories to retail merchants and consumers regarding malicious mobile applications that generate synthetic payment confirmation receipts and fabricated sound alerts.

## Fraud Modus Operandi
1. **Spoofed Payment Interface**: Perpetrators utilize rogue Android applications that replicate genuine payment interfaces (e.g. Paytm, PhonePe, Google Pay).
2. **Synthetic Transaction Details**: The application generates a fake green 'Payment Successful' screen displaying the merchant's business name, the correct amount, and a fabricated 12-digit UTR reference number.
3. **Visual Confirmation Ruse**: The fraudster shows the screen to the shopkeeper and leaves before the merchant verifies their actual bank statement or POS soundbox.
4. **Relevant Threat Indicators**: `fake_payment_confirmation`, `brand_impersonation`.

## Merchant Guidelines
Merchants must always verify receipt of funds through bank SMS alerts, official soundbox notifications, or by inspecting their own merchant app balance before completing goods delivery.
