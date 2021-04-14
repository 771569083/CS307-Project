import collections
import json
import pathlib
import tqdm
import uvicorn

from sqlalchemy import func

from database import (
    session, add, get, create_all,
    Department, Course, Class, People, Semester, ClassPeople,
    Explain,
)
from memory import memory
from utils import Fake, TaskBase, parse_prerequisite, batches
from app.database.utils import create_all as create_all_ext


class Task2(TaskBase):
    '''Import data

    - Design scripts to import data into your database from those two files (
        course_info.json and select_course.csv
    )
    - Finding ways to improve the efficiency of time consuming during your
      importing process, and make comparison between different importing ways
    - Make sure all data is successfully imported
    '''
    def __init__(
        self, path_course_info, locale, encoding, student_number, class_minmax, batch_size,
    ):
        '''
        Argument:
            - path_course_info: Tuple[str], i.e. ('data', 'course_info.json')
            - locale: str, i.e. 'zh'
            - encoding: str, i.e. 'utf-8'
            - student_number: int, i.e. 1_000_000
            - class_minmax: Tuple[int], i.e. (0, 7)
            - batch_size: int, i.e. 1_000
        '''
        self._path = pathlib.Path(*path_course_info)
        self._fake = Fake(locale=locale)
        self._encoding = encoding
        self._number = student_number
        self._minmax = lambda: self._fake.randint(*class_minmax)
        self._batch = batch_size

    def create_all(self):
        create_all()
        return self._end('[Done] create_all')

    def add_course_info(self):
        '''Department, semester, Course, People, Class
        '''
        add.department(None)  # 未选专业
        semester_id = add.semester(2021, 1).id  # 暂时只添加了一个学期
        data = json.loads(self._path.read_text(self._encoding))
        for course in tqdm.tqdm(data):  # 添加课程常规信息
            add.course(
                course['courseHour'], course['courseCredit'], course['courseId'],
                course['courseName'], course['courseDept'],
            )
            teachers = (course['teacher'] or '').split(',')
            ranges = range(len(teachers))
            add.peoples(*add.people_yield(
                (self._fake.teacher_uid() for _ in ranges),
                teachers,
                (self._fake.boolean() for _ in ranges),
                (course['courseDept'] for _ in ranges)
            ))
            add.class_(
                course['totalCapacity'], course['className'], course['classList'],
                course['courseId'], semester_id, teachers,
            )
        for course in tqdm.tqdm(data):  # 添加课程依赖
            prerequisite = parse_prerequisite(course['prerequisite'] or '')
            add.course_prerequisite(course['courseId'], prerequisite)
        return self._end('[Done] add_course_info')

    def add_select_course(self):
        '''ClassPeople
        '''
        first = lambda x: x[0]
        department_names = tuple(map(first, get._by(Department.name, all=True)))
        class_ids = tuple(map(first, get._by(Class.id, all=True)))
        for batch in tqdm.tqdm(batches(range(self._number), self._batch)):
            uids = tuple(filter(
                lambda x: not get.people(uid=x),
                (self._fake.student_uid() for _ in range(len(batch)))
            ))
            ranges = range(len(uids))
            add.peoples(*add.people_yield(uids,
                (self._fake.name() for _ in ranges),
                (self._fake.boolean() for _ in ranges),
                (self._fake.choices(department_names)[0] for _ in ranges)
            ))
            class_idses = (
                set(self._fake.choices(class_ids, k=self._minmax())) for _ in ranges
            )
            add.class_peoples(*sum(
                add.class_people_yield(
                    uids, class_idses, ('S' for _ in ranges),
                ), ()
            ))
        return self._end('[Done] add_select_course')


