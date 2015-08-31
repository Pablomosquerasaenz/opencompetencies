from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib import colors

from competencies.models import SubjectArea

class PDFTest():
    def __init__(self, response):
        # response argument is used as the file object.
        self.response = response
        self.styles = getSampleStyleSheet()

        self.title = ''
        self.subtitle = ''

    def makeSummary(self, org, sa, sdas, cas, eus):
        """Generates a pdf of the sa_summary page."""
        print('building doc...')

        # Prep document.
        self.Title = org.name
        self.subtitle = sa.subject_area

        doc = SimpleDocTemplate(self.response, pagesize=landscape(letter))
        Story = [Spacer(1,0.5*inch)]
        style = self.styles["Normal"]
        light_gray = (0.9, 0.9, 0.9)
        dark_gray = (0.75, 0.75, 0.75)
        elements = []

        ca_col_width, eu_col_width = 3*inch, 6*inch
        col_widths = (ca_col_width, eu_col_width)
        
        # Build a series of separate tables.
        #  Easy to manage styling this way.

        # Header row.
        data = [(org.alias_ca.title(), org.alias_eu.title())]
        table = Table(data, colWidths=col_widths)
        elements.append(table)
        table.setStyle(TableStyle([('BACKGROUND', (0,0), (0,0), dark_gray),
                                   ('BACKGROUND', (1,0), (1,0), light_gray),
                                   ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                                   ]))

        data = []

        # Subject area competency areas.
        for ca in cas:
            if not ca.subdiscipline_area:
                p = Paragraph(ca.competency_area, style)
                data.append((p, ''))
                for eu in eus:
                    if eu.competency_area == ca:
                        p = Paragraph(eu.essential_understanding, style)
                        data.append(('', p))

        # Add sda competency areas.
        for sda in sdas:
            p = Paragraph(sda.subdiscipline_area, style)
            data.append((p, ''))
            for ca in cas:
                if (ca.subdiscipline_area
                    and ca.subdiscipline_area.subdiscipline_area == sda.subdiscipline_area):
                    p = Paragraph(ca.competency_area, style)
                    data.append((p, ''))
                    for eu in eus:
                        if eu.competency_area == ca:
                            p = Paragraph(eu.essential_understanding, style)
                            data.append(('', p))

        table = Table(data, colWidths=(3*inch, 6*inch))
        elements.append(table)
        table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), light_gray),]))

        doc.build(elements)

        return self.response
        # # Add competency areas and essential understandings.
        # for sda in sa.subdisciplinearea_set.all():
        #     p = Paragraph(sda.subdiscipline_area, style)
        #     Story.append(p)
        #     Story.append(Spacer(1, 0.2*inch))

        #doc.build(Story, onFirstPage=self.myFirstPage, onLaterPages=self.myLaterPages)
