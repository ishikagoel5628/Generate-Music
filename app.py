# import sys
# import re 
# import os
import numpy as np 

import pickle

from music21 import converter, instrument, note, chord, stream
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Activation, Dense, LSTM, Dropout, Flatten

from flask import Flask, redirect, url_for, request, render_template,Response,send_file,send_from_directory
import tensorflow as tf
from tensorflow.keras.models import load_model



app = Flask(__name__)
UPLOAD_FOLDER= "C://Users//ishik//Documents//projects github//output"

def create_network(network_in, n_vocab): 
    """Create the model architecture"""
    model = Sequential()
    model.add(LSTM(128, input_shape=network_in.shape[1:], return_sequences=True))
    model.add(Dropout(0.2))
    model.add(LSTM(128, return_sequences=True))
    model.add(Flatten())
    model.add(Dense(256))
    model.add(Dropout(0.3))
    model.add(Dense(n_vocab))
    model.add(Activation('softmax'))
    model.compile(loss='categorical_crossentropy', optimizer='adam')

    return model

def get_inputSequences(notes, pitchnames, n_vocab):
    """ Prepare the sequences used by the Neural Network """
    # map between notes and integers and back
    note_to_int = dict((note, number) for number, note in enumerate(pitchnames))

    sequence_length = 100
    network_input = []
    for i in range(0, len(notes) - sequence_length, 1):
        sequence_in = notes[i:i + sequence_length]
        network_input.append([note_to_int[char] for char in sequence_in])
    
    network_input = np.reshape(network_input, (len(network_input), 100, 1))
    
    return (network_input)

def create_midi(prediction_output):
    """ convert the output from the prediction to notes and create a midi file
        from the notes """
    offset = 0
    output_notes = []

    # create note and chord objects based on the values generated by the model
    for pattern in prediction_output:
        # pattern is a chord
        if ('.' in pattern) or pattern.isdigit():
            notes_in_chord = pattern.split('.')
            notes = []
            for current_note in notes_in_chord:
                new_note = note.Note(int(current_note))
                new_note.storedInstrument = instrument.Piano()
                notes.append(new_note)
            new_chord = chord.Chord(notes)
            new_chord.offset = offset
            output_notes.append(new_chord)
        # pattern is a note
        else:
            new_note = note.Note(pattern)
            new_note.offset = offset
            new_note.storedInstrument = instrument.Piano()
            output_notes.append(new_note)

        # increase offset each iteration so that notes do not stack
        offset += 0.5

    midi_stream = stream.Stream(output_notes)
    
    # print('Saving Output file as midi....')

    midi_stream.write('midi', fp='C://Users//ishik//Documents//projects github//output//test_output.mid')

def generate_notes(model, network_input, pitchnames, n_vocab):
    """ Generate notes from the neural network based on a sequence of notes """
    # Pick a random integer
    start = np.random.randint(0, len(network_input)-1)

    int_to_note = dict((number, note) for number, note in enumerate(pitchnames))
    
    # pick a random sequence from the input as a starting point for the prediction
    pattern =list(network_input[start])
    prediction_output = []
    
    print('Generating notes........')

    # generate 500 notes
    for note_index in range(500):
        prediction_input = np.reshape(pattern, (1, len(pattern), 1))
        prediction_input = prediction_input / float(n_vocab)
        prediction_input=np.asarray(prediction_input).astype(np.float32)
        prediction = model.predict(prediction_input, verbose=0)
        
        # Predicted output is the argmax(P(h|D))
        index = np.argmax(prediction)

        # Mapping the predicted interger back to the corresponding note
        result = int_to_note[index]
        # Storing the predicted output
        prediction_output.append(result)
        pattern.append(index)
        # Next input to the model
        pattern = pattern[1:len(pattern)]

    print('Notes Generated...')
    return prediction_output



def pred():
    """ Generate a piano midi file """
    #load the notes used to train the model
    notes = pickle.load(open('C://Users//ishik//Documents//projects github//notes (3)','rb'))

    # Get all pitch names
    pitchnames = sorted(set(item for item in notes))
    # Get all pitch names
    n_vocab = len(set(notes))
    
    network_input = get_inputSequences(notes, pitchnames, n_vocab)
    normalized_input = network_input / float(n_vocab)
    
    model=load_model('model.hdf5')
    # model = tf.keras.models.load_model("model.hdf5")
    print('Model Loaded')
    prediction_output = generate_notes(model, network_input, pitchnames, n_vocab)
    create_midi(prediction_output)


# @app.route('/', methods=['GET'])
# def index():
#     return render_template("index.html")
# @app.route("/wav")
# def streamwav():
#     def gene():
#         with open("C://Users//ishik//Documents//projects github//output//test_output.mid", "rb") as fwav:
#             data = fwav.read(1024)
#             while data:
#                 yield data
#                 data = fwav.read(1024)
#     return Response(gene(), mimetype="audio/x-wav")

@app.route('/', methods=['GET','POST'])
def generate():
    if request.method == 'POST':
        # Get the file from post request
        # audio_file = request.files['audio']
        # # Save the file to ./uploads
        # # basepath = os.path.dirname(__file__)
        # if audio_file:
        #     file_path = os.path.join(UPLOAD_FOLDER, audio_file.filename)
        #     audio_file.save(file_path)

        pred()
        new_file = open('C://Users//ishik//Documents//projects github//output//test_output.mid', 'rb') 
        return send_file(new_file, mimetype='audio/mid',as_attachment=True,attachment_filename='sample'+'.mid')
        # return render_template("index.html",output=new_file)
        # return send_from_directory(UPLOAD_FOLDER, new_file)
    return render_template("index.html",ouput=0)
if __name__== "__main__":
    app.run(debug=True)