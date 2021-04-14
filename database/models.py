__all__ = [
    'Base', 'engine', 'session',
    'Department', 'Course', 'Class', 'People', 'Semester',
    'ClassPeople',
]


from sqlalchemy import (
    Table, Column, String, Integer, Boolean,
    UniqueConstraint, ForeignKey, Index,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

try:
    from .config import database_url
except:
    from .config_demo import database_url


Base = declarative_base()
engine = create_engine(database_url)
DBSession = sessionmaker(bind=engine)
session = DBSession()


def __repr__(self):
    f = lambda x: not x.startswith('_')
    g = lambda k, v: f'{k}={repr(v)}'
    items = self.__dict__.items()
    return f'{self.__tablename__}({", ".join(g(k, v) for k, v in items if f(k))})'


Base.__repr__ = __repr__


class Department(Base):
    __tablename__ = 'department'

    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=True, unique=True)

    courses = relationship('Course')
    peoples = relationship('People')


class ClassPeople(Base):
    __tablename__ = 'ClassPeople'

    class_id = Column(Integer, ForeignKey('class.id'), primary_key=True)
    people_id = Column(Integer, ForeignKey('people.id'), primary_key=True)
    role = Column(String(1), nullable=False)

    class_ = relationship('Class', back_populates='peoples')
    people = relationship('People', back_populates='classes')


class Course(Base):
    __tablename__ = 'course'

    id = Column(Integer, primary_key=True)
    hour = Column(Integer, nullable=False)
    credit = Column(Integer, nullable=False)
    code = Column(String(16), nullable=False, unique=True)
    name = Column(String(64), nullable=False)
    prerequisite = Column(String(None), nullable=False)

    department_id = Column(Integer, ForeignKey('department.id'))
    department = relationship('Department', back_populates='courses')

    classes = relationship('Class')


class Class(Base):
    __tablename__ = 'class'

    id = Column(Integer, primary_key=True)
    capacity = Column(Integer, nullable=False)
    course_id = Column(Integer, ForeignKey('course.id'))
    semester_id = Column(Integer, ForeignKey('semester.id'))
    name = Column(String(64), nullable=False)
    list = Column(String(None), nullable=False)

    UniqueConstraint('course_id', 'semester_id', 'name')

    course = relationship('Course', back_populates='classes')
    semester = relationship('Semester', back_populates='classes')

    peoples = relationship('ClassPeople', back_populates='class_')

    def remaining_amount(self, role='S'):
        '''
        TODO: 如果是积分选课，可以定时更新课程余量信息
        '''
        return self.capacity - session.query(ClassPeople).filter_by(class_id=self.id, role=role).count()


class Semester(Base):
    __tablename__ = 'semester'

    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    season = Column(Integer, nullable=False)

    UniqueConstraint('year', 'season')

    classes = relationship('Class', back_populates='semester')


class People(Base):
    __tablename__ = 'people'

    id = Column(Integer, primary_key=True)
    uid = Column(Integer, nullable=False, unique=True)
    name = Column(String(64), nullable=False)
    is_female = Column(Boolean, nullable=False)

    department_id = Column(Integer, ForeignKey('department.id'))
    department = relationship('Department', back_populates='peoples')

    classes = relationship('ClassPeople', back_populates='people')


Index('index_ClassPeople_class_role', ClassPeople.class_id, ClassPeople.role)
