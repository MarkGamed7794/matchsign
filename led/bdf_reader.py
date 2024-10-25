# Converts a BDF to a binary matrix.

def read_font(filename: str) -> dict:
    characters = {
        "width": 0,
        "widths": {},
        "baseline": 0,
    }
    with open(filename, "r") as file:
        bounding_box = [0, 0, 0, 0]
        current_char = {
            "name": "",
            "codepoint": 0,
            "bitmap": [],
            "bounding_box": [0, 0, 0, 0],
            "advance": 0,
        }

        while True:
            line = file.readline()
            if(line == ""):
                break

            instruction, *arguments = line.strip().split(" ")
            #print(f"Instruction: {instruction} / Arguments: {str(arguments)}")

            if(instruction == "COMMENT"):
                # Comment, do nothing
                continue

            if(instruction == "STARTFONT"):
                # Font start
                continue

            if(instruction == "STARTCHAR"):
                current_char["name"] = arguments[0]
                continue

            if(instruction == "FONT_ASCENT"):
                characters["baseline"] = int(arguments[0])
                continue

            if(instruction == "ENCODING"):
                current_char["codepoint"] = int(arguments[0])
                continue

            if(instruction == "FONTBOUNDINGBOX"):
                bounding_box[0] = int(arguments[0])
                bounding_box[1] = int(arguments[1])
                bounding_box[2] = int(arguments[2])
                bounding_box[3] = int(arguments[3])
                continue

            if(instruction == "DWIDTH"):
                current_char["advance"] = int(arguments[0])

            if(instruction == "BBX"):
                current_char["bounding_box"][0] = int(arguments[0])
                current_char["bounding_box"][1] = int(arguments[1])
                current_char["bounding_box"][2] = int(arguments[2])
                current_char["bounding_box"][3] = int(arguments[3])

            if(instruction == "BITMAP"):
                current_char["bitmap"] = []

                dummy_lines_top = bounding_box[1] - current_char["bounding_box"][1] - (current_char["bounding_box"][3])

                while True:
                    if(dummy_lines_top > 0):
                        dummy_lines_top -= 1
                        bitmapline = "000000"
                    else:
                        bitmapline = file.readline().strip()
                    if(bitmapline == "ENDCHAR"):
                        break
                    #print(f"Bitmap: {bitmapline}")

                    current_char["bitmap"].append(
                        [int(x) for x in 
                        bin(int("1" + bitmapline, 16))[3:3+bounding_box[0]]]
                    )

                characters[chr(current_char["codepoint"])] = current_char["bitmap"]
                characters["widths"][chr(current_char["codepoint"])] = current_char["advance"]
                continue

        characters["width"] = bounding_box[0] + 1
    return characters