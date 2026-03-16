from flask import Blueprint, render_template, make_response, request
from flask_login import login_required, current_user
from app.models.task import Task, TaskComment, ActivityLog
from app.models.user import User
from datetime import datetime, date
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.units import mm
import io

reports_bp = Blueprint('reports', __name__)

# ── Colour palette ─────────────────────────────────────────────────────────
ORANGE  = colors.HexColor('#FF6B35')
INK     = colors.HexColor('#0D0D14')
DARK    = colors.HexColor('#1E1E2E')
GREY    = colors.HexColor('#6B7280')
LIGHT   = colors.HexColor('#9CA3AF')
RULE    = colors.HexColor('#E5E7EB')
ROW_ALT = colors.HexColor('#FAFAFA')
HDR_BG  = colors.HexColor('#F4F4F6')
WHITE   = colors.white

STATUS_COLOR = {
    'not_started': colors.HexColor('#6B7280'),
    'in_progress': colors.HexColor('#2563EB'),
    'blocked':     colors.HexColor('#DC2626'),
    'completed':   colors.HexColor('#059669'),
}
STATUS_LABEL = {
    'not_started': 'Not Started',
    'in_progress': 'In Progress',
    'blocked':     'Blocked',
    'completed':   'Completed',
}
PRIORITY_COLOR = {
    'low':      colors.HexColor('#059669'),
    'medium':   colors.HexColor('#D97706'),
    'high':     colors.HexColor('#EA580C'),
    'critical': colors.HexColor('#DC2626'),
}

def ps(name, **kw):
    defaults = dict(fontName='Helvetica', fontSize=9, leading=13, textColor=INK)
    defaults.update(kw)
    return ParagraphStyle(name, **defaults)

def hex_of(c):
    return '#%02x%02x%02x' % (int(c.red * 255), int(c.green * 255), int(c.blue * 255))


# ── Page canvas (header + footer drawn on every page) ─────────────────────
def draw_page(canvas, doc, meta):
    W, H = A4
    L = 18 * mm
    R = W - 18 * mm

    canvas.saveState()

    # ── Accent bar (top) ────────────────────────────────────────────────────
    canvas.setFillColor(ORANGE)
    canvas.rect(0, H - 6 * mm, W, 6 * mm, fill=1, stroke=0)

    # ── Left accent stripe ──────────────────────────────────────────────────
    canvas.setFillColor(ORANGE)
    canvas.rect(0, 0, 3 * mm, H, fill=1, stroke=0)

    # ── Header content — positioned safely below the orange bar ─────────────
    # "TaskForge" wordmark
    canvas.setFont('Helvetica-Bold', 16)
    canvas.setFillColor(INK)
    canvas.drawString(L, H - 15 * mm, 'TaskForge')

    # Sub-label next to wordmark
    # canvas.setFont('Helvetica', 9)
    # canvas.setFillColor(GREY)
    # canvas.drawString(L + 62, H - 14.5 * mm, 'Daily Activity Report')

    # Report date — below wordmark
    canvas.setFont('Helvetica-Bold', 10)
    canvas.setFillColor(INK)
    canvas.drawString(L, H - 22 * mm, meta['date_str'])

    # Developer name — right-aligned, same row as wordmark
    canvas.setFont('Helvetica-Bold', 10)
    canvas.setFillColor(INK)
    canvas.drawRightString(R, H - 15 * mm, meta['who'])

    # Task count line — below developer name
    n = meta['task_count']
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(LIGHT)
    canvas.drawRightString(R, H - 22 * mm, f"{n} task{'s' if n != 1 else ''} with activity")

    # Divider line
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.8)
    canvas.line(L, H - 27 * mm, R, H - 27 * mm)

    # ── Footer ──────────────────────────────────────────────────────────────
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(L, 14 * mm, R, 14 * mm)

    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(LIGHT)
    canvas.drawString(L, 10 * mm, 'Confidential — TaskForge Internal Report')
    canvas.drawRightString(R, 10 * mm,
        f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}   ·   Page {doc.page}")

    canvas.restoreState()


# ── Routes ─────────────────────────────────────────────────────────────────
@reports_bp.route('/reports')
@login_required
def index():
    users = User.query.order_by(User.name).all()
    return render_template('reports/index.html',
                           users=users, today=date.today().isoformat())


