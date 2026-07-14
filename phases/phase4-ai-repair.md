# Phase 4 — AI Repair & Verification

## Goal
Integrate OpenAI for intelligent code repair when deterministic fixes fail.

## Deliverables
- OpenAI client service with structured outputs
- Pydantic response schema: file_path, explanation, unified_diff, confidence, risk
- AI repair engine with context assembly (failing test + source code + error)
- Patch application from unified diff
- Test re-run after AI patch
- Mutation testing (one targeted check)
- Regression test generation (one test if needed)
- Confidence and risk scoring
- Retry logic with exponential backoff
- Token usage tracking

## Success Criteria
- AI receives structured context and returns structured patches
- Patches apply cleanly to source files
- Re-run tests pass after AI repair
- Mutation check validates fix quality
- Confidence scores display on agent cards
- Total pipeline execution under 60 seconds
