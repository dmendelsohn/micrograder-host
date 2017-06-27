from enum import Enum

class ConditionType(Enum):
    After = 1   # after(t=0) or after(condition)
    Or = 2      # or(subconditions)
    And = 3     # and(subconditions)

class Condition:
    # if cond_type is AFTER, cause is required
    #   subconditions[1:] are ignored
    #   cause is evaluated after subcondition[0].satisfied_at
    #       ... or t=0 if subconditions not given
    # if cond_type is Or or And, subconditions must be non-empty list of conditions, cause is ignored
    def __init__(self, cond_type, cause=None, subconditions=None):
        self.satisfied_at = None  # Initially, condition is automatically unsatisfied (i.e. t=None)
        self.type = cond_type
        self.cause = cause # integer (i.e. time), or function from request -> boolean
        self.subconditions = subconditions
        self.last_update_request = None

    def is_satisfied(self):
        return self.satisfied_at is not None

    # request: of type Request
    # returns None
    # updates satisfied_at given the incoming request, and updates child conditions if necessary
    def update(self, request):
        if self.last_update_request == request:
            return # No need to do anything, already updated for this request
        self.last_update_request = request

        if self.is_satisfied():
            return # No need to do anything, condition already satisfied

        elif self.type == ConditionType.After:
            if self.subconditions: # Ensure it's a non-empty list
                self.subconditions[0].update(request)
                start_time = self.subconditions[0].satisfied_at
            else:
                start_time = 0 # No subconditions, so subcondition satisfied at t=0

            if start_time is not None:
                if isinstance(self.cause, int): # satisfy a certain number of millis after start
                    satisfied_time = start_time + self.cause
                    if satisfied_time <= request.timestamp:
                        self.satisfied_at = satisfied_time
                else: # cause is a function from request -> boolean
                    if self.cause(request):
                        self.satisfied_at = request.timestamp

        elif self.type == ConditionType.Or:
            sub_times = []
            for subcondition in self.subconditions:
                subcondition.update(request)
                sub_times.append(subcondition.satisfied_at)
            
            if any(t is not None for t in sub_times): # If any t != None, we're satisfied
                self.satisfied_at = min(t for t in sub_times if t is not None) # min of non-Nones

        elif self.type == ConditionType.And:
            sub_times = []
            for subcondition in self.subconditions:
                subcondition.update(request)
                sub_times.append(subcondition.satisfied_at)
            
            if None not in sub_times: # If all elts in sub_times are not None, we're satisfied
                self.satisfied_at = max(sub_times)
