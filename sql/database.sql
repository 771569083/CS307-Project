-- -----------------------------------------------------
-- Table Department
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Department (
  id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  name CHAR(64),  -- 考虑学生没有选专业
  UNIQUE (name)
);


-- -----------------------------------------------------
-- Table Course
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Course (
  id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  code CHAR(16) NOT NULL,
  prerequisite TEXT NOT NULL,
  hour INTEGER NOT NULL,
  credit INTEGER NOT NULL,
  name CHAR(64) NOT NULL,
  department_id INTEGER NOT NULL,
  UNIQUE (code),
  CONSTRAINT fk_Course_Department
    FOREIGN KEY (department_id)
    REFERENCES Department (id)
);


-- -----------------------------------------------------
-- Table People
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS People (
  id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  uid INTEGER NOT NULL,
  name CHAR(64) NOT NULL,
  is_female BOOLEAN NOT NULL,
  department_id INTEGER NOT NULL,
  UNIQUE (uid),
  CONSTRAINT fk_People_Department
    FOREIGN KEY (department_id)
    REFERENCES Department (id)
);


-- -----------------------------------------------------
-- Table Class
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Class (
  id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  capacity INTEGER NOT NULL,
  semester_id INTEGER NOT NULL,
  name CHAR(64) NOT NULL,
  list TEXT NOT NULL,
  course_id INTEGER NOT NULL,
  UNIQUE (course_id, semester_id, name),
  CONSTRAINT fk_Class_Course
    FOREIGN KEY (course_id)
    REFERENCES Course (id),
  CONSTRAINT fk_Class_Semester
    FOREIGN KEY (semester_id)
    REFERENCES Semester (id)
);


-- -----------------------------------------------------
-- Table Semester
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Semester (
  id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  year INTEGER NOT NULL,
  season INTEGER NOT NULL,  -- 1: 春, 2: 夏, 3: 秋, 4: 冬
  UNIQUE(year, season)
);


-- -----------------------------------------------------
-- Table ClassPeople
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS ClassPeople (
  class_id INTEGER NOT NULL,
  people_id INTEGER NOT NULL,
  role CHAR(1) NOT NULL,  -- T: 老师, U: 本科生
  PRIMARY KEY (class_id, people_id),
  CONSTRAINT fk_ClassPeople_Class
    FOREIGN KEY (class_id)
    REFERENCES Class (id),
  CONSTRAINT fk_ClassPeople_People
    FOREIGN KEY (people_id)
    REFERENCES People (id)
);


-- -----------------------------------------------------
-- TODO: Table Grade / CoursePeople
-- -----------------------------------------------------
-- pass


-- -----------------------------------------------------
-- Index
-- -----------------------------------------------------
CREATE INDEX index_ClassPeople_class_role
ON "ClassPeople" (class_id, role);
