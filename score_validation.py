STEAM_INT32_MAX = 2_147_483_647


def validate_run_submission(score, details):
    try:
        score = int(score)
    except (TypeError, ValueError):
        return False, "score_not_integer"

    if score < 0:
        return False, "negative_score"
    if not isinstance(details, dict):
        return False, "missing_run_details"
    try:
        details_score = int(details.get("score", score))
    except (TypeError, ValueError):
        return False, "invalid_run_details"
    if details_score != score:
        return False, "score_mismatch"

    duration = details.get("duration_seconds")
    stage = details.get("stage")
    wave = details.get("wave")
    if not all(isinstance(value, int) for value in (duration, stage, wave)):
        return False, "invalid_run_details"
    if duration <= 0 or duration > 604800:
        return False, "invalid_duration"
    if stage < 1 or stage > 10000 or wave < 1 or wave > 10000:
        return False, "invalid_progress"

    # Limită foarte permisivă, destinată numai salvărilor evident corupte.
    plausible_maximum = (
        250_000
        + duration * 100_000
        + stage * 5_000_000
    )
    if score > plausible_maximum:
        return False, "implausible_score_rate"
    return True, "ok"


def steam_score_value(score):
    return min(STEAM_INT32_MAX, max(0, int(score)))
