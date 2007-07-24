"""
This module contains several flavors of constraint solver classes.
Each has a method solve_for(name) and a method set(\*\*kwds). These methods
are used by the constraint solver (solver.Solver) to set the variables.

Variables should be of type solver.Variable.

Available constraints are:

- EqualsConstraint - make 'a' and 'b' equal
- LessThanConstraint - ensure one variable stays smaller than the orther
- EquationConstraint - solve a linear equation

# TODO:

- LineConstraint - Solves the equation where a line is connected to
       a line or side at a specific point.
- LineToCenterConstraint - constraint to be used when a line connects
       to a rectangular element. The line is connected on the side, but
       keeps opointing to the center
- ShortestLineConstraint - The last segment of the line is pointing to
       a rectangualar or line like object and the length of the line
       is kept to a minimum
"""
from __future__ import division
import operator

__version__ = "$Revision$"
# $HeadURL$

# is simple abs(x - y) > EPSILON enough for canvas needs?
EPSILON = 1e-6

def equals(a, b):
    return abs(a - b) < EPSILON


class Constraint(object):
    """
    Constraint base class.

    - _variables - list of all variables
    - _weakest   - list of weakest variables
    """
    disabled = False

    def __init__(self, *variables):
        """
        Create new constraint, register all variables, and find weakest
        variables.
        """
        self._variables = []
        for v in variables:
            self._variables.append(v)

        self.create_weakest_list()


    def create_weakest_list(self):
        """
        Create list of weakest variables.
        """
        # strength = min([v.strength for v in self._variables])
        strength = min(v.strength for v in self._variables)
        self._weakest = [v for v in self._variables if v.strength == strength]


    def variables(self):
        """
        Return an iterator which iterates over the variables that are
        held by this constraint.
        """
        return self._variables


    def weakest(self):
        """
        Return the weakest variable. The weakest variable should be always
        as first element of Constraint._weakest list.
        """
        return self._weakest[0]


    def mark_dirty(self, v):
        """
        Mark variable v dirty and if possible move it to the end of
        Constraint._weakest list to maintain weakest variable invariants
        (see gaphas.solver module documentation).
        """
        if v is self.weakest():
            self._weakest.remove(v)
            self._weakest.append(v)


    def solve_for(self, var):
        """
        Solve the constraint for a given variable.
        The variable itself is updated.
        """
        raise NotImplemented



class EqualsConstraint(Constraint):
    """
    Simple Constraint, takes two arguments: 'a' and 'b'. When solved the
    attribute passed to solve_for() is set equal to the other.

    >>> from solver import Variable
    >>> a, b = Variable(1.0), Variable(2.0)
    >>> eq = EqualsConstraint(a, b)
    >>> eq.solve_for(a)
    >>> a
    Variable(2, 20)
    >>> a.value = 10.8
    >>> eq.solve_for(b)
    >>> b
    Variable(10.8, 20)
    """

    def __init__(self, a=None, b=None):
        super(EqualsConstraint, self).__init__(a, b)
        self.a = a
        self.b = b

    def solve_for(self, var):
        assert var in (self.a, self.b)

        if not equals(self.a.value, self.b.value):
            if var is self.a:
                self.a.value = self.b.value
            else:
                self.b.value = self.a.value


class CenterConstraint(Constraint):
    """
    Simple Constraint, takes three arguments: 'a', 'b' and center.
    When solved, the constraint ensures 'center' is located in the middle
    of 'a' and 'b'.

    >>> from solver import Variable
    >>> a, b, center = Variable(1.0), Variable(3.0), Variable()
    >>> eq = CenterConstraint(a, b, center)
    >>> eq.solve_for(a)
    >>> a
    Variable(1, 20)
    >>> center
    Variable(2, 20)
    >>> a.value = 10
    >>> eq.solve_for(b)
    >>> b
    Variable(3, 20)
    >>> center
    Variable(6.5, 20)
    """

    def __init__(self, a=None, b=None, center=None):
        super(CenterConstraint, self).__init__(a, b, center)
        self.a = a
        self.b = b
        self.center = center

    def solve_for(self, var):
        assert var in (self.a, self.b, self.center)

        v = (self.a.value + self.b.value) / 2.0
        if not equals(self.center.value, v):
            self.center.value = v


