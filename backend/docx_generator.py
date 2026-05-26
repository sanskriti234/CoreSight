import docx
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import nsdecls, qn
from docx.oxml import OxmlElement
import os
from datetime import datetime
from paths import BASE_DIR,ATTENDANCE_DIR, ENCODINGS_DIR, IMAGES_DIR, DETAILS_DIR, DOCUMENTS_DIR,FRONTEND_DIR

# =========================================================
# 1. HELPER FUNCTIONS
# =========================================================

def set_cell_border(cell, **kwargs):
    """
    Set cell_border
    """
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = tcPr.first_child_found_in("w:tcBorders")
    if tcBorders is None:
        tcBorders = OxmlElement("w:tcBorders")
        tcPr.append(tcBorders)
    for ElemName, ElemAttrs in kwargs.items():
        element = tcBorders.find(qn(f"w:{ElemName}"))
        if element is None:
            element = OxmlElement(f"w:{ElemName}")
            tcBorders.append(element)
        for AttribName, AttribValue in ElemAttrs.items():
            element.set(qn(f"w:{AttribName}"), str(AttribValue))

def set_cell_shading(cell, fill_color, color="auto"):
    """
    Set cell shading (background color).
    """
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), color)
    shd.set(qn('w:fill'), fill_color)
    tcPr.append(shd)

def set_cell_text_margins(cell, **margins):
    """
    Sets individual text margins (padding) for a cell in Dxa units (twentieths of a point).
    """
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()

    existing_tcMar = tcPr.find(qn("w:tcMar"))
    if existing_tcMar is not None:
        tcPr.remove(existing_tcMar)

    tcMar = OxmlElement("w:tcMar")

    margin_map = {
        "top": "w:top",
        "bottom": "w:bottom",
        "start": "w:start", # corresponds to left
        "end": "w:end"      # corresponds to right
    }

    for margin_name, dxa_value in margins.items():
        if margin_name in margin_map:
            margin_el = OxmlElement(margin_map[margin_name])
            margin_el.set(qn("w:w"), str(dxa_value))
            margin_el.set(qn("w:type"), "dxa")
            tcMar.append(margin_el)

    if margins:
        tcPr.append(tcMar)

def add_table_heading(table, text):
    """
    Adds a merged, centered, and shaded heading row to a table.
    NOTE: Assumes the last row has 2 cells for merging.
    """
    last_row_cells = table.rows[-1].cells
    merged_cell = last_row_cells[0].merge(last_row_cells[1])
    p = merged_cell.paragraphs[0]
    p.text = text
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4) # Add small vertical padding
    p.paragraph_format.space_after = Pt(4)
    
    run = p.runs[0]
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x00, 0x00, 0x00)
    set_cell_shading(merged_cell, fill_color="E0E0E0") # Light gray fill
    
    # Set vertical alignment to center for the heading
    tc = merged_cell._tc
    tcPr = tc.get_or_add_tcPr()
    vAlign = OxmlElement('w:vAlign')
    vAlign.set(qn('w:val'), 'center')
    tcPr.append(vAlign)
    
    return merged_cell

def add_table_row(table, key, value, padding_dxa):
    """
    Adds a key-value pair row to the table and styles it, using LEFT alignment
    for professional readability.
    """
    row = table.add_row().cells

    # Key cell (LEFT ALIGNED)
    p_key = row[0].paragraphs[0]
    run_key = p_key.add_run(key)
    run_key.font.bold = True
    run_key.font.name = 'Times New Roman'
    run_key.font.size = Pt(7)
    p_key.alignment = WD_ALIGN_PARAGRAPH.LEFT 
    set_cell_text_margins(row[0], start=padding_dxa, end=padding_dxa, top=padding_dxa, bottom=padding_dxa)

    # Value cell (LEFT ALIGNED)
    p_val = row[1].paragraphs[0]
    run_val = p_val.add_run(value or "---") # Ensure None/empty strings are handled
    run_val.font.name = 'Times New Roman'
    run_val.font.size = Pt(8)
    p_val.alignment = WD_ALIGN_PARAGRAPH.LEFT 
    set_cell_text_margins(row[1], start=padding_dxa, end=padding_dxa, top=padding_dxa, bottom=padding_dxa)

    # Set Vertical Alignment to Center for data cells
    for cell in row:
        tc = cell._tc
        tcPr = cell._tc.get_or_add_tcPr()
        vAlign = OxmlElement('w:vAlign')
        vAlign.set(qn('w:val'), 'center')
        tcPr.append(vAlign)

    return row[0], row[1]