class Task3(TaskBase):
    '''Compare database and file

    - Store the data into a database table. Then use DML (Data Manipulation
      Language) in SQL to do simple analysis of your db. Record the execution
      time of your algorithm.
    - Store the data into a file, and then load it into RAM. The data in RAM
      can be any format you preferred. Design an algorithm to simple analysis
      of your file. In this case, you can reorganize data into some other
      format for faster retrieval. Record the execution time of your algorithm.
    '''
    def __init__(
        self, path_pickle, number, echo,
    ):
        '''
        Argument:
            - path_pickle: Tuple[str], i.e. ('memory.pickle', )
            - number: int, i.e. 100
            - echo: bool, i.e. False
        '''
        self._path = pathlib.Path(*path_pickle)
        self._number = number
        self._echo = echo
        self._list = '[{"weekList": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"], "location": "荔园6栋404机房", "classTime": "9-10", "weekday": 2}, {"weekList": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"], "location": "荔园1栋102", "classTime": "7-8", "weekday": 2}]'

    def convert_to_file(self):
        '''Store the data into a file, and then load it into RAM
        '''
        m = memory.Memory()
        m.set(  # departments
            key='departments', fields=('name', ),
            values=[
                memory.Department(
                    name=department.name,
                ) for department in get._by(Department, all=True)
            ]
        )
        m.set(  # semesters
            key='semesters', fields=('year', 'season'),
            values=[
                memory.Semester(
                    year=semester.year, season=semester.season, classes=[],
                ) for semester in get._by(Semester, all=True)
            ]
        )
        m.set(  # peoples
            key='peoples', fields=('uid', ),
            values=[
                memory.People(
                    uid=people.uid, name=people.name, is_female=people.is_female,
                    role=('T' if people.uid>30000000 else 'S'), classes=[],
                    department=m.cache('departments', people.department.name),
                ) for people in get._by(People, all=True)
            ]
        )
        m.set(  # courses
            key='courses', fields=('code', ),
            values=[
                memory.Course(
                    hour=course.hour, credit=course.credit, code=course.code, name=course.name,
                    prerequisite=course.prerequisite, classes=[],
                    department=m.cache('departments', course.department.name),
                )
                for course in get._by(Course, all=True)
            ]
        )
        m.set(  # classes
            key='classes', fields=(),
            values=[
                memory.Class(
                    capacity=class_.capacity, name=class_.name,
                    list=json.loads(class_.list),
                    course=m.cache('courses', class_.course.code),
                    semester=m.cache('semesters', class_.semester.year, class_.semester.season),
                    peoples=[
                        m.cache('peoples', people.people.uid)
                        for people in class_.peoples
                    ],
                )
                for class_ in get._by(Class, all=True)
            ]
        )
        m.dump(self._path)
        return self._end('[Done] convert_to_file')

    def benchmark(self):
        '''Record the execution time of your algorithm
        '''
        result = dict()
        functions = (self._benchmark_i, self._benchmark_u, self._benchmark_d, self._benchmark_s)
        kwarg = lambda dom, m=None: {'database_or_memory': dom, 'm': m}
        e = Explain(echo=self._echo)
        me = memory.Explain(echo=self._echo)
        m = memory.Memory.load(self._path).relationship()
        # SQL
        result['SQL'] = e.execute_sql(self._number, tuple(f.__doc__ for f in functions))
        # ORM
        result['ORM'] = e.execute_orm(self._number, functions,
            argses=tuple(() for _ in functions),
            kwargses=tuple(kwarg(True) for _ in functions),
        )
        # MEMORY
        result['MEMORY'] = me.execute_raw(self._number, functions,
            argses=tuple(() for _ in functions),
            kwargses=tuple(kwarg(False, m) for _ in functions),
        )
        print(result)
        return self._end('[Done] benchmark')

    def _benchmark_i(self, database_or_memory=True, m=None):
        '''
        insert into People (id, uid, name, is_female, department_id) values
            (10797, 12000001, '张三', true, 7), (10798, 12000002, '李四', false, 7);
        insert into Semester (id, year, season) values (2, 2021, 2);
        insert into Class (id, capacity, course_id, semester_id, name, list) values
            (597, 35, 91, 2, '中英双语1班-实验1班', '');
        insert into "ClassPeople" (class_id, people_id, role) values
            (597, 10797, 'S'), (597, 10798, 'S');
        '''
        if database_or_memory:
            add._all(
                People(id=10797, uid=12000001, name='张三', is_female=True, department_id=7),
                People(id=10798, uid=12000002, name='李四', is_female=False, department_id=7),
            )
            add._all(Semester(id=2, year=2021, season=2))
            class_ = Class(
                id=597, capacity=35, course_id=91, semester_id=2, name='中英双语1班-实验1班', list='',
            )
            add._all(class_)
            add._all(
                ClassPeople(class_id=597, people_id=10797, role='S'),
                ClassPeople(class_id=597, people_id=10798, role='S'),
            )
        else:
            m = m or memory.Memory.load(self._path)
            department = m.cache('departments', '计算机科学与工程系')
            course = m.cache('courses', 'CS307')
            peoples = [
                memory.People(12000001, '张三', 'S', True, department, []),
                memory.People(12000002, '李四', 'S', False, department, []),
            ]
            semester = memory.Semester(2021, 2, [])
            class_ = memory.Class(35, '中英双语1班-实验1班', [], course, semester, peoples)
            m.append(key='peoples', fields=('uid', ), values=peoples)
            m.append(key='semesters', fields=('year', 'season'), values=[semester])
            m.append(key='classes', fields=(), values=[class_])

    def _benchmark_u(self, database_or_memory=True, m=None):
        '''
        update Class as c
        set list = '[{"weekList": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"], "location": "荔园6栋404机房", "classTime": "9-10", "weekday": 2}, {"weekList": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"], "location": "荔园1栋102", "classTime": "7-8", "weekday": 2}]'
        where c.id = 597;
        '''
        if database_or_memory:
            class_ = get._by(Class, id=597)
            if class_:
                class_.list = self._list
                add._all()
        else:
            m = m or memory.Memory.load(self._path)
            semester = m.cache('semesters', 2021, 2)
            list_ = json.loads(self._list)
            for class_ in m['classes']:
                if class_.semester == semester:
                    class_.list.extend(list_)

    def _benchmark_d(self, database_or_memory=True, m=None):
        '''
        delete from "ClassPeople" as cp where cp.people_id in (10797, 10798);
        delete from Class as c where c.id = 597;
        delete from Semester as s where s.id = 2;
        delete from People as p where p.id in (10797, 10798);
        '''
        if database_or_memory:
            session.query(ClassPeople).filter(ClassPeople.people_id.in_((10797, 10798))).delete()
            session.commit()
            session.query(Class).filter_by(id=597).delete()
            session.commit()
            session.query(Semester).filter_by(id=2).delete()
            session.commit()
            session.query(People).filter(People.id.in_((10797, 10798))).delete()
            session.commit()
        else:
            m = m or memory.Memory.load(self._path)
            m.delete('classes', lambda x: any(p.uid in (12000001, 12000002) for p in x.peoples))
            m.delete('semesters', lambda x: x.year==2021 and x.season==2)
            m.delete('peoples', lambda x: x.uid in (12000001, 12000002))

    def _benchmark_s(self, database_or_memory=True, m=None):
        '''
        with ClassStudent as (
            select cp.class_id, cp.people_id
            from "ClassPeople" as cp
            where cp.role = 'S'
        ), StudentSemesterClass as (
            select s.id as semester_id, count(*) as count
            from ClassStudent as cs
                inner join Class as cl on cl.id = cs.class_id
                    inner join Semester as s on s.id = cl.semester_id
            group by cs.people_id, s.id
        ), SemesterClass as (
            select ssc.semester_id, ssc.count, count(*) as number
            from StudentSemesterClass as ssc
            group by ssc.semester_id, ssc.count
            having ssc.count > 1
        )
        select
            '在 ' || s.year || ' 学年第 ' || s.season || ' 学期' ||
            '选了 ' || sc.count || ' 门课程的学生有 ' || sc.number || ' 人。'
        from SemesterClass as sc
            inner join Semester as s on s.id = sc.semester_id
        order by sc.number desc;
        '''
        if database_or_memory:
            ClassStudent = (
                session.query(ClassPeople.class_id, ClassPeople.people_id)
                    .filter_by(role='S')
                    .cte('ClassStudent')
            )
            StudentSemesterClass = (
                session.query(Semester.id.label('semester_id'), func.count().label('count'))
                    .select_from(ClassStudent)
                    .join(Class, Class.id==ClassStudent.c.class_id)
                    .join(Semester, Semester.id==Class.semester_id)
                    .group_by(ClassStudent.c.people_id, Semester.id)
                    .cte('StudentSemesterClass')
            )
            SemesterClass = (
                session.query(
                    StudentSemesterClass.c.semester_id, StudentSemesterClass.c.count,
                    func.count().label('number')
                )
                    .group_by(StudentSemesterClass.c.semester_id, StudentSemesterClass.c.count)
                    .having(StudentSemesterClass.c.count>1)
                    .cte('SemesterClass')
            )
            result = (
                session.query(
                    Semester.year, Semester.season,
                    SemesterClass.c.count, SemesterClass.c.number
                )
                    .select_from(SemesterClass)
                    .join(Semester, Semester.id==SemesterClass.c.semester_id)
                    .order_by(SemesterClass.c.number.desc())
            )
            return tuple(
                '在 {} 学年第 {} 学期选了 {} 门课程的学生有 {} 人。'.format(*row)
                for row in result
            )
        else:
            m = m or memory.Memory.load(self._path).relationship()
            data = collections.defaultdict(lambda: collections.defaultdict(int))
            counter = collections.defaultdict(int)
            for people in m['peoples']:
                if people.role == 'S':
                    counter.clear()
                    for class_ in people.classes:
                        key = class_.semester.year, class_.semester.season
                        counter[key] += 1
                    for semester, count in counter.items():
                        data[semester][count] += 1
            return sum(
                (
                    tuple(
                        '在 {} 学年第 {} 学期选了 {} 门课程的学生有 {} 人。'.format(
                            *semester, count, number
                        ) for count, number in subdata.items() if count>1
                    ) for semester, subdata in data.items()
                ), ()
            )


class Task4(TaskBase):
    '''Website
    '''
    def __init__(self, host, port):
        '''
        Argument:
            - host: str, i.e. '127.0.0.1'
            - locale: int, i.e. 5000
        '''
        self._host = host
        self._port = port

    def create_all_ext(self):
        create_all_ext()
        return self._end('[Done] create_all_ext')

    def deploy(self):
        uvicorn.run('app:app', host=self._host, port=self._port)
        return self._end('[Done] deploy')


class Task:
    ii = Task2
    iii = Task3
    iv = Task4


class F:
    def __getattribute__(self, name):
        return name
f = F()
