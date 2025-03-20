import mysql.connector
import random
from mido import MidiFile, MidiTrack, Message

#Connect to Database
def dbConnection():
    return mysql.connector.connect(
        host="localhost",
        user="adi",   
        password="password",  
        database="music_database"
    )
        
#Create Note Class
class Note:
    def __init__(self, name, pitch):
        self.name = name
        self.pitch = pitch

    def get_pitch(self):
        return self.pitch

    def get_name(self):
        return self.name

#Create Scale Class
class Scale:
    def __init__(self, root, mode):
        self.root = root
        self.mode = mode
        self.notes = self.fetch_notes_from_db()

    def fetch_notes_from_db(self):
        conn = dbConnection()
        cursor = conn.cursor()
        query = """
        SELECT Notes.name, Notes.pitch FROM ScaleNotes
        JOIN Notes ON ScaleNotes.note_id = Notes.note_id
        JOIN Scales ON ScaleNotes.scale_id = Scales.scale_id
        WHERE Scales.name = %s
        ORDER BY Notes.pitch;
        """
        cursor.execute(query, (f"{self.root} {self.mode}",))
        scale_notes = [Note(row[0], row[1]) for row in cursor.fetchall()]
        conn.close()
        return scale_notes

#Create MelodyGenerator Class
class MelodyGenerator:
    def __init__(self, scale, length):
        self.scale = scale
        self.length = length

    def generate_melody(self):
        return [random.choice(self.scale.notes) for _ in range(self.length)]

#Create ChordGenerator Class
class ChordGenerator:
    def __init__(self, melody, scale):
        self.melody = melody
        self.scale = scale

    def generate_chords(self):
        chords = []
        scale_notes = self.scale.notes  # Fetch scale notes

        for note in self.melody:
            chord = [note]  # Root note of the chord

            # Generate a major or minor chord based on the scale structure
            for interval in [2, 4]:  # Third and fifth intervals
                index = (scale_notes.index(note) + interval) % len(scale_notes)

                if 0 <= index < len(scale_notes):  # Ensure index is within range
                    chord.append(scale_notes[index])

            # If chord contains more than one note, add it to the list
            if len(chord) > 1:
                chords.append(self.bubble_sort_chord(chord))

        return chords

    def bubble_sort_chord(self, chord):
        for i in range(len(chord) - 1):
            for j in range(len(chord) - i - 1):
                if chord[j].pitch > chord[j + 1].pitch:
                    chord[j], chord[j + 1] = chord[j + 1], chord[j]
        return chord


#Create MIDIFileManager
class MIDIFileManager:
    def __init__(self, filename="output.mid"):
        self.filename = filename
        self.mid = MidiFile()
        self.melody_track = MidiTrack()
        self.chord_track = MidiTrack()
        self.mid.tracks.append(self.melody_track)
        self.mid.tracks.append(self.chord_track)

    def write_melody(self, melody):
        for note in melody:
            self.melody_track.append(Message('note_on', note=note.pitch, velocity=64, time=0))
            self.melody_track.append(Message('note_off', note=note.pitch, velocity=64, time=480))  # Matches quarter note length

    def write_chords(self, melody, chords):
        for i in range(len(melody)):  # Ensure chords align with melody
            chord = chords[i]  # Get corresponding chord for the melody note
            
            # Start all chord notes exactly when melody starts
            for chord_note in chord:
                self.chord_track.append(Message('note_on', note=chord_note.pitch, velocity=64, time=0))

            # Stop all chord notes exactly when melody stops
            for chord_note in chord:
                self.chord_track.append(Message('note_off', note=chord_note.pitch, velocity=64, time=0))  # Ensure same timing
            
            # Ensure proper time spacing between notes and chords
            self.chord_track.append(Message('note_off', note=chord[0].pitch, velocity=0, time=480))  # Move to next note timing

    def save_file(self):
        self.mid.save(self.filename)


##MAIN##
def main():
    print("Running Musigen \n")
    scale_name = input("Decide Scale From \nC Ionian \nD Dorian \nE Phrygian \nF Lydian \nG Mixolydian \nA Aeolian \nB Locrian \n: ")
    length = int(input("Decide Length of Melody 4-32 Notes: "))

    scale = Scale(scale_name.split()[0], scale_name.split()[1])
    melody_generator = MelodyGenerator(scale, length)
    melody = melody_generator.generate_melody()

    chord_generator = ChordGenerator(melody, scale)
    chords = chord_generator.generate_chords()

    midi_manager = MIDIFileManager()
    midi_manager.write_melody(melody)
    midi_manager.write_chords(melody, chords)
    midi_manager.save_file()

if __name__ == "__main__":
    main()

