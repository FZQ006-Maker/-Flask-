from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Student, Course, Score
from sqlalchemy import func
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///grades.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# 创建数据库表
with app.app_context():
    db.create_all()

# ---------- 首页仪表盘 ----------
@app.route('/')
def index():
    student_count = Student.query.count()
    course_count = Course.query.count()
    score_count = Score.query.count()
    # 整体平均分
    avg_score = db.session.query(func.avg(Score.score)).scalar()
    avg_score = round(avg_score, 2) if avg_score else 0
    return render_template('index.html',
                           student_count=student_count,
                           course_count=course_count,
                           score_count=score_count,
                           avg_score=avg_score)

# ================== 学生管理 ==================
@app.route('/students')
def student_list():
    students = Student.query.order_by(Student.student_id).all()
    return render_template('students.html', students=students)

@app.route('/student/add', methods=['GET', 'POST'])
def student_add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        student_id = request.form.get('student_id', '').strip()
        class_name = request.form.get('class_name', '').strip()
        if not name or not student_id:
            flash('姓名和学号不能为空', 'danger')
            return redirect(url_for('student_add'))
        if Student.query.filter_by(student_id=student_id).first():
            flash('学号已存在', 'danger')
            return redirect(url_for('student_add'))
        student = Student(name=name, student_id=student_id, class_name=class_name)
        db.session.add(student)
        db.session.commit()
        flash('学生添加成功', 'success')
        return redirect(url_for('student_list'))
    return render_template('student_form.html', student=None)

@app.route('/student/edit/<int:id>', methods=['GET', 'POST'])
def student_edit(id):
    student = Student.query.get_or_404(id)
    if request.method == 'POST':
        student.name = request.form.get('name', '').strip()
        new_student_id = request.form.get('student_id', '').strip()
        student.class_name = request.form.get('class_name', '').strip()
        if not student.name or not new_student_id:
            flash('姓名和学号不能为空', 'danger')
            return redirect(url_for('student_edit', id=id))
        # 检查学号是否与其他学生重复
        exist = Student.query.filter(Student.student_id == new_student_id, Student.id != id).first()
        if exist:
            flash('学号已存在', 'danger')
            return redirect(url_for('student_edit', id=id))
        student.student_id = new_student_id
        db.session.commit()
        flash('学生信息更新成功', 'success')
        return redirect(url_for('student_list'))
    return render_template('student_form.html', student=student)

