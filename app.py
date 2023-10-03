from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
import io
from google.cloud import speech_v1
from google.cloud.speech_v1 import enums
from google.cloud.speech_v1 import types

app = Flask(__name__)

# create a SQLAlchemy engine
engine = create_engine('sqlite:///videos.db', echo=True)

#create a session factory
Sesion = sessionmaker(bind=engine)

# create a declarative base class
Base = declarative_base()

class VideoChunk(Base):
    id = Column(Integer, primary_key=True)
    chunk_number = Column(Integer)
    video_chunk = Column(LargeBinary)

    def __init__(self, chunk_number, video_chunk):
        self.chunk_number = chunk_number
        self.video_chunk = video_chunk

    def to_dict(self):
        return {'id': self.id, 'chunk_number': self.chunk_number}

# create the table
Base.metadata.create_all(engine)

#endpoint to upload a video chunk
@app.route('/videos/chunks', methods=['POST'])
def upload_video_chunk():
    session = Session()

    chunk_number = request.form.get("chunk_number")
    video_chunk = request.files['video_chunk'].read()

    #create a new video chunk object and store it in the database
    video_chunk_obj = VideoChunk(chunk_number=chunk_number, video_chunk=video_chunk)
    session.add(video_chunk_obj)
    session.commit()

    session.close()

    return jsonify({'message': 'success'})

#endpoint to transcribe a video
@app.route('/videos/transcribe', methods=['POST'])
def transcribe_video():
    session = Session()

    # retrieve the video chunks from the database and assemble them into a single file
    video_chunks = session.query(VideoChunk).all()
    video_file_bytes = b''.join([chunk.video_chunk for chunk in video_chunks])
    video_file = io.BytesIO(video_file_bytes)

    # perform speech transcription using Google Cloud Speech-to-Text API
    client = speech_v1.SpeechClient()

    # configure settings for transcription
    language_code = 'en-US'
    sample_rate_hertz = 44100
    encoding = enums.RecognitionConfig.AudioEncoding.LINEAR16

    config = types.RecognitionConfig(encoding=encoding, sample_rate_hertz=sample_rate_hertz, language_code=language_code)

    audio = types.RecognitionAudio(content=video_file.read())

    response = client.recognize(config, audio)

    # store the transcription in the database
    transcription = response.results[0].alternatives[0].transcript
    session.add(Transcription(data=transcription))
    session.commit()

    session.close()

    return jsonify({'message': 'success', 'transcription': transcription})

if __name__ == '__main__':
    app.run(debug=True)
