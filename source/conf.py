project = 'Sprawozdanie'
author = 'Mateusz Brokos, Szymon Blatkowski'
release = '1.0'

extensions = []

templates_path = ['_templates']
exclude_patterns = []

html_theme = 'sphinx_rtd_theme'
latex_toplevel_sectioning = 'chapter'


# Ważne! Dla PDF (LaTeX)
latex_engine = 'pdflatex'
latex_elements = {
    'papersize': 'a4paper',
    'pointsize': '11pt',
    'classoptions': ',openany',
    'tableofcontents': r'\tableofcontents',
}
