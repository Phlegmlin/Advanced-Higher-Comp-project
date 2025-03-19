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
                # Find the index of the current note in the scale
                try:
                    note_index = next(i for i, n in enumerate(scale_notes) if n.pitch == note.pitch)
                    # Calculate the index of the chord tone
                    chord_tone_index = note_index + interval
                    
                    if chord_tone_index < len(scale_notes):
                        # Note is within range, add it normally
                        chord.append(scale_notes[chord_tone_index])
                    else:
                        # Note would be out of range, find equivalent note an octave lower
                        # In MIDI, an octave is 12 semitones
                        lower_octave_pitch = scale_notes[chord_tone_index % len(scale_notes)].pitch - 12
                        
                        # Find a note with this pitch or create one if it doesn't exist
                        matching_note = next((n for n in scale_notes if n.pitch == lower_octave_pitch), None)
                        
                        if matching_note:
                            chord.append(matching_note)
                        else:
                            # Create a new note with adjusted pitch
                            # Extract note name from the out-of-range note
                            note_name = scale_notes[chord_tone_index % len(scale_notes)].name
                            new_note = Note(f"{note_name}(-1 oct)", lower_octave_pitch)
                            chord.append(new_note)
                except StopIteration:
                    # If the note is not found in the scale, just skip this interval
                    pass

            # Always add the chord, even if it's just a single note
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
        self.note_duration = 480  # Standard duration for notes

    def write_melody(self, melody):
        if not melody:
            return
            
        # First note starts at time=0
        self.melody_track.append(Message('note_on', note=melody[0].pitch, velocity=64, time=0))
        self.melody_track.append(Message('note_off', note=melody[0].pitch, velocity=64, time=self.note_duration))
        
        # Subsequent notes start after previous note ends
        for note in melody[1:]:
            self.melody_track.append(Message('note_on', note=note.pitch, velocity=64, time=0))
            self.melody_track.append(Message('note_off', note=note.pitch, velocity=64, time=self.note_duration))

    def write_chords(self, chords):
        if not chords:
            return
            
        # Process all chords
        for i, chord in enumerate(chords):
            # Turn on all notes in chord simultaneously
            for j, note in enumerate(chord):
                if j == 0 and i == 0:
                    # First note of first chord starts at time=0
                    self.chord_track.append(Message('note_on', note=note.pitch, velocity=64, time=0))
                else:
                    # All other notes start simultaneously with the first note
                    self.chord_track.append(Message('note_on', note=note.pitch, velocity=64, time=0))
            
            # Turn off all notes in chord simultaneously after note_duration
            for j, note in enumerate(chord):
                if j == 0:
                    # First note off carries the duration
                    self.chord_track.append(Message('note_off', note=note.pitch, velocity=64, time=self.note_duration))
                else:
                    # All other notes in the chord end at the same time
                    self.chord_track.append(Message('note_off', note=note.pitch, velocity=64, time=0))

    def save_file(self):
        self.mid.save(self.filename)


##MAIN##
def main():
    print("Running Musigen \n")
    scale_name = input("Enter scale (C Ionian, D Dorian, etc.): ")
    length = int(input("Enter melody length (4-32 notes): "))

    parts = scale_name.split()
    if len(parts) >= 2:
        root = parts[0]
        mode = " ".join(parts[1:])  # Handle mode names with spaces
    else:
        print("Invalid scale format. Using C Ionian as default.")
        root = "C"
        mode = "Ionian"

    scale = Scale(root, mode)
    melody_generator = MelodyGenerator(scale, length)
    melody = melody_generator.generate_melody()

    chord_generator = ChordGenerator(melody, scale)
    chords = chord_generator.generate_chords()

    midi_manager = MIDIFileManager()
    midi_manager.write_melody(melody)
    midi_manager.write_chords(chords)
    midi_manager.save_file()

    # Manual output formatting
    print(f"\nScale: {scale.root} {scale.mode}")
    print("Generated Melody:")
    for note in melody:
        print(f"{note.name} ({note.pitch})", end=" ")

    print("\nGenerated Chords:")
    for chord in chords:
        chord_notes = [f"{note.name} ({note.pitch})" for note in chord]
        print(chord_notes)

    print(f"\nMIDI file saved as {midi_manager.filename}")

if __name__ == "__main__":
    main()