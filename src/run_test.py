from .case import TestCase
from .communication import SerialCommunication
from .frame import Condition
from .frame import ConditionType
from .frame import Frame
from .request import EventType
from .request import InputType 
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
        print("Interaction {}...".format(i))
        req, resp = total_log[i]
        print(req)
        print(resp)
    return test_case.assess()

def main():
    init_condition = Condition(ConditionType.After, 
                               cause=lambda req: req.data_type == EventType.Init)
    end_condition = Condition(ConditionType.After,
                              cause=3000, subconditions=[init_condition])
    frame = Frame(init_condition, end_condition,
                    inputs={
                        (InputType.DigitalRead, 13): Sequence([0],[1]),
                        (InputType.AnalogRead, 0): Sequence([0],[1.65]),
                        (InputType.Accelerometer, 'x'): Sequence([0], [1.5]),
                        (InputType.Accelerometer, 'y'): Sequence([0], [1.6]),
                        (InputType.Accelerometer, 'z'): Sequence([0], [1.7]),
                        (InputType.Gyroscope, 'x'): Sequence([0], [100]),
                        (InputType.Gyroscope, 'y'): Sequence([0], [110]),
                        (InputType.Gyroscope, 'z'): Sequence([0], [120]),
                        (InputType.Magnetometer, 'x'): Sequence([0], [10000]),
                        (InputType.Magnetometer, 'y'): Sequence([0], [11000]),
                        (InputType.Magnetometer, 'z'): Sequence([0], [12000])
                    })
    case = TestCase(end_condition, frames=[frame], test_points=[], aggregators={})
    result = run_test(case)