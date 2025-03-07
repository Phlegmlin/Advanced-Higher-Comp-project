#Database Connection
def get_db_connection():
    return mysql.connector.connect(
        host="",
        user="",   
        password="",  
        database=""
        
#Note Class
class Note:
    def __init__(self, name, pitch):
        self.name = name
        self.pitch = pitch

    def get_pitch(self):
        return self.pitch

    def get_name(self):
        return self.name

#Scale Class
class Scale:
    def __init__(self, root, scale_type):
        self.__root = root
        self.__type = scale_type
        self.__notes = self.fetch_from_db()

    def fetch_from_db(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT note, pitch FROM ScaleNotes WHERE root = %s AND type = %s"
        cursor.execute(query, (self.__root, self.__type))
        scale_notes = [Note(row[0], row[1]) for row in cursor.fetchall()]
        conn.close()
        return scale_notes

    def get_notes(self):
        return self.__notes

#Melody Generator
class MelodyGenerator:
    def __init__(self, scale, length):
        self.scale = scale
        self.length = length

    def generate_melody(self):
        return [random.choice(self.scale.get_notes()) for _ in range(self.length)]

#Chord Generator
class ChordGenerator:
    def __init__(self, melody, scale):
        self.melody = melody
        self.scale = scale

    def generate_chords(self):
        chords = []
        for note in self.melody:
            chord = [note]
            for interval in [2, 4]:
                index = (self.scale.get_notes().index(note) + interval) % len(self.scale.get_notes())
                chord.append(self.scale.get_notes()[index])
            chords.append(self.bubble_sort_chord(chord))
        return chords

    @staticmethod
    def bubble_sort_chord(chord):
        n = len(chord)
        for i in range(n - 1):
            for j in range(n - i - 1):
                if chord[j].pitch > chord[j + 1].pitch:
                    chord[j], chord[j + 1] = chord[j + 1], chord[j]
        return chord

#MIDI File Creation
class MIDIFileManager:
    def __init__(self, filename="static/output.mid"):
        self.filename = filename
        self.mid = MidiFile()
        self.melody_track = MidiTrack()
        self.chord_track = MidiTrack()
        self.mid.tracks.append(self.melody_track)
        self.mid.tracks.append(self.chord_track)

    def write_melody(self, melody):
        for note in melody:
            self.melody_track.append(Message('note_on', note=note.get_pitch(), velocity=64, time=480))
            self.melody_track.append(Message('note_off', note=note.get_pitch(), velocity=64, time=480))

    def write_chords(self, chords):
        for chord in chords:
            for note in chord:
                self.chord_track.append(Message('note_on', note=note.get_pitch(), velocity=64, time=0))
            self.chord_track.append(Message('note_off', note=chord[0].get_pitch(), velocity=64, time=480))

    def save_file(self):
        self.mid.save(self.filename)
        return self.filename

#Flask API Route to Handle Form Submission
@app.route("/generate", methods=["POST"])
def generate_music():
    data = request.json
    scale = data["scale"]
    length = int(data["length"])
    random_mode = data["random"]

    scale_obj = Scale(scale, "Major" if scale == "major" else "Minor")
    melody_generator = MelodyGenerator(scale_obj, length)
    melody = melody_generator.generate_melody()

    chord_generator = ChordGenerator(melody, scale_obj)
    chords = chord_generator.generate_chords()

    midi_manager = MIDIFileManager()
    midi_manager.write_melody(melody)
    midi_manager.write_chords(chords)
    midi_file_path = midi_manager.save_file()

    return jsonify({"melody": [(note.get_name(), note.get_pitch()) for note in melody],
                    "chords": [[(n.get_name(), n.get_pitch()) for n in chord] for chord in chords],
                    "midi_file": "/" + midi_file_path})

#Flask Route to Download MIDI File
@app.route("/download_midi")
def download_midi():
    return send_file("static/output.mid", as_attachment=True)

#Run Flask App
if __name__ == "__main__":
    if not os.path.exists("static"):
        os.makedirs("static")
    app.run(debug=True)