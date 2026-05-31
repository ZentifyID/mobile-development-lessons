def get_display_attempts_by_test(tests, attempts):
    latest_attempts = {}
    perfect_attempts = {}

    ordered_attempts = sorted(
        attempts,
        key=lambda attempt: (attempt.created_at, attempt.pk or 0),
        reverse=True,
    )
    for attempt in ordered_attempts:
        latest_attempts.setdefault(attempt.test_id, attempt)
        if attempt.percent == 100:
            perfect_attempts.setdefault(attempt.test_id, attempt)

    return {
        test.pk: perfect_attempts.get(test.pk) or latest_attempts.get(test.pk)
        for test in tests
    }


def attach_display_attempts(tests, attempts, attr_name='display_attempt'):
    display_attempts = get_display_attempts_by_test(tests, attempts)

    for test in tests:
        setattr(test, attr_name, display_attempts.get(test.pk))

    return display_attempts


def summarize_test_progress(tests):
    if not tests:
        return {
            'passed_tests': 0,
            'average_test_percent': 0,
        }

    total_percent = 0
    passed_tests = 0

    for test in tests:
        attempt = getattr(test, 'display_attempt', None)
        total_percent += attempt.percent if attempt else 0
        if attempt and attempt.is_passed:
            passed_tests += 1

    return {
        'passed_tests': passed_tests,
        'average_test_percent': round(total_percent / len(tests)),
    }
