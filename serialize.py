def encode(data, registry):
    '''transform object to json-encodable data'''
    if type(data) is list or type(data) == tuple:
        return [encode(x, registry) for x in data]
    elif type(data) is dict:
        return {k: encode(v, registry) for k, v in data.items()}
    elif data is None or type(data) in [int, bool, float, str]:
        return data
    elif hasattr(data, '__name__'): # this shall be a function
        if data.__name__[0] == '<':
            raise Exception('cannot encode lambdas')
        return {'__name__': data.__name__}
    else:
        key = str(id(data))
        if key not in registry:
            registry[key] = 1 # populate key to prevent cycles
            registry[key] = {'__type__': data.__class__.__name__, '__value__': encode(data.__dict__, registry), '__id__': key}
        return {'__ref__': key}

def decode(data, mapping, registry):
    '''transform json-decoded data to object'''
    if type(data) is list:
        return [decode(x, mapping, registry) for x in data]
    if type(data) is dict:
        if '__ref__' in data:
            if type(registry[data['__ref__']]) is dict:
                return decode(registry[data['__ref__']], mapping, registry)
            return registry[data['__ref__']]
        elif '__name__' in data:
            return mapping[data['__name__']]
        elif '__type__' in data:
            obj = mapping[data['__type__']]() # build empty object in case of cycle
            registry[data['__id__']] = obj
            obj.__init__(**decode(data['__value__'], mapping, registry))
            return obj
        return {k: decode(v, mapping, registry) for k, v in data.items()}
    else:
        return data

