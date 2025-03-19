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
            self.melody_track.append(Message('note_on', note=note.pitch, velocity=64, time=480))
            self.melody_track.append(Message('note_off', note=note.pitch, velocity=64, time=480))

    def write_chords(self, chords):
        for chord in chords:
            for note in chord:
                self.chord_track.append(Message('note_on', note=note.pitch, velocity=64, time=0))
            
            # Instead of time=0, match melody note duration (480)
            self.chord_track.append(Message('note_off', note=chord[0].pitch, velocity=64, time=480))

    def save_file(self):
        self.mid.save(self.filename)


##MAIN##
def main():
    print("Running Musigen \n")
    scale_name = input("Enter scale (C Ionian, D Dorian, etc.): ")
    length = int(input("Enter melody length (4-32 notes): "))

    scale = Scale(scale_name.split()[0], scale_name.split()[1])
    melody_generator = MelodyGenerator(scale, length)
    melody = melody_generator.generate_melody()  # ✅ Define melody before using it

    chord_generator = ChordGenerator(melody, scale)  # ✅ Now melody is defined
    chords = chord_generator.generate_chords()

    midi_manager = MIDIFileManager()
    midi_manager.write_melody(melody)
    midi_manager.write_chords(chords)  # ✅ Ensure chords are written
    midi_manager.save_file()

    # Manual output formatting
    print(f"\nScale: {scale.root} {scale.mode}")
    print("Generated Melody:")
    for note in melody:
        print(f"{note.name} ({note.pitch})", end=" ")

    print("\nGenerated Chords:")
    for chord in chords:
        print([f"{note.name} ({note.pitch})" for note in chord])

    print(f"\nMIDI file saved as {midi_manager.filename}")

if __name__ == "__main__":
    main()C 
