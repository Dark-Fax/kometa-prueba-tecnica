import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, HRFlowable
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor

OUTPUT_DIR = "generated_files"

def generate_module_pdf(module_title: str, content: str, description: str, filename: str) -> str:
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    # Configuración del documento con márgenes elegantes
    doc = SimpleDocTemplate(
        filepath, 
        pagesize=letter, 
        topMargin=0.75*inch, 
        bottomMargin=0.75*inch,
        leftMargin=0.75*inch,
        rightMargin=0.75*inch
    )
    
    styles = getSampleStyleSheet()
    
    # Paleta de colores Kometa
    primary_color = HexColor("#1A365D")   # Azul Ejecutivo Profundo
    secondary_color = HexColor("#4A5568") # Gris Corporativo
    accent_color = HexColor("#DD6B20")    # Naranja de Acento
    
    # Estilos Tipográficos Customizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=primary_color,
        spaceAfter=6
    )
    
    desc_style = ParagraphStyle(
        'CustomDesc',
        parent=styles['Italic'],
        fontName='Helvetica-Oblique',
        fontSize=11,
        leading=14,
        textColor=secondary_color,
        spaceAfter=15
    )
    
    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=accent_color,
        spaceBefore=12,
        spaceAfter=8
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=16,          # Mejor interlineado para lectura fluida
        textColor=HexColor("#2D3748"),
        alignment=4           # Justificado estricto
    )

    story = []
    
    # Cabecera del informe
    story.append(Paragraph(module_title, title_style))
    story.append(Paragraph(description, desc_style))
    
    # Línea divisoria elegante
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=15))
    
    # Inyección Automática de la Imagen del Módulo (si existe)
    # Reutiliza la imagen generada para que el PDF se vea ilustrado
    image_path = filepath.replace(".pdf", ".png")
    if os.path.exists(image_path):
        story.append(Image(image_path, width=5.5*inch, height=3.6*inch))
        story.append(Spacer(1, 0.2 * inch))
    
    story.append(Paragraph("Desarrollo de Contenido", h2_style))
    
    # Renderizado de párrafos justificados
    for paragraph in content.split("\n\n"):
        if paragraph.strip():
            story.append(Paragraph(paragraph.strip(), body_style))
            story.append(Spacer(1, 0.12 * inch))
            
    doc.build(story)
    return filepath