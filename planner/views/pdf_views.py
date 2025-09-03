from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View
from django.http import HttpResponse, Http404
from django.utils import timezone
from django.contrib import messages
from datetime import datetime, timedelta, date
import io
from collections import defaultdict

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from ..models import Task, TimeBlock
from ..forms import PdfScheduleForm


class SchedulePdfFormView(LoginRequiredMixin, TemplateView):
    """View for displaying the PDF export form."""
    template_name = 'planner/schedule_pdf_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PdfScheduleForm()
        return context
    
    def post(self, request, *args, **kwargs):
        form = PdfScheduleForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            
            # Redirect to PDF generation view with parameters
            return redirect('planner:schedule_pdf_generate', 
                          start_date=start_date.strftime('%Y-%m-%d'),
                          end_date=end_date.strftime('%Y-%m-%d'))
        
        return self.render_to_response({'form': form})


class SchedulePdfGenerateView(LoginRequiredMixin, View):
    """View for generating and serving the PDF schedule."""
    
    def get(self, request, start_date, end_date, *args, **kwargs):
        try:
            # Parse dates
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # Validate date range
            if start_date_obj > end_date_obj:
                messages.error(request, "Invalid date range.")
                return redirect('planner:schedule_pdf_form')
            
            if (end_date_obj - start_date_obj).days > 28:
                messages.error(request, "Date range cannot exceed 4 weeks.")
                return redirect('planner:schedule_pdf_form')
            
            # Generate PDF
            pdf_buffer = self._generate_schedule_pdf(request.user, start_date_obj, end_date_obj)
            
            # Create response
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            filename = f"schedule_{start_date}_{end_date}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except ValueError:
            raise Http404("Invalid date format")
        except Exception as e:
            messages.error(request, f"Error generating PDF: {str(e)}")
            return redirect('planner:schedule_pdf_form')
    
    def _generate_schedule_pdf(self, user, start_date, end_date):
        """Generate the actual PDF content."""
        buffer = io.BytesIO()
        
        # Create the PDF document
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=18)
        
        # Build the content
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2563eb')
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#64748b')
        )
        
        day_header_style = ParagraphStyle(
            'DayHeader',
            parent=styles['Heading3'],
            fontSize=14,
            spaceAfter=10,
            spaceBefore=20,
            textColor=colors.HexColor('#1e40af')
        )
        
        # Add title
        title = Paragraph(f"Task Schedule", title_style)
        story.append(title)
        
        # Add date range
        date_range = Paragraph(
            f"{start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}", 
            subtitle_style
        )
        story.append(date_range)
        story.append(Spacer(1, 20))
        
        # Get scheduled tasks for the date range
        start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
        
        scheduled_tasks = Task.objects.filter(
            user=user,
            start_time__isnull=False,
            start_time__gte=start_datetime,
            start_time__lte=end_datetime
        ).order_by('start_time')
        
        # Group tasks by date
        tasks_by_date = defaultdict(list)
        for task in scheduled_tasks:
            task_date = task.start_time.date()
            tasks_by_date[task_date].append(task)
        
        # Get unscheduled tasks
        unscheduled_tasks = Task.objects.filter(
            user=user,
            start_time__isnull=True,
            status__in=['todo', 'in_progress'],
            deadline__gte=start_datetime,
            deadline__lte=end_datetime
        ).order_by('deadline', 'priority')
        
        # Generate calendar for each day
        current_date = start_date
        while current_date <= end_date:
            # Add day header
            day_header = Paragraph(
                f"{current_date.strftime('%A, %B %d, %Y')}", 
                day_header_style
            )
            story.append(day_header)
            
            # Get tasks for this day
            day_tasks = tasks_by_date.get(current_date, [])
            
            if day_tasks:
                # Create table for scheduled tasks
                table_data = [['Time', 'Task', 'Duration', 'Priority']]
                
                for task in day_tasks:
                    start_time = timezone.localtime(task.start_time)
                    end_time = timezone.localtime(task.end_time) if task.end_time else None
                    
                    time_str = start_time.strftime('%I:%M %p')
                    if end_time:
                        time_str += f" - {end_time.strftime('%I:%M %p')}"
                    
                    duration_str = f"{task.estimated_hours:.1f}h" if task.estimated_hours else "N/A"
                    priority_str = task.get_priority_display()
                    
                    table_data.append([
                        time_str,
                        task.title[:40] + ('...' if len(task.title) > 40 else ''),
                        duration_str,
                        priority_str
                    ])
                
                # Style the table
                table = Table(table_data, colWidths=[1.5*inch, 3*inch, 1*inch, 1*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#374151')),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                
                # Add priority-based row coloring
                for i, task in enumerate(day_tasks, 1):
                    if task.priority == 4:  # Urgent
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#fee2e2'))
                        ]))
                    elif task.priority == 3:  # High
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#fef3c7'))
                        ]))
                
                story.append(table)
            else:
                # No scheduled tasks for this day
                no_tasks_para = Paragraph(
                    "No scheduled tasks for this day", 
                    styles['Normal']
                )
                story.append(no_tasks_para)
            
            story.append(Spacer(1, 15))
            current_date += timedelta(days=1)
        
        # Add unscheduled tasks section if any exist
        if unscheduled_tasks:
            story.append(PageBreak())
            
            unscheduled_header = Paragraph("Unscheduled Tasks", title_style)
            story.append(unscheduled_header)
            story.append(Spacer(1, 20))
            
            # Create table for unscheduled tasks
            table_data = [['Task', 'Deadline', 'Estimated Hours', 'Priority']]
            
            for task in unscheduled_tasks:
                deadline_str = task.deadline.strftime('%m/%d/%Y %I:%M %p') if task.deadline else "No deadline"
                duration_str = f"{task.estimated_hours:.1f}h" if task.estimated_hours else "N/A"
                priority_str = task.get_priority_display()
                
                table_data.append([
                    task.title[:50] + ('...' if len(task.title) > 50 else ''),
                    deadline_str,
                    duration_str,
                    priority_str
                ])
            
            unscheduled_table = Table(table_data, colWidths=[3*inch, 2*inch, 1*inch, 1*inch])
            unscheduled_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#374151')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            # Add priority-based row coloring for unscheduled tasks
            for i, task in enumerate(unscheduled_tasks, 1):
                if task.priority == 4:  # Urgent
                    unscheduled_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#fee2e2'))
                    ]))
                elif task.priority == 3:  # High
                    unscheduled_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#fef3c7'))
                    ]))
            
            story.append(unscheduled_table)
        
        # Add footer with generation info
        story.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#6b7280')
        )
        footer = Paragraph(
            f"Generated on {timezone.now().strftime('%B %d, %Y at %I:%M %p')}", 
            footer_style
        )
        story.append(footer)
        
        # Build the PDF
        doc.build(story)
        
        buffer.seek(0)
        return buffer