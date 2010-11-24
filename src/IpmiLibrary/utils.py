from robot.utils import normalizing

def find_attribute(obj, attr, prefix):
    attr = str(attr)
    for i_attr in dir(obj):
        normalized_i_attr = normalizing.normalize(i_attr, ignore='_')
        normalized_attr = normalizing.normalize(prefix + attr,
                ignore='_')
        if normalized_i_attr == normalized_attr:
            return getattr(obj, i_attr)

    try:
        attr = int(attr, 0)
        return attr
    except ValueError:
        raise RuntimeError('Attribute "%s" in "%s" not found.' % (attr, obj))

def int_any_base(i, base=0):
    try:
        return int(i, base)
    except TypeError:
        return i
    except ValueError:
        raise RuntimeError('Could not parse integer "%s"' % i)