def style_table(table, key_width_cm, value_width_cm):
    """
    Applies borders and sets column widths for the data table.
    """
    table.columns[0].width = Cm(key_width_cm)
    table.columns[1].width = Cm(value_width_cm)

    border_style = {"sz": 6, "val": "single", "color": "#888888", "space": "0"}
    borders = {
        "top": border_style,
        "bottom": border_style,
        "start": border_style,
        "end": border_style,
    }
    for row in table.rows:
        for cell in row.cells:
            set_cell_border(cell, **borders)
            
            # Set Vertical Alignment to Center (redundant but ensures consistency)
            tc = cell._tc
            tcPr = tc.get_or_add_tcPr()
            vAlign = OxmlElement('w:vAlign')
            vAlign.set(qn('w:val'), 'center')
            tcPr.append(vAlign)

# =========================================================
# 2. MAIN FUNCTION (MODIFIED FOR BANSAL INSTITUTE HEADER)
# =========================================================

def generate_student_profile_docx(student_data, image_path, output_path):
    """
    Generates a student profile DOCX file with a fully centered header,
    including the Bansal logo and required footer elements.
    """

    # ====================================================
    # <<< ADJUSTABLE VARIABLES FOR SIZING AND POSITIONING >>>
    # ====================================================
    # Image Sizing (in Centimeters)
    LOGO_WIDTH_CM = 1.8 
    STUDENT_PHOTO_WIDTH_CM = 2.5 

    # Vertical spacing before the header block
    HEADER_VERTICAL_SPACING_LINES_TOP = 1 
    
    # Professional Color and Font Size for Header Text
    HEADER_TEXT_COLOR = RGBColor(0x00, 0x33, 0x66) # Dark Blue
    INSTITUTE_NAME_FONT_SIZE = 12 # Pt 
    AFFILIATION_FONT_SIZE = 10 # Pt
    SESSION_FONT_SIZE = 9 # Pt
    
    # Table Sizing (in Centimeters) - Remaining Body Table
    TABLE_KEY_WIDTH_CM = 6.0
    TABLE_VALUE_WIDTH_CM = 12.0

    # Cell Padding (internal spacing) - Applied only to data rows
    TABLE_CELL_PADDING_DXA = 25

    # Vertical spacing before signatures
    SIGNATURE_VERTICAL_SPACING_LINES = 2
    # ====================================================

    # --- Helper to get data safely ---
    def get_data(key):
        return student_data.get(key, "---") or "---"

    # --- Data Mapping (unchanged) ---
    personal_details_map = [
        ("NAME", "name"),
        ("EMAIL", "email"),
        ("PHONE", "phone"),
        ("DEPARTMENT", "department"),
        ("DOB", "dob"),
        ("ADDRESS", "address"),
    ]

    parent_details_map = [
        ("FATHER NAME", "father_name"),
        ("FATHER PHONE", "father_phone"),
        ("MOTHER NAME", "mother_name"),
        ("MOTHER PHONE", "mother_phone"),
        ("GUARDIAN NAME", "guardian_name"),
        ("GUARDIAN PHONE", "guardian_phone"),
    ]

    education_details_map = [
        ("HIGHSCHOOL BOARD", "highschool_board"),
        ("HIGHSCHOOL YEAR", "highschool_year"),
        ("HIGHSCHOOL MARKS", "highschool_marks"),
        ("INTERMEDIATE BOARD", "intermediate_board"),
        ("INTERMEDIATE YEAR", "intermediate_year"),
        ("INTERMEDIATE MARKS", "intermediate_marks"),
        ("DIPLOMA", "diploma"),
    ]

    # 1. Initialize Document
    doc = Document()
    
    # --- Get current timestamp for footer ---
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    footer_text = f"GENERATED BY CORESIGHT - {timestamp}"


    # 2. Set Page Margins and Add Footer
    sections = doc.sections
    for section in sections:
        section.top_margin = Cm(1.27)
        section.bottom_margin = Cm(1.27)
        section.left_margin = Cm(1.27)
        section.right_margin = Cm(1.27)
        
        # --- ADD FOOTER ---
        footer = section.footer
        p_footer = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        p_footer.text = footer_text
        p_footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        run_footer = p_footer.runs[0] if p_footer.runs else p_footer.add_run(footer_text)
        run_footer.font.size = Pt(8)
        run_footer.font.italic = True
        run_footer.font.color.rgb = RGBColor(0x80, 0x80, 0x80)
        
    # Apply top spacing 
    for _ in range(HEADER_VERTICAL_SPACING_LINES_TOP):
        doc.add_paragraph()

    # =================================================================
    # 3. HEADER SECTION: Logo, Institute Name, Affiliation, Session
    # =================================================================
    
    # Set the logo file path using the user's input
    logo_file = r"D:Projects/CoreSight/frontend/assets/BansalLogo.jpg"
    
    # 3.1. Add Logo (Centered)
    p_logo = doc.add_paragraph()
    p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_logo.paragraph_format.space_before = Pt(0) 
    p_logo.paragraph_format.space_after = Pt(2) 
    
    try:
        if os.path.exists(logo_file):
            p_logo.add_run().add_picture(logo_file, width=Cm(LOGO_WIDTH_CM))
        else:
            p_logo.add_run(f"[Logo Not Found: {os.path.basename(logo_file)}]").font.size = Pt(8)
    except Exception as e:
        print(f"Error adding logo: {e}")

    # 3.2. Add Text Stack (Fully Centered)
    # Institution Name
    p_inst_name = doc.add_paragraph()
    p_inst_name.paragraph_format.space_before = Pt(0) 
    p_inst_name.paragraph_format.space_after = Pt(0)
    p_inst_name.alignment = WD_ALIGN_PARAGRAPH.CENTER 
    run_inst_name = p_inst_name.add_run("Bansal Institute of Engineering and Technology")
    run_inst_name.font.name = 'Times New Roman'
    run_inst_name.font.size = Pt(INSTITUTE_NAME_FONT_SIZE) 
    run_inst_name.font.bold = True
    run_inst_name.font.color.rgb = HEADER_TEXT_COLOR
    
    # Affiliation
    p_affiliation = doc.add_paragraph()
    p_affiliation.paragraph_format.space_before = Pt(0)
    p_affiliation.paragraph_format.space_after = Pt(0)
    p_affiliation.alignment = WD_ALIGN_PARAGRAPH.CENTER 
    run_aff = p_affiliation.add_run("Affiliated to AKTU, Lucknow")
    run_aff.font.name = 'Times New Roman'
    run_aff.font.size = Pt(AFFILIATION_FONT_SIZE)
    run_aff.font.color.rgb = HEADER_TEXT_COLOR

    # Session
    
    # In docx_generator.py

    # Retrieve the data safely
    academic_year = get_data("academic_year")

    # 1. Create a clean paragraph
    p_session = doc.add_paragraph()
    p_session.paragraph_format.space_before = Pt(0)
    p_session.paragraph_format.space_after = Pt(8)
    p_session.alignment = WD_ALIGN_PARAGRAPH.CENTER 

    # 2. Add the complete text using a single run
    run_sess = p_session.add_run(f"Academic Session: {academic_year}") # Use academic_year variable!

    # 3. Apply the required styling to the run
    run_sess.font.name = 'Times New Roman'
    run_sess.font.size = Pt(SESSION_FONT_SIZE)
    run_sess.font.color.rgb = HEADER_TEXT_COLOR 
    run_sess.font.bold = True # Added for typical header emphasis
  
    # 4. Add horizontal line (as a paragraph border)
    p_line = doc.add_paragraph()
    p_line.paragraph_format.space_before = Pt(0)
    p_line.paragraph_format.space_after = Pt(0) 
    
    pPr = p_line._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    pPr.append(pBdr)
    bottom_border = OxmlElement('w:bottom')
    bottom_border.set(qn('w:val'), 'single')
    bottom_border.set(qn('w:sz'), '12') # Thicker line
    bottom_border.set(qn('w:color'), '003366') # Matching the dark blue color
    bottom_border.set(qn('w:space'), '1')
    pBdr.append(bottom_border)

    # 5. Add Student Photo Section
    doc.add_paragraph() # Add space right after the line
    
    photo_file = image_path 
    try:
        if os.path.exists(photo_file):
            doc.add_picture(photo_file, width=Cm(STUDENT_PHOTO_WIDTH_CM))
            last_paragraph = doc.paragraphs[-1]
            last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        else:
            doc.add_paragraph("[Student Photo Placeholder]").alignment = WD_ALIGN_PARAGRAPH.CENTER
    except Exception as e:
        print(f"Error adding student photo (Check file path: {photo_file}): {e}")

    # Add Roll Number
    p_roll = doc.add_paragraph()
    p_roll.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_roll.paragraph_format.space_after = Pt(8) # Space before table
    run_roll = p_roll.add_run(f"Roll No: {get_data('roll_no')}")
    run_roll.font.name = 'Times New Roman'
    run_roll.font.size = Pt(9)
    run_roll.font.bold = True

    # =========================================================
    # 6. SINGLE MERGED TABLE IMPLEMENTATION (REMAINING BODY)
    # =========================================================

    master_table = doc.add_table(rows=1, cols=2)
    master_table.style = 'Table Grid'
    master_table.autofit = False

    # Personal Details
    add_table_heading(master_table, "PERSONAL DETAILS")
    for label, data_key in personal_details_map:
        add_table_row(master_table, label, get_data(data_key), TABLE_CELL_PADDING_DXA)

    # Parent's Details
    master_table.add_row()
    add_table_heading(master_table, "PARENT'S DETAILS")
    for label, data_key in parent_details_map:
        add_table_row(master_table, label, get_data(data_key), TABLE_CELL_PADDING_DXA)

    # Educational Details
    master_table.add_row()
    add_table_heading(master_table, "EDUCATIONAL DETAILS")
    for label, data_key in education_details_map:
        add_table_row(master_table, label, get_data(data_key), TABLE_CELL_PADDING_DXA)

    # Apply Universal Styling
    style_table(master_table, TABLE_KEY_WIDTH_CM, TABLE_VALUE_WIDTH_CM)

    # =========================================================

    # Add vertical spacing before signatures
    for _ in range(SIGNATURE_VERTICAL_SPACING_LINES):
        doc.add_paragraph()

    # 7. Add Footer Signatures
    table_sig = doc.add_table(rows=1, cols=2)
    table_sig.autofit = False

    sections = doc.sections
    effective_width_emu = sections[0].page_width - sections[0].left_margin - sections[0].right_margin
    
    SIGNATURE_COL_1_WIDTH_EMU = effective_width_emu // 2
    SIGNATURE_COL_2_WIDTH_EMU = effective_width_emu - SIGNATURE_COL_1_WIDTH_EMU

    table_sig.columns[0].width = SIGNATURE_COL_1_WIDTH_EMU
    table_sig.columns[1].width = SIGNATURE_COL_2_WIDTH_EMU

    # Mentor's Signature
    cell_mentor = table_sig.rows[0].cells[0]
    p_mentor = cell_mentor.paragraphs[0]
    p_mentor.text = "Mentor's Signature"
    p_mentor.alignment = WD_ALIGN_PARAGRAPH.LEFT 
    p_mentor.runs[0].font.name = 'Times New Roman'
    p_mentor.runs[0].font.size = Pt(9)
    p_mentor.runs[0].font.bold = True

    # Student's Signature
    cell_student = table_sig.rows[0].cells[1]
    p_student = cell_student.paragraphs[0]
    p_student.text = "Student's Signature"
    p_student.alignment = WD_ALIGN_PARAGRAPH.RIGHT 
    p_student.runs[0].font.name = 'Times New Roman'
    p_student.runs[0].font.size = Pt(9)
    p_student.runs[0].font.bold = True

    # Remove borders from the signature table
    for row in table_sig.rows:
        for cell in row.cells: 
            set_cell_border(cell,
                            top={"sz": 0, "val": "nil"},
                            bottom={"sz": 0, "val": "nil"},
                            start={"sz": 0, "val": "nil"},
                            end={"sz": 0, "val": "nil"})


    # --- Save Document ---
    try:
        doc.save(output_path)
        print(f"Successfully generated DOCX at '{output_path}'")
    except Exception as e:
        print(f"Error saving DOCX file at '{output_path}': {e}")


# =========================================================
# 3. PLACEHOLDER FUNCTIONS (Kept for compatibility)
# =========================================================

def generate_custom_docx(data, template_path, output_path):
    """Placeholder function."""
    try:
        doc = Document()
        doc.add_heading("Custom Document Placeholder", 0)
        doc.add_paragraph(f"Data received: {str(data)}")
        doc.save(output_path)
    except Exception as e:
        print(f"Error in placeholder 'generate_custom_docx': {e}")

class DocxGenerator:
    """Placeholder class."""
    def __init__(self, template_path=None):
        self.template_path = template_path

    def generate(self, data, output_path):
        try:
            doc = Document()
            doc.add_heading("DocxGenerator Class Output Placeholder", 0)
            doc.add_paragraph(f"Data received: {str(data)}")
            doc.save(output_path)
        except Exception as e:
            print(f"Error in placeholder 'DocxGenerator.generate': {e}")