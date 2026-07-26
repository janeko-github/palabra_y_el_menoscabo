from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from database import Base

class Word(Base):
    __tablename__ = "words"
    id = Column(Integer, primary_key=True, index=True)
    term = Column(String(255), nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    meanings = relationship("Meaning", back_populates="word", cascade="all, delete-orphan", lazy="selectin")
    synonyms = relationship("Synonym", back_populates="word", cascade="all, delete-orphan", lazy="selectin")
    antonyms = relationship("Antonym", back_populates="word", cascade="all, delete-orphan", lazy="selectin")
    etymologys = relationship("Etymology", back_populates="word", cascade="all, delete-orphan", lazy="selectin")
    usecases = relationship("UseCase", back_populates="word", cascade="all, delete-orphan", lazy="selectin")

class Meaning(Base):
    __tablename__ = "meanings"
    id = Column(Integer, primary_key=True, index=True)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    meaning_text = Column(Text, nullable=False)
    word = relationship("Word", back_populates="meanings")

class Synonym(Base):
    __tablename__ = "synonyms"
    id = Column(Integer, primary_key=True, index=True)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    synonym_text = Column(String(255), nullable=False)
    word = relationship("Word", back_populates="synonyms")

class Antonym(Base):
    __tablename__ = "antonyms"
    id = Column(Integer, primary_key=True, index=True)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    antonym_text = Column(String(255), nullable=False)
    word = relationship("Word", back_populates="antonyms")

class Etymology(Base):
    __tablename__ = "etymologys"
    id = Column(Integer, primary_key=True, index=True)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    etymology_text = Column(String(255), nullable=False)
    word = relationship("Word", back_populates="etymologys")    

class UseCase(Base):
    __tablename__ = "usecases"
    id = Column(Integer, primary_key=True, index=True)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    usecase_text = Column(Text, nullable=False)
    word = relationship("Word", back_populates="usecases")
