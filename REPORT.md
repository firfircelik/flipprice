# FlipPrice — Project Report (live DEV Week 2 submission)

Canonical post: https://dev.to/firfircelik/flipprice-a-side-hustle-pricing-copilot-for-vintage-resellers-457m
Source of truth for the submission narrative is the author's full report text (shared in session, 2026-10-14). The live DEV body is a condensed rendering of it (all 9 sections, all 3 figures, all measured numbers) due to API payload limits. Key figures:

- static/img/arch.png — architecture
- static/img/dogfood.png — 3-item dogfood results
- static/img/latency.png — latency measurements
- FIRST_USER_TEST.md — agent-run dogfood log

Measured numbers (Apple M2, 2026-10-14): Gemma 3 draft 6.0s; pricing cold 5.2s, warm 9ms; offline round trip 1.6s; suite 8/8. RF inversion: like_new 97.51 vs fair 103.36. TabPFN gating: 17s to 5s cold.
