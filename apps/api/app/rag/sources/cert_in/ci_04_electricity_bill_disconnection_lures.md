---
title: "CERT-In Advisory: Vishing and SMS Scams Threatening Immediate Utility Disconnection"
source_type: "CERT-In"
category: "vishing"
original_reference: "Paraphrased from CERT-In warning on electricity bill payment extortion scripts."
---

# CERT-In Advisory: Vishing and SMS Scams Threatening Immediate Utility Disconnection

## Threat Summary
CERT-In has observed widespread social engineering campaigns leveraging electricity and water bill payment deadlines. Consumers receive urgent SMS messages or automated phone calls claiming power supply will be cut off by 9:30 PM due to un-updated bill payments.

## Attack Mechanics & Indicators
1. **Time-Bound Threat**: Threatening immediate utility cutoff creating panic and emotional urgency.
2. **Fraudulent Helpline Numbers**: Messages direct the recipient to contact a personal mobile number masquerading as the 'Electricity Officer'.
3. **Remote Desktop Hijacking**: When called, scammers persuade the victim to install remote assistance applications (e.g., AnyDesk, TeamViewer) under the pretext of bill reconciliation.
4. **Relevant Threat Indicators**: `urgency_language`, `vishing_script_pattern`, `tech_support_lure`, `credential_request`.

## Recommended Safeguards
Utility providers never instruct consumers to dial individual mobile numbers or download third-party remote apps to rectify billing issues.
