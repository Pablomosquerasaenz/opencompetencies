from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
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
        # Prep document.
        doc = SimpleDocTemplate(self.response, pagesize=landscape(letter), topMargin=36,
                                bottomMargin=36)
        Story = [Spacer(1,0.5*inch)]
        style = self.styles["Normal"]
        light_gray = (0.9, 0.9, 0.9)
        dark_gray = (0.75, 0.75, 0.75)
        elements = []

        # Define styles.
        eu_style = ParagraphStyle('eu_style', fontName='Helvetica', bulletText=u'\u2022',
                                  leftIndent=10, borderWidth=0, borderColor='black')

        # Add title and subtitle.
        p_style = ParagraphStyle('title', fontName='Helvetica-Bold', fontSize=20,
                                 spaceAfter=0)
        elements.append(Paragraph(org.name, p_style))
        p_style.fontName = 'Helvetica'
        p_style.fontSize = 16
        p_style.spaceAfter = 20
        elements.append(Paragraph(sa.subject_area, p_style))

        spacer_width = 0.05*inch
        ca_col_width = 3*inch - spacer_width/2
        eu_col_width = 6*inch - spacer_width/2
        col_widths = (ca_col_width, spacer_width, eu_col_width)
        
        # Build a series of separate tables.
        #  Easy to manage styling this way.

        # --- Header row. ---
        data = [(org.alias_ca.title()+'s', '', org.alias_eu.title()+'s')]
        table = Table(data, colWidths=col_widths)
        elements.append(table)
        table.setStyle(TableStyle([('BACKGROUND', (0,0), (0,0), dark_gray),
                                   ('BACKGROUND', (2,0), (2,0), light_gray),
                                   ('BOTTOMPADDING', (0,0), (-1,-1), 10),
                                   ('FONTSIZE', (0,0), (-1,-1), 14),
                                   ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
                                   ]))
        # Clear data.
        data = []

        # Spacer row.
        self.add_spacer_row(elements, col_widths, spacer_width)

        # --- Subject area competency areas. ---
        # Each competency area and its eus are a separate table.
        for ca in cas:
            if not ca.subdiscipline_area:
                p = Paragraph(ca.competency_area, style)
                data.append((p, '',  ''))

                for eu in eus:
                    if eu.competency_area == ca:
                        # # Line up first eu with ca.
                        # # DEV: Starting to work, but breaks ca into separate tables
                        # #      for every eu.
                        # if data[-1][0]:
                        #     if ca.competency_area.strip() == data[-1][0].text:
                        #         #data[-1][2] = p
                        #         p_e = Paragraph(eu.essential_understanding, style)
                        #         data[-1] = (p, '', p_e)
                        # else:
                        p = Paragraph(eu.essential_understanding, eu_style)
                        data.append(('', '', p))
            if data:
                # Build table.
                table = Table(data, colWidths=col_widths)
                elements.append(table)
                # TOPPADDING setting is a hack until first eu is added to ca data tuple.
                #  When that's implemented, remove TOPPADDING setting.
                #  Same for sda ca eus.
                table.setStyle(TableStyle([('BACKGROUND', (0,0), (0,-1), dark_gray),
                                           ('BACKGROUND', (2,0), (2,-1), light_gray),
                                           ('BOTTOMPADDING', (0,-1), (-1,-1), 10),
                                           ('TOPPADDING', (0,1), (2,1), -10),
                                           ]))
                data = []
                self.add_spacer_row(elements, col_widths, spacer_width)


        # Add sda competency areas.
        for sda in sdas:
            # Add a single-row table for the sda.
            p_style = ParagraphStyle('title', fontName='Helvetica-Bold', fontSize=14,
                                 spaceBefore=5, spaceAfter=10)
            elements.append(Paragraph(sda.subdiscipline_area, p_style))

            # Each competency area and its eus are a separate table.
            for ca in cas:
                if (ca.subdiscipline_area
                    and ca.subdiscipline_area.subdiscipline_area == sda.subdiscipline_area):
                    p = Paragraph(ca.competency_area, style)
                    data.append((p, '', ''))
                    for eu in eus:
                        if eu.competency_area == ca:
                            p = Paragraph(eu.essential_understanding, eu_style)
                            data.append(('', '', p))

                if data:
                    # Build table.
                    table = Table(data, colWidths=col_widths)
                    elements.append(table)
                    table.setStyle(TableStyle([('BACKGROUND', (0,0), (0,-1), dark_gray),
                                               ('BACKGROUND', (2,0), (2,-1), light_gray),
                                               ('BOTTOMPADDING', (0,-1), (-1,-1), 10),
                                               ('TOPPADDING', (0,1), (2,1), -12),
                                               ]))
                    data = []
                    self.add_spacer_row(elements, col_widths, spacer_width)

        # Build the document, and return the response.
        doc.build(elements)
        return self.response

    def add_spacer_row(self, elements, col_widths, spacer_width):
        """Add a spacer row between competency areas."""
        data = [('', '', '')]
        table = Table(data, colWidths=col_widths, rowHeights=(spacer_width))
        elements.append(table)