@app.route('/student/delete/<int:id>')
def student_delete(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    flash('学生已删除', 'warning')
    return redirect(url_for('student_list'))

# ================== 课程管理 ==================
@app.route('/courses')
def course_list():
    courses = Course.query.order_by(Course.course_id).all()
    return render_template('courses.html', courses=courses)

@app.route('/course/add', methods=['GET', 'POST'])
def course_add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        course_id = request.form.get('course_id', '').strip()
        credit = request.form.get('credit', 0, type=float)
        if not name or not course_id:
            flash('课程名和课程编号不能为空', 'danger')
            return redirect(url_for('course_add'))
        if Course.query.filter_by(course_id=course_id).first():
            flash('课程编号已存在', 'danger')
            return redirect(url_for('course_add'))
        course = Course(name=name, course_id=course_id, credit=credit)
        db.session.add(course)
        db.session.commit()
        flash('课程添加成功', 'success')
        return redirect(url_for('course_list'))
    return render_template('course_form.html', course=None)

@app.route('/course/edit/<int:id>', methods=['GET', 'POST'])
def course_edit(id):
    course = Course.query.get_or_404(id)
    if request.method == 'POST':
        course.name = request.form.get('name', '').strip()
        new_course_id = request.form.get('course_id', '').strip()
        course.credit = request.form.get('credit', 0, type=float)
        if not course.name or not new_course_id:
            flash('课程名和课程编号不能为空', 'danger')
            return redirect(url_for('course_edit', id=id))
        exist = Course.query.filter(Course.course_id == new_course_id, Course.id != id).first()
        if exist:
            flash('课程编号已存在', 'danger')
            return redirect(url_for('course_edit', id=id))
        course.course_id = new_course_id
        db.session.commit()
        flash('课程信息更新成功', 'success')
        return redirect(url_for('course_list'))
    return render_template('course_form.html', course=course)

@app.route('/course/delete/<int:id>')
def course_delete(id):
    course = Course.query.get_or_404(id)
    db.session.delete(course)
    db.session.commit()
    flash('课程已删除', 'warning')
    return redirect(url_for('course_list'))

# ================== 成绩管理 ==================
@app.route('/scores')
def score_list():
    # 获取筛选参数
    student_id_filter = request.args.get('student_id', '', type=int)
    course_id_filter = request.args.get('course_id', '', type=int)
    query = Score.query
    if student_id_filter:
        query = query.filter(Score.student_id == student_id_filter)
    if course_id_filter:
        query = query.filter(Score.course_id == course_id_filter)
    scores = query.order_by(Score.student_id, Score.course_id).all()

    # 传递所有学生和课程，供筛选下拉框使用
    all_students = Student.query.order_by(Student.student_id).all()
    all_courses = Course.query.order_by(Course.course_id).all()

    # 计算当前筛选条件下的统计（仅当有成绩时）
    if scores:
        avg = db.session.query(func.avg(Score.score)).filter(query.whereclause).scalar()
        max_s = db.session.query(func.max(Score.score)).filter(query.whereclause).scalar()
        min_s = db.session.query(func.min(Score.score)).filter(query.whereclause).scalar()
        stats = {
            'avg': round(avg, 2) if avg else 0,
            'max': max_s if max_s else 0,
            'min': min_s if min_s else 0
        }
    else:
        stats = None

    return render_template('scores.html', scores=scores,
                           all_students=all_students, all_courses=all_courses,
                           student_id_filter=student_id_filter,
                           course_id_filter=course_id_filter,
                           stats=stats)

@app.route('/score/add', methods=['GET', 'POST'])
def score_add():
    students = Student.query.order_by(Student.student_id).all()
    courses = Course.query.order_by(Course.course_id).all()
    if request.method == 'POST':
        student_id = request.form.get('student_id', type=int)
        course_id = request.form.get('course_id', type=int)
        score = request.form.get('score', type=float)
        if not student_id or not course_id or score is None:
            flash('请完整填写信息', 'danger')
            return redirect(url_for('score_add'))
        if score < 0 or score > 100:
            flash('分数应在0-100之间', 'danger')
            return redirect(url_for('score_add'))
        # 检查唯一性
        exist = Score.query.filter_by(student_id=student_id, course_id=course_id).first()
        if exist:
            flash('该学生此课程成绩已存在，请编辑或删除', 'danger')
            return redirect(url_for('score_add'))
        new_score = Score(student_id=student_id, course_id=course_id, score=score)
        db.session.add(new_score)
        db.session.commit()
        flash('成绩添加成功', 'success')
        return redirect(url_for('score_list'))
    return render_template('score_form.html', score=None, students=students, courses=courses)

@app.route('/score/edit/<int:id>', methods=['GET', 'POST'])
def score_edit(id):
    score = Score.query.get_or_404(id)
    students = Student.query.order_by(Student.student_id).all()
    courses = Course.query.order_by(Course.course_id).all()
    if request.method == 'POST':
        score.student_id = request.form.get('student_id', type=int)
        score.course_id = request.form.get('course_id', type=int)
        new_score_val = request.form.get('score', type=float)
        if not score.student_id or not score.course_id or new_score_val is None:
            flash('请完整填写信息', 'danger')
            return redirect(url_for('score_edit', id=id))
        if new_score_val < 0 or new_score_val > 100:
            flash('分数应在0-100之间', 'danger')
            return redirect(url_for('score_edit', id=id))
        # 检查唯一性（排除自身）
        exist = Score.query.filter(
            Score.student_id == score.student_id,
            Score.course_id == score.course_id,
            Score.id != id
        ).first()
        if exist:
            flash('该学生此课程成绩已存在', 'danger')
            return redirect(url_for('score_edit', id=id))
        score.score = new_score_val
        db.session.commit()
        flash('成绩更新成功', 'success')
        return redirect(url_for('score_list'))
    return render_template('score_form.html', score=score, students=students, courses=courses)

@app.route('/score/delete/<int:id>')
def score_delete(id):
    score = Score.query.get_or_404(id)
    db.session.delete(score)
    db.session.commit()
    flash('成绩已删除', 'warning')
    return redirect(url_for('score_list'))

if __name__ == '__main__':
    app.run(debug=True)
