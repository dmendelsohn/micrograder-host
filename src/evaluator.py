from . import prefs
from . import utils
from .screen import Screen
from .sequence import Sequence

from collections import namedtuple
import operator


EvaluatedValue = namedtuple("EvaluatedValue", ["value", "portion", "passed"])

EvalPointResult = namedtuple("EvalPointResult", ["passed", "observed"])

ChannelResult = namedtuple("ChannelResult", ["passed", "points"])

class EvalPoint:
    def __init__(self, condition_id, expected_value, check_interval, *,
                 check_function=operator.eq, portion=1.0):
        self.condition_id = condition_id
        self.expected_value = expected_value
        self.check_interval = check_interval
        self.check_function = check_function
        self.portion = portion # Required fraction of interval with correct value

    # Evaluates whether or not this point is satisfied
    # condition_met_at: time condition was met, or None if not met
    # sequence: Sequence for relevant (data_type,channel)
    # Returns a (bool, list of tuples) tuple:
    #   bool represents whether or not the point is satisfied
    #   each tuple in list is (value_observed, portion_observed, passed),
    #       representing the values observed the assessment interval,
    #       sorted by portion_observed descending
    def evaluate(self, condition_met_at, sequence):
        if condition_met_at is None:
            return EvalPointResult(False, [])

        (start, end) = self.check_interval
        start += condition_met_at
        end += condition_met_at

        values = sequence.profile_interval((start,end))

        # Add pass/fail for each value tuple
        portion_correct = 0.0
        for i in range(len(values)):
            value, portion = values[i]
            if self.check_function(self.expected_value, value):
                values[i] = EvaluatedValue(value, portion, True)
                portion_correct += portion
            else:
                values[i] = EvaluatedValue(value, portion, False)

        passed = (portion_correct >= self.portion * 0.9999) # Tiny bit of lenience, due to floating point issues
        return EvalPointResult(passed, values)

    def describe(self, condition_description=None, point_result=None):
        desc = {}

        if condition_description is None:
            condition_description = "condition {}".format(self.condition_id)
        interval_desc = str(self.check_interval) + " relative to " + condition_description
        desc["Time Interval"] = interval_desc

        criterion_desc = "Correct for {0:.2f}% of interval".format(100*self.portion)
        check_function_desc = utils.get_description(self.check_function)
        if check_function_desc is not None:
            criterion_desc += " with check function ({})".format(check_function_desc)
        desc["Pass Criterion"] = criterion_desc

        desc["Expected Value"] = utils.get_description(self.expected_value,
                                                       default=self.expected_value)

        if point_result is None:
            desc["Result"] = "NOT EVALUATED"
            desc["Observed Values"] = []
        else:
            if point_result.passed:
                desc["Result"] = "PASS"
            else:
                desc["Result"] = "FAIL"

            desc["Observed Values"] = []
            for eval_value in point_result.observed:
                value_description = {
                    "Value": utils.get_description(eval_value.value, default=eval_value.value),
                    "Percentage of Interval": "{0:.2f}%".format(100*eval_value.portion),
                    "Correct": "Yes" if eval_value.passed else "No"
                }

                desc["Observed Values"].append(value_description)

        return desc

    def __eq__(self, other):
        return type(other) is type(self) and self.__dict__ == other.__dict__

    def __str__(self):
        return repr(self)

    def __repr__(self):
        s = ("EvalPoint: condition_id={}, expected_value={}, "
             "check_interval={}, check_function={}, portion={}")
        return s.format(self.condition_id, self.expected_value, self.check_interval,
                        self.check_function, self.portion)

class Evaluator:
    # conditions: a list of relevant Conditions
    # points: a list of EvalPoints
    def __init__(self, conditions, points, *,
                 aggregators=None):
        if aggregators is None:
            aggregators = prefs.default_aggregators()

        self.conditions = conditions # List of relevant Conditions
        self.points = points # Map from (data_type,channel)->list(EvalPoint)
        self.aggregators = aggregators # Preferences<Aggregator>

    # log: a RequestLog of the test that was run
    # Returns a map from (data_type,channel)->(bool, list)
    #   the boolean represents the overall result for this channel
    #   each elt of list is of EvalPointResults corresponding to each
    #   EvalPoint (in the same order seen in the values of self.points)
    def evaluate(self, log):
        satisfied_times = [log.condition_satisfied_at(c) for c in self.conditions]
        sequences = log.extract_sequences()
        
        results = {} # Map to be returned
        for key in self.points:
            sequence = sequences.get(key, Sequence())
            point_results = []
            for point in self.points[key]:
                condition_met_at = satisfied_times[point.condition_id]
                point_results.append(point.evaluate(condition_met_at, sequence))

            agg = self.aggregators.get_preference(key)
            overall_result = agg([res.passed for res in point_results])
            results[key] = ChannelResult(overall_result, point_results)

        return results

    # Returns a JSON-style dictionary detailing the results
    # channel_results: a map from (data_type,channel)->ChannelResult
    # Return dict maps (data_type,channel)->ChannelDescription
    # ChannelDescription has keys "Result", "Points", and maybe "Aggregation Function"
    def describe(self,  channel_results):
        desc = {}
        for key in channel_results:
            channel_desc = {}
            (passed, point_results) = channel_results[key]

            if passed:
                channel_desc["Result"] = "PASS"
            else:
                channel_desc["Result"] = "FAIL"

            agg = self.aggregators.get_preference(key)
            agg_desc = utils.get_description(agg)
            if agg_desc is not None:
                channel_desc["Aggregator Description"] = agg_desc

            channel_desc["Points"] = []
            for (point, point_result) in zip(self.points[key], point_results):
                condition = self.conditions[point.condition_id]
                condition_desc = utils.get_description(condition)
                channel_desc["Points"].append(point.describe(condition_desc, point_result))

            desc[key] = channel_desc
        return desc

    # Takes the output of descibe(), and replaces all the images
    # with descriptive text.  Images are returned as a separate list (order matters)
    # Returns list of Images, alters input description
    def replace_images(self, description, omit_blanks=True):
        images = []

        # adds image to images (if necessary) and returns replacement text
        def replace_image(screen, omit_blanks):
            if omit_blanks and screen.get_num_pixels_lit() == 0:
                return "Blank image"
            else:
                images.append(screen.to_image())
                return "Image {}".format(len(images)-1)

        # obj must be dict or list
        def helper(obj, omit_blanks):
            if type(obj) is list:
                for i in range(len(obj)):
                    if type(obj[i]) is Screen:
                        obj[i] = replace_image(obj[i], omit_blanks)
                    else:
                        helper(obj[i], omit_blanks)
            elif type(obj) is dict:
                for (key, value) in obj.items():
                    if type(value) is Screen:
                        obj[key] = replace_image(value, omit_blanks)
                    else:
                        helper(value, omit_blanks)

        helper(description, omit_blanks)
        return images

    def __eq__(self, other):
        return type(self) is type(other) and self.__dict__ == other.__dict__

    def __str__(self):
        return repr(self)

    def __repr__(self):
        s = "Evaluator: conditions={}, test_points={}, aggregators={}"
        return s.format(self.conditions, self.test_points, self.aggregators)