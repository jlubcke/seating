import simplejson


class SearchResult(object):
    def __init__(self):
        self.state = None
        self.energy = None

    def to_json(self):
        return simplejson.dumps({'state': self.state.to_json, 'energy': self.energy})

    @classmethod
    def from_json(cls, json):
        state_as_dict = simplejson.loads(json)
        state = cls()
        state.state = state_as_dict.get('state')
        state.energy = state_as_dict.get('energy')
        return state
