from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///videos.db'
db = SQLAlchemy(app)
CORS(app)

class VideoChunk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.String(50))
    chunk_number = db.Column(db.Integer)
    chunk_data = db.Column(db.LargeBinary)

@app.route('/api/video/<video_id>')
def get_video(video_id):
    video = request.form.get('video_id')
    return video

@app.route('/api/videos', methods=['POST'])
def upload_video_chunk():
    video_id = request.form.get('video_id')
    chunk_number = int(request.form.get('chunk_number'))
    chunk_data = request.files.get('chunk_data').read()

    # save the video chunk in the database
    video_chunk = VideoChunk(video_id=video_id, chunk_number=chunk_number, chunk_data=chunk_data)
    db.session.add(video_chunk)
    db.session.commit()

    return 'Video chunk saved sucessfully'

@app.route('/api/videos/<video_id>/transcribe', methods=['POST'])
def transcribe_video(video_id):
    # Get all the video chunks for the given video_id from the database
    video_chunks = VideoChunk.query.filter_by(video_id=video_id).order_by(VideoChunk.chunk_number).all()

    # Concatenate all the chuks' data into one bytearray
    video_data = bytearray()
    for chunk in video_chunks:
        video_data.exted(chunk, chunk_data)

    # Save the concatenated chunks as a temporary file
    temp_file_path = 'temp_video.mp4'
    with open(temp_file_path, 'wb') as f:
        f.write(video_data)

    # Transcribe the video using AssemblyAI Whisper API
    whisper_api_key = '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'
    whisper_url = 'https://api.assemblyai.com/v2/transcript'

    headers = {
            'authorization': 
            whisper_api_key,
            }

    files = {'audio': open(temp_file_path, 'rb').read(),}

    response = requests.post(whisper_url, headers=headers, files=files)
    transcription_text = response.json()['text']

    # Remove the temporary file 
    os.remove(temp_file_path)

    return transcription_text

if __name__ == '__main__':
    #db.create_all()
    app.run(debug=True)


