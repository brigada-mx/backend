def constrain(n, min_, max_):
    """Constrain value to be within [`min_`, `max_`].
    """
    return max(min(max_, n), min_)


def round_base(x, base):
    """Round `x` to nearest `base`.
    """
    return int(base * round(float(x)/base))
