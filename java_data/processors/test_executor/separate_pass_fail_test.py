import argparse
import re
from typing import List, NamedTuple


class TestCase(NamedTuple):
    name: str
    start_idx: int
    end_idx: int
    content: str


# Regular expression pattern to detect @Test annotations and method definitions
pattern = re.compile(
    r"@Test\s+public\s+void\s+(\w+)\s*\([^)]*\)[^{]*{", re.DOTALL
)


# Function to find start and end indices, and extract method names
def find_test_cases(code: str) -> List[TestCase]:
    test_cases = []
    for match in pattern.finditer(code):
        method_name = match.group(1)
        start_index = match.start()
        method_body_start = code.find("{", start_index) + 1
        brace_count = 1
        for i in range(method_body_start, len(code)):
            if code[i] == "{":
                brace_count += 1
            elif code[i] == "}":
                brace_count -= 1
            if brace_count == 0:
                end_index = i + 1
                break
        test_cases.append(
            TestCase(
                method_name, start_index, end_index, code[start_index:end_index]
            )
        )
    return test_cases


def main(args):
    with open(args.test_result) as f:
        test_result = f.readlines()

    failure_pattern = re.compile(r"^\d+\) (test\d+)\(RegressionTest\d+\)\n$")
    failure_tests = [
        re.match(failure_pattern, line).group(1)
        for line in test_result
        if re.match(failure_pattern, line)
    ]

    with open(args.all_test_file) as f:
        all_test_code = f.read()

    test_cases = find_test_cases(all_test_code)

    pass_test_code = all_test_code
    fail_test_code = all_test_code

    for test_case in test_cases:
        if test_case.name in failure_tests:
            pass_test_code = pass_test_code.replace(test_case.content, "")
        else:
            fail_test_code = fail_test_code.replace(test_case.content, "")

    pass_test_code = pass_test_code.replace(
        "RegressionTest0", "RegressionPassTest0"
    )
    fail_test_code = fail_test_code.replace(
        "RegressionTest0", "RegressionFailTest0"
    )

    with open(args.test_pass_file, "w") as f:
        f.write(pass_test_code)

    with open(args.test_fail_file, "w") as f:
        f.write(fail_test_code)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", dest="test_result")
    parser.add_argument("--all", dest="all_test_file")
    parser.add_argument("--pass", dest="test_pass_file")
    parser.add_argument("--fail", dest="test_fail_file")
    args = parser.parse_args()
    main(args)
