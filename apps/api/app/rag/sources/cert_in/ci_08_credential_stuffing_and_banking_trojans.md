---
title: "CERT-In Advisory: Emerging Mobile Banking Trojans and Overlay Injection Attacks"
source_type: "CERT-In"
category: "malware"
original_reference: "Paraphrased from CERT-In technical briefing on overlay injection trojans targeting mobile banking."
---

# CERT-In Advisory: Emerging Mobile Banking Trojans and Overlay Injection Attacks

## Threat Summary
CERT-In has observed new strains of banking trojans active in India. These malware variants exploit Android Accessibility Services to perform credential harvesting and keystroke logging on mobile financial applications.

## Attack Mechanics & Indicators
1. **Trojan Delivery via Side-Loading**: Malware is distributed via fake utility or banking update links distributed through SMS and WhatsApp.
2. **Overlay Injection**: When the victim opens a legitimate banking application, the malware detects the foreground package and displays an identical transparent webview overlay capturing user input.
3. **Automated Transfer Execution**: The trojan intercepts two-factor SMS OTPs and executes unauthorized fund transfers without alerting the victim.
4. **Relevant Threat Indicators**: `credential_request`, `suspicious_url_path`, `lookalike_domain`.

## Recommended Safeguards
Never enable Accessibility Service permissions for applications installed from outside verified official app repositories.
