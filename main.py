import io
import csv
import os
import genanki
import pandas as pd
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel, Field

from database import engine, Base, get_db
from models import Word, Meaning, Synonym, Antonym, Etymology,UseCase


# ── Lifespan (reemplaza @app.on_event("startup")) ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown (opcional, si necesitas limpiar algo al cerrar)
    """Hacer backup de la base de datos a GitHub al cerrar"""
    try:
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mensaje_commit = f"Backup DB {fecha}"
        
        # Verificar que existe el archivo
        if not os.path.exists(DATABASE):
            print(f"⚠️  No se encontró {DATABASE}")
            return
        
        # Comandos git
        comandos = [
            ["git", "add", DATABASE],
            ["git", "commit", "-m", mensaje_commit],
            ["git", "push"]
        ]
        
        for cmd in comandos:
            resultado = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            print(f"✅ {' '.join(cmd[:2])}: {resultado.stdout.strip()}")
        
        print(f"🚀 Backup completado: {mensaje_commit}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en git: {e.stderr}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

    pass


# ── Esquemas Pydantic ──
class MeaningIn(BaseModel):
    meaning_text: str

class SynonymIn(BaseModel):
    synonym_text: str

class AntonymIn(BaseModel):
    antonym_text: str

class EtymologyIn(BaseModel):
    etymology_text: str

class UseCaseIn(BaseModel):
    usecase_text: str

class WordCreate(BaseModel):
    term: str = Field(..., min_length=1, max_length=255)
    meanings: List[MeaningIn] = []
    synonyms: List[SynonymIn] = []
    antonyms: List[AntonymIn] = []
    etymologys: List[EtymologyIn] = []
    usecases: List[UseCaseIn] = []

class WordUpdate(BaseModel):
    term: Optional[str] = Field(None, min_length=1, max_length=255)
    meanings: Optional[List[MeaningIn]] = None
    synonyms: Optional[List[SynonymIn]] = None
    antonyms: Optional[List[AntonymIn]] = None
    etymologys: Optional[List[EtymologyIn]] = None
    usecases: Optional[List[UseCaseIn]] = None

class MeaningOut(BaseModel):
    id: int
    meaning_text: str
    class Config:
        from_attributes = True

class SynonymOut(BaseModel):
    id: int
    synonym_text: str
    class Config:
        from_attributes = True

class AntonymOut(BaseModel):
    id: int
    antonym_text: str
    class Config:
        from_attributes = True

class EtymologyOut(BaseModel):
    id: int
    etymology_text: str
    class Config:
        from_attributes = True        
class UseCaseOut(BaseModel):
    id: int
    usecase_text: str
    class Config:
        from_attributes = True

class WordOut(BaseModel):
    id: int
    term: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    meanings: List[MeaningOut] = []
    synonyms: List[SynonymOut] = []
    antonyms: List[AntonymOut] = []
    etymologys: List[EtymologyOut] = []
    usecases: List[UseCaseOut] = []
    
    class Config:
        from_attributes = True


# ── App ──
app = FastAPI(
    title="La Palabra y el Menoscabo",
    version="1.0.0",
    lifespan=lifespan
)

# Servir frontend
if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")


# ── CRUD ──
@app.get("/words", response_model=List[WordOut])
async def list_words(q: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    stmt = select(Word).order_by(Word.term)
    if q:
        stmt = stmt.where(Word.term.ilike(f"%{q}%"))
    result = await db.execute(stmt)
    return result.scalars().all()

@app.get("/words/{word_id}", response_model=WordOut)
async def get_word(word_id: int, db: AsyncSession = Depends(get_db)):
    word = await db.get(Word, word_id)
    if not word:
        raise HTTPException(status_code=404, detail="Palabra no encontrada")
    return word

@app.post("/words", response_model=WordOut, status_code=201)
async def create_word(data: WordCreate, db: AsyncSession = Depends(get_db)):
    word = Word(term=data.term)
    db.add(word)
    await db.flush()

    for m in data.meanings:
        db.add(Meaning(word_id=word.id, meaning_text=m.meaning_text))
    for s in data.synonyms:
        db.add(Synonym(word_id=word.id, synonym_text=s.synonym_text))
    for a in data.antonyms:
        db.add(Antonym(word_id=word.id, antonym_text=a.antonym_text))
    for e in data.etymologys:
        db.add(Etymology(word_id=word.id, etymology_text=e.etymology_text))
    for u in data.usecases:
        db.add(UseCase(word_id=word.id, usecase_text=u.usecase_text))

    await db.commit()
    await db.refresh(word)
    return word

@app.put("/words/{word_id}", response_model=WordOut)
async def update_word(word_id: int, data: WordUpdate, db: AsyncSession = Depends(get_db)):
    word = await db.get(Word, word_id)
    if not word:
        raise HTTPException(status_code=404, detail="Palabra no encontrada")

    if data.term is not None:
        word.term = data.term

    # Reemplazar relaciones si vienen en la petición
    if data.meanings is not None:
        await db.execute(delete(Meaning).where(Meaning.word_id == word_id))
        for m in data.meanings:
            db.add(Meaning(word_id=word_id, meaning_text=m.meaning_text))

    if data.synonyms is not None:
        await db.execute(delete(Synonym).where(Synonym.word_id == word_id))
        for s in data.synonyms:
            db.add(Synonym(word_id=word_id, synonym_text=s.synonym_text))

    if data.antonyms is not None:
        await db.execute(delete(Antonym).where(Antonym.word_id == word_id))
        for a in data.antonyms:
            db.add(Antonym(word_id=word_id, antonym_text=a.antonym_text))
    if data.etymologys is not None:
        await db.execute(delete(Etymology).where(Etymology.word_id == word_id))
        for e in data.etymologys:
            db.add(Etymology(word_id=word_id, etymology_text=e.etymology_text))
    if data.usecases is not None:
        await db.execute(delete(UseCase).where(UseCase.word_id == word_id))
        for u in data.usecases:
            db.add(UseCase(word_id=word_id, usecase_text=u.usecase_text))

    await db.commit()
    await db.refresh(word)
    return word

@app.delete("/words/{word_id}", status_code=204)
async def delete_word(word_id: int, db: AsyncSession = Depends(get_db)):
    word = await db.get(Word, word_id)
    if not word:
        raise HTTPException(status_code=404, detail="Palabra no encontrada")
    await db.delete(word)
    await db.commit()
    return


# ── Exportaciones ──
@app.get("/export/csv")
async def export_csv(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Word))
    words = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "term", "meanings", "synonyms", "antonyms", "etymology", "usecases", "created_at", "updated_at"])

    for w in words:
        meanings = " | ".join([m.meaning_text for m in w.meanings])
        synonyms = ", ".join([s.synonym_text for s in w.synonyms])
        antonyms = ", ".join([a.antonym_text for a in w.antonyms])
        etymologys = ", ".join([a.etymology_text for a in w.etymologys])
        usecases = ", ".join([u.usecase_text for u in w.usecases])

        
        writer.writerow([w.id, w.term, meanings, synonyms, antonyms, etymologys, usecases, w.created_at, w.updated_at])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=palabras.csv"}
    )

