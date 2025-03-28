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

#Validate if scale exists in database
def scaleExists(scale_name):
    conn = dbConnection()
    cursor = conn.cursor()
    query = "SELECT COUNT(*) FROM Scales WHERE name = %s"
    cursor.execute(query, (scale_name,))
    result = cursor.fetchone()[0]
    conn.close()
    return result > 0
        
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
        self.notes = self.getNotes()

    def getNotes(self):
        conn = dbConnection()
        cursor = conn.cursor()
        query = """
        SELECT Notes.name, Notes.pitch FROM ScaleNotes
        JOIN Notes ON ScaleNotes.note_id = Notes.note_id
        JOIN Scales ON ScaleNotes.scale_id = Scales.scale_id
        WHERE Scales.name = %s
        ORDER BY Notes.pitch;
        """
        #Array of Objects
        cursor.execute(query, (f"{self.root} {self.mode}",))
        scale_notes = [Note(row[0], row[1]) for row in cursor.fetchall()]
        conn.close()
        return scale_notes

#Create MelodyGenerator Class
class MelodyGenerator:
    def __init__(self, scale, length):
        self.scale = scale
        self.length = length

    def generateMelody(self):
        return [random.choice(self.scale.notes) for _ in range(self.length)]

#Create ChordGenerator Class
class ChordGenerator:
    def __init__(self, melody, scale):
        self.melody = melody
        self.scale = scale
    #Array of Objects
    def generateChords(self):
        chords = []
        scale_notes = self.scale.notes
        for note in self.melody:
            chord = [note]
            for interval in [2, 4]:
                index = (scale_notes.index(note) + interval) % len(scale_notes)
                if 0 <= index < len(scale_notes):
                    chord.append(scale_notes[index])
            if len(chord) > 1:
                chords.append(self.bubblesortChord(chord))

        return chords
    #Advanced Higher Bubble Sort
    def bubblesortChord(self, chord):
        n = len(chord)
        swapped = True
        while swapped == True and n > 0:
            swapped = False
            for index in range(0, n-1):
                if chord[index].pitch > chord[index+1].pitch:
                    temp = chord[index]
                    chord[index] = chord[index+1]
                    chord[index+1] = temp
                    swapped = True
            n = n - 1
        return chord


#Create MIDIFileManager
class MIDIFileManager:
    def __init__(self, filename="musigen.mid"):
        self.filename = filename
        self.mid = MidiFile()
        self.melody_track = MidiTrack()
        self.chord_track = MidiTrack()
        self.mid.tracks.append(self.melody_track)
        self.mid.tracks.append(self.chord_track)

    def write_melody(self, melody):
        for note in melody:
            self.melody_track.append(Message('note_on', note=note.pitch, velocity=64, time=0))
            self.melody_track.append(Message('note_off', note=note.pitch, velocity=64, time=480))

    def write_chords(self, melody, chords):
        for i in range(len(melody)):
            chord = chords[i]
            
            
            for chord_note in chord:
                self.chord_track.append(Message('note_on', note=chord_note.pitch, velocity=64, time=0))

            
            for chord_note in chord:
                self.chord_track.append(Message('note_off', note=chord_note.pitch, velocity=64, time=0))
            
            
            self.chord_track.append(Message('note_off', note=chord[0].pitch, velocity=0, time=480))

    def save_file(self):
        self.mid.save(self.filename)


##MAIN##
def main():
    run = True
    while run:
        print("Musigen\n")
        scale_valid = False
        while not scale_valid:
            print("Available Scales:")
            print("C Ionian \nD Dorian \nE Phrygian \nF Lydian \nG Mixolydian \nA Aeolian \nB Locrian")
            scale_input = input("Enter scale: ")
            if len(scale_input.split()) == 2 and scaleExists(scale_input):
                scale_valid = True
            else:
                print("Error: Choose a Valid Scale")
        
        length_valid = False
        while not length_valid:
            length_input = input("Enter melody length (4-32): ")
            if length_input.isdigit():
                length = int(length_input)
                if 4 <= length <= 32:
                    length_valid = True
                else:
                    print("Error: Length must be between 4 and 32.")
            else:
                print("Error: Please enter a number.")
        
        root, mode = scale_input.split()[0], scale_input.split()[1]
        scale = Scale(root, mode)
        melody_generator = MelodyGenerator(scale, length)
        melody = melody_generator.generateMelody()

        chord_generator = ChordGenerator(melody, scale)
        chords = chord_generator.generateChords()

        midi_manager = MIDIFileManager()
        midi_manager.write_melody(melody)
        midi_manager.write_chords(melody, chords)
        midi_manager.save_file()
        
        print("MIDI file created as 'musigen.mid'")
        
        again = input("Generate another melody? (y/n): ")
        if again.lower() != "y":
            run = False
            print("Program Ended")

if __name__ == "__main__":
    main()