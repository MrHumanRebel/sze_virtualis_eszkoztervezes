"""Build clean A4 project PDFs. No simulation results are made up.

The requirements PDF is a typeset transcription, not the original upload.
Fonts come from the runner's system and are not committed to this repo.
"""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
import argparse

W,H=A4
M=46
INK=HexColor("#14171B")
MUTED=HexColor("#58616A")
SOFT=HexColor("#88919A")
RULE=HexColor("#E3E7EA")
ACCENT=HexColor("#087E82")
PALE=HexColor("#E9F3F3")

def setup():
    for d in (Path("/usr/share/fonts/truetype/lato"),Path("/usr/share/fonts/truetype/dejavu")):
        if (d/"Lato-Regular.ttf").is_file():
            files=("Lato-Regular.ttf","Lato-Bold.ttf","Lato-Heavy.ttf")
        elif (d/"DejaVuSans.ttf").is_file():
            files=("DejaVuSans.ttf","DejaVuSans-Bold.ttf","DejaVuSans-Bold.ttf")
        else:
            continue
        for name,file in zip(("Lato","LatoBold","LatoHeavy"),files):
            pdfmetrics.registerFont(TTFont(name,str(d/file)))
        return
    raise RuntimeError("Lato / DejaVu font missing")

def txt(c,x,y,s,size=10,bold=False,color=INK,heavy=False):
    c.setFillColor(color)
    c.setFont("LatoHeavy" if heavy else "LatoBold" if bold else "Lato",size)
    c.drawString(x,y,s)

def para(c,x,y,rich,w=None,size=9.8,leading=14.8,color=MUTED):
    p=Paragraph(rich,ParagraphStyle("P",fontName="Lato",fontSize=size,leading=leading,textColor=color))
    _,height=p.wrap(w or W-2*M,H)
    p.drawOn(c,x,y-height)
    return y-height

def rule(c,y):
    c.setStrokeColor(RULE)
    c.setLineWidth(.75)
    c.line(M,y,W-M,y)

def page(c,num,header="VIRTUÁLIS ESZKÖZTERVEZÉS"):
    c.setFillColor(HexColor("#FFFFFF"))
    c.rect(0,0,W,H,stroke=0,fill=1)
    txt(c,M,H-39,header,8.2,True,SOFT)
    txt(c,W-108,H-39,"2026 / 27 · I.",8,color=SOFT)
    rule(c,H-53)
    rule(c,42)
    txt(c,M,27,"GKLM_AUTM029   /   SZE",7.6,color=SOFT)
    txt(c,W-M-27,27,f"{num:02d}",8,True,SOFT)

def heading(c,h,sub):
    txt(c,M,H-108,h,25,heavy=True)
    para(c,M,H-125,sub,size=10.2,leading=15.5)

def chip(c,x,y,s):
    width=pdfmetrics.stringWidth(s,"LatoBold",8)+24
    c.setFillColor(PALE)
    c.roundRect(x,y-7,width,20,10,stroke=0,fill=1)
    txt(c,x+12,y,s,8,True,ACCENT)

def card(c,x,y,w,h,a,b):
    c.setFillColor(HexColor("#FFFFFF"))
    c.setStrokeColor(RULE)
    c.roundRect(x,y,w,h,10,stroke=1,fill=1)
    txt(c,x+12,y+h-20,a,9.3,True)
    txt(c,x+12,y+13,b,8.1,color=SOFT)

def arrow(c,x,y,ex):
    c.setStrokeColor(SOFT)
    c.setLineWidth(1.2)
    c.line(x,y,ex,y)
    c.line(ex,y,ex-5,y+3)
    c.line(ex,y,ex-5,y-3)