class LessThanConstraint(Constraint):
    """
    Ensure @smaller is less than @bigger. The variable that is passed
    as to-be-solved is left alone (cause it is the variable that has not
    been moved lately). Instead the other variable is solved.

    >>> from solver import Variable
    >>> a, b = Variable(3.0), Variable(2.0)
    >>> lt = LessThanConstraint(smaller=a, bigger=b)
    >>> lt.solve_for(a)
    >>> a, b
    (Variable(3, 20), Variable(3, 20))
    >>> b.value = 0.8
    >>> lt.solve_for(b)
    >>> a, b
    (Variable(0.8, 20), Variable(0.8, 20))

    Also minimal delta between two values can be set
    >>> a, b = Variable(10.0), Variable(8.0)
    >>> lt = LessThanConstraint(smaller=a, bigger=b, delta=5)
    >>> lt.solve_for(a)
    >>> a, b
    (Variable(10, 20), Variable(15, 20))
    """

    def __init__(self, smaller=None, bigger=None, delta=0.0):
        super(LessThanConstraint, self).__init__(smaller, bigger)
        self.smaller = smaller
        self.bigger = bigger
        self.delta = delta

    def solve_for(self, var):
        if self.smaller.value > self.bigger.value - self.delta:
            if var is self.smaller:
                self.bigger.value = self.smaller.value + self.delta
            elif var is self.bigger:
                self.smaller.value = self.bigger.value - self.delta


# Constants for the EquationConstraint
ITERLIMIT = 1000        # iteration limit

class EquationConstraint(Constraint):
    """
    Equation solver using attributes and introspection.

    Takes a function, named arg value (opt.) and returns a Constraint object
    Calling EquationConstraint.solve_for will solve the equation for
    variable @arg, so that the outcome is 0.

    >>> from solver import Variable
    >>> a, b, c = Variable(), Variable(4), Variable(5)
    >>> cons = EquationConstraint(lambda a, b, c: a + b - c, a=a, b=b, c=c)
    >>> cons.solve_for(a)
    >>> a
    Variable(1, 20)
    >>> a.value = 3.4
    >>> cons.solve_for(b)
    >>> b
    Variable(1.6, 20)

    From: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/303396
    """
    
    def __init__(self, f, **args):
        super(EquationConstraint, self).__init__(*args.values())
        self._f = f
        self._args = {}
        # see important note on order of operations in __setattr__ below.
        for arg in f.func_code.co_varnames[0:f.func_code.co_argcount]:
            self._args[arg] = None
        self._set(**args)

    def __repr__(self):
        argstring = ', '.join(['%s=%s' % (arg, str(value)) for (arg, value) in
                             self._args.items()])
        if argstring:
            return 'EquationConstraint(%s, %s)' % (self._f.func_code.co_name, argstring)
        else:
            return 'EquationConstraint(%s)' % self._f.func_code.co_name

    def __getattr__(self, name):
        """
        Used to extract function argument values.
        """
        self._args[name]
        return self.solve_for(name)

    def __setattr__(self, name, value):
        """
        Sets function argument values.
        """
        # Note - once self._args is created, no new attributes can
        # be added to self.__dict__.  This is a good thing as it throws
        # an exception if you try to assign to an arg which is inappropriate
        # for the function in the solver.
        if self.__dict__.has_key('_args'):
            if name in self._args:
                self._args[name] = value
            elif name in self.__dict__:
                self.__dict__[name] = value
            else:
                raise KeyError, name
        else:
            object.__setattr__(self, name, value)

    def _set(self, **args):
        """
        Sets values of function arguments.
        """
        for arg in args:
            self._args[arg]  # raise exception if arg not in _args
            setattr(self, arg, args[arg])


    def solve_for(self, var):
        """
        Solve this constraint for the variable named 'arg' in the
        constraint.
        """
        args = {}
        for nm, v in self._args.items():
            args[nm] = v.value
            if v is var: arg = nm
        v = self._solve_for(arg, args) 
        if var.value != v:
            var.value = v


    def _solve_for(self, arg, args):
        """
        Newton's method solver
        """
        #args = self._args
        close_runs = 10   # after getting close, do more passes
        if args[arg]:
            x0 = args[arg]
        else:
            x0 = 1
        if x0 == 0:
            x1 = 1
        else:
            x1 = x0*1.1
        def f(x):
            """function to solve"""
            args[arg] = x
            return self._f(**args)
        fx0 = f(x0)
        n = 0
        while 1:                    # Newton's method loop here
            fx1 = f(x1)
            if fx1 == 0 or x1 == x0:  # managed to nail it exactly
                break
            if abs(fx1-fx0) < EPSILON:    # very close
                close_flag = True
                if close_runs == 0:       # been close several times
                    break
                else:
                    close_runs -= 1       # try some more
            else:
                close_flag = False
            if n > ITERLIMIT:
                print "Failed to converge; exceeded iteration limit"
                break
            slope = (fx1 - fx0) / (x1 - x0)
            if slope == 0:
                if close_flag:  # we're close but have zero slope, finish
                    break
                else:
                    print 'Zero slope and not close enough to solution'
                    break
            x2 = x0 - fx0 / slope           # New 'x1'
            fx0 = fx1
            x0 = x1
            x1 = x2
            n += 1
        return x1



