---
title: "RBI Public Notice: Fraudulent UPI Collect Requests and Remote Authorizations"
source_type: "RBI"
category: "upi_fraud"
original_reference: "Paraphrased from RBI consumer education alert on UPI debit collect requests."
---

# RBI Public Notice: Fraudulent UPI Collect Requests and Remote Authorizations

## Regulatory Warning
The Reserve Bank of India cautions the general public against deceptive Unified Payments Interface (UPI) collect requests. Fraudsters exploit consumer misunderstandings regarding the distinction between sending and receiving digital payments.

## Fraud Mechanics & Core Indicators
1. **Deceptive Refund Claim**: The fraudster poses as a buyer on an online marketplace (e.g., OLX, Quikr) or a customer service executive claiming to refund an overpayment.
2. **Collect Request Dispatch**: The scammer initiates a 'Collect Money' or 'Pull' transaction request on a UPI app instead of transferring funds.
3. **PIN Requirement Misconception**: Victims are told: 'Enter your 6-digit UPI PIN to receive money in your account'. In reality, entering a UPI PIN always results in a debit.
4. **Relevant Threat Indicators**: `qr_upi_deeplink_suspicious`, `credential_request`, `unauthorized_debit`, `urgency_language`.

## Consumer Directive
Remember the golden rule of UPI: You NEVER need to enter your UPI PIN to receive money into your bank account. Entering your PIN will instantly deduct money from your account.
