# CS307 Project1

## 小组信息和分工

成员  :
- 梁钰栋（11711217）
- 王焕辰（11810419）

## 任务一：数据库设计
通过分别建立院系（Department）、课程（Course）、人员（People）、班级（Class）、班级成员（ClassPeople）6个表，来完成数据库的建立。

+ 院系表格中包含：
  + 主键（Primary Key）：自增的整数型 id
  + 唯一（Unique）：最大长度为64的 CHAR 类型院系名称（name）

+ 课程表格中包含：
  + 主键（Primary Key）：自增的整数型 id
  + 非空（Not null）：最大长度为16的 CHAR 类型课程代码（code），文本类型的先修课（prerequisite），整数型的课程课时（hour），整数型的课程学分（credit），最大长度为 64 的 CHAR 类型课程名称（name），整数型的院系id（department_id）
  + 唯一（Unique）：课程代码（code）
  + 外键（Foreign Key）：院系 id（department_id）与 院系表中的 id 链接

+ 人员表格中包含：
  + 主键（Primary Key）：自增的整数型 id
  + 非空（Not null）：整数型的 uid，最大长度为 64 的 CHAR 类型姓名（name），布尔类型的性别判断（is_female）以及整数型的院系 id（department_id）
  + 唯一（Unique）：uid
  + 外键（Foreign Key）：院系 id（department_id）与 院系表中的 id 链接

+ 班级表格中包含：
    + 主键（Primary Key）：自增的整数型 id
    + 非空（Not null）：整数型的课程容量（capacity），整数型的学期编号（semester_id），最大长度为 64 的 CHAR 类型班级名（name），text类型的 weeklist（list）以及整数型的课程 id（course_id）
    + 唯一（Unique）：课程 id，学期 id 以及班级名的联合
    + 外键（Foreign Key）：课程 id（course_id）与 课程中的 id 链接，学期 id（semester_id）与学期表中的 id 链接

+ 学期表中包含：
    + 主键（Primary Key）：自增的整数型 id
    + 非空（Not null）：整数型的年（year），整数型的季节（season）
    + 唯一（Unique）：年与季节的联合

+ 班级成员表中包含：
  + 主键（Primary Key）：由班级 id 以及成员 id 组成的联合主键
  + 非空（Not null）：整数型的班级 id（class_id），整数型的成员 id（people_id）以及最大长度为 1 的 CHAR 类型职责（role）
  + 外键（Foreign Key）：班级 id（class_id）与 班级中的 id 链接，成员 id（people_id）与人员表中的 id 链接

+ 班级成员 ClassPeople 中有索引

+ 整体数据库关系结构：

