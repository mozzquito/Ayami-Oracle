---
pattern: A cert and key living in the same folder, downloaded on the same day, with similar filenames is not evidence they're a matching pair — only a modulus comparison proves it
date: 2026-08-09
source: "rrr: ayami-oracle"
concepts: [tls, ssl, certificates, verification, openssl]
---

# Verify crypto match, not filename similarity

While chasing a missing private key for a DigiCert wildcard cert, two new files turned up in the same investigation: `star_impactwildlife_com.crt` (issued 2026-08-07 02:42) and `_.impactwildlife.com.key` + `.csr` (created 2026-08-07 15:33, ~13 hours later, same day, same domain, plausible-looking filenames). It would have been easy to assume they were a matching pair and hand over install instructions using them together.

They were not a pair. `openssl x509 -noout -modulus -in cert.crt | openssl md5` and `openssl rsa -noout -modulus -in key.key | openssl md5` produced different hashes — the key belonged to a *later* CSR that had apparently never been submitted/signed, not the cert that was already issued. The key did match the CSR's own modulus, which is what made it possible to recover the situation (submit that CSR for a DigiCert reissue) instead of declaring total loss.

**Rule**: never recommend installing a cert+key pair (or any two crypto artifacts meant to match) based on filename, folder co-location, or same-day timestamps. Always run the modulus/fingerprint comparison first. Same-day proximity in file timestamps can mean "generated as part of the same request" OR "generated as an abandoned retry a few hours later" — indistinguishable without checking the math.
