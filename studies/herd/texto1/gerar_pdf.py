import sys,markdown
from xhtml2pdf import pisa
from xhtml2pdf.default import DEFAULT_FONT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
for n,f in (('tnr','tnr.ttf'),('tnrb','tnrb.ttf'),('tnri','tnri.ttf')): pdfmetrics.registerFont(TTFont(n,'./'+f))
addMapping('tnr',0,0,'tnr');addMapping('tnr',1,0,'tnrb');addMapping('tnr',0,1,'tnri');addMapping('tnr',1,1,'tnrb')
DEFAULT_FONT['tnr']='tnr'
src,out=sys.argv[1],sys.argv[2]
body=markdown.markdown(open(src).read(),extensions=['tables'])
css="""@page{size:a4;margin:2.2cm 2.2cm}body{font-family:tnr;font-size:10.5pt;line-height:1.35}
h1{font-size:15pt;text-align:center}h2{font-size:12pt;margin-top:14pt}p{text-align:justify}
td,th{border:0.5pt solid #888;padding:3pt 5pt;font-size:9.5pt}th{background:#eee}"""
html=f"<html><head><meta charset='utf-8'><style>{css}</style></head><body>{body}</body></html>"
with open(out,'wb') as f: r=pisa.CreatePDF(html,dest=f,encoding='utf-8')
print('erros',r.err)