@reports_bp.route('/reports/daily-pdf')
@login_required
def daily_pdf():
    # Date
    try:
        report_date = date.fromisoformat(
            request.args.get('date', date.today().isoformat()))
    except Exception:
        report_date = date.today()

    # Scope
    if current_user.role == 'developer':
        tasks = Task.query.filter_by(assignee_id=current_user.id).all()
        report_user = current_user
    elif current_user.is_manager:
        uid = request.args.get('user_id')
        if uid:
            report_user = User.query.get_or_404(int(uid))
            tasks = Task.query.filter_by(assignee_id=report_user.id).all()
        else:
            tasks = Task.query.order_by(Task.priority.desc()).all()
            report_user = None
    else:
        return make_response('Permission denied', 403)

    # Collect tasks active on report_date
    day_s = datetime.combine(report_date, datetime.min.time())
    day_e = datetime.combine(report_date, datetime.max.time())
    rows = []
    for t in tasks:
        acts = (ActivityLog.query.filter_by(task_id=t.id)
                .filter(ActivityLog.timestamp.between(day_s, day_e))
                .order_by(ActivityLog.timestamp).all())
        coms = (TaskComment.query.filter_by(task_id=t.id)
                .filter(TaskComment.created_at.between(day_s, day_e))
                .order_by(TaskComment.created_at).all())
        if acts or coms or (t.updated_at and t.updated_at.date() == report_date):
            rows.append({'task': t, 'acts': acts, 'coms': coms})

    # PDF document
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=32 * mm,   # clears header area cleanly
        bottomMargin=22 * mm,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
    )
    TW = A4[0] - 36 * mm   # usable text width
    meta = {
        'date_str':   report_date.strftime('%A, %B %d, %Y'),
        'who':        report_user.name if report_user else 'All Developers',
        'task_count': len(rows),
    }
    on_page = lambda c, d: draw_page(c, d, meta)

    story = []

    # ── Empty state ─────────────────────────────────────────────────────────
    if not rows:
        story.append(Spacer(1, 20))
        story.append(Paragraph(
            'No activity was recorded on this date.',
            ps('empty', fontSize=11, textColor=GREY, alignment=TA_CENTER, leading=20)
        ))
        doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
        buf.seek(0)
        resp = make_response(buf.read())
        resp.headers['Content-Type'] = 'application/pdf'
        resp.headers['Content-Disposition'] = f'inline; filename=taskforge-{report_date}.pdf'
        return resp

    # ── Summary pills row ────────────────────────────────────────────────────
    counts = {}
    for r in rows:
        counts[r['task'].status] = counts.get(r['task'].status, 0) + 1

    pills = []
    for s, lbl in STATUS_LABEL.items():
        n = counts.get(s, 0)
        if n == 0:
            continue
        c_hex = hex_of(STATUS_COLOR[s])
        pills.append(f'<font color="{c_hex}"><b>{n} {lbl}</b></font>')

    story.append(Paragraph(
        '    ·    '.join(pills),
        ps('pills', fontSize=8.5, textColor=GREY,
           backColor=colors.HexColor('#FFF8F5'),
           borderPadding=(7, 12, 7, 12), spaceAfter=14,
           borderColor=colors.HexColor('#FFD5C5'), borderWidth=0.6,
           borderRadius=3)
    ))

    # ── One table for all tasks ──────────────────────────────────────────────
    # Column widths: Task+Assignee | Status | Priority | Due | Activity & Notes
    C = [66*mm, 23*mm, 20*mm, 24*mm, TW - 66*mm - 23*mm - 20*mm - 24*mm]

    # Styles
    TH  = ps('th',  fontName='Helvetica-Bold', fontSize=7.5, textColor=GREY,    leading=11)
    TN  = ps('tn',  fontName='Helvetica-Bold', fontSize=9,   textColor=INK,     leading=13)
    SUB = ps('sub', fontSize=7.5,              textColor=LIGHT, leading=11)
    AC  = ps('ac',  fontSize=8,                textColor=colors.HexColor('#374151'), leading=12)
    CM  = ps('cm',  fontSize=8,                textColor=GREY,  leading=12)
    NO  = ps('no',  fontSize=8,                textColor=LIGHT, leading=11)

    data = [[
        Paragraph('TASK / ASSIGNEE', TH),
        Paragraph('STATUS',          TH),
        Paragraph('PRIORITY',        TH),
        Paragraph('DUE DATE',        TH),
        Paragraph('ACTIVITY & NOTES',TH),
    ]]

    for item in rows:
        t = item['task']

        # ── Task cell ────────────────────────────────────────────────────
        assignee = t.assignee.name if t.assignee else 'Unassigned'
        task_cell = [Paragraph(t.title, TN), Paragraph(assignee, SUB)]

        # ── Status cell ──────────────────────────────────────────────────
        sc_hex = hex_of(STATUS_COLOR.get(t.status, colors.HexColor('#6B7280')))
        status_cell = Paragraph(
            f'<font color="{sc_hex}"><b>{STATUS_LABEL.get(t.status, t.status)}</b></font>',
            ps('s', fontSize=8, leading=11))

        # ── Priority cell ────────────────────────────────────────────────
        pc_hex = hex_of(PRIORITY_COLOR.get(t.priority, colors.HexColor('#6B7280')))
        priority_cell = Paragraph(
            f'<font color="{pc_hex}"><b>{t.priority.upper()}</b></font>',
            ps('p', fontSize=8, leading=11))

        # ── Due date cell ────────────────────────────────────────────────
        if t.due_date:
            overdue = t.is_overdue
            dc = '#DC2626' if overdue else '#374151'
            suffix = ' ⚠' if overdue else ''
            due_cell = Paragraph(
                f'<font color="{dc}">{t.due_date.strftime("%b %d, %Y")}{suffix}</font>',
                ps('d', fontSize=8, leading=11))
        else:
            due_cell = Paragraph('<font color="#9CA3AF">—</font>', ps('d', fontSize=8, leading=11))

        # ── Activity & notes cell ─────────────────────────────────────────
        events = []
        for a in item['acts']:
            ts = a.timestamp.strftime('%H:%M')
            events.append(Paragraph(
                f'<font color="#FF6B35">▸</font> '
                f'<font color="#9CA3AF">{ts}</font>  {a.action}', AC))
        for c in item['coms']:
            ts = c.created_at.strftime('%H:%M')
            note = c.comment[:100] + ('…' if len(c.comment) > 100 else '')
            events.append(Paragraph(
                f'<font color="#3B82F6">▸</font> '
                f'<font color="#9CA3AF">{ts}</font>  <i>"{note}"</i>', CM))
        if not events:
            events = [Paragraph('<font color="#9CA3AF">No log entries</font>', NO)]

        data.append([task_cell, status_cell, priority_cell, due_cell, events])

    tbl = Table(data, colWidths=C, repeatRows=1)
    tbl.setStyle(TableStyle([
        # ── Header ───────────────────────────────────────────────────────
        ('BACKGROUND',    (0, 0), (-1, 0),  HDR_BG),
        ('LINEBELOW',     (0, 0), (-1, 0),  1.5,  ORANGE),
        ('TOPPADDING',    (0, 0), (-1, 0),  7),
        ('BOTTOMPADDING', (0, 0), (-1, 0),  7),
        ('LEFTPADDING',   (0, 0), (-1, 0),  8),
        ('RIGHTPADDING',  (0, 0), (-1, 0),  6),
        # ── Data rows ────────────────────────────────────────────────────
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [WHITE, ROW_ALT]),
        ('TOPPADDING',    (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 9),
        ('LEFTPADDING',   (0, 1), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 1), (-1, -1), 6),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW',     (0, 1), (-1, -1), 0.4, RULE),
        # ── Column separators ─────────────────────────────────────────────
        ('LINEBEFORE',    (1, 0), (-1, -1), 0.4, RULE),
        # ── Outer border ─────────────────────────────────────────────────
        ('BOX',           (0, 0), (-1, -1), 0.8, RULE),
    ]))

    story.append(tbl)
    story.append(Spacer(1, 14))

    # ── Footer sign-off line ─────────────────────────────────────────────────
    story.append(HRFlowable(width=TW, thickness=0.6, color=RULE, spaceAfter=5))
    story.append(Paragraph(
        f'End of report  ·  {len(rows)} task{"s" if len(rows) != 1 else ""}  ·  {meta["date_str"]}',
        ps('eof', fontSize=7.5, textColor=LIGHT, alignment=TA_CENTER)
    ))

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    buf.seek(0)

    resp = make_response(buf.read())
    resp.headers['Content-Type'] = 'application/pdf'
    resp.headers['Content-Disposition'] = f'inline; filename=taskforge-{report_date}.pdf'
    return resp