def model_report(path):
    c=canvas.Canvas(str(path),pagesize=A4,pageCompression=1)
    c.setTitle("Virtuális eszköztervezés – modellterv")
    page(c,1)
    chip(c,M,690,"2D / DISZKRÉT ESEMÉNYSZIMULÁCIÓ")
    txt(c,M,641,"PC-konfigurációk",29,heavy=True)
    txt(c,M,605,"minőségellenőrzése és kiszállítása",20,heavy=True)
    para(c,M,574,"A feladatot három külön részfolyamatra bontottam. Először kiszűröm a hibás számítógépeket, utána a jó darabokat csomagolom, végül két rakodó között osztom el a munkát.",size=10.7,leading=16.7)
    rule(c,510)
    for x,num,title,desc in [
        (M,"10 000","beérkező számítógép","A szimuláció bemenete"),
        (221,"30%","hibás termék","Selejt a minőségellenőrzésnél"),
        (400,"2 m","minden szalag","Állomásközi továbbítás")]:
        txt(c,x,469,num,23,heavy=True)
        txt(c,x,448,title,9,True,MUTED)
        txt(c,x,430,desc,7.7,color=SOFT)
    rule(c,415)
    txt(c,M,380,"Fő anyagáramlás",15,True)
    steps=[(M,105,"Beérkezés","10 000 db"),(166,107,"Ellenőrzés","70 / 30"),
           (288,94,"Csomagolás","1 PC + 1 anyag"),(399,150,"Szállítás","66 / 34")]
    for x,w,a,b in steps: card(c,x,251,w,74,a,b)
    for i in range(3): arrow(c,steps[i][0]+steps[i][1]+3,287,steps[i+1][0]-4)
    para(c,M,210,"<b>Selejtág:</b> a hibás számítógépek külön kimenetre kerülnek. A csomagoláshoz csak a minőségellenőrzésen megfelelt darabok jutnak el.",size=10,leading=16)
    txt(c,M,131,"Miért ez a felépítés?",13.5,True)
    para(c,M,112,"A három részmodell külön is átlátható, a főmodell mégis egyetlen folyamatként fut. A százalékos elágazásokhoz nincs szükség külön vezérlőkódra.",size=9.5,leading=15)
    c.showPage()

    page(c,2)
    heading(c,"A három részfolyamat","A munkaállomásokat külön Frame-ekben építem fel, majd a fő 2D modellbe illesztem őket.")
    blocks=[
        (626,"01","MINŐSÉGELLENŐRZÉS","Ellenőrzés 180 s  /  címkézés 20 / 20 s",
         "A termékek 70%-a a csomagolásra, 30%-a a selejtkimenetre halad."),
        (465,"02","CSOMAGOLÁS","PC és csomagolóanyag előkészítése: 20 / 20 s",
         "A csomagolás 600 s. Minden számítógéphez egy csomagolóanyag kell. Ezután 60 s adminisztráció következik."),
        (304,"03","SZÁLLÍTÁS-ELŐKÉSZÍTÉS","Adminisztráció 60 s  /  rakodók 300 / 600 s",
         "A csomagok 66/34 arányban oszlanak meg. A kiszállítás további 60 s.")
    ]
    for y,no,title,meta,body in blocks:
        rule(c,y+26)
        txt(c,M,y,no,12,True,ACCENT)
        txt(c,M+40,y,title,13,heavy=True)
        txt(c,M+40,y-27,meta,8.8,True,MUTED)
        para(c,M+40,y-42,body,W-2*M-40,9.5,15)
    rule(c,187)
    txt(c,M,163,"Várható szűk keresztmetszet",11.2,True)
    para(c,M,145,"A 10 perces csomagolás a leghosszabb egyedi művelet. Először itt vizsgálnám az állomáskihasználtságot és a várakozást. Ezt végül a Plant Simulation statisztikáinak kell igazolniuk.",size=9.35,leading=14.6)
    c.showPage()

    page(c,3)
    heading(c,"Beállítások és értékelés","Külön kezelem a feladatlapon megadott értékeket és a modellhez felvett feltételezéseket.")
    rows=[
        ("Ellenőrzés","180 s","Feladat szerint"),
        ("Selejtarány","30%","Feladat szerint"),
        ("Címkézés","20 / 20 s","Feladat szerint"),
        ("Előkészítések","20 / 20 s","Feladat szerint"),
        ("Csomagolás","600 s","1:1 anyagigény"),
        ("Adminisztráció","60 / 60 s","Feladat szerint"),
        ("Rakodók","300 / 600 s","66 / 34%"),
        ("Kiszállítás","60 s","Feladat szerint"),
        ("Szalaghossz","2 m","Minden kapcsolaton"),
        ("Szalagsebesség","1 m/s","Modellfeltevés"),
        ("Érkezési ütem","1 s","Modellfeltevés"),
    ]
    y=613
    txt(c,M,y+20,"ÁLLOMÁS / PARAMÉTER",8.6,True,SOFT)
    txt(c,335,y+20,"ÉRTÉK",8.6,True,SOFT)
    rule(c,y+9)
    for a,b,annotation in rows:
        txt(c,M,y-21,a,9.9)
        txt(c,335,y-21,b,10.1,True)
        txt(c,416,y-21,annotation,7.6,color=SOFT)
        rule(c,y-33)
        y-=41
    txt(c,M,112,"Mérési cél",11.4,True)
    para(c,M,96,"A 10 000 beérkező számítógép teljes tételének átfutási idejét mérem. A jó és a selejt kimenet darabszámainak összege 10 000. A selejtarány sztochasztikus, ezért nem minden futásban pontosan 3000 hibás termék keletkezik.",size=9.1,leading=14)
    c.showPage()

    page(c,4)
    heading(c,"Ellenőrzés és leadás","Csak a Siemens Plant Simulation tényleges futtatásából származó adat kerülhet a végleges eredmények közé.")
    for y,num,name,desc in [
        (613,"01","Szerkezeti ellenőrzés","3 külön Frame, 23 szállítószalag, megadott állomásidők és elágazások."),
        (494,"02","Szimuláció","10 000 beérkezés, jó és hibás darabok, teljes futási idő."),
        (375,"03","Állomásstatisztika","Siemens Chart a kihasználtságról és a várakozásról."),
        (256,"04","Mentés és beadás","A végső fájl: Neptun-kód.spp. Leadás előtt Plant Simulationben ellenőrzöm.")]:
        rule(c,y+25)
        txt(c,M,y,num,12,True,ACCENT)
        txt(c,M+40,y,name,12,True)
        para(c,M+40,y-17,desc,W-2*M-40,9.4,14.7)
    rule(c,157)
    txt(c,M,133,"Mérési eredmény",10.6,True)
    para(c,M,114,"Átfutási idő és valódi alkalmazásképernyőképek csak a Siemens-futtatás után csatolhatók. Ez a dokumentum nem tartalmaz becsült vagy kitalált mérési eredményt.",size=9.2,leading=14.5)
    c.showPage()
    c.save()

