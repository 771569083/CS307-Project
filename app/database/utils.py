import warnings

from .models import (
    Base, engine, session,
    Department, Course, Class, People, PeopleExt, Semester,
    ClassPeople,
)


class add:
    @classmethod
    def user(cls, uid, email, password):
        user = get.user(uid)
        if not user:
            user = PeopleExt(uid, email, password)
            cls._all(user)
        return user

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
    @classmethod
    def user(cls, uid):
        return cls._by(PeopleExt, uid=uid)

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


def create_all():
    Base.metadata.create_all(engine)