![information_schema](https://github.com/771569083/CS307-Project/blob/master/image/information_schema.png)



## 任务二：数据的导入
在数据的导入过程中，分为三个部分，本别是通过对象关系映射来建立所有数据库表，读取并批量导入课程信息，读取并批量导入选课信息

- 对于建立所有数据库表，我们通过运用 ORM（对象关系映射），将数据库中的表及其各属性与 Python 中的对象相关联，以 sqlalchemy 库作为中介来完成数据库设计部分所说数据库的建立，我们对每个表都定义了对应类，并通过实例化这些对象来用 sqlalchemy 库在数据库中建立表

- 对于读取并批量导入课程信息。首先对 course_info.json 文件做一些简单的处理，然后将除先修课程以外的其他课程数据通过 add 类中针对不同表的不同方法，导入到数据库中。 对于 add 类，通过对各表定义的不同的方法来导入，并结合上面所说的各表在 python 中的对象来 add 进去。

同时，定义了私有方法 _all：运用 sqlalchemy 库的 API 实现事务处理（用其中的 sessionmaker() 来创建 session 对象，用于事务处理，包含 add_all，commit，rollback 方法），即每一次调用 add 类中的方法来将数据添加到数据库的过程都是在一个事务中进行的。

主要代码：此处对象只设一列 院系 （./database/utils.py）

```python
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
    def _all(cls, *instances):
        try:
            session.add_all(instances)
            session.commit()
            return True
        except:
            warnings.warn(f'Add fails: instances={instances}')
            session.rollback()
            return False
```

由于使用了 sqlalchemy 库，可以进行批量导入，即每次数据量满足 commands 中 Task2 类中 batch_size 时才统一导入这一部分，我们这里设置为 1000。

由于在完全获取所有课程的课程信息之前，若直接导入先修课程，有可能还没有该先修课程的具体课程信息，因此，需要在完成其他课程数据的导入后，再将先修课程的相关数据导入。对于先修课程数据的处理：首先通过“并且”来将合取形式分解，进而去除括号并通过“或者”来将析取形式分解，并进行序列化，得到如`[[课程A，课程B]，课程C]`这样的形式，并根据已有课程表格中的主键 id 转化，导入到课程表格中的先修课程列中。

主要代码：(./commands.py)

```python
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
```

- 对于读取并批量导入选课信息。值得一提的是，由于我们的数据库人员表格中 uid 一值包括老师，但 project 随提供的已有数据（课程信息，选课信息）只有学生的 uid，为了更好的提高数据的质量，并且更简单的解决选课信息的导入过程，我们用 Faker 库，根据上一部分已经成功导入到数据库中的课程信息，来自造选课数据，其规模与所给的 select_course.csv 一致。

信息包含：
+ 学生姓名
+ 学生uid
+ 老师uid
+ 学生所选课程：根据 课程表格中的 id 采取均匀分布的随机选取 (0，7) 门课程。

在生成完这些数据之后，继续采用和导入课程信息一样的方法批量导入选课信息。

主要代码：(./commands.py)

````python
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
````

+ 可拓展
  + 课程余量，同时也就解决了每个班的目前的所选人数问题：获取该班级（Class）的课程容量，并获取该班级是对应id且职责（role）是学生的课程成员（ClassPeople）的数量。最后相减，就是目前该班级所剩课程余量，想要获取现在有多少人在该班级也可以参照此过程。

    主要代码：(./database/models.py)

    ```python
    def remaining_amount(self, role='S'):
            '''
          TODO: 如果是积分选课，可以定时更新课程余量信息
            '''
          return self.capacity - session.query(ClassPeople).filter_by(class_id=self.id, role=role).count()
    ```

  + 添加索引：由于考虑到要频繁使用班级成员（ClassPeople）中 class_id 以及 role 属性，我们通过 sqlalchemy 中现成的 Index 接口（name, table_attribute，table_attribute……），为他们设置了联合索引，来更快速的获得查询结果。
  
    主要代码: (./database/models.py)
  
    ````python
    Index('index_ClassPeople_class_role', ClassPeople.class_id, ClassPeople.role)
    ````
  
+ 导入时间对比：

   | 数据              | 批量导入 | 直接导入 |
   | ----------------- | -------- | -------- |
   | select_course.csv | 8 h      | 25 h     |

   另外，我们还做了将数据导入到不同数据库的时间对比，这部分将在 Task3 描述。



## 任务三：数据库模型和自定义模型的比较
开发环境： (./Pipfile)

```toml
[[source]]
url = "https://mirrors.aliyun.com/pypi/simple"
verify_ssl = true
name = "pypi"

[packages]
sqlalchemy = "*"
tqdm = "*"
faker = "*"
psycopg2 = "*"

[requires]
python_version = "3.8"

```

有关数据修改优化重组，在 Task2 中已经提及。

第三部分中，我们对数据库模型和直接将数据储存到文件中并重新载入到 RAM 中进行一些列对比。包括将数据转换成文件，将基于 DML 的数据库操作以及直接对数据文件进行相应类似的操作做对比：（在数据库进行数据操作语言（DML）即增删改查的时间，以及对已经重新载入德文件数据进行相应操作的时间）。

为了更好的优化后续的文件形式数据 DML 操作，定义了 Memory 类，思路是：将含有关系映射到数据库的这些对象，在保留他们之间关系的前提下，提取这些对象，并把他们存到文件中。这里，我们实现了一个 memory 类，用以转换成文件，并将这些对象数据用 pickle 序列化储存：

在memory类中，我们尽可能的仿照数据库的储存方式：将从数据库各表获取的原始数据用一个字典 _raw 储存，将各表的唯一属性（Unique column）用一个字典  _cache 去储存 ，这一特定唯一值用以在脱离数据库后的对象们间建立关系。如 学期（semester）对象中每个班级都是唯一的，就可以加入到 semester 的 cache 下面，而内容就是班级（class）对象的原始数据。而每个对象都定义一个类，对应到各表中的列，是类中的成员变量。这些成员变量可以是基本数据类型，也可以是可选列表，且里面的索引是其他类的引用（即这个列表可以含有null或元素）。并添加了增删改查，即 get，append，update 以及 delete 4 个方法用于后面比较时间。

主要代码：

+ memory 类部分 (./memory/models.py)

  ````python
  class Memory:
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
  ````

+ 对象部分，此处只设一例课程 Course (./memory/models.py)

  ````python
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
  ````

- 转换成文件方法部分，此处只设一列 set 院系 department (./commands.py)

  ````python
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
          m.dump(self._path)
          return self._end('[Done] convert_to_file')
  ````

- 对比部分，我们除了用通过 ORM 来对数据库进行增删改查操作与载入文件后的相应操作做对比，还通过 sqlalchemy 来生成对应的SQL语句，然后用SQL直接对数据库进行增删改查操作的方式和上面两种方式做对比。还对不同数据库：SQLite 与 PostgreSQL 这两个数据库进行增删改查进行了对比。

+ 下面首先是直接对数据库用 SQL 进行增删改查，通过 ORM 来对数据库进行增删改查以及在载入文件数据后用自己所写方法进行增删改查的平均时间对比 （单位： 秒）：			

| 方式   | 增                  | 改                 | 删                | 查                |
| ------ | ------------------- | ------------------ | ----------------- | ----------------- |
| SQL    | 0.008229446411132   | 0.007556028366088  | 0.017671799659    | 0.0551107597351   |
| ORM    | 0.015049998760223   | 0.008168644905090  | 0.015069091320037 | 0.062302780151367 |
| Memory | 2.0012855529785e-05 | 6.000280380249e-05 | 0.006245532035827 | 0.010259635448455 |

对于这个结果，数据库时间反倒慢一些，原因有两个：
1. 我们所用来测试时间的 SQL 语句比较简单，没有用到一些在数据库中有特定优化过的方法。

2. 我们对于载入并储存在内存的这些数据尽可能地仿照关系数据库来添加特性，再加上 Python 中指针的特性，因此优化的比较好。

而 ORM 比直接用 SQL 语句慢是正常的，直接通过用 SQL 语句来对数据库进行增删改查比间接通过映射的时间短是自然。

+ 然后是不同数据库：SQLite 与 PostgreSQL 间的对比 （单位：秒）：

| 数据库     | 增                 | 改                | 查                 | 查                |
| ---------- | ------------------ | ----------------- | ------------------ | ----------------- |
| SQLite     | 0.034855136871337  | 0.008770892620086 | 0.04497499942779   | 0.041084523200988 |
| PostgreSQL | 8.048534393310e-05 | 0.0               | 0.0012919163703918 | 0.014770812988281 |

+ 不同数据库导入数据的时间对比 ： 

| 数据库         | course_info.json（完整） | select_course.csv（35000条） |
| -------------- | ----------------------- | ----------------------------- |
| 本地SQLite     | 15 s                    | 20 s                          |
| 远程PostgreSQL | 1 min 49 s              | 5 min 33 s                    |

### 总结：

通过仿照数据库存储的简易模式来管理从文件载入到内存的这些数据，并和数据库进行相同增删改查操作后发现，正是因为我们在 memory 类中添加了这些对象之间的关系，以及各对象自身的一些约束条件，才使得最后的结果甚至会比数据库好。也间接证明了数据库管理上，对各表之间的关系，索引以及表内，表间约束是数据库管理及优化的一个方法。



## 附录
### 代码架构
```
│  README.md
│  Pipfile                # Pipfile 虚拟环境配置与管理
│  Pipfile.lock
│  main.py
│  commands.py            # 与需求对应的命令，包括 Task.ii、Task.iii
│  utils.py               # 处理数据时使用到的工具
│
├─data                    # 数据文件夹
│      course_info.json
│      select_course.csv
│
├─database                # 将与数据库相关操作封装成模块
│      __init__.py
│      config.py          # 数据库配置文件，用来切换不同数据库
│      models.py          # ORM 模型
│      utils.py           # ORM 模型的增删改查操作
│
├─memory                  # 将与内存相关操作封装成模块
│      __init__.py
│      models.py          # 内存数据模型及增删改查操作（类方法）
│
└─sql
       database.sql      # 与 ORM 等价的建库 SQL 语句
       benchmark.sql     # 比较数据库与内存数据模型的基准 SQL 语句
```
