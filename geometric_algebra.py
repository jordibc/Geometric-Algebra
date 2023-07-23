"""
Class to represent a multivector in geometric algebra, and related functions.
"""


class MultiVector:
    """
    A multivector has terms (blades) that look like [[x, base_array], ...],
    where base_array looks like [] for a scalar, [i] for ei, [1, 2] for e12...
    """

    def __init__(self, blades, signature=None):
        self.signature = signature
        self.blades = simplify_blades(blades)

    def __add__(self, v):
        v_blades = [[v, []]] if type(v) in [int, float] else v.blades

        return MultiVector([vi.copy() for vi in self.blades] +
                           [vi.copy() for vi in v_blades], self.signature)

    def __radd__(self, v):
        assert type(v) in [int, float]
        return self + v

    def __neg__(self):
        blades = [vi.copy() for vi in self.blades]

        for blade in blades:
            blade[0] = -blade[0]

        return MultiVector(blades, self.signature)

    def __sub__(self, v):
        return self + -v

    def __rsub__(self, v):
        assert type(v) in [int, float]
        return v + -self

    def __mul__(self, v):
        v_blades = [[v, []]] if type(v) in [int, float] else v.blades

        prod = []
        for term_i in self.blades:
            for term_j in v_blades:
                elem, factor = simplify_element(term_i[1] + term_j[1],
                                                self.signature)
                prod.append([factor * term_i[0] * term_j[0], elem])

        return MultiVector(prod, self.signature)

    def __rmul__(self, v):
        assert type(v) in [int, float]
        return self * v

    def __truediv__(self, v):
        if type(v) in [int, float]:
            v_inv = MultiVector([[1/v, []]], self.signature)
        elif len(v.blades) == 1:
            x, e = v.blades[0]
            v_inv = MultiVector([[1/x, e]], v.signature)
        else:
            raise ValueError('Cannot divide by non-blade: %s' % v)

        return self * v_inv

    def __rtruediv__(self, v):
        if len(self.blades) == 1:
            x, e = self.blades[0]
            inv = MultiVector([[1/x, e]], self.signature)
            return v * inv
        else:
            raise ValueError('Cannot divide by non-blade: %s' % self)

    def reverse(self):
        blades = [c.copy() for c in self.blades]

        for blade in blades:
            x, e = blade
            if (len(e) // 2) % 2 == 1:
                blade[0] = -x

        return MultiVector(blades, self.signature)

    @property
    def T(self):
        return self.reverse()

    def __eq__(self, v):
        return self.blades == v.blades and self.signature == v.signature

    def __float__(self):
        if not self.blades:
            return 0.0
        elif len(self.blades) == 1 and self.blades[0][1] == []:
            return float(self.blades[0][0])
        else:
            raise ValueError('Cannot convert to float: %s' % self)

    def __int__(self):
        if not self.blades:
            return 0
        elif len(self.blades) == 1 and self.blades[0][1] == []:
            return int(self.blades[0][0])
        else:
            raise ValueError('Cannot convert to float: %s' % self)

    def __str__(self):
        if not self.blades:
            return '0'
        e_str = lambda e: '' if not e else '*e' + ''.join(map(str, e))
        return ' + '.join('%s%s' % (x, e_str(e)) for x, e in self.blades)

    def __repr__(self):
        return self.__str__()  # so it looks nice in the interactive sessions
        # A more raw representation would be:
        #   signature_str = '' if self.signature is None else f', {self.signature}'
        #   return 'MultiVector(%s%s)' % (self.blades, signature_str)


def simplify_blades(v):
    """Return the blades of a multivector simplified.

    Example: 3 + 5 e12 + 6 e12 + 0.2  ->  3.2 + 11 e12
    """
    # The changes are made in-place.
    i = 0
    while i < len(v):
        if v[i][0] == 0:  # remove any terms like  0 e_
            v.pop(i)

            if i > 0:
                i -= 1  # so we compare next time from the previous element
        elif i + 1 >= len(v):
            break  # nothing left to compare, we are done
        elif v[i][1] == v[i+1][1]:  # add together terms with the same  e_
            v[i][0] += v[i+1][0]
            v.pop(i+1)
        elif (len(v[i][1]), v[i][1]) > (len(v[i+1][1]), v[i+1][1]):  # sort
            v[i], v[i+1] = v[i+1], v[i]  # 3 e12 + 5 e1  ->  5 e1 + 3 e12

            if i > 0:
                i -= 1  # so we keep comparing this element
        else:
            i += 1

    return v


def simplify_element(e, signature=None):
    """Return the simplification of a basis element, and the factor it carries.

    Example: e13512  ->  e235, +1  (if  e1*e1 == +1)
    """
    factor = 1

    i = 0
    while i < len(e) - 1:
        if e[i] == e[i+1]:  # repeated element -> contract
            if signature:
                factor *= signature[e[i]]

            e.pop(i)
            e.pop(i)
        elif e[i] > e[i+1]:  # unsorted order -> swap
            factor *= -1  # perpendicular vectors anticommute

            e[i], e[i+1] = e[i+1], e[i]

            if i > 0:
                i -= 1  # so we keep comparing this element
        else:  # go to the next element
            i += 1

    return e, factor


def dot(a, b):
    assert a.signature == b.signature
    v = a * b
    return MultiVector([v.blades[0]], a.signature)

def wedge(a, b):
    assert a.signature == b.signature
    v = a * b
    return MultiVector([v.blades[-1]], a.signature)