class BalanceConstraint(Constraint):
    """
    Ensure that a variable @v is between values specified by @band
    and in distance proportional from @band[0].

    Consider
    >>> from solver import Variable, WEAK
    >>> a, b, c = Variable(2.0), Variable(3.0), Variable(2.3, WEAK)
    >>> bc = BalanceConstraint(band=(a,b), v=c)
    >>> c.value = 2.4
    >>> c
    Variable(2.4, 10)
    >>> bc.solve_for(c)
    >>> a, b, c
    (Variable(2, 20), Variable(3, 20), Variable(2.3, 10))

    Band does not have to be band[0] < band[1]
    >>> a, b, c = Variable(3.0), Variable(2.0), Variable(2.45, WEAK)
    >>> bc = BalanceConstraint(band=(a,b), v=c)
    >>> c.value = 2.50
    >>> c
    Variable(2.5, 10)
    >>> bc.solve_for(c)
    >>> a, b, c
    (Variable(3, 20), Variable(2, 20), Variable(2.45, 10))
    """

    def __init__(self, band=None, v=None, balance=None):
        super(BalanceConstraint, self).__init__(band[0], band[1], v)
        self.band = band
        self.balance = balance
        self.v = v

        if self.balance is None:
            self.update_balance()


    def update_balance(self):
        b1, b2 = self.band
        w = b2 - b1
        if w != 0:
            self.balance = (self.v - b1) / w
        else:
            self.balance = 0


    def solve_for(self, var):
        b1, b2 = self.band
        w = b2.value - b1.value
        value = b1.value + w * self.balance
        if not equals(var.value, value):
            var.value = value