@app.get("/export/xlsx")
async def export_xlsx(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Word))
    words = result.scalars().all()

    rows = []
    for w in words:
        rows.append({
            "ID": w.id,
            "Palabra": w.term,
            "Significados": "\n".join([f"• {m.meaning_text}" for m in w.meanings]),
            "Sinónimos": ", ".join([s.synonym_text for s in w.synonyms]),
            "Antónimos": ", ".join([a.antonym_text for a in w.antonyms]),
            "Etimología": ", ".join([a.etymology_text for a in w.etymologys]),
            "Casos de uso": ", ".join([u.usecase_text for u in w.usecases]),
            
            "Creado": w.created_at,
            "Actualizado": w.updated_at,
        })

    df = pd.DataFrame(rows)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Palabras")
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=palabras.xlsx"}
    )

@app.get("/export/pdf")
async def export_pdf(db: AsyncSession = Depends(get_db)):
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import cm

    result = await db.execute(select(Word))
    words = result.scalars().all()

    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleCustom',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor("#2c3e50"),
        spaceAfter=20,
        alignment=1
    )
    heading2 = ParagraphStyle(
        'Heading2Custom',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor("#34495e"),
        spaceAfter=6,
        spaceBefore=12
    )
    body = styles["BodyText"]
    body.fontSize = 10

    story = []
    story.append(Paragraph("La Palabra y el Menoscabo", title_style))
    story.append(Paragraph(f"Exportación generada el {datetime.now().strftime('%d/%m/%Y %H:%M')}", body))
    story.append(Spacer(1, 12))

    for w in words:
        story.append(Paragraph(f"<b>{w.term}</b>", heading2))

        if w.meanings:
            story.append(Paragraph("<b>Significados:</b>", body))
            for m in w.meanings:
                story.append(Paragraph(f"• {m.meaning_text}", body))
        if w.synonyms:
            syns = ", ".join([s.synonym_text for s in w.synonyms])
            story.append(Paragraph(f"<b>Sinónimos:</b> {syns}", body))
        if w.antonyms:
            ants = ", ".join([a.antonym_text for a in w.antonyms])
            story.append(Paragraph(f"<b>Antónimos:</b> {ants}", body))
        if w.etymologys:
            ants = ", ".join([a.etymology_text for a in w.etymologys])
            story.append(Paragraph(f"<b>Etimología:</b> {ants}", body))            
        if w.usecases:
            ants = ", ".join([a.usecase_text for a in w.usecases])
            story.append(Paragraph(f"<b>Casos de uso:</b> {ants}", body))

        story.append(Spacer(1, 8))

    doc.build(story)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=palabras.pdf"}
    )

