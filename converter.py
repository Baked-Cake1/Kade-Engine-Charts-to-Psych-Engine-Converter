import json
import argparse
import os


def format_num(val):
    """
    Converts numbers like 4.0 to 4 to match Psych Engine's cleaner JSON style.
    Leaves floats like 1.3 unchanged.
    """
    if isinstance(val, (float, int)):
        return int(val) if val == int(val) else val
    return val

def convert_kade_to_psych(kade_data):
    kade_song = kade_data.get("song", {})
    psych_song = {}

    # 1. Copy over base properties
    for key, value in kade_song.items():
        if key not in ["notes", "lengthInSteps"]:
            psych_song[key] = value

    # 2. Add required Psych Engine properties
    psych_song.setdefault("events", [])
    psych_song.setdefault("gfVersion", None)
    psych_song["format"] = "psych_v1_convert"

    # 3. Format numeric properties (e.g., bpm: 100.0 -> 100)
    for key in ["bpm", "speed"]:
        if key in psych_song:
            psych_song[key] = format_num(psych_song[key])

    psych_notes = []

    # 4. Process each section and its notes
    for section in kade_song.get("notes", []):
        psych_section = {}
        must_hit = section.get("mustHitSection", False)

        # Copy other section properties (excluding legacy ones)
        for key, val in section.items():
            if key not in ["sectionNotes", "lengthInSteps"]:
                psych_section[key] = val

        # Convert Kade's `lengthInSteps` to Psych's `sectionBeats` (16 steps = 4 beats)
        length_in_steps = section.get("lengthInSteps", 16)
        psych_section["sectionBeats"] = format_num(length_in_steps / 4)
        
        # Ensure mustHitSection exists
        psych_section["mustHitSection"] = must_hit

        psych_section_notes = []
        for note in section.get("sectionNotes", []):
            if len(note) < 3:
                continue

            time = format_num(note[0])
            note_data = format_num(note[1])
            sustain = format_num(note[2])

            new_note_data = note_data

            # FNF ENGINE LOGIC DIFFERENCE:
            # Kade: 0-3 = Active Character, 4-7 = Other Character
            # Psych: 0-3 = ALWAYS Player, 4-7 = ALWAYS Opponent
            if not must_hit:
                # If it's the opponent's turn, Kade sets Opponent to 0-3 and Player to 4-7.
                # We shift this by 4 to map them properly to Psych's absolute layout.
                if isinstance(new_note_data, int) and 0 <= new_note_data <= 7:
                    new_note_data = (new_note_data + 4) % 8

            new_note = [time, new_note_data, sustain]

            if len(note) > 3:
                new_note.extend(note[3:])

            psych_section_notes.append(new_note)

        psych_section["sectionNotes"] = psych_section_notes
        psych_notes.append(psych_section)

    psych_song["notes"] = psych_notes

    return {"song": psych_song}


def main():
    parser = argparse.ArgumentParser(description="Convert Kade Engine FNF Charts to Psych Engine Format.")
    parser.add_argument("input", help="Path to the Kade Engine .json file")
    parser.add_argument("-o", "--output", help="Path for the output Psych Engine .json file (Optional)", default=None)

    args = parser.parse_args()
    input_path = args.input

    if not os.path.exists(input_path):
        print(f"Error: File '{input_path}' not found.")
        return

    output_path = args.output
    if not output_path:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}-psych{ext}"

    print(f"Reading '{input_path}'...")
    with open(input_path, 'r', encoding='utf-8') as f:
        try:
            kade_data = json.load(f)
        except json.JSONDecodeError:
            print("Error: Invalid JSON file.")
            return

    print("Converting data...")
    psych_data = convert_kade_to_psych(kade_data)

    print(f"Saving to '{output_path}'...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(psych_data, f, indent='\t')

    print("Conversion successful!")

if __name__ == "__main__":
    main()
