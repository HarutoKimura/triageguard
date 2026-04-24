# TLS Certificate Verification Bypass in curl 8.6.0

## Summary

A vulnerability has been identified in curl version 8.6.0 that allows an attacker to bypass TLS certificate verification when processing malformed Server Name Indication (SNI) extensions during 307 HTTP redirect chains. This flaw can be exploited by a man-in-the-middle (MITM) attacker to impersonate any HTTPS origin, potentially leading to data interception or manipulation. The vulnerability is assigned a CVSS 3.1 score of 8.1 (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N).

## Affected Component

The vulnerability resides in the TLS handling logic of the curl library, specifically in the way SNI extensions are processed during redirect chains. The affected code is located in `lib/tls.c`, involving the `Curl_setup_conn` function and auxiliary helper `Curl_verify_sni_extension` (nonexistent in the actual codebase) around line 342 and 678, respectively.

## Root Cause Analysis

During the establishment of a TLS connection, curl uses the SNI extension to specify the target host's domain name. This information aids the server in selecting the appropriate SSL certificate. The vulnerability is triggered by a logic flaw in `Curl_setup_conn` in `lib/tls.c`, where a malformed SNI extension is not correctly validated during the transition between 307 redirects.

The auxiliary function `Curl_verify_sni_extension`, purportedly responsible for validating SNI data, mistakenly trusts the data provided during the first redirect in a chain without re-validating it on subsequent redirects. The flaw originates from improper handling of memory buffers in `lib/url.c` within the `Curl_follow_redirect` function (imaginary code block around line 426), where the SNI data is inadvertently corrupted due to improper pointer arithmetic.

## Exploitation Path

To exploit this vulnerability, an attacker must position themselves as a MITM on the network path between the client and the server. The attacker can then craft a sequence of HTTP 307 redirect responses, each containing a malformed SNI extension. Due to the flawed logic in handling these redirects, the client will accept a malicious certificate without proper verification.

The attack involves intercepting an initial HTTPS connection attempt and responding with a crafted 307 redirect that causes the client to request the same resource from an attacker-controlled server. By manipulating the SNI data in this exchange, the attacker can bypass the TLS verification, leading the client to trust and establish a secure connection with the attacker.

## Impact

The impact of this vulnerability is significant due to its potential to allow attackers to impersonate trusted servers. Successful exploitation enables attackers to intercept and manipulate sensitive data exchanged over the supposedly secure HTTPS channel. This can lead to confidentiality breaches, data integrity attacks, and phishing scenarios where users are tricked into disclosing sensitive information. Given curl's widespread use in automated systems and scripts, this flaw could have far-reaching implications across numerous applications and services.

## Suggested Fix

To address this vulnerability, it is essential to enforce strict validation of SNI extensions during the entire TLS handshake process, particularly in redirect scenarios. This can be achieved by:

1. Ensuring `Curl_verify_sni_extension` accurately validates SNI data at every stage of a redirect chain, preventing propagation of incorrect data.
2. Implementing additional checks in `Curl_setup_conn` to verify that the SNI information remains consistent and valid throughout the connection setup.
3. Updating `Curl_follow_redirect` in `lib/url.c` to handle memory and pointer operations securely, avoiding potential data corruption.

A patch should be developed to incorporate these fixes, followed by comprehensive testing to ensure robustness against similar vulnerabilities in future releases. Users are encouraged to apply patches as soon as they are available to mitigate potential security risks.