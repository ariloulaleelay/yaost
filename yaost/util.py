from yaost.vector import Vector


def nice_float(v: float):
    result = f'{v:.6f}'
    result = result.rstrip('0').rstrip('.')
    return result


def _serialize_argument(v):
    if isinstance(v, bool):
        chunk = 'true' if v else 'false'
    elif isinstance(v, (int, float)):
        chunk = nice_float(v)
    elif isinstance(v, Vector):
        chunk = _serialize_argument([v.x, v.y, v.z])
    elif isinstance(v, (list, tuple)):
        chunk = '[{}]'.format(','.join(_serialize_argument(vv) for vv in v))
    elif isinstance(v, str):
        chunk = f'"{v}"'
    else:
        raise RuntimeError(f'Unknown type of v: {type(v)}')
    return chunk


def full_arguments_line(args=(), kwargs=()):
    chunks = []
    for arg in args:
        chunk = _serialize_argument(arg)
        chunks.append(chunk)

    for key in sorted(kwargs):
        value = kwargs[key]
        if value is None:
            continue
        key_str = key
        if key_str == 'fn':
            key_str = '$fn'
        chunks.append(f'{key_str}={_serialize_argument(value)}')
    return ','.join(chunks)
