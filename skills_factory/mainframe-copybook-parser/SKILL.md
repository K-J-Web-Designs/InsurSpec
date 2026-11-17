---
name: mainframe-copybook-parser
description: Parses legacy COBOL copybooks into typed structs and handles EBCDIC-to-ASCII conversion, COMP-3 packed decimals, and fixed-width records.
---

# Mainframe Copybook Parser Skill

## 1. Binary & Encoding Rules
- Explicitly declare codepage (`cp037` / `cp500` EBCDIC) and signed `COMP-3` packed-decimal nibble decoding.
- Never silently truncate trailing spaces or malformed numeric zones; route bad records to a quarantined error ledger.

## 2. Boundary Testing
- Include parameterized tests for positive, negative, and zero-padded `PIC S9(...) COMP-3` fields.
