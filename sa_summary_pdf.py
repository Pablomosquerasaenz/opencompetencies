from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch

# May only need these when being run manually, which I'm doing for development.
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'opencompetencies.settings'

import django
django.setup()

from competencies.models import SubjectArea


class PDFTest():
    def __init__(self):
        self.PAGE_HEIGHT = defaultPageSize[1]
        self.PAGE_WIDTH = defaultPageSize[0]
        self.styles = getSampleStyleSheet()

        self.title = ''
        self.subtitle = ''

    def myFirstPage(self, canvas, doc):
        canvas.saveState()

        canvas.setFont('Times-Bold',16)
        canvas.drawString(inch, self.PAGE_HEIGHT-inch, self.Title)
        canvas.setFont('Times-Bold',14)
        canvas.drawString(inch, self.PAGE_HEIGHT-1.25*inch, self.subtitle+'blah')

        canvas.restoreState()

    def myLaterPages(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Times-Roman', 9)
        canvas.restoreState()

    def makeSummary(self, sa_id):
        """Generates a pdf of the sa_summary page."""
        print('building doc...')

        # Get data for this sa.
        sa = SubjectArea.objects.get(id=sa_id)
        org = sa.organization
        sdas = sa.subdisciplinearea_set.all()

        # Prep document.
        self.Title = org.name
        self.subtitle = sa.subject_area

        doc = SimpleDocTemplate("sa_summary.pdf")
        Story = [Spacer(1,0.5*inch)]
        style = self.styles["Normal"]

        self.first_col_x = inch
        self.second_col_x = self.PAGE_WIDTH / 3
        
        # Add competency areas and essential understandings.
        for sda in sa.subdisciplinearea_set.all():
            p = Paragraph(sda.subdiscipline_area, style)
            Story.append(p)
            Story.append(Spacer(1, 0.2*inch))

        doc.build(Story, onFirstPage=self.myFirstPage, onLaterPages=self.myLaterPages)


pdftest = PDFTest()
pdftest.makeSummary(24)
