import sys

import pytest
from django.test.runner import DiscoverRunner


class PytestTestRunner(DiscoverRunner):
    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        argv = [str(arg) for arg in test_labels] if test_labels else []
        return sys.exit(pytest.main(argv))
