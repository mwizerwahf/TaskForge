from flask import Blueprint, render_template, make_response, request
from flask_login import login_required, current_user
from app.models.task import Task, TaskComment, ActivityLog
from app.models.user import User
from datetime import datetime, date
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
import io

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
@login_required
def index():
    users = User.query.order_by(User.name).all()
    today = date.today().isoformat()
    return render_template('reports/index.html', users=users, today=today)

@reports_bp.route('/reports/daily-pdf')
@login_required
def daily_pdf():
    today = date.today()
    report_date_str = request.args.get('date', today.isoformat())
    try:
        report_date = date.fromisoformat(report_date_str)
    except Exception:
        report_date = today

    if current_user.role == 'developer':
        tasks = Task.query.filter_by(assignee_id=current_user.id).all()
        report_user = current_user
    elif current_user.is_manager:
        uid = request.args.get('user_id')
        if uid:
            report_user = User.query.get_or_404(int(uid))
            tasks = Task.query.filter_by(assignee_id=report_user.id).all()
        else:
            tasks = Task.query.all()
            report_user = None
    else:
        return make_response('Permission denied', 403)

    worked_tasks = []
    for t in tasks:
        day_start = datetime.combine(report_date, datetime.min.time())
        day_end = datetime.combine(report_date, datetime.max.time())
        acts = ActivityLog.query.filter_by(task_id=t.id).filter(ActivityLog.timestamp.between(day_start, day_end)).all()
        coms = TaskComment.query.filter_by(task_id=t.id).filter(TaskComment.created_at.between(day_start, day_end)).all()
        if acts or coms or (t.updated_at and t.updated_at.date() == report_date):
            worked_tasks.append({'task': t, 'activities': acts, 'comments': coms})

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch, leftMargin=0.75*inch, rightMargin=0.75*inch)
    story = []
    story.append(Paragraph('TaskForge Daily Report', ParagraphStyle('T', fontSize=22, fontName='Helvetica-Bold', textColor=colors.HexColor('#FF6B35'), alignment=TA_CENTER, spaceAfter=6)))
    story.append(Paragraph(f'Date: {report_date.strftime("%B %d, %Y")}', ParagraphStyle('S', fontSize=11, textColor=colors.HexColor('#666666'), alignment=TA_CENTER, spaceAfter=4)))
    if report_user:
        story.append(Paragraph(f'Developer: {report_user.name}', ParagraphStyle('S2', fontSize=11, textColor=colors.HexColor('#666666'), alignment=TA_CENTER)))
    story.append(Spacer(1, 0.1*inch))
    story.append(HRFlowable(width='100%', thickness=2, color=colors.HexColor('#FF6B35')))
    story.append(Spacer(1, 0.15*inch))
    if not worked_tasks:
        story.append(Paragraph('No activity recorded for this date.', ParagraphStyle('N', fontSize=11)))
    else:
        for item in worked_tasks:
            t = item['task']
            story.append(Paragraph(f'Task: {t.title}', ParagraphStyle('TH', fontSize=13, fontName='Helvetica-Bold', textColor=colors.HexColor('#111118'), spaceAfter=4)))
            tbl = Table([['Status', t.status_label, 'Priority', t.priority.upper()], ['Assignee', t.assignee.name if t.assignee else 'Unassigned', 'Due', str(t.due_date or 'N/A')]], colWidths=[1.2*inch,2.3*inch,1.2*inch,2.3*inch])
            tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(0,-1),colors.HexColor('#f0f0f0')),('BACKGROUND',(2,0),(2,-1),colors.HexColor('#f0f0f0')),('FONTSIZE',(0,0),(-1,-1),9),('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#dddddd')),('PADDING',(0,0),(-1,-1),4)]))
            story.append(tbl)
            story.append(Spacer(1, 0.08*inch))
            if item['activities']:
                story.append(Paragraph('Activity:', ParagraphStyle('AH', fontSize=10, fontName='Helvetica-Bold')))
                for a in item['activities']:
                    story.append(Paragraph(f'  [{a.timestamp.strftime("%H:%M")}] {a.action}', ParagraphStyle('A', fontSize=9, leftIndent=12, textColor=colors.HexColor('#555'))))
            if item['comments']:
                story.append(Paragraph('Comments:', ParagraphStyle('CH', fontSize=10, fontName='Helvetica-Bold')))
                for c in item['comments']:
                    story.append(Paragraph(f'  [{c.created_at.strftime("%H:%M")}] {c.comment}', ParagraphStyle('C', fontSize=9, leftIndent=12, textColor=colors.HexColor('#555'))))
            story.append(Spacer(1, 0.1*inch))
            story.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#cccccc')))
            story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(f'Generated by TaskForge on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', ParagraphStyle('F', fontSize=8, textColor=colors.HexColor('#999'), alignment=TA_CENTER)))
    doc.build(story)
    buffer.seek(0)
    resp = make_response(buffer.read())
    resp.headers['Content-Type'] = 'application/pdf'
    resp.headers['Content-Disposition'] = f'attachment; filename=taskforge-{report_date}.pdf'
    return resp
