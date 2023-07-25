"""
Class to represent a multivector in geometric algebra, and related functions.
"""


class MultiVector:
    """
    A multivector has terms (blades) that look like [[x, base_array], ...],
    where base_array looks like [] for a scalar, [i] for ei, [1, 2] for e12...
    """

    def __init__(self, blades, signature=None):
        assert signature is None or type(signature) == dict, 'Bad signature.'
        self.signature = signature
        self.blades = simplify_blades(blades)

    def __add__(self, v):  # multivector + whatever
        assert type(v) in [int, float] or v.signature == self.signature

        v_blades = [[v, []]] if type(v) in [int, float] else v.blades

        return MultiVector([blade.copy() for blade in self.blades] +
                           [blade.copy() for blade in v_blades], self.signature)

    def __radd__(self, v):  # number + multivector
        assert type(v) in [int, float]
        return self + v

    def __neg__(self):  # - self
        blades = [blade.copy() for blade in self.blades]

        for blade in blades:
            blade[0] = -blade[0]

        return MultiVector(blades, self.signature)

    def __sub__(self, v):  # multivector - whatever
        return self + -v

    def __rsub__(self, v):  # number - multivector
        assert type(v) in [int, float]
        return v + -self

    def __mul__(self, v):  # multivector * whatever  (geometric product)
        assert type(v) in [int, float] or v.signature == self.signature

        v_blades = [[v, []]] if type(v) in [int, float] else v.blades

        prod = []
        for x, ei in self.blades:
            for y, ej in v_blades:
                elem, factor = simplify_element(ei + ej, self.signature)
                prod.append([factor * x * y, elem])

        return MultiVector(prod, self.signature)

    def __rmul__(self, v):  # number * multivector
        assert type(v) in [int, float]
        return self * v

    def __truediv__(self, v):  # multivector / whatever
        if type(v) in [int, float]:
            v_inv = MultiVector([[1/v, []]], self.signature)
            return self * v_inv

        assert v.signature == self.signature
        try:
            v_r = v.reverse()
            v_norm2 = float(v * v_r)
            v_inv = v_r / v_norm2
            return self * v_inv
        except ValueError:
            raise ValueError('Multivector has no inverse: %s' % v)

    def __rtruediv__(self, v):  # number / multivector
        try:
            r = self.reverse()
            norm2 = float(self * r)
            inv = r / norm2
            return v * inv
        except ValueError:
            raise ValueError('Multivector has no inverse: %s' % self)

    def __pow__(self, n):
        assert type(n) == int, 'Can only raise to an integer'

        v = 1
        for i in range(abs(n)):
            v *= self

        if n >= 0:
            return v
        else:
            return 1/v

    def reverse(self):
        blades = [blade.copy() for blade in self.blades]

        for blade in blades:
            x, e = blade
            if (len(e) // 2) % 2 == 1:
                blade[0] = -x

        return MultiVector(blades, self.signature)

    @property
    def T(self):
        return self.reverse()

    def __eq__(self, v):
        if type(v) in [int, float]:
            try:
                return float(self) == v
            except ValueError:  # if we couldn't convert to float...
                return False  # no way we are equal!

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
            raise ValueError('Cannot convert to int: %s' % self)

    def __getitem__(self, r):  # grade-projection operator <A>_r
        blades = [blade for blade in self.blades if len(blade[1]) == r]
        return MultiVector(blades, self.signature)

    def __str__(self):
        if not self.blades:
            return '0'

        def blade_str(blade):
            x, e = blade
            show_e = (e != [])  # show the basis element, except for scalars
            show_x = (x != 1 or not show_e)  # do not show the number if just 1
            return ((str(x) if show_x else '') +
                    ('*' if show_x and show_e else '') +
                    (('e' + ''.join(f'{ei}' for ei in e)) if show_e else ''))

        return ' + '.join(blade_str(blade) for blade in self.blades)

    def __repr__(self):
        return self.__str__()  # so it looks nice in the interactive sessions
        # A more raw representation would be:
        #   sig_str = '' if self.signature is None else f', {self.signature}'
        #   return 'MultiVector(%s%s)' % (self.blades, sig_str)


def simplify_blades(v):
    """Return the blades of a multivector simplified.

    Example: 3 + 5*e12 + 6*e12 + 0.2  ->  3.2 + 11*e12
    """
    # The changes to v are made in-place.
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
            v[i], v[i+1] = v[i+1], v[i]  # 3*e12 + 5*e1  ->  5*e1 + 3*e12

            if i > 0:
                i -= 1  # so we keep comparing this element
        else:
            i += 1

    return v


def simplify_element(e, signature=None):
    """Return the simplification of a basis element, and the factor it carries.

    Example: e13512  ->  e235, +1  (if  e1*e1 == +1)
    """
    # The changes to e are made in-place.
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
    """Return the dot product (inner product) of multivectors a and b."""
    grades_a = [len(e) for _, e in a.blades]
    grades_b = [len(e) for _, e in b.blades]

    assert grades_a and grades_b, 'Dot not defined (yet) for scalars.'

    ga, gb = grades_a[0], grades_b[0]
    assert all(g == ga for g in grades_a) and all(g == gb for g in grades_b), \
        'Can only dot blades (for the moment).'

    return (a * b)[abs(ga - gb)]


def wedge(a, b):
    """Return the wedge product (exterior/outer product) of a and b."""
    grades_a = [len(e) for _, e in a.blades]
    grades_b = [len(e) for _, e in b.blades]

    assert grades_a and grades_b, 'Wedge not defined (yet) for scalars.'

    ga, gb = grades_a[0], grades_b[0]
    assert all(g == ga for g in grades_a) and all(g == gb for g in grades_b), \
        'Can only wedge blades (for the moment).'

    return (a * b)[ga + gb]


def commutator(a, b):
    return (a * b - b * a) / 2


def basis(signature, start=None):
    """Return basis elements of a geometric algebra with the given signature."""
    # A signature looks like (p, q) or (p, q, r), saying how many basis vectors
    # have a positive square (+1), negative (-1) and zero (0) respectively.
    #
    # A signature can also be a dict that tells you for each basis element what
    # its square is. For example, astrophysicists use for spacetime:
    #   signature = {0: -1, 1: +1, 2: +1, 3: +1}  # t, x, y, z  with e0 = e_t
    # whereas particle physicists normally use:
    #   signature = {0: +1, 1: -1, 2: -1, 3: -1}
    # which is the same as [1, 3] or even [1, 3, 0] in the alternative notation.

    if type(signature) == dict:
        assert start is None, 'Cannot use start when using a dict as signature.'
        start = min(signature)
        assert sorted(signature) == list(range(start, start+len(signature))), \
            'Basis vectors have to be successive numbers.'
    else:
        start = start if start is not None else 1
        n_pos, n_neg = signature[:2]
        n_null = signature[2] if len(signature) == 3 else 0
        signature = dict(zip(range(start, start + n_pos + n_neg + n_null),
                             [+1]*n_pos + [-1]*n_neg + [0]*n_null))

    n = len(signature)  # number of vectors

    elements = []

    e = []  # current element
    while e is not None:
        elements.append(e)
        e = next_element(e, n, start)

    return [MultiVector([[1, e]], signature) for e in elements]


def is_last(e, n, start=1):
    """Is e the last of the blades with that number of vectors?"""
    # An example of last blade for n=4, with 2 vectors: [2, 3]
    return e == list(range(start + n - len(e), start + n))


def next_element(e, n, start=1):
    """Return the multivector (in dim n) base element next to e."""
    if is_last(e, n, start):
        return list(range(start, start+len(e)+1)) if len(e) < n else None

    e_next = e.copy()  # new element (we will modify it in-place)

    # Find the last position that doesn't contain its maximum possible value.
    pos = next(len(e_next) - 1 - i for i in range(len(e_next))
               if e_next[-1 - i] != start + n - 1 - i)  # max possible value

    e_next[pos] += 1  # increment at that position
    for i in range(pos + 1, len(e_next)):
        e_next[i] = e_next[i-1] + 1  # and make the following ones follow up

    return e_next
