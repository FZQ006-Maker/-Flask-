from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), nullable=False)
    student_id = db.Column(db.String(20), unique=True, nullable=False)  # 学号
    class_name = db.Column(db.String(64))  # 班级
    scores = db.relationship('Score', backref='student', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Student {self.student_id} {self.name}>'

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), nullable=False)
    course_id = db.Column(db.String(20), unique=True, nullable=False)  # 课程编号
    credit = db.Column(db.Float, default=0)  # 学分
    scores = db.relationship('Score', backref='course', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Course {self.course_id} {self.name}>'

class Score(db.Model):
    __tablename__ = 'scores'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)  # 分数 0-100
    # 联合唯一约束：同一学生同一课程只能有一条成绩
    __table_args__ = (db.UniqueConstraint('student_id', 'course_id', name='_student_course_uc'),)

    def __repr__(self):
        return f'<Score Student:{self.student_id} Course:{self.course_id} Score:{self.score}>'