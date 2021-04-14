__all__ = [
    'Memory', 'Explain',
    'Department', 'Semester', 'People', 'Course', 'Class',
]


import pathlib
import pickle
import time

from typing import NamedTuple, Optional, List, ForwardRef


class Memory:
    def __init__(self):
        self._keys = {
            'departments', 'semesters', 'peoples', 'courses', 'classes',
        }
        self._raw = dict()
        self._cache = dict()

    def __getitem__(self, key):
        return self.get(key)

    @classmethod
    def load(self, *path):
        return pickle.loads(
            pathlib.Path(*path).read_bytes()
        )

    @property
    def keys(self):
        return self._keys

    def get(self, key):
        return self._raw.get(key, None)

    def set(self, key, values, fields=()):
        assert key in self._keys and isinstance(values, list)
        self._raw[key] = values
        if fields:
            self._cache[key] = {
                tuple(getattr(value, field) for field in fields): value
                for value in values
            }

    def append(self, key, values, fields=()):
        assert key in self._keys and isinstance(values, list)
        self._raw[key] += values
        if fields:
            for value in values:
                unique = tuple(getattr(value, field) for field in fields)
                assert unique not in self._cache[key]
                self._cache[key][unique] = value

    def delete(self, key, condition):
        for ith, member in enumerate(self._raw[key]):
            if condition(member):
                self._raw[key][ith] = None
                for unique, value in self._cache.get(key, {}).items():
                    if value == member:
                        del self._cache[key][unique]
                        break
        self._raw[key] = list(filter(bool, self._raw[key]))

    def cache(self, key, *cache_key):
        return self._cache[key][cache_key]

    def relationship(self):
        for semester in self._raw['semesters']:
            semester.cache(self._raw['classes'])
        for people in self._raw['peoples']:
            people.cache(self._raw['classes'])
        for course in self._raw['courses']:
            course.cache(self._raw['classes'])
        return self

    def dump(self, *path):
        pathlib.Path(*path).write_bytes(
            pickle.dumps(self)
        )

    def _done(self):
        return set(self._raw) == self._keys


class Explain:
    def __init__(self, echo=False):
        self._tic = 0.0
        self._echo = print if echo else lambda *x: None

    def tic(self):
        self._tic = time.time()

    def toc(self):
        return time.time() - self._tic

    def execute_raw(self, number, functions, argses=((), ), kwargses=({}, )):
        totals = [0] * len(functions)
        for _ in range(number):
            for ith, function in enumerate(functions):
                self.tic()
                function(*argses[ith], **kwargses[ith])
                totals[ith] += self.toc() / number
        return totals


class Department(NamedTuple):
    name: Optional[str] = None


class Semester(NamedTuple):
    year: int
    season: int

    classes: List[ForwardRef('Class')]

    def cache(self, classes):
        if not self.classes:
            self.classes.extend([
                class_ for class_ in classes if class_.semester==self
            ])


class People(NamedTuple):
    uid: int
    name: str
    role: str
    is_female: bool

    department: Department

    classes: List[ForwardRef('Class')]

    def cache(self, classes):
        if not self.classes:
            self.classes.extend([
                class_ for class_ in classes if self in class_.peoples
            ])


class Course(NamedTuple):
    hour: int
    credit: int
    code: str
    name: str
    prerequisite: str

    department: Department

    classes: List[ForwardRef('Class')]

    def cache(self, classes):
        if not self.classes:
            self.classes.extend([
                class_ for class_ in classes if class_.course==self
            ])


class Class(NamedTuple):
    capacity: int
    name: str
    list: List

    course: Course
    semester: Semester

    peoples: List[People]

    def remaining_amount(self, role='S'):
        return self.capacity - sum(1 for p in self.peoples if p.role==role)


def __repr__(self):
    def recursion(field):
        value = getattr(self, field)
        if isinstance(value, tuple):
            return f'{type(value).__name__}(...)'
        elif isinstance(value, list):
            return '[...]'
        else:
            return value
    arguments = ', '.join(
        f'{field}={recursion(field)}' for field in self._fields
    )
    return f'{type(self).__name__}({arguments})'


Department.__repr__ = __repr__
Semester.__repr__ = __repr__
People.__repr__ = __repr__
Course.__repr__ = __repr__
Class.__repr__ = __repr__
