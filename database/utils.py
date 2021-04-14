__all__ = ['add', 'get', 'Explain', 'create_all']


import json
import time
import warnings

from sqlalchemy import event
from sqlalchemy.engine import Engine

from .models import (
    Base, engine, session,
    Department, Course, Class, People, Semester,
    ClassPeople,
)


class add:
    '''添加数据到数据库
    '''
    @classmethod
    def department(cls, name):
        department = get.department(name)
        if not department:
            department = Department(name=name)
            cls._all(department)
        return department

    @classmethod
    def course(cls, hour, credit, code, name, department_name):
        course = get.course(code=code)
        if not course:
            course = Course(
                hour=hour, credit=credit, code=code, name=name, prerequisite='[]',
                department_id=add.department(department_name).id,
            )
            cls._all(course)
        return course

    @classmethod
    def course_prerequisite(cls, code, prerequisite=[]):
        '''
        Argument:
            prerequisite: Tuple[Tuple[str]], [['机械设计基础'], ['控制工程基础', '控制工程基础']]

        Note:
            - 因为先修课数据的依赖采用的是非 UNIQUE 的 NAME 列，所以程序逻辑不严谨
        '''
        target_course = get.course(code=code)
        for ith, items in enumerate(prerequisite):
            for jth, item in enumerate(items):
                course = get.course(name=item)
                prerequisite[ith][jth] = course.id if course else None
            prerequisite[ith] = list(set(filter(bool, prerequisite[ith])))
        target_course.prerequisite = json.dumps(list(filter(bool, prerequisite)))
        cls._all()
        return target_course

    @classmethod
    def people(cls, uid, name, is_female, department_name):
        flag, people = next(
            cls.people_yield(
                (uid, ), (name, ), (is_female, ), (department_name, )
            )
        )
        (not flag) and cls._all(people)
        return people

    @classmethod
    def people_yield(cls, uids, names, is_females, department_names):
        for uid, name, is_female, department_name in zip(
            uids, names, is_females, department_names
        ):
            people = get.people(uid)
            flag = bool(people)
            if not flag:
                people = People(
                    uid=uid, name=name, is_female=is_female,
                    department_id=add.department(department_name).id
                )
            yield flag, people

    @classmethod
    def peoples(cls, *flags_peoples):
        cls._all(*(people for flag, people in flags_peoples if not flag))

    @classmethod
    def class_(cls, capacity, name, list, course_code, semester_id, teacher_names=[]):
        '''
        Note:
            - 因为先修课数据的教师采用的是非 UNIQUE 的 NAME 列，所以程序逻辑不严谨
        '''
        class_ = get.class_(course_code, semester_id, name)
        if not class_:
            class_ = Class(
                capacity=capacity, semester_id=semester_id, name=name,
                course_id=get.course(code=course_code).id,
                list=json.dumps(list, ensure_ascii=False),
            )
            for name in teacher_names:
                class_people = ClassPeople(role='T')
                class_people.people = get.people(name=name)
                class_.peoples.append(class_people)
            cls._all(class_)
        return class_

    @classmethod
    def class_people(cls, uid, class_ids, role='S'):
        class_peoples = next(
            cls.class_people_yield((uid, ), (class_ids, ), (role, ))
        )
        cls._all(*class_peoples)
        return class_peoples

    @classmethod
    def class_people_yield(cls, uids, class_idses, roles):
        for uid, class_ids, role in zip(uids, class_idses, roles):
            people_id = get.people(uid=uid).id
            yield tuple(
                ClassPeople(class_id=class_id, people_id=people_id, role=role)
                for class_id in class_ids
            )

    @classmethod
    def class_peoples(cls, *class_peoples):
        cls._all(*class_peoples)

    @classmethod
    def semester(cls, year, season):
        semester = get.semester(year, season)
        if not semester:
            semester = Semester(year=year, season=season)
            cls._all(semester)
        return semester

    @classmethod
    def _all(cls, *instances):
        try:
            session.add_all(instances)
            session.commit()
            return True
        except:
            warnings.warn(f'Add fails: instances={instances}')
            session.rollback()
            return False


class get:
    '''数据库数据获取
    '''
    @classmethod
    def department(cls, name):
        return get._by(Department, name=name)

    @classmethod
    def course(cls, code=None, **kwargs):
        kwargs = kwargs or {'code': code}
        return get._by(Course, **kwargs)

    @classmethod
    def people(cls, uid=None, **kwargs):
        kwargs = kwargs or {'uid': uid}
        return get._by(People, **kwargs)

    @classmethod
    def class_(cls, course_code, semester_id, name):
        course_id = cls.course(code=course_code).id
        return get._by(Class, course_id=course_id, semester_id=semester_id, name=name)

    @classmethod
    def semester(cls, year, season):
        return get._by(Semester, year=year, season=season)

    @classmethod
    def _by(cls, *models, all=False, count=False, iter=False, lock=None, **condition):
        try:
            query = session.query(*models).filter_by(**condition)
            if lock:
                query = query.with_lockmode(lock)
            if all:
                return query.all()
            if count:
                return query.count()
            if iter:
                return query
            return query.first()
        except Exception as e:
            print(e)
            args = f'models={repr(models)}, all={all}, condition={condition}'
            warnings.warn(f'Query fails: {args}')
            session.rollback()
            return list() if all else None


class Explain:
    def __init__(self, echo=False):
        self._current = None
        self._tic, self._toc = 0.0, 0.0
        self._echo = print if echo else lambda *x: None

        @event.listens_for(Engine, 'before_cursor_execute')
        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            self._current = statement
            self._tic = time.time()
            self._echo('[QUERY_START]', repr(self._current))

        @event.listens_for(Engine, 'after_cursor_execute')
        def after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            assert self._current == statement
            self._toc = time.time()
            self._echo('[QUERY_END]')

    @property
    def elapsed(self):
        return self._toc - self._tic

    @property
    def current(self):
        return self._current

    def execute_sql(self, number, statements, **kwargs):
        totals = [0] * len(statements)
        for _ in range(number):
            for ith, statement in enumerate(statements):
                for statement in statement.split(';')[:-1]:
                    session.execute(statement+';', **kwargs)
                    totals[ith] += self.elapsed / number
        return totals

    def execute_orm(self, number, functions, argses=((), ), kwargses=({}, )):
        totals = [0] * len(functions)
        for _ in range(number):
            for ith, function in enumerate(functions):
                function(*argses[ith], **kwargses[ith])
                totals[ith] += self.elapsed / number
        return totals


def create_all():
    Base.metadata.create_all(engine)
