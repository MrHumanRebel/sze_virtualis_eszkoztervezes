"""Produce a clean Hungarian results report from genuine Siemens evidence only.

Unlike the static model notes this PDF can only exist after a validated real run.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def generate(output_dir: Path) -> Path:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import HexColor
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle

    out=Path(output_dir).resolve()
    manifest=json.loads((out/"evidence_manifest.json").read_text(encoding="utf-8"))
    metrics=json.loads((out/"simulation_result.json").read_text(encoding="utf-8"))
    if not (metrics["complete"] and metrics["processed"]==10000 and
            metrics["pass_quantity_and_quality_tolerance"] and
            manifest["synthetic_images"] is False and len(manifest["screenshots"])==5):
        raise RuntimeError("Nem áll rendelkezésre igazolt Siemens-mérés.")
    spp=out/manifest["model"]
    if not spp.is_file() or _sha(spp)!=manifest["spp_sha256"]:
        raise RuntimeError("SPP forrás SHA256-ellenőrzés sikertelen.")
    for name,data in manifest["screenshots"].items():
        path=out/"screenshots"/name
        if not path.is_file() or _sha(path)!=data["sha256"]:
            raise RuntimeError("Képernyőkép SHA256-ellenőrzés sikertelen: "+name)

    W,H=A4
    M=42
    DARK=HexColor("#16191D")
    GREY=HexColor("#6C7780")
    RULE=HexColor("#E4E8EA")
    TEAL=HexColor("#0D7E81")
    regular="Helvetica"
    bold="Helvetica-Bold"
    fonts=(
        (Path("C:/Windows/Fonts/segoeui.ttf"),Path("C:/Windows/Fonts/segoeuib.ttf")),
        (Path("/usr/share/fonts/truetype/lato/Lato-Regular.ttf"),
         Path("/usr/share/fonts/truetype/lato/Lato-Bold.ttf")),
    )
    for r,b in fonts:
        if r.is_file() and b.is_file():
            pdfmetrics.registerFont(TTFont("ReportRegular",str(r)))
            pdfmetrics.registerFont(TTFont("ReportBold",str(b)))
            regular="ReportRegular"
            bold="ReportBold"
            break

    def txt(c,x,y,value,size=10,strong=False,color=DARK):
        c.setFont(bold if strong else regular,size)
        c.setFillColor(color)
        c.drawString(x,y,str(value))

    def line(c,y):
        c.setStrokeColor(RULE)
        c.setLineWidth(.7)
        c.line(M,y,W-M,y)

    def para(c,x,top,rich,width,size=9.4,leading=14.5):
        p=Paragraph(rich,ParagraphStyle("p",fontName=regular,fontSize=size,
                                        leading=leading,textColor=GREY))
        _,height=p.wrap(width,H)
        p.drawOn(c,x,top-height)
        return top-height

    def shell(c,no):
        c.setFillColor(HexColor("#FFFFFF"))
        c.rect(0,0,W,H,stroke=0,fill=1)
        txt(c,M,H-37,"MÉRÉSI JEGYZŐKÖNYV",8.2,True,GREY)
        txt(c,W-134,H-37,"GKLM_AUTM029",8.1,color=GREY)
        line(c,H-53)
        line(c,40)
        txt(c,M,25,"SIEMENS PLANT SIMULATION  /  2D",7.5,color=GREY)
        txt(c,W-M-15,25,f"{no:02d}",8.0,True,GREY)

    def screenshot(c,x,top,w,h,name):
        img=ImageReader(str(out/"screenshots"/name))
        iw,ih=img.getSize()
        k=min(w/iw,h/ih)
        dw,dh=iw*k,ih*k
        c.drawImage(img,x,top-dh,dw,dh,mask="auto")
        c.setStrokeColor(RULE)
        c.rect(x,top-dh,dw,dh,stroke=1,fill=0)
        return top-dh

    path=out/"Siemens_meresi_jegyzokonyv.pdf"
    c=canvas.Canvas(str(path),pagesize=A4,pageCompression=1)
    c.setTitle("Plant Simulation – mért eredmények")
    shell(c,1)
    txt(c,M,720,"Szimulációs eredmény",25,True)
    txt(c,M,686,"10 000 számítógép · teljes tétel",10,color=GREY)
    line(c,661)
    stats=[
        (M,"10 000","feldolgozott"),
        (183,str(metrics["good"]),"jó termék"),
        (326,str(metrics["bad"]),"selejt"),
        (447,f"{metrics['defect_ratio']*100:.1f}%","selejtarány")
    ]
    for x,value,label in stats:
        txt(c,x,622,value,19,True)
        txt(c,x,600,label,8.5,color=GREY)
    line(c,578)
    seconds=metrics["lot_lead_time_seconds"]
    if not isinstance(seconds,(int,float)):
        raise RuntimeError("A Siemens mért szimulációs ideje hiányzik.")
    txt(c,M,543,"Teljes tétel átfutási ideje",11.2,True)
    txt(c,M,508,f"{float(seconds)/3600:,.2f} óra",27,True,TEAL)
    txt(c,M,486,f"SimTime: {seconds} másodperc",8.7,color=GREY)
    txt(c,M,442,"Főmodell – eredeti alkalmazáskép",11.5,True)
    screenshot(c,M,425,W-2*M,238,"01_fomodell.png")
    txt(c,M,159,"A képek közvetlenül a Plant Simulationből származnak.",9,True)
    para(c,M,142,"Az eredmény nem becslés: a futás végén a jó és rossz darabok számlálója együtt pontosan 10 000-et ad. A screenshotokat és az SPP modellt SHA256 alapján azonosítottam.",W-2*M,9.4,14.7)
    c.showPage()

    shell(c,2)
    txt(c,M,721,"Állomások és modellrészletek",23,True)
    txt(c,M,693,"A dokumentált nézeteket az eredeti Siemens alkalmazás exportálta.",9.5,color=GREY)
    for top,label,name in [
        (657,"01 / Minőségellenőrzés","02_minosegellenorzes.png"),
        (452,"02 / Csomagolás","03_csomagolas.png"),
        (247,"03 / Szállítás-előkészítés","04_szallitas_elokeszites.png")
    ]:
        txt(c,M,top,label,10.7,True)
        screenshot(c,M,top-11,W-2*M,171,name)
    c.showPage()
    shell(c,3)
    txt(c,M,719,"Állomásstatisztika",23,True)
    screenshot(c,M,683,W-2*M,390,"05_allomasstatisztika.png")
    txt(c,M,250,"Fájlazonosítás",11.3,True)
    line(c,236)
    txt(c,M,216,"SPP:",9,True)
    txt(c,M+49,216,manifest["model"],9)
    txt(c,M,196,"SHA256:",9,True)
    checksum=manifest["spp_sha256"]
    txt(c,M+49,196,checksum[:32],8,color=GREY)
    txt(c,M+49,182,checksum[32:],8,color=GREY)
    txt(c,M,158,"Képek:",9,True)
    txt(c,M+49,158,"5 db / eredeti Siemens export",9,color=GREY)
    txt(c,M,139,"Rögzítve:",9,True)
    txt(c,M+49,139,manifest["created_utc"],8.3,color=GREY)
    para(c,M,109,"A SHA256 ellenőrzés a fájlok változatlanságát igazolja. A szimuláció eredményeit a Plant Simulation futtatása szolgáltatja.",W-2*M,8.9,13.5)
    c.showPage()
    c.save()
    return path