@app.get("/export/anki")
async def export_anki(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Word))
    words = result.scalars().all()

    model_id = 1607392319
    deck_id = 2059400110

    my_model = genanki.Model(
        model_id,
        'Palabra y Menoscabo Model',
        fields=[
            {'name': 'Palabra'},
            {'name': 'Significados'},
            {'name': 'Sinónimos'},
            {'name': 'Antónimos'},
            {'name': 'Etimología'},
            {'name': 'Casos de uso'},
        ],
        templates=[
            {
                'name': 'Tarjeta 123',
                'qfmt': '<div style="font-size:24px;text-align:center;"><b>{{Palabra}}</b></div>',
                'afmt': '{{FrontSide}}<hr id="answer">'
                        '<div style="font-size:16px;"><b>Significados:</b><br>{{Significados}}</div>'
                        '<div style="font-size:16px;margin-top:8px;"><b>Sinónimos:</b> {{Sinónimos}}</div>'
                        '<div style="font-size:16px;margin-top:8px;"><b>Antónimos:</b> {{Antónimos}}</div>'
                        '<div style="font-size:16px;margin-top:8px;"><b>Etimología:</b> {{Etimología}}</div>'
                        '<div style="font-size:16px;margin-top:8px;"><b>Casos de uso:</b> {{Casos de uso}}</div>'
                        ,
                        
            },
        ],
        css='.card { font-family: arial; font-size: 20px; text-align: center; color: black; background-color: white; }'
    )

    my_deck = genanki.Deck(deck_id, 'La Palabra y el Menoscabo')

    for w in words:
        meanings = "<br>".join([f"• {m.meaning_text}" for m in w.meanings]) or "-"
        synonyms = ", ".join([s.synonym_text for s in w.synonyms]) or "-"
        antonyms = ", ".join([a.antonym_text for a in w.antonyms]) or "-"
        etymologys = ", ".join([a.etymology_text for a in w.etymologys]) or "-"
        usecases = ",".join([f"• {u.usecase_text}" for u in w.usecases]) or "-"

        note = genanki.Note(
            model=my_model,
            fields=[w.term, meanings, synonyms, antonyms, etymologys, usecases]
        )
        my_deck.add_note(note)

    output = io.BytesIO()
    genanki.Package(my_deck).write_to_file(output)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=palabras_y_menoscabo.apkg"}
    )
