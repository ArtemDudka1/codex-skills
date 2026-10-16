"""Small strict JSON schemas and independent validation of model output."""


def obj(properties):
    return {'type':'object', 'properties':properties, 'required':list(properties), 'additionalProperties':False}


def array(items):
    return {'type':'array', 'items':items}


STRING = {'type':'string'}
STRINGS = array(STRING)
FINDING = obj({'title':STRING, 'severity':{'type':'string','enum':['critical','high','medium','low']},
               'file':STRING, 'line':{'type':'integer','minimum':1}, 'evidence':STRING,
               'reproduction':STRING, 'recommendation':STRING})
AUDIT = obj({'summary':STRING, 'findings':array(FINDING), 'plan':STRINGS})
EDIT = obj({'summary':STRING, 'addressed_ids':STRINGS, 'unresolved_ids':STRINGS})
SCORE = obj({'candidate':{'type':'string','enum':['A','B']}, **{
    field:{'type':'integer','minimum':0,'maximum':10}
    for field in ('coverage','correctness','verification','maintainability')}})


def schema_for(role, phase='code'):
    if role == 'audit' or (role == 'defend' and phase == 'audit'):
        return AUDIT
    if role in ('implement','defend'):
        return EDIT
    if role == 'consolidate':
        return obj({'summary':STRING, 'groups':array(obj({'ids':STRINGS,'rationale':STRING}))})
    if role == 'attack':
        return obj({'summary':STRING, 'issues':array(obj({'severity':FINDING['properties']['severity'],'evidence':STRING,'finding_id':STRING})), 'carry_forward':STRINGS})
    if role == 'judge':
        return obj({'summary':STRING, 'scores':array(SCORE)})
    if role == 'final':
        return obj({'summary':STRING, 'blocking_issues':STRINGS, 'findings':array(obj({
            'finding_id':STRING,'status':{'type':'string','enum':['verified_fixed','unresolved','unconfirmed']},
            'evidence':STRING}))})
    raise ValueError(f'Unknown role: {role}')


def validate(value, schema, location='$'):
    kind = schema['type']
    expected = {'object':dict,'array':list,'string':str,'integer':int}[kind]
    if type(value) is not expected:
        raise ValueError(f'{location}: expected {kind}')
    if 'enum' in schema and value not in schema['enum']:
        raise ValueError(f'{location}: invalid enum value')
    if kind == 'object':
        if set(value) != set(schema['required']):
            raise ValueError(f'{location}: unexpected or missing fields')
        for key, child in schema['properties'].items():
            validate(value[key], child, f'{location}.{key}')
    elif kind == 'array':
        for index, item in enumerate(value):
            validate(item, schema['items'], f'{location}[{index}]')
    elif kind == 'integer':
        if value < schema.get('minimum', value) or value > schema.get('maximum', value):
            raise ValueError(f'{location}: outside allowed range')


def validate_response(value, role, phase='code'):
    validate(value, schema_for(role, phase))
    if role == 'judge' and sorted(row['candidate'] for row in value['scores']) != ['A','B']:
        raise ValueError('Judge must score A and B exactly once')
