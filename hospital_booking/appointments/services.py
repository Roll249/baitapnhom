"""
PDF generation services for medical records and booking confirmations
"""
from io import BytesIO
from django.conf import settings

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.platypus import PageBreak
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


def generate_medical_record_pdf(medical_record):
    """
    Generate PDF for medical record including prescriptions
    """
    if not HAS_REPORTLAB:
        return None
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=1,  # Center
        spaceAfter=20,
        textColor=colors.HexColor('#667eea')
    )
    story.append(Paragraph("PHIEU KHAM BENH", title_style))
    story.append(Spacer(1, 20))
    
    # Hospital info
    story.append(Paragraph("Benh Vien HealthCare", styles['Heading2']))
    story.append(Paragraph("Dia chi: So 123, Yen Hoa, Cau Giay, Ha Noi", styles['Normal']))
    story.append(Paragraph("Hotline: 1900 1234", styles['Normal']))
    story.append(Spacer(1, 30))
    
    # Appointment info
    appointment = medical_record.appointment
    patient = appointment.patient
    
    info_data = [
        ['Ngay kham:', str(appointment.appointment_date)],
        ['Gio kham:', str(appointment.appointment_time)],
        ['Bac si:', str(appointment.doctor)],
        ['Chuyen khoa:', appointment.doctor.specialization.name if appointment.doctor.specialization else ''],
    ]
    
    info_table = Table(info_data, colWidths=[4*cm, 10*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 20))
    
    # Patient info
    story.append(Paragraph("THONG TIN BENH NHAN", styles['Heading3']))
    patient_data = [
        ['Ho ten:', str(patient)],
        ['Ngay sinh:', str(patient.date_of_birth or 'Khong co')],
        ['Gioi tinh:', patient.get_gender_display() if patient.gender else 'Khong co'],
    ]
    patient_table = Table(patient_data, colWidths=[4*cm, 10*cm])
    patient_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 20))
    
    # Diagnosis
    story.append(Paragraph("CHAN DOAN", styles['Heading3']))
    story.append(Paragraph(medical_record.diagnosis, styles['Normal']))
    story.append(Spacer(1, 15))
    
    if medical_record.notes:
        story.append(Paragraph("GHI CHU", styles['Heading3']))
        story.append(Paragraph(medical_record.notes, styles['Normal']))
        story.append(Spacer(1, 15))
    
    if medical_record.treatment_plan:
        story.append(Paragraph("KE HOACH DIEU TRI", styles['Heading3']))
        story.append(Paragraph(medical_record.treatment_plan, styles['Normal']))
        story.append(Spacer(1, 15))
    
    # Prescriptions
    if medical_record.prescriptions.exists():
        story.append(PageBreak())
        story.append(Paragraph("DON THUOC", styles['Heading2']))
        story.append(Spacer(1, 10))
        
        prescription_data = [
            ['STT', 'Ten thuoc', 'Lieu luong', 'Tan suat', 'Thoi gian']
        ]
        
        for i, rx in enumerate(medical_record.prescriptions.all(), 1):
            prescription_data.append([
                str(i),
                rx.medicine_name,
                rx.dosage,
                rx.frequency,
                rx.duration
            ])
        
        rx_table = Table(prescription_data, colWidths=[1.5*cm, 4.5*cm, 3*cm, 3*cm, 3*cm])
        rx_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(rx_table)
        
        # Instructions
        story.append(Spacer(1, 20))
        story.append(Paragraph("<b>Huong dan su dung:</b>", styles['Normal']))
        for rx in medical_record.prescriptions.all():
            if rx.instructions:
                story.append(Paragraph(f"- {rx.medicine_name}: {rx.instructions}", styles['Normal']))
    
    # Follow-up
    if medical_record.follow_up_date:
        story.append(Spacer(1, 30))
        story.append(Paragraph("LICH TAI KHAM", styles['Heading3']))
        story.append(Paragraph(
            f"Ngay tai kham: {medical_record.follow_up_date}",
            styles['Normal']
        ))
        if medical_record.follow_up_reason:
            story.append(Paragraph(
                f"Ly do: {medical_record.follow_up_reason}",
                styles['Normal']
            ))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_booking_confirmation_pdf(confirmation):
    """
    Generate PDF for booking confirmation with QR code
    """
    if not HAS_REPORTLAB:
        return None
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    appointment = confirmation.appointment
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        alignment=1,
        spaceAfter=10,
        textColor=colors.HexColor('#667eea')
    )
    story.append(Paragraph("PHIEU KHAM DIEN TU", title_style))
    story.append(Spacer(1, 10))
    
    # Confirmation code
    code_style = ParagraphStyle(
        'Code',
        parent=styles['Heading2'],
        fontSize=24,
        alignment=1,
        textColor=colors.HexColor('#764ba2')
    )
    story.append(Paragraph(f"Ma xac nhan: {confirmation.confirmation_code}", code_style))
    story.append(Spacer(1, 30))
    
    # Appointment details
    info_data = [
        ['Ngay kham:', str(appointment.appointment_date)],
        ['Gio kham:', str(appointment.appointment_time)],
        ['Bac si:', str(appointment.doctor)],
        ['Chuyen khoa:', appointment.doctor.specialization.name if appointment.doctor.specialization else ''],
        ['Phi kham:', f"{appointment.doctor.consultation_fee:,.0f} VND"],
    ]
    
    info_table = Table(info_data, colWidths=[4*cm, 10*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 20))
    
    # Patient info
    patient = appointment.patient
    story.append(Paragraph("THONG TIN BENH NHAN", styles['Heading3']))
    patient_data = [
        ['Ho ten:', str(patient)],
        ['Dien thoai:', patient.user.phone or 'Khong co'],
        ['Email:', patient.user.email or 'Khong co'],
    ]
    patient_table = Table(patient_data, colWidths=[4*cm, 10*cm])
    patient_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(patient_table)
    
    # Clinic info
    if appointment.doctor.clinic_name:
        story.append(Spacer(1, 20))
        story.append(Paragraph("DIA DIEM KHAM", styles['Heading3']))
        clinic_data = [
            ['Phong kham:', appointment.doctor.clinic_name],
        ]
        if appointment.doctor.clinic_address:
            clinic_data.append(['Dia chi:', appointment.doctor.clinic_address])
        if appointment.doctor.clinic_phone:
            clinic_data.append(['Hotline:', appointment.doctor.clinic_phone])
        
        clinic_table = Table(clinic_data, colWidths=[4*cm, 10*cm])
        clinic_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(clinic_table)
    
    # Notes
    story.append(Spacer(1, 30))
    story.append(Paragraph("<b>Luu y:</b>", styles['Normal']))
    story.append(Paragraph("- Vui long den truoc 15 phut de lam thu tuc", styles['Normal']))
    story.append(Paragraph("- Mang theo CMND/CCCD va BHYT (neu co)", styles['Normal']))
    story.append(Paragraph("- Quet ma QR hoac doc ma xac nhan tai quay le tan", styles['Normal']))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer
