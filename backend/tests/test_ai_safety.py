from app.services.ai_repair import (
    AIRegressionTest,
    AIRepairPatch,
    AIRepairProposal,
    is_safe_repair_content,
    normalize_unified_diff_headers,
    repair_content_safety_reason,
    resolve_repair_target,
    is_safe_regression_test,
    is_safe_repair_patch,
)


def test_ai_repair_patch_must_target_supplied_relative_source_file() -> None:
    patch = AIRepairPatch(
        file_path="app/models.py",
        explanation="Add validation.",
        unified_diff="--- a/app/models.py\n+++ b/app/models.py\n@@ -1 +1 @@\n-old\n+new\n",
        confidence=0.8,
        risk="low",
    )

    assert is_safe_repair_patch(patch, {"app/models.py": "old\n"})
    assert not is_safe_repair_patch(patch.model_copy(update={"file_path": "../secrets.py"}), {"app/models.py": "old\n"})
    assert not is_safe_repair_patch(patch.model_copy(update={"file_path": "app/other.py"}), {"app/models.py": "old\n"})


def test_ai_repair_normalizes_safe_no_prefix_unified_diff_headers() -> None:
    patch = AIRepairPatch(
        file_path="app/models.py",
        explanation="Add validation.",
        unified_diff="--- app/models.py\n+++ app/models.py\n@@ -1 +1 @@\n-old\n+new\n",
        confidence=0.8,
        risk="low",
    )

    normalized = normalize_unified_diff_headers(patch)

    assert "--- a/app/models.py" in normalized.unified_diff
    assert "+++ b/app/models.py" in normalized.unified_diff
    assert is_safe_repair_patch(normalized, {"app/models.py": "old\n"})


def test_ai_repair_content_must_be_a_bounded_change_to_supplied_file() -> None:
    proposal = AIRepairProposal(
        file_path="app/models.py",
        explanation="Add a validation method.",
        updated_content="class User:\n    def is_valid(self):\n        return True\n",
        confidence=0.8,
        risk="low",
    )

    assert is_safe_repair_content(proposal, {"app/models.py": "class User:\n    pass\n"})
    assert not is_safe_repair_content(proposal.model_copy(update={"file_path": "../outside.py"}), {"app/models.py": "class User:\n    pass\n"})
    assert not is_safe_repair_content(proposal.model_copy(update={"updated_content": "same\n"}), {"app/models.py": "same\n"})
    assert repair_content_safety_reason(
        proposal.model_copy(update={"file_path": "../outside.py"}),
        {"app/models.py": "class User:\n    pass\n"},
    ) == "target path must be a relative Python source file"


def test_ai_repair_resolves_only_an_unambiguous_supplied_basename() -> None:
    proposal = AIRepairProposal(
        file_path="models.py",
        explanation="Add validation.",
        updated_content="class User:\n    pass\n",
        confidence=0.8,
        risk="low",
    )

    resolved = resolve_repair_target(proposal, {"app/models.py": "class User:\n    pass\n"})
    ambiguous = resolve_repair_target(
        proposal,
        {"app/models.py": "class User:\n    pass\n", "tests/models.py": "pass\n"},
    )

    assert resolved.file_path == "app/models.py"
    assert ambiguous.file_path == "models.py"


def test_ai_regression_test_must_stay_under_discovered_test_target() -> None:
    candidate = AIRegressionTest(
        file_path="tests/test_user_regression.py",
        content="def test_user_regression():\n    assert True\n",
        explanation="Protect user validation.",
        confidence=0.7,
    )

    assert is_safe_regression_test(candidate, ["tests"])
    assert not is_safe_regression_test(candidate.model_copy(update={"file_path": "../test_escape.py"}), ["tests"])
    assert not is_safe_regression_test(candidate.model_copy(update={"content": "import subprocess\n"}), ["tests"])
