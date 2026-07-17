# Synchronisation conflict demonstration

- Test: deliberately removed a protected-region end marker in an isolated copy.
- Result: conflict detected as `missing marker pair`.
- Safety behaviour: the malformed source note remained byte-for-byte untouched.
- Production vault state: clean; this report is retained as the fixture demonstration.
