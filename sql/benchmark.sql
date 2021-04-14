-- 使用 '\timing on' 或者 'explain analyze' 记录运行时间


-- 增
insert into People (id, uid, name, is_female, department_id) values
    (10797, 12000001, '张三', true, 7), (10798, 12000002, '李四', false, 7);
insert into Semester (id, year, season) values (2, 2021, 2);
insert into Class (id, capacity, course_id, semester_id, name, list) values
    (597, 35, 91, 2, '中英双语1班-实验1班', '');
insert into "ClassPeople" (class_id, people_id, role) values
    (597, 10797, 'S'), (597, 10798, 'S');


-- 改
update Class as c
set list = '[{"weekList": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"], "location": "荔园6栋404机房", "classTime": "9-10", "weekday": 2}, {"weekList": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"], "location": "荔园1栋102", "classTime": "7-8", "weekday": 2}]'
where c.id = 597;


-- 删
delete from "ClassPeople" as cp where cp.people_id in (10797, 10798);
delete from Class as c where c.id = 597;
delete from Semester as s where s.id = 2;
delete from People as p where p.id in (10797, 10798);


-- 查
with ClassStudent as (
    select cp.class_id, cp.people_id
    from "ClassPeople" as cp
    where cp.role = 'S'
)
select
    ds.name || ' 学号为 ' || p.uid || ' 的 ' || p.name ||
    ' 在 ' || s.year || ' 学年第 ' || s.season || ' 学期' ||
    '修读了由 ' || dc.name || ' 开设的课程代码为 ' || co.code || ' 的 ' || co.name || '，' ||
    case p.is_female when true then '她' else '他' end || '所在的班级为 ' || cl.name || '。'
from ClassStudent as cs
    inner join Class as cl on cl.id = cs.class_id
        inner join Course as co on co.id = cl.course_id
            inner join Department as dc on dc.id = co.department_id
        inner join Semester as s on s.id = cl.semester_id
    inner join People as p on p.id = cs.people_id
        inner join Department as ds on ds.id = p.department_id;

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
