---
title: "Scam Intel Alert: Technical Support Impersonation and Remote Desktop Hijacking"
source_type: "Scam-Intel"
category: "tech_support"
original_reference: "Paraphrased from threat intelligence on remote administration tool exploitation."
---

# Scam Intel Alert: Technical Support Impersonation and Remote Desktop Hijacking

## Threat Intelligence Overview
Threat actors operate high-volume call centers targeting banking and e-wallet consumers by posing as customer support representatives resolving pending transactions or failed bill payments.

## Modus Operandi & Indicators
1. **SEO Poisoning / Inbound Call**: Fraudsters place fake customer support phone numbers on search engines for airlines, food delivery, and banking services.
2. **Instruction to Install Remote Tools**: The caller claims they need to diagnose the error and instructs the victim to download legitimate remote management software (AnyDesk, TeamViewer QuickSupport, RustDesk).
3. **Session Code Capture**: Once installed, the victim is asked to read out the 9-digit session code, granting full screen viewing and remote control access.
4. **Unauthorized Banking Transfers**: With remote control, the attacker observes net banking logins and initiates unauthorized transfers while the victim's screen is obscured or blacked out.
5. **Relevant Threat Indicators**: `tech_support_lure`, `remote_access_request`, `credential_request`, `vishing_script_pattern`.

## Preventive Advice
Never install screen-sharing or remote desktop software on instructions from an incoming phone caller. Genuine support teams never request screen control to resolve customer complaints.