STEPS=[
"Készítsen egy új modellt 2D-ben!",
"Hozzon létre egy mappát, ebben készítse el a három beillesztendő vázlatot!",
"Az ellenőrzés 3 percet vesz igénybe.",
"A termékek 30%-a hibás (rossz).",
"A címkézés mindkét esetben 20 másodpercet vesz igénybe.",
"A csomagolóanyag és a számítógépek előkészítése 20 másodpercet vesz igénybe",
"A csomagolási művelet 10 percet vesz igénybe. (1 elemhez- 1 csomagoló anyag)",
"A csomagolás utáni- és a szállítás előkészítési adminisztráció időszükséglete 1 perc.",
"A szállítás előkészítési fázisban a Rakodó-1 5 perc, a Rakodó-2 10 perc alatt végzi a tevékenységet, ezért az érkező csomagokat 66-34%-os arányban irányítsuk feléjük.",
"A kiszállítás 1 percet igényel.",
"Grafikon segítségével ábrázolja az állomások statisztikáját.",
"Határozza meg az átfutási időt 10000 db számítógép beérkezése esetén."
]

def assignment_transcript(path):
    c=canvas.Canvas(str(path),pagesize=A4,pageCompression=1)
    c.setTitle("Beadandó feladat – tartalmi átirat")
    page(c,1,"FELADATLAP / SZÖVEGES ÁTIRAT")
    txt(c,M,714,"Beadandó feladat",24,heavy=True)
    chip(c,M,671,"AZ EREDETI KÉTOLDALAS KIÍRÁS ALAPJÁN")
    y=para(c,M,632,"<b>Feladat:</b> Egy számítógép konfigurációk összeszerelésével foglalkozó vállalat folyamatainak szimulációja. A kidolgozandó feladat a vállalat minőségellenőrzési, csomagolási, és szállítás-előkészítési műveleteit is érinti.",size=10.1,leading=16,color=INK)
    txt(c,M,y-31,"A szerelősor elvi elrendezése",13,True)
    y-=69
    flow=[("Kész termék","beérkezése"),("Minőség","ellenőrzés"),("Csomagolás",""),
          ("Szállítás","előkészítés"),("Kiszállítás","")]
    for i,(a,b) in enumerate(flow):
        x=M+i*103
        card(c,x,y-52,91,50,a,b)
        if i<4: arrow(c,x+93,y-25,x+100)
    txt(c,M+123,y-75,"Selejtág: Rossz termék elszállítása",9.2,color=MUTED)
    y-=134
    txt(c,M,y,"Az egyes munkahelyek felépítése",13,True)
    y-=41
    for a,b in [
        ("Minőségellenőrzés","Ellenőrzés → jó / rossz címkézés → külön kimenetek"),
        ("Csomagolás","PC és csomagolóanyag előkészítés → csomagolás → adminisztráció"),
        ("Szállítás-előkészítés","Adminisztráció → 66 / 34% → két rakodó → kiszállítás")]:
        txt(c,M,y,a,11.4,True)
        para(c,M+13,y-16,b,W-2*M-13,9.4,14.5)
        y-=76
    c.showPage()
    page(c,2,"FELADATLAP / SZÖVEGES ÁTIRAT")
    txt(c,M,716,"Műszaki követelmények",23,heavy=True)
    intro="Feladat: Az ábrákon látható módon felépíteni a szimulációs modellt. Az állomások közötti alkatrész továbbítás minden esetben 2 m-es szállítószalagon történik. A minőségellenőrzés, csomagolás, és szállítás előkészítés munkaállomásokat külön vázlaton kell elkészíteni, majd beilleszteni egy 2D-s szimulációs modellbe."
    y=para(c,M,677,intro,size=9.4,leading=14.2)-25
    for i,step in enumerate(STEPS,1):
        txt(c,M,y-2,f"{i:02d}",8.4,True,ACCENT)
        y=para(c,M+27,y+6,step,W-2*M-27,9.3,13.2,color=INK)-10
    rule(c,y-2)
    para(c,M,y-19,"<b>A beadandó anyag az elkészült .spp fájl, fájlnév a Neptun kód!</b>",size=10,leading=14.4,color=INK)
    txt(c,M,70,"Tartalmi átirat – nem az eredeti PDF bájtpontos másolata.",7.6,color=SOFT)
    c.showPage()
    c.save()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir",type=Path,default=Path("docs/generated"))
    out=parser.parse_args().output_dir
    out.mkdir(parents=True,exist_ok=True)
    setup()
    model_report(out/"Modelltajekoztato.pdf")
    assignment_transcript(out/"Feladatkiiras_atirat.pdf")
    for path in out.glob("*.pdf"):print(path,path.stat().st_size)

if __name__=="__main__":
    main()
