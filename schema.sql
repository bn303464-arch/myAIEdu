CREATE TABLE IF NOT EXISTS students (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  name        TEXT NOT NULL,
  phone       TEXT NOT NULL UNIQUE,
  age_group   TEXT CHECK (age_group IN ('40s','50s')),
  occupation  TEXT,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS courses (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  title       TEXT NOT NULL,
  cohort      TEXT NOT NULL,
  start_date  TEXT,
  capacity    INTEGER NOT NULL DEFAULT 10,
  price       INTEGER NOT NULL DEFAULT 0,
  UNIQUE (title, cohort)
);

CREATE TABLE IF NOT EXISTS lessons (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  course_id   INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
  week_no     INTEGER NOT NULL CHECK (week_no BETWEEN 1 AND 8),
  topic       TEXT NOT NULL,
  goal        TEXT,
  is_core     INTEGER NOT NULL DEFAULT 0,
  UNIQUE (course_id, week_no)
);

CREATE TABLE IF NOT EXISTS enrollments (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id    INTEGER NOT NULL REFERENCES students(id),
  course_id     INTEGER NOT NULL REFERENCES courses(id),
  status        TEXT NOT NULL DEFAULT 'applied'
                CHECK (status IN ('applied','confirmed','completed','dropped')),
  willing_price INTEGER,
  satisfaction  INTEGER CHECK (satisfaction BETWEEN 1 AND 5),
  enrolled_at   TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (student_id, course_id)
);

CREATE INDEX IF NOT EXISTS idx_enroll_course ON enrollments(course_id, status);
