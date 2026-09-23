#!/usr/bin/env python3
"""Compile the rendered ASN.1 modules and round-trip a RunMetadata + IdCard value in DER."""
import pathlib, sys, asn1tools
B = pathlib.Path(__file__).resolve().parents[1] / "build" / "specs"
spec = asn1tools.compile_files([str(B / "x509" / "CatboyExtensions.asn1"), str(B / "cms" / "CatboySignedAttributes.asn1")], "der")
rm = {"version": 1, "issuer": "https://token.actions.githubusercontent.com", "repository": "owner/repo",
      "workflowRef": "owner/repo/.github/workflows/x.yml@refs/heads/main", "sha": bytes(20), "runId": "1", "runAttempt": 1, "trigger": "release"}
assert spec.decode("RunMetadata", spec.encode("RunMetadata", rm))["repository"] == "owner/repo"
card = {"version": 1, "cardGuid": bytes(16), "pronouns": "they/them", "issuedAt": __import__("datetime").datetime(2026, 9, 23, 0, 0, 0)}
assert spec.decode("IdCard", spec.encode("IdCard", card))["pronouns"] == "they/them"
print("asn1check: RunMetadata + IdCard DER round-trip ok")
