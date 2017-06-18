from .case import TestCase
from .communication import SerialCommunication
from .frame import Condition
from .frame import ConditionType
from .request import EventType
from .response import ErrorResponse

def run_test(test_case):
    sc = SerialCommunication()
    while not sc.connect():
        # Do nothing, wait for connection
        pass

    total_log = []
    print("Starting Test")
    while True:
        request = sc.get_request()
        if request.is_valid:
            response = test_case.update(request)
        else:
            response = ErrorResponse()

        sc.send_response(response)
        total_log.append((request, response))
        if response.is_error or response.test_complete:
            break

    print("Finished test, total log:")
    for i in range(len(total_log)):
        print("Interaction {}".format(i))
        req, resp = total_log[i]
        print(req)
        print(resp)
    return test_case.assess()

def main():
    init_condition = Condition(ConditionType.After, cause=lambda req: req.data_type == EventType.Init)
    end_condition = Condition(ConditionType.After, cause=3000, subconditions=[init_condition])  # 3sec after init
    case = TestCase(end_condition, frames=[], test_points=[], aggregators={}) # Bare minimum, basically just logging
    result = run_test(case)