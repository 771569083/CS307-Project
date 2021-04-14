import faker
import math
import random


class Fake:
    choices = random.choices
    randint = random.randint

    def __init__(self, locale='zh'):
        self._f = faker.Faker(locale=locale)
        self._args = {
            'teacher_uid': 30000000,
            'student_uid': 11700000,
        }

    def boolean(self):
        return bool(random.randint(0, 1))

    def teacher_uid(self):
        self._args['teacher_uid'] += 1
        return self._args['teacher_uid']

    def student_uid(self):
        self._args['student_uid'] += 1
        return self._args['student_uid']

    def name(self):
        return self._f.name()


class TaskBase:
    def __or__(self, subtask_name):
        subtask = getattr(self, subtask_name, None)
        assert subtask, 'variable `subtask_name` must in {{{}}}'.format(
            ', '.join(filter(lambda x: not x.startswith('_'), dir(Task2)))
        )
        return subtask()

    def _end(self, remark):
        print(remark)
        return self


def parse_prerequisite(prerequisite):
    '''Parse prerequisite

    Example:
        - (固体物理 或者 固体物理) 并且 量子力学II
    '''
    f = lambda x: list(set(filter(bool, map(str.strip, x))))
    g = lambda x: x.replace('(', '').replace(')', '')
    return [
        f(g(part).split('或者'))
        for part in prerequisite.split('并且')
    ]


def batches(subscriptable, batch_size):
    for ith in range(math.ceil(len(subscriptable)/batch_size)):
        yield subscriptable[ith*batch_size: (ith+1)*batch_size]