class LineConstraint(Constraint):
    """
    Ensure a point is kept on a line.

    Attributes:
     - _line: line defined by tuple ((x1, y1), (x2, y2))
     - _point: point defined by tuple (x, y)
    """

    def __init__(self, line, point):
        super(LineConstraint, self).__init__(line[0][0], line[0][1], line[1][0], line[1][1], point[0], point[1])

        self._line = line
        self._point = point
        self.update_ratio()

    def update_ratio(self):
        """
        >>> from gaphas.solver import Variable
        >>> line = (Variable(0), Variable(0)), (Variable(30), Variable(20))
        >>> point = (Variable(15), Variable(4))
        >>> lc = LineConstraint(line=line, point=point)
        >>> lc.update_ratio()
        >>> lc.ratio_x, lc.ratio_y
        (0.5, 0.20000000000000001)
        >>> line[1][0].value = 40
        >>> line[1][1].value = 30
        >>> lc.solve_for(point[0])
        >>> lc.ratio_x, lc.ratio_y
        (0.5, 0.20000000000000001)
        >>> point
        (Variable(20, 20), Variable(6, 20))
        """
        sx, sy = self._line[0]
        ex, ey = self._line[1]
        px, py = self._point

        try:
            self.ratio_x = float(px.value - sx.value) / float(ex.value - sx.value)
        except ZeroDivisionError:
            self.ratio_x = 0.0
        try:
            self.ratio_y = float(py.value - sy.value) / float(ey.value - sy.value)
        except ZeroDivisionError:
            self.ratio_y = 0.0

        
    def solve_for(self, var=None):
        self._solve()

    def _solve(self):
        """
        Solve the equation for the connected_handle.
        >>> from gaphas.solver import Variable
        >>> line = (Variable(0), Variable(0)), (Variable(30), Variable(20))
        >>> point = (Variable(15), Variable(4))
        >>> lc = LineConstraint(line=line, point=point)
        >>> lc.update_ratio()
        >>> lc.solve_for(point[0])
        >>> point
        (Variable(15, 20), Variable(4, 20))
        >>> line[1][0].value = 40
        >>> line[1][1].value =  30
        >>> lc.solve_for(point[0])
        >>> point
        (Variable(20, 20), Variable(6, 20))
        """
        sx, sy = self._line[0]
        ex, ey = self._line[1]
        px, py = self._point

        x = sx.value + (ex.value - sx.value) * self.ratio_x
        y = sy.value + (ey.value - sy.value) * self.ratio_y

        if not equals(px.value, x):
            px.value = x
        if not equals(py.value, y):
            py.value = y




#
# Obsolete:
#
class Projector(object):
    """
    Base class for variable space projectors.

    Variable space projectors allow to convert variables' values to common
    space before constraint solving.

    Consider two geometrical objects defined by their position (x0, y0)
    and object's affine information (see gaphas.tests.test_projector module)
    >>> from solver import Variable
    >>> from gaphas.tests.test_projector import Rectangle, Vector, AffineProjector
    >>> r = Rectangle(5, 5, 20, 20)
    >>> v = Vector(5, 50, 5, -25)

    To keep vector's terminal point on a rectangle's bottom side create
    affine projector and appropriate constraints
    >>> proj = AffineProjector()
    >>> zero = Variable(0)  # used for balance constraint band
    >>> bc = BalanceConstraint(band=(zero, r.width), v=v.x, balance=0.25)
    >>> eq = EqualsConstraint(a=r.height, b=v.y)
    >>> proj(bc, data={v.x: v.x0, r.width: r.x0, zero: r.x0})
    >>> proj(eq, data={v.y: v.y0, r.height: r.y0})
    
    Let's change rectangle dimensions
    >>> r.width.value = 24
    >>> r.height.value = 25

    and use constraints to keep vector's terminal point on rectangle bottom
    side
    >>> bc.solve_for(v.x)
    >>> eq.solve_for(v.y)
    >>> v.x, v.y
    (Variable(6, 20), Variable(-20, 20))

    It is also possible to use projection in case of other constraint's
    methods than 'solve_for'
    >>> r = Rectangle(5, 5, 20, 20)
    >>> v = Vector(10, 50, 5, -25)
    >>> zero = Variable(0)
    >>> bc = BalanceConstraint(band=(zero, r.width), v=v.x)
    >>> proj(bc, data={v.x: v.x0, r.width: r.x0, zero: r.x0}, f=bc.update_balance)
    >>> bc.update_balance()
    >>> bc.balance
    0.5
    """
    def _cproj(self):
        """
        Perform projection to common space.
        """
        raise NotImplemented


    def _iproj(self):
        """
        Perform projection to internal space.
        """
        raise NotImplemented


    def __call__(self, c, *args, **kw):
        """
        Decorator for Constraint.solve_for method to perform projection to
        common space before variable solving and later project to internal
        variable space.
        """
        if 'f' in kw:
            f = kw['f']
            fn = f.__name__
        else:
            f = c.solve_for
            fn = 'solve_for'

        def wrapper(*fargs):
            self._cproj(c, *args, **kw)
            f(*fargs)
            self._iproj(c, *args, **kw)

        setattr(c, fn, wrapper)



if __name__ == '__main__':
    import doctest, sys
    sys.path.append('..')
    doctest.testmod()

# vim:sw=4:et:ai
