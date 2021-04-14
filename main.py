from commands import Task, f


Task.ii(
    path_course_info=('data', 'course_info.json'),
    locale='zh',
    encoding='utf-8',
    student_number=10_000,
    class_minmax=(0, 7),
    batch_size=1_000,
) | f.create_all | f.add_course_info | f.add_select_course

Task.iii(
    path_pickle=('memory.pickle', ),
    number=100,
    echo=False,
) | f.convert_to_file | f.benchmark

# Task.iv(
#     host='127.0.0.1',
#     port=5000,
# ) | f.create_all_ext | f.deploy
