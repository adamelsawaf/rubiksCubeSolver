from copy   import deepcopy
from random import randint, choice
from typing import Any, Callable
from sys    import exit




# All possible valid moves on a 3x3 Rubik's Cube (with variations of course, such as: R2, u', Fw3', M2', S3, x', Y3):


#  Uppercase face moves represent single-slice moves, and lowercase face movesrepresent double-slice moves.
POSSIBLE_FACE_MOVE_ROOTS    : tuple[str] = ("R", "U", "F", "L", "D", "B")

#  Only allowing uppercase slice moves.
POSSIBLE_SLICE_MOVE_ROOTS   : tuple[str] = ("M", "E", "S")

#  Allow uppercase or lowercase cube rotations.
POSSIBLE_CUBE_ROTATION_ROOTS: tuple[str] = ("x", "y", "z")

#  All possible (reduced) move stems, for any move.
POSSIBLE_MOVE_STEMS         : tuple[str] = ("" , "'", "2")




#  Color printing formatting using red-green-blue pixel values.
def formatRGB(r: int, g: int, b: int) -> str:
    if((type(r) == int) and (r >= 0)):
        if((type(g) == int) and (g >= 0)):
            if((type(b) == int) and (b >= 0)):
                return f"\033[38;2;{r};{g};{b}m"
            else:
                raise ValueError(f"formatRBG:\n\tparameter b: \"{str(b)}\" is not a non-negative integer.")
        else:
            raise ValueError(f"formatRBG:\n\tparameter g: \"{str(g)}\" is not a non-negative integer.")
    else:
        raise ValueError(f"formatRBG:\n\tparameter r: \"{str(r)}\" is not a non-negative integer.")


#  Formatting strings for printing to the console.
DEFAULT  : str = "\033[0m"
BOLD     : str = "\033[1m"
ITALICS  : str = "\033[3m"
UNDERLINE: str = "\033[4m"
CROSSED  : str = "\033[9m"

#  Integer abstractions for colors and faces of a cube object.
WHITE : int = (UP    := 0)
ORANGE: int = (LEFT  := 1)
GREEN : int = (FRONT := 2)
RED   : int = (RIGHT := 3)
BLUE  : int = (BACK  := 4)
YELLOW: int = (DOWN  := 5)

#  Standard RBG values for printing out cube states in colorblind mode.
W: str = formatRGB(255, 255, 255)     #  white
O: str = formatRGB(255, 165,   0)     #  orange
G: str = formatRGB(  0, 255,   0)     #  green
R: str = formatRGB(255,   0,   0)     #  red
B: str = formatRGB(  0,   0, 255)     #  blue
Y: str = formatRGB(255, 255,   0)     #  yellow

#  FLIP_COLOR[i] is equal to the number representing the face of the cube opposite of the face represented by i,
#  so FLIP_COLOR[i] is equal to FLIP_COLOR[FLIP_COLOR[i]] for i in len(FLIP_COLOR).
FLIP_COLOR: list[int] = [5, 3, 4, 1, 2, 0]

#  A tuple of all corner pieces on the cube, as tuples.
CORNERS   : tuple[tuple[int]] = \
(
    (WHITE , BLUE  , RED    ),
    (WHITE , ORANGE, BLUE   ),
    (WHITE , GREEN , ORANGE ),
    (WHITE , RED   , GREEN  ),

    (YELLOW, GREEN , RED   ),
    (YELLOW, ORANGE, GREEN ),
    (YELLOW, BLUE  , ORANGE),
    (YELLOW, RED   , BLUE  )
)


#  The list representing the solved state of a cube object.
SOLVED_CUBE: list[list[int]] = \
[
    [WHITE]  * 9,
    [ORANGE] * 9,
    [GREEN]  * 9,
    [RED]    * 9,
    [BLUE]   * 9,
    [YELLOW] * 9
]


#  Useful tuples for printing out the state of a cube.
EMOJI_SQUARES  :    tuple[str] = ("⬜",   "🟧",    "🟩",    "🟥",   "🟦",   "🟨")
RGB_COLORS     :    tuple[str] = ( W,       O,        G,       R,       B,      Y)
STR_COLORS     :    tuple[str] = ("W",     "O",      "G",     "R",     "B",    "Y")
STR_COLORS_FULL:    tuple[str] = ("white", "orange", "green", "red",   "blue", "yellow")
FACES          :    tuple[str] = ("Up",    "Left",   "Front", "Right", "Back", "Down")


#  A dictionary used for flipping a move across it's perpendicular axis.
FLIP_MOVE: dict[str, str] = \
{
    "R": "L",
    "U": "D",
    "F": "B"
}

#  To make FLIP_MOVE a "two-way" dictionary.
for key in FLIP_MOVE.copy():
    FLIP_MOVE[FLIP_MOVE[key]] = key


#  A dictionary used to rotate a slice move using a cube rotation.
CUBE_ROTATE_FACE: dict[str, dict[str, str]] = \
{
    "R":
        {
            "y": "F",
            "z": "D",
        },

    "U": 
        {
            "x": "B",
            "z": "R",
        },

    "F": 
        {
            "x": "U",
            "y": "L",
        },
}


#  A dictionary used to simplify a set of moves in a sequence of moves to a single cube rotation.
REVEAL_ROTATIONS_DICTIONARY: dict[tuple[str], str] = \
{
    ("L' M' R",    "Rw L'",  "Lw' R",    "r L'",  "l' R") :  "x",
    ("L M R'",     "Rw' L",   "r' L",   "Lw R'",  "l R'") :  "x'",
    ("L2 M2 R2",  "Rw2 L2",  "r2 L2",  "Lw2 R2",  "l2 R2"):  "x2",

    ("U E' D'",   "Uw D'",   "u D'",   "Dw' U",   "d' U") :  "y",
    ("U' E D",    "Uw' D",   "u' D",   "Dw U'",   "d U'") :  "y'",
    ("U2 E2 D2",  "Uw2 D2",  "u2 D2",  "Dw2 U2",  "d2 U2"):  "y2",

    ("F S B'",    "Fw B'",   "f B'",   "Bw' F",   "b' F") :  "z",
    ("F' S' B",   "Fw' B",   "f' B",   "Bw F'",   "b F'") :  "z'",
    ("F2 S2 B2",  "Fw2 B2",  "f2 B2",  "Bw2 F2",  "b2 F2"):  "z2"
}


#  A dictionary used to simply a set of moves in a sequence of moves to fewer moves,
#  using many wide moves, slice moves, and cube rotations.
SIMPLIFY_CLEANUP_DICTIONARY: dict[tuple[str], str] = \
{
    ("L' R x'" , "r' R" , "Rw' R" , "l L'" , "Lw L'")  : "M" ,
    ("L R' x"  , "r R'" , "Rw R'" , "l' L" , "Lw' L")  : "M'",
    ("L2 R2 x2", "r2 R2", "Rw2 R2", "l2 L2", "Lw2 L2") : "M2",
        
    ("R r L l"    , "R r L Lw"    , "R Rw L l"    , "R Rw L Lw"    ,
     "R' r' L' l'", "R' r' L' Lw'", "R' Rw' L' l'", "R' Rw' L' Lw'") : "R2 L2",
    

    ("U D' y'" , "u' U" , "Uw' U" , "d D'" , "Dw D'")  : "E" ,
    ("U' D y"  , "u U'" , "Uw U'" , "d' D" , "Dw' D")  : "E'",
    ("U2 D2 y2", "u2 U2", "Uw2 U2", "d2 D2", "Dw2 D2") : "E2",

    ("U u D d"      , "U u D Dw"    , "U Uw D d"    , "U Uw D Dw"    ,
     "U' u' D' d'"  , "U' u' D' Dw'", "U' Uw' D' d'", "U' Uw' D' Dw'") : "U2 D2",


    ("B F' z"  , "f F'" , "Fw F'" , "b' B" , "Bw' B")  : "S" ,
    ("B' F z'" , "f' F" , "Fw' F" , "b B'" , "Bw B'")  : "S'",
    ("B2 F2 z2", "f2 F2", "Fw2 F2", "b2 B2", "Bw2 B2") : "S2",

    ("F f B b"      , "F f B Bw"    , "F Fw B b"    , "F Fw B Bw"    ,
     "F' f' B' b'"  , "F' f' B' Bw'", "F' Fw' B' b'", "F' Fw' B' Bw'")  : "F2 B2",



    ("L2 M' R" ,) : "L' x",
    ("L M' R"  ,) : "L2 x",
    ("L' M2 R" ,) : "M' x",
    ("L' M R"  ,) : "M2 x",
    ("L' M' R2",) : "R x" ,
    ("L' M' R'",) : "R2 x",

    ("L2 M R'" ,) : "L x'" ,
    ("L' M R'" ,) : "L2 x'",
    ("L M2 R'" ,) : "M x'" ,
    ("L M' R'" ,) : "M2 x'",
    ("L M R2"  ,) : "R' x'",
    ("L M R"   ,) : "R2 x'",

    ("L M2 R2" ,) : "L' x2",
    ("L' M2 R2",) : "L x2" ,
    ("L2 M' R2",
     "L' R x"  ,
     "L l r2"  , "L l Rw2"  , "L Lw r2"  , "L Lw Rw2"  ,
     "l2 R' r'", "l2 R' Rw'", "Lw2 R' r'", "Lw2 R' Rw'",
     "R2 L' l'", "R2 L' Lw'",
     "L2 R r"  , "L2 R Rw")     : "M x2" ,
    ("L2 M2 R" ,) : "R' x2",
    ("L2 M2 R'",) : "R x2" ,

    ("U2 E' D'",) : "U y" ,
    ("U' E' D'",) : "U2 y",
    ("U E2 D'" ,) : "E' y",
    ("U E D'"  ,) : "E2 y",
    ("U E' D2" ,) : "D' y",
    ("U E' D"  ,) : "D2 y",

    ("U2 E D"  ,) : "U' y'",
    ("U E D"   ,) : "U2 y'",
    ("U' E2 D" ,) : "E y'" ,
    ("U' E' D" ,) : "E2 y'",
    ("U' E D2" ,) : "D y'" ,
    ("U' E D'" ,) : "D2 y'",

    ("U E2 D2" ,) : "U' y2",
    ("U' E2 D2",) : "U y2" ,
    ("U2 E2 D2",
     "U' D y'" ,
     "u2 D' d'", "u2 D' Dw'", "Uw2 D' d'", "Uw2 D' Dw'",
    "d2 U u"   , "d2 U Uw"  , "Dw2 U u"  , "Dw2 U Uw"  ,
    "D2 U' u'" , "D2 U' Uw'",
    "U2 D d"   , "U2 D Dw") : "E' y2",
    ("U2 E' D2",
     "U D' y" ,
     "u2 D d" , "u2 D Dw"  , "Uw2 D d"  , "Uw2 D Dw"  ,
    "d2 U' u'", "d2 U' Uw'", "Dw2 U' u'", "Dw2 U' Uw'",
    "D2 U u", "D2 U Uw",
    "U2 D' d'", "U2 D' Dw'") : "E y2" ,
    ("U2 E2 D" ,) : "D' y2",
    ("U2 E2 D'",) : "D y2" ,

    ("F2 S B'" ,) : "F z" ,
    ("F' S B'" ,) : "F2 z",
    ("F S2 B'" ,) : "S z" ,
    ("F S' B'" ,) : "S2 z",
    ("F S B2"  ,) : "B' z",
    ("F S B"   ,) : "B2 z",

    ("F2 S' B" ,) : "F' z'",
    ("F S' B"  ,) : "F2 z'",
    ("F' S2 B" ,) : "S' z'",
    ("F' S B"  ,) : "S2 z'",
    ("F' S' B2",) : "B z'" ,
    ("F' S' B'",) : "B2 z'",

    ("F S2 B2" ,) : "F' z2",
    ("F' S2 B2",) : "F z2" ,
    ("F2 S B2",
     "B' F z" ,
     "f2 B b"  , "f2 B Bw"  , "Fw2 B b"  , "Fw2 B Bw"  ,
     "b2 F' f'", "b2 F' Fw'", "Bw2 F' f'", "Bw2 F' Fw'",
     "F2 B' b'", "F2 B' Bw'",
     "B2 F f"  , "B2 F Fw") : "S' z2",
    ("F2 S' B2",
     "B F' z'" ,
     "f2 B' b'", "f2 B' Bw'", "Fw2 B' b'", "Fw2 B' Bw'",
     "b2 F f"  , "b2 F Fw"  , "Bw2 F f"  , "Bw2 F Fw"  ,
     "F2 B b"  , "F2 B Bw"  ,
     "B2 F' f'", "B2 F' Fw'") : "S z2",
    ("F2 S2 B" ,) : "B' z2",
    ("F2 S2 B'",) : "B z2" ,


    ("L x"  , "R M'")  : "r" ,
    ("L' x'", "R' M")  : "r'",
    ("L2 x2", "R2 M2") : "r2",

    ("R x'" , "L M")   : "l" ,
    ("R' x" , "L' M'") : "l'",
    ("R2 x2", "L2 M2") : "l2",

    ("D y"  , "U E'")  : "u" ,
    ("D' y'", "U' E")  : "u'",
    ("D2 y2", "U2 E2") : "u2",

    ("U y'" , "D E")   : "d" ,
    ("U' y" , "D' E'") : "d'",
    ("U2 y2", "D2 E2") : "d2",

    ("B z"  , "F S")   : "f" ,
    ("B' z'", "F' S'") : "f'",
    ("B2 z2", "F2 S2") : "f2",

    ("F z'" , "B S'")  : "b" ,
    ("F' z" , "B' S")  : "b'",
    ("F2 z2", "B2 S2") : "b2",


    ("L' R x2" ,) : "M x"  ,
    ("L R' x2" ,) : "M' x'",
    ("L R' x'"   ,
     "L2 M R2"   ,
     "L' l' r2"  , "L' l' Rw2", "L' Lw' r2", "L' Lw' Rw2",
     "l2 R r"    , "l2 R Rw"  , "Lw2 R r"  , "Lw2 R Rw"  ,
     "R2 L l"    , "R2 L Lw"  ,
     "L2 R' r'"  , "L2 R' Rw'") : "M' x2",
    ("L2 R2 x'",) : "M2 x" ,
    ("L2 R2 x'",) : "M2 x" ,

    ("U D' y2" ,) : "E y'" ,
    ("U' D y2" ,) : "E' y" ,
    ("U2 D2 y'",) : "E2 y" ,
    ("U2 D2 y" ,) : "E2 y'",

    ("B F' z2" ,) : "S z"  ,
    ("B' F z2" ,) : "S' z'",
    ("B2 F2 z'",) : "S2 z" ,
    ("B2 F2 z" ,) : "S2 z'",


    ("r M"  ,): "R" ,
    ("r' M'",): "R'",
    ("r2 M2",): "R2",

    ("l M'" ,): "L" ,
    ("l' M" ,): "L'",
    ("l2 M2",): "L2",

    ("u E"  ,): "U" ,
    ("u' E'",): "U'",
    ("u2 E2",): "U2",

    ("d E'" ,): "D" ,
    ("d' E" ,): "D'",
    ("d2 E2",): "D2",

    ("f S'" ,): "F" ,
    ("f' S" ,): "F'",
    ("f2 S2",): "F2",

    ("b S"  ,): "B" ,
    ("b' S'",): "B'",
    ("b2 S2",): "B2"
}


#  Returns whether a given string is a valid face move or not.
def isValidFaceMove(move: str) -> bool:
    if(type(move) != str):
        return False
    elif(((m := move.strip()) != "") and (m[0] + m[-1] == "()")):
        return isValidFaceMove(m[1: -1])
    else:
        def isValidFaceMove_helper(move: str) -> bool:
            if(move == ""):
                return True

            elif((type(move) != str) or (move[0].upper() not in POSSIBLE_FACE_MOVE_ROOTS)):
                return False
            
            elif(len(move) == 2):
                return (move[1] == "2") or (move[1] == "3") or ((move[0] in POSSIBLE_FACE_MOVE_ROOTS) and (move[1] == "w"))
            
            elif(len(move) == 3):
                return (move[0] in POSSIBLE_FACE_MOVE_ROOTS) and (move[1] == "w") and ( (move[2] == "2") or (move[2] == "3") )
            
            else:
                return (len(move) == 1)

        if((m[len(m) - 1:] == "'") and (m != "'")):
            return isValidFaceMove_helper(m[:len(m) - 1])
        else:
            return isValidFaceMove_helper(m)

#  Returns whether a given string is a valid slice move or not.
def isValidSliceMove(move: str) -> bool:
    if((type(move) == str) and ((m := move.strip()) != "") and (m[0] + m[-1] == "()")):
        return isValidSliceMove(m[1: -1])
    else:
        return (type(move) == str) and \
            (
                    ((moveTrimmed := move.strip()) == "") or \
                    (
                        (moveTrimmed[0] in POSSIBLE_SLICE_MOVE_ROOTS) and \
                            (
                                (moveTrimmed[1:] == "") or (moveTrimmed[1:] == "'") or (moveTrimmed[1:] == "2") or \
                                (moveTrimmed[1:] == "3") or (moveTrimmed[1:] == "2'") or (moveTrimmed[1:] == "3'") \
                            )
                    )
            )

#  Returns whether a given string is a valid cube rotation or not.
def isValidCubeRotation(move: str) -> bool:
    if(type(move) != str):
        return False
    elif(((m := move.strip()) != "") and (m[0] + m[-1] == "()")):
        return isValidSliceMove(m[1: -1])
    elif(m == ""):
        return True
    elif(m[0].lower() not in POSSIBLE_CUBE_ROTATION_ROOTS):
        return False
    elif(len(m) == 2):
        return (m[1] == "'") or (m[1] == "2") or (m[1] == "3")
    elif(len(m) == 3):
        return ((m[1] == "2") or (m[1] == "3")) and (m[2] == "'")
    else:
        return (len(m) == 1)


#  Concatenates a list of strings into a single string.
def concatenateStringList(L: list[str], separator: str = " ") -> str:
    if(type(L) != list):
        raise TypeError(f"concatenateStringList:\n\tparameter L: \"{str(L)}\" is not a list.")
    elif(type(separator) != str):
        raise TypeError(f"concatenateStringList:\n\tparameter separator: \"{str(separator)}\" is not a string.")
    elif(L == []):
        return ""
    elif(type(L[0]) != str):
        raise TypeError(f"concatenateStringList:\n\tin parameter L: \"{str(L[0])}\" is not a string.")
    else:
        return L[0] + (separator if(len(L) > 1) else "") + concatenateStringList(L[1:], separator)


#  Returns whether a given string is a valid move or not, including parentheses.
def isValidMove(move: str) -> bool:
    return isValidFaceMove(move) or isValidSliceMove(move) or isValidCubeRotation(move)


#  Returns the non-negative index of the first occurence of a value in a list,
#  or -1 if the value does not occur in the list.
def firstOccurenceInList_index(L: list, x: Any) -> int:
    if(type(L) != list):
        raise TypeError(f"FirstOccurenceInList_index:\n\tparameter L: \"{str(L)}\" is not a list.")
    elif(x in L):
        return L.index(x)
    else:
        return -1


#  Returns the positive index of the matching closing parenthesis ")" to the first open
#  parenthesis "(" in a string or list. Returns -1 if the matching ")" is not found in the string.
def matchingCloseParen_index(s: str | list) -> int:
    if(type(s) not in [str, list]):
        raise TypeError(f"matchingCloseParen_index:\n\tparameter s: \"{str(s)}\" is not a string or list.")
    if(firstOccurenceInList_index(list(s), "(") == -1):
        return - 1
    else:
        parenBalance: int = 1
        for i in range(s.index("(") + 1, len(s)):
            parenBalance +=   (1 if(s[i] == "(") else (-1 if(s[i] == ")") else 0))
            if(parenBalance == 0):
                return i
        
        return -1


# Returns whether a given string is a valid sequence of moves or not, including parentheses.
def areValidMoves(moves: str) -> bool:
    if(type(moves) != str):
        raise TypeError(f"areValidMoves:\n\tparameter moves: \"{str(moves)}\" is not a string.")
    elif(len(tokens := moves.replace("(", " ( ").replace(")", " ) ").split()) <= 1):
        return isValidMove(moves)
    elif((ms := moves.strip()).count("(")   !=   ms.count(")")):
        return False
    elif("(" in ms):
        openParen_index : int = ms.index("(")
        closeParen_index: int = matchingCloseParen_index(ms)

        return areValidMoves(ms[:openParen_index]) and  \
               areValidMoves(ms[openParen_index + 1: closeParen_index]) and  \
               areValidMoves(ms[closeParen_index + 1:])
    else:
        return areValidMoves(tokens[0]) and areValidMoves(concatenateStringList(tokens[1:])) 


#  Splits a move into a list of length two, first containting its root, and second containing its stem.
def moveSplit(move: str) -> list[str]:
    if(not isValidMove(move)):
        raise ValueError(f"moveSplit:\n\tparameter move: \"{str(move)}\" is not a valid move.")
    elif(((ms := move.strip()) == "") or ("w" in move)):
        return [ms[:2], ms[2:]]
    else:
        return [ms[0], ms[1:]]


#  Returns whether a given string is a valid move root or not.
def isValidMoveRoot(root: str) -> bool:
    return (type(root) == str) and  \
           (
                ((rt := root.strip()) == "") or  \
                (rt.upper() in POSSIBLE_FACE_MOVE_ROOTS) or  \
                (rt in POSSIBLE_SLICE_MOVE_ROOTS) or  \
                (rt.lower() in POSSIBLE_CUBE_ROTATION_ROOTS) or  \
                ((rt[0].upper() == rt[0]) and (rt[1:] == "w"))
           )

#  Returns whether a given string is a valid move stem or not.
def isValidMoveStem(stem: str) -> bool:
    if(type(stem) != str):
        raise TypeError(f"isValidMoveStem:\n\tparameter stem: \"{str(stem)}\" is not a string.")
    
    tip: str = stem.strip()[1:]

    match stem.strip()[0:1]:      #  check the base of the stem of the move
        case("" | "2" | "3"):
            return (tip == "") or (tip == "'")
        case("'"):
            return (tip == "")
        case _:
            return False


#  Converts a move stem (a string) to an int representing that stem, which can be any from {-1, 1, 2}.
def moveStemToInt(stem: str) -> int:
    if(type(stem) != str):
        raise TypeError(f"moveStemToInt:\n\tparameter stem: \"{str(stem)}\" is not a string.")
    else:
        x: int

        if((s := stem.strip()) == ""):
            x = 1
        else:
            match s[0]:
                case("'" | "3"):
                    x = -1
                case("2"):
                    x = 2
                case _:
                    raise ValueError(f"moveStemToInt:\n\tparameter stem: \"{str(stem)}\" is not a valid move stem.")
                
        if(len(s) > 1):
            if(s[1:] == "'"):
                x *= -1
            else:
                raise ValueError(f"moveStemToInt:\n\tparameter stem: \"{str(stem)}\" is not a valid move stem.")
        
        return (x if (x != -2) else 2)

#  Converts an int (mod 4) to a move stem (a string).
def intToMoveStem(n: int) -> str:
    if(type(n) != int):
        raise TypeError(f"intToMoveStem:\n\tparameter n: \"{str(n)}\" is not an int.")
    else:
        match(n % 4):
            case(0 | 1):
                return ""
            case(2):
                return "2"
            case(3):
                return "'"
            case _:
                raise ValueError(f"intToMoveStem:\n\tparameter n: \"{str(n)}\" is not a valid int.")


#  Returns whether two given strings are equivalent move roots
#  (this is mostly for dealing with the two different ways to write wide moves, 
#  for example "r" and "Rw").
def areEquivalentMoveRoots(root0: str, root1: str) -> bool:
    if(not isValidMoveRoot(root0)):
         raise ValueError(f"areEquivalentMoveRoots:\n\tparameter root0: \"{str(root0)}\" is not a valid move root.")
    elif(not isValidMoveRoot(root1)):
         raise ValueError(f"areEquivalentMoveRoots:\n\tparameter root1: \"{str(root1)}\" is not a valid move root.")
    else:
        return (root0 == root1) or \
               (isValidCubeRotation(root0) and isValidCubeRotation(root1) and (root0.lower() == root1.lower())) or \
               (
                   (root0[0:1].lower() == root1[0:1].lower()) and \
                       (
                           ((root0.lower() == root0) and ("w" in root1)) or \
                           (("w" in root0) and (root1.lower() == root1)) \
                       )
               )


#  Returns whether two given strings are equivalent moves
#  (this is mostly for dealing with the two different ways to write wide moves, 
#  for example "r" and "Rw").
def areEquivalentMoves(move0: str, move1: str) -> bool:
    if(not isValidMove(move0)):
         raise ValueError(f"areEquivalentMoves:\n\tparameter move0: \"{str(move0)}\" is not a valid move.")
    elif(not isValidMove(move1)):
         raise ValueError(f"areEquivalentMoves:\n\tparameter move1: \"{str(move1)}\" is not a valid move.")
    else:
        ms0: list[str] = moveSplit(move0)
        ms1: list[str] = moveSplit(move1)
        return areEquivalentMoveRoots(ms0[0], ms1[0]) and (moveStemToInt(ms0[1]) == moveStemToInt(ms1[1]))


#  Takes two moves and combines them into a single move, for example
#  R + R2 -> R'. If the two moves cannot be combined as like terms like this, then the
#  two strings are just trimmed and then concatenated together with a space in between.
def combineTwoMoves(move0: str, move1: str) -> str:
    if(not isValidMove(move0)):
        raise ValueError(f"combineTwoMoves:\n\tparameter move0: \"{str(move0)}\" is not a valid move.")
    elif(not isValidMove(move1)):
        raise ValueError(f"combineTwoMoves:\n\tparameter move1: \"{str(move1)}\" is not a valid move.")
    elif(move0 != move0.strip()):
        return combineTwoMoves(move0.strip(), move1)
    elif(move1 != move1.strip()):
        return combineTwoMoves(move0, move1.strip())
    elif((set(move0.replace(" ", "").replace("\n", "").replace("\t", "")) in [{}, {"(", ")"}]) or  \
         (set(move1.replace(" ", "").replace("\n", "").replace("\t", "")) in [{}, {"(", ")"}])):
        return move0 + move1
    elif((move0[0] + move0[-1]) == "()"):
        return combineTwoMoves(move0[1: -1], move1)
    elif((move1[0] + move1[-1]) == "()"):
        return combineTwoMoves(move0, move1[1: -1])
    elif(not areEquivalentMoveRoots(moveSplit(move0)[0], moveSplit(move1)[0])):
        return (move0.strip() + " " + move1.strip()).strip()
    else:
        root0: str = moveSplit(move0)[0]
        root1: str = moveSplit(move1)[0]
        stem0: str = moveSplit(move0)[1]
        stem1: str = moveSplit(move1)[1]
        newStemNumber: int = moveStemToInt(stem0) + moveStemToInt(stem1)
        newRoot: str
        if((newStemNumber % 4) != 0):
            if(
                   (
                       (root0[0:1].lower() == root1[0:1].lower()) and \
                            (
                                ((root0.lower() == root0) and ("w" in root1)) or \
                                (("w" in root0) and (root1.lower() == root1)) \
                            )
                   )
              ):
                newRoot = root0
            elif( (isValidCubeRotation(move0) and isValidCubeRotation(move1) and (root0.lower() == root1.lower())) ):
                newRoot = move0[0]
            else:
                newRoot = root0
            return newRoot + intToMoveStem(newStemNumber)
        else:
            return ""

#  Combines all adjacent like terms in a sequence of moves.
def combineMoves(moves: str) -> str:
    if(not areValidMoves(moves)):
        raise ValueError(f"combineMoves:\n\tparameter moves: \"{str(moves)}\" are not valid moves.")
    elif((tokens := moves.replace("(", " ").replace(")", " ").split())     ==     []):
        return ""
    elif(len(tokens) == 1):
        return tokens[0]
    else:
        combineFirstTwo: str = combineTwoMoves(tokens[0], tokens[1])
        if(len(combineFirstTwo.split()) == 2):
            return tokens[0] + " " + combineMoves(concatenateStringList(tokens[1:])).strip()
        else:
            return combineMoves(combineFirstTwo + " " + concatenateStringList(tokens[2:])).strip()


#  Takes an unary move operator and a sequence of moves (a string), maps
#  the operator to every move in the string, and returns the new string.
#  Parentheses in the move sequence are ignored.
def mapMoves(func: Callable[[str], str], moves: str) -> str:
    if(not callable(func)):
        raise TypeError(f"mapMove:\n\tparameter func: \"{str(func)}\" is not a valid function.")
    elif(not areValidMoves(moves)):
        raise ValueError(f"mapMove:\n\tparameter moves: \"{str(moves)}\" are not valid moves.")
    elif(set(moves.replace(" ", "").replace("\n", "").replace("\t", "")) in [{}, {"(", ")"}]):
        return ""
    else:
        tokens: list[str] = moves.replace("(", " ( ").replace(")", " ) ").split()
        result: str = ""
        for move in tokens:
            result += (func(move) if(move not in "()") else move) + " "
        return cleanUpSpacing(result)


#  Reverses the order of a sequence of moves (a string).
def reverseMoves(moves: str) -> str:
    if(not areValidMoves(moves)):
        raise ValueError(f"reverseMoves:\n\tparameter moves: \"{str(moves)}\" are not valid moves.")
    else:
        result: str = ""
        for move in moves.replace("(", " ( ").replace(")", " ) ").split():
            result = move + " " + result
        return cleanUpSpacing(result.replace("(", "🟩").replace(")", "(").replace("🟩", ")"))


#  Reduces a move to its lowest possible stem, for example R3' -> R.
#  If a move is already reduced, it just trims it.
def reduceMove(move: str) -> str:
    if(not isValidMove(move)):
        raise ValueError(f"reduceMove:\n\tparameter move: \"{str(move)}\" is not a valid move.")
    else:
        moveList: list[str] = moveSplit(move)
        root: str = moveList[0]
        stem: str = moveList[1]

        match stem:
            case "2'":
                return root + "2"
            case "3":
                return root + "'"
            case "3'":
                return root
            case _:
                return move.strip()

#  Reduces a sequence of moves (a string) to their lowest possible stems.
def reduceMoves(moves: str) -> str:
    return mapMoves(reduceMove, moves)

#  "Unreduces" a move to its highest possible stem, for example R -> R3'.
#  If a move is already unreduced, it just trims it.
def unreduceMove(move: str) -> str:
    if(not isValidMove(move)):
        raise ValueError(f"unreduceMove:\n\tparameter move: \"{str(move)}\" is not a valid move.")
    elif(move.strip() == ""):
        return ""
    else:
        moveList: list[str] = moveSplit(move)
        root: str = moveList[0]
        stem: str = moveList[1]

        match stem:
            case "":
                return root + "3'"
            case "'":
                return root + "3"
            case "2":
                return root + "2'"
            case _:
                return move.strip()

#  "Unreduces" a sequence of moves (a string) to their highest possible stems.
def unreduceMoves(moves: str) -> str:
    return mapMoves(unreduceMove, moves)


#  Returns the inverse of a move, preserving any unreduced stems (for inverting possible finger tricks as well).
def invertMove(move: str) -> str:
    if(not isValidMove(move)):
        raise ValueError(f"invertMove:\n\tparameter move: \"{str(move)}\" is not a valid move.")
    elif(((ms := move.strip()) != "") and (ms[0] + ms[-1] == "()")):
        return move[1: -1]
    elif(ms == ""):
        return ""
    elif(ms[-1] == "'"):
        return ms[: -1]
    else:
        return ms + "'"


#  Returns the inverse of a sequence of moves (a string), inverting each move individually, 
#  then reversing the order of the entire sequence.
def invertMoves(moves: str) -> str:
    return reverseMoves(mapMoves(invertMove, moves))

#  Cleans up the spacing between moves in a string of moves, including parentheses, one space between each move.
def cleanUpSpacing(moves: str) -> str:
    if(not areValidMoves(moves)):
        raise ValueError(f"cleanUpSpacing:\n\tparameter moves: \"{str(moves)}\" are not valid moves.")
    else:
        def cleanUpSpacing_helper(moves: str) -> str:

            #  If the entire sequence of moves is surrounded by a pair of parentheses, remove them.
            if(((ms := moves.strip()) != "") and  \
               ((ms[0] + ms[-1]) == "()") and  \
               areValidMoves(mt := ms[1: -1])
              ):
                return cleanUpSpacing_helper(mt)

            else:
                #  Remove all pairs of parentheses that don't contain any moves inside them (only whitespace)
                ms = concatenateStringList(moves.replace("(", " ( ").replace(")", " ) ").split()).replace("( )", " ")

                #  Remove all pairs of parentheses that only contain exactly one move inside them
                tokens: list[str] = ms.replace("(", " ( ").replace(")", " ) ").split()
                i     : int       = firstOccurenceInList_index(tokens, "(")
                result: str       = concatenateStringList(tokens[:i])
                if(i != -1):
                    while(i < len(tokens)):
                        if((i < (len(tokens) - 2)) and (tokens[i] == "(") and (tokens[i + 1] not in "()") and (tokens[i + 2] == ")")):
                            result += " " + tokens[i + 1]
                            i += 3
                        else:
                            result += " " + tokens[i]
                            i += 1
                    ms = result     #  update ms

                #  Remove all redundant pairs of parentheses, for ex:
                #  ((R U R' U')) F2   ->   (R U R' U') F2
                tokens: list[str] = ms.replace("(", " ( ").replace(")", " ) ").split()
                i     : int       = firstOccurenceInList_index(tokens, "(")
                result: str       = concatenateStringList(tokens[:i])
                if(i != -1):
                    while(i < len(tokens)):
                        if((tokens[i] == "(") and (tokens[i + 1] == "(") and  \
                        (tokens[(cp := matchingCloseParen_index(tokens[i:]) + i) - 1] == ")")):
                           result += " " + concatenateStringList(tokens[i + 1: cp])
                           i = cp + 1
                        else:
                            result += " " + tokens[i]
                            i += 1
                    ms = result     #  update ms

                #  Finally, tidy up all the spacing between moves and parentheses before returning the sequence of moves.
                result = ""
                for move in ms.replace("(", " ( ").replace(")", " ) ").split():
                    if((result[-1:] != "(") and (move != ")")):
                        result += " "
                    result += move
                
                return result

        #  Keep repeating the algorithm until the sequence of moves containts the least number of parentheses
        #  ( to remove all unnecessary parentheses, included repeated ones like "(((R U))) L" ).
        result: str = cleanUpSpacing_helper(moves)
        while(result.count("(") > cleanUpSpacing_helper(result).count("(")):
            result = cleanUpSpacing_helper(result)


        return result.strip()


#  Returns the axis on which a move operates on, returns one of {"R", "U", "F", "RUF"}.
#  "RUF" is returned if and only if the move simplifies to the identity move.
def moveAxis(move: str) -> str:
    if(not isValidMove(move)):
        raise ValueError(f"moveAxis:\n\tparameter move: \"{str(move)}\" is not a valid move.")
    elif(((m := move.strip()) != "") and (m[0] + m[-1] == "()")):
        return moveAxis(m[1: -1])
    elif(m == ""):
        return "RUF"
    else:
        match moveSplit(m)[0][0].upper():
            case "R" | "L" | "M" | "X":
                return "R"
                
            case "U" | "D" | "E" | "Y":
                return "U"
            
            case _:     #  case "F" | "B" | "S" | "Z":
                return "F"


#  Flips a move across its perpendicular axis.
def flipMove(move: str) -> str:
    if(not isValidMove(move)):
        raise ValueError(f"flipMove:\n\tparameter move: \"{str(move)}\" is not a valid move.")
    elif(((m := move.strip()) != "") and (m[0] + m[-1] == "()")):
        return flipMove(m[1: -1])
    elif(m == ""):
        return ""
    else:
        m_root:     str  = moveSplit(m)[0]
        m_stem:     str  = moveSplit(m)[1]
        lowercase:  bool = (m == m.lower())
        has_w:      bool = (m_root[-1] == "w")
        
        if(isValidFaceMove(m)):
            resultRoot: str = FLIP_MOVE[m_root[0].upper()]
            return   (resultRoot if(not lowercase) else resultRoot.lower())   +   ("" if(not has_w) else "w")   +   m_stem
        else:
            return invertMove(m)

#  Flips a string of moves across their respective perpendicular axes.
def flipMoves(moves: str) -> str:
    return mapMoves(flipMove, moves)


#  Given two moves, the first needed to be a cube rotation, this function returns the move
#  resulting from simplifying the following sequence of three moves: (rotation move rotation'),
#  where rotation' represents the inverse of the rotation.
def rotateMove(rotation: str, move: str) -> str:
    if(type(rotation) != str):
        raise TypeError(f"rotateMove:\n\tparameter rotation: \"{str(rotation)}\" is not a string.")
    elif(not isValidCubeRotation(rotation)):
        raise ValueError(f"rotateMoves:\n\tparameter rotation: \"{rotation}\" is not a valid cube rotation.")
    elif(not isValidMove(move)):
        raise ValueError(f"rotateMove:\n\tparameter move: \"{str(move)}\" is not a valid move.")
    elif((moveAxis(rotation) == moveAxis(move)) or (move.strip() == "") or (rotation.strip() == "")):
        return move
    else:
        m_root:     str = moveSplit(move)[0]
        m_stem:     str = moveSplit(move)[1]
        lowercase:  bool = (m_root == m_root.lower())
        has_w:      bool = (m_root[-1] == "w")

        rr: str = reduceMove(rotation).lower()
        result: str

        if(rr[-1] == "2"):
            return flipMove(move)
        
        match rr[0]:
            case "x":
                match m_root[0].upper():
                    case "U":
                        result = "F"
                    case "F":
                        result = "D"
                    case "B":
                        result = "U"
                    case "D":
                        result = "B"
                    
                    case "E":
                        result = "S"
                    case "S":
                        result = "E"
                    
                    case "Y":
                        result = chr(ord(m_root) + 1)
                    case _:     #  case "Z":
                        result = chr(ord(m_root) - 1)

            case "y":
                match m_root[0].upper():
                    case "R":
                        result = "B"
                    case "L":
                        result = "F"
                    case "F":
                        result = "R"
                    case "B":
                        result = "L"
                    
                    case "M":
                        result = "S"
                    case "S":
                        result = "M"
                    
                    case "X":
                        result = chr(ord(m_root) + 2)
                    case _:     #  case "Z":
                        result = chr(ord(m_root) - 2)

            case _:     #  case "z":
                match m_root[0].upper():
                    case "R":
                        result = "U"
                    case "L":
                        result = "D"
                    case "U":
                        result = "L"
                    case "D":
                        result = "R"
                    
                    case "M":
                        result = "E"
                    case "E":
                        result = "M"
                    
                    case "X":
                        result = chr(ord(m_root) + 1)
                    case _:     #  case "Y":
                        result = chr(ord(m_root) - 1)
            
        if(lowercase):
            result = result.lower()
        elif(has_w):
            result += "w"

        result += m_stem
        result = ((flipMove(result)) if(rr[-1] == "'") else result)

        if(
            ((rr[0] == "x") and (m_root.upper() in ["E", "Z"])) or \
            ((rr[0] == "y") and (m_root.upper() in ["S", "X"])) or \
            ((rr[0] == "z") and (m_root.upper() in ["E", "Y"]))
          ):
          result = invertMove(result)

        return result

#  Given a cube rotation and a sequence of moves, this function returns the sequence of moves
#  resulting from simplifying the following sequence of moves: (rotation moves rotation'),
#  where rotation' represents the inverse of the rotation.
def rotateMoves(rotation: str, moves: str) -> str:
    if(not isValidCubeRotation(rotation)):
        raise ValueError(f"rotateMoves:\n\tparameter rotation: \"{str(rotation)}\" is not a valid cube rotation.")
    elif(not areValidMoves(moves)):
        raise ValueError(f"rotateMoves:\n\tparameter moves: \"{str(moves)}\" are not valid moves.")
    elif(set(moves.replace(" ", "").replace("\n", "").replace("\t", "")) in [{}, {"(", ")"}]):
        return ""
    else:
        tokens: list[str] = moves.replace("(", " ( ").replace(")", " ) ").split()
        result: str = ""
        for move in tokens:
            result += (rotateMove(rotation, move) if(move not in "()") else move) + " "
        return cleanUpSpacing(result)

#  Simplifies all subsequences of the form (rotation moves rotation') in a sequence of moves, where
#  rotation' represents the inverse of some cube rotation. In other words, if a cube rotation appears in a sequence of moves,
#  the inverse of that cube rotation will never appear in that sequence after being passed through this function.
def simplifyRotationPairs(moves: str) -> str:
    if(not areValidMoves(moves)):
        raise ValueError(f"simplifyRotationPairs:\n\tparameter moves: \"{str(moves)}\" are not valid moves.")
    else:
        if((tokens := moves.replace("(", " ").replace(")", " ").split()) == []):
            return ""
        else:
            T: list[str] = tokens[1:]
            m_inverse: str = invertMove(m := tokens[0])
            foilii: list[int] = list(
                                      filter(
                                        lambda n: n != -1,
                                        [
                                            firstOccurenceInList_index(T, reduceMove(m_inverse).lower()),
                                            firstOccurenceInList_index(T, reduceMove(m_inverse).upper()),
                                            firstOccurenceInList_index(T, unreduceMove(m_inverse).lower()),
                                            firstOccurenceInList_index(T, unreduceMove(m_inverse).upper()),
                                        ]
                                      )
                                    )
            if(isValidCubeRotation(m) and (foilii != [])):
                endBlock: int = min(foilii)               
                rotated:  str = rotateMoves(m, concatenateStringList(tokens[1:(endBlock + 1)]))
                theRest:  str = simplifyRotationPairs(concatenateStringList(tokens[(endBlock + 2):]))
                return simplifyRotationPairs(rotated + " " + theRest).strip()
            else:
                return (m + " " + simplifyRotationPairs(concatenateStringList(tokens[1:]))).strip()


#  Replaces all sublists in a given list that match a given set with a given replacement,
#  and this sublist can be in any order, as long as it is consecutive in the list.
def replaceSubsetInList(L: list, S: set, replacement: Any) -> list:
    if(type(L) != list):
        raise TypeError(f"replaceSubsetInList:\n\tparameter L: \"{str(L)}\" is not a list.")
    elif(type(S) != set):
        raise TypeError(f"replaceSubsetInList:\n\tparameter S: \"{str(S)}\" is not a set.")
    elif(len(S) == 0):
        return L
    else:
        i: int = 0
        result: list = []
        while(i <= len(L) - len(S)):
            if(set(L[i: i + len(S)]) == S):
                result.append(replacement)
                i += len(S)
            else:
                result.append(L[i])
                i += 1

        return result + L[i:]
        

#  Uses the REVEAL_ROTATIONS_DICTIONARY to simplify any subsequences in a string of moves to a single cube rotation.
def revealRotations(moves: str) -> str:
    if(not areValidMoves(moves)):
        raise ValueError(f"revealRotations:\n\parameter moves: \"{str(moves)}\" are not valid moves.")
    else:
        tokens: list[str] = moves.split()
        justRearranged: list[str] = tokens.copy()

        for key in REVEAL_ROTATIONS_DICTIONARY:
            for t in key:
                tokens = replaceSubsetInList(tokens, set(t.split()), REVEAL_ROTATIONS_DICTIONARY[key])
        
        return moves if(tokens == justRearranged) else concatenateStringList(tokens)


#  Keeps track of where a specific face of the cube is located after performing a cube rotation.
#  Returns one of the cube's faces: {"R", "U", "F", "L", "D", "B"}.
def cubeRotateFace(face: str, rotation: str) -> str:
    if(face not in POSSIBLE_FACE_MOVE_ROOTS):
        raise ValueError(f"cubeRotateFace:\n\tparameter face: \"{str(face)}\" is not a valid face.")
    elif(not isValidCubeRotation(rotation)):
        raise ValueError(f"cubeRotateFace:\n\tparameter rotation: \"{str(rotation)}\" is not a valid rotation.")
    elif(((_r := rotation.strip()) != "") and (_r[0] + _r[-1] == "()")):
        return cubeRotateFace(face, _r[1: -1])
    elif(moveAxis(face) in moveAxis(rotation)):
        return face
    else:
        rr: str = reduceMove(_r)[-1]
        if(rr == "2"):
            return FLIP_MOVE[face]
        else:
            result: str
            if(face in "RUF"):
                result = CUBE_ROTATE_FACE[face][rotation[0].lower()]
            else:
                result = FLIP_MOVE[CUBE_ROTATE_FACE[FLIP_MOVE[face]][rotation[0].lower()]]
            
            if(rr == "'"):
                result = FLIP_MOVE[result]
            return result

#  Keeps track of where a specific face of the cube is located after performing a sequence of cube rotations.
#  Returns one of the cube's faces: {"R", "U", "F", "L", "D", "B"}.
def cubeRotatesFace(face: str, rotations: str) -> str:
    if(face not in POSSIBLE_FACE_MOVE_ROOTS):
        raise ValueError(f"cubeRotatesFace:\n\tparameter face: \"{str(face)}\" is not a valid face.")
    elif(type(rotations) != str):
        raise TypeError(f"cubeRotatesFace:\n\tparameter rotations: \"{str(rotations)}\" is not a string.")
    else:
        result: str = face
        for rotation in rotations.replace("(", " ").replace(")", " ").split():
            if(not isValidCubeRotation(rotation)):
                raise ValueError(f"cubeRotatesFace:\n\tin parameter rotation: \"{rotation}\" is not a valid cube rotation.")
            else:
                result = cubeRotateFace(result, rotation)

        return result


#  Given three cube rotations, this function simplifies them to a sequence of at most two cube rotations.
def simplifyRotationTriplet(r0: str, r1: str, r2: str) -> str:
    if(not isValidCubeRotation(r0)):
        raise ValueError(f"simplifyRotationTriplet:\n\tparameter r0: \"{str(r0)}\" is not a valid rotation.")
    elif(not isValidCubeRotation(r1)):
        raise ValueError(f"simplifyRotationTriplet:\n\tparameter r1: \"{str(r1)}\" is not a valid rotation.")
    elif(not isValidCubeRotation(r2)):
        raise ValueError(f"simplifyRotationTriplet:\n\tparameter r2: \"{str(r2)}\" is not a valid rotation.")
    elif(((r0 := r0.strip()) != "") and (r0[0] + r0[-1] == "()")):
        return simplifyRotationTriplet(r0[1: -1], r1, r2)
    elif(((r1 := r1.strip()) != "") and (r1[0] + r1[-1] == "()")):
        return simplifyRotationTriplet(r0, r1[1: -1], r2)
    elif(((r2 := r2.strip()) != "") and (r2[0] + r2[-1] == "()")):
        return simplifyRotationTriplet(r0, r1, r2[1: -1])
    elif((len(r0) * len(r1) * len(r2)) == 0):
        return combineMoves(f"{r0} {r1} {r2}")
    else:
        result: str = ""

        match cubeRotatesFace("U", concatenateStringList([r0, r1, r2])):
            case "R":
                result = "z" + result
            case "L":
                result = "z'" + result
            case "U":
                pass
            case "D":
                result = "x2" + result
            case "F":
                result = "x'" + result
            case _:     #  case "B":
                result = "x" + result
        
        result =  " " + result
        
        match cubeRotatesFace("F", concatenateStringList([r0, r1, r2, invertMove(result)])):
            case "R":
                result = "y'" + result
            case "L":
                result = "y" + result
            case "F":
                pass
            case _:     #  case "B":
                result = "y2" + result

        return result.strip()

#  Simplifies all subsequences of cube rotations of at least length three in a sequence (string) of moves,
#  simplfying these subsequences to subsequences of at most two cube rotations.
def simplifyRotationTriplets(moves: str) -> str:
    if(type(moves) != str):
        raise TypeError(f"simplifyRotationTriplets:\n\tparameter moves: \"{str(moves)}\" is not a string.")
    elif(moves.strip() == ""):
        return ""
    elif(not isValidMove(   (tokens := moves.replace("(", " ").replace(")", " ").split())   [0]   )):
        raise ValueError(f"simplifyRotationTriplets:\n\tin parameter moves: \"{tokens[0]}\" is not a valid move.")
    elif((len(tokens) >= 2) and (not isValidMove(tokens[1]))):
        raise ValueError(f"simplifyRotationTriplets:\n\tin parameter moves: \"{tokens[1]}\" is not a valid move.")
    elif((len(tokens) >= 3) and (not isValidMove(tokens[2]))):
        raise ValueError(f"simplifyRotationTriplets:\n\tin parameter moves: \"{tokens[2]}\" is not a valid move.")
    elif(len(tokens) < 3):
        return concatenateStringList(tokens)
    elif(isValidCubeRotation(tokens[0]) and isValidCubeRotation(tokens[1]) and isValidCubeRotation(tokens[2])):
        return simplifyRotationTriplets(simplifyRotationTriplet(tokens[0], tokens[1], tokens[2]) + " " + concatenateStringList(tokens[3:]))
    else:
        return tokens[0] + " " + simplifyRotationTriplets(concatenateStringList(tokens[1:]))

#  Uses the SIMPLIFY_CLEANUP_DICTIONARY to simplify any unordered subsequences in a sequence of moves,
#  using many complex moves such as wide moves, slice moves, and cube rotations.
def simplifyCleanUp(moves: str) -> str:
    if(type(moves) != str):
        raise TypeError(f"simplifyCleanUp:\n\tparameter moves: \"{str(moves)}\" is not a string.")
    else:
        tokens: list[str] = moves.replace("(", " ").replace(")", " ").split()
        justRearranged: list[str] = tokens.copy()
        for move in tokens:
            if(not isValidMove(move)):
                raise ValueError(f"simplifyCleanUp:\n\tin parameter moves: \"{move}\" is not a valid move.")

        for key in SIMPLIFY_CLEANUP_DICTIONARY:
            for t in key:
                tokens = replaceSubsetInList(tokens, set(t.split()), SIMPLIFY_CLEANUP_DICTIONARY[key])
        
        return moves if(tokens == justRearranged) else concatenateStringList(tokens)


#  Takes a string of moves and splits it into a list of lists of strings, making splits
#  when the axis of the next move is different than the current move. Moves in each list of the
#  resulting list belong to the same axis, such as R and L.
def splitMovesAxes(moves: str) -> str:
    if(type(moves) != str):
        raise TypeError(f"splitMovesAxes:\n\tparameter moves: \"{str(moves)}\" is not a string.")
    else:        
        result     : list[list[str]] = []
        currentList: list[str]       = []

        for move in moves.replace("(", " ").replace(")", " ").split():
            if(not isValidMove(move)):
                raise ValueError(f"splitMovesAxes:\n\tin parameter moves: \"{move}\" is not a valid move.")
            elif((currentList == []) or (moveAxis(currentList[0]) == moveAxis(move))):
                currentList.append(move)
            else:
                result.append(currentList)
                currentList = [move]

        return result + [currentList]


#  Splits a string of moves into their respective axes in a 2D list, sorts each list of moves in this list first by
#  their move roots, then stable sorts by the first characters of the moves in a case-insensitive manner. The resulting 2D list of
#  strings is then concatenated all together into a single string and is finally returned.
def sortMoveAxes(moves: str) -> str:
    if(type(moves) != str):
        raise TypeError(f"sortMoveAxes:\n\tparameter moves: \"{str(moves)}\" is not a string.")
    else:
        for move in (m := moves.replace("(", " ").replace(")", " ")).split():
            if(not isValidMove(move)):
                raise ValueError(f"sortMoveAxes:\n\tin parameter moves: \"{move}\" is not a valid move.")
                
        result: str = ""
        for axis in splitMovesAxes(m):
            result += concatenateStringList(sorted(sorted(axis, key = lambda x: moveSplit(x)[0]), key = lambda x: x[0].lower() if x != "" else "")) + " "

        return result.strip()


#  Simplifies a string of moves, using all of the move simplication algorithms previously described. Internally, this
#  function is repeatedly applied until the resulting string of moves contains the minimum number of moves possible.
def simplifyMoves(moves: str) -> str:    
    if(type(moves) != str):
        raise TypeError(f"simplifyMoves:\n\tparameter moves: \"{str(moves)}\" is not a string.")
    else:
        for move in moves.replace("(", " ").replace(")", " ").split():
            if(not isValidMove(move)):
                raise ValueError(f"simplifyMoves:\n\tin parameter moves: \"{move}\" is not a valid move.")

        def simplifier(m: str) -> str:
            return simplifyCleanUp(simplifyRotationPairs(simplifyRotationTriplets(revealRotations(combineMoves(sortMoveAxes(reduceMoves(m)))))))
        
        result:    str = simplifier(moves)
        newResult: str = simplifier(result)
        while(len(newResult.split()) < len(result.split())):
            result = newResult
            newResult = simplifier(result)
        return result if(result != cleanUpSpacing(moves.replace("(", " ").replace(")", " "))) else cleanUpSpacing(moves)


#  Generates a random move. Specifying WCA as False will make it possible to generate more complex
#  moves that are not allowed in official WCA tournament scrambles (wide moves, slice moves, and cube rotations).
#  With WCA specified as False, there is a 70% chance to generate a face move, a 20% chance to generate a slice move,
#  and a 10% chance to generate a cube rotation. If WCA is specified as False and a face move is generated, there is a
#  20% chance that it is a wide move (a 10% chance to make its root lowercase, and a 10% chance to append a "w" to its root).
#  All cube rotations have a 75% chance of being lowercase, and a 25% chance of being uppercase.
def generateRandomMove(WCA: bool = True) -> str:
    if(type(WCA) != bool):
        raise TypeError(f"generateRandomMove:\n\tparameter WCA: \"{str(WCA)}\" is not a bool.")
    else:
        roots: tuple[str]

        #  randomly choose the root of the move
        if(WCA or ((chance := randint(1, 100)) <= 70)):
            roots = POSSIBLE_FACE_MOVE_ROOTS
        elif(chance <= 90):
            roots = POSSIBLE_SLICE_MOVE_ROOTS
        else:
            roots = POSSIBLE_CUBE_ROTATION_ROOTS
        root: str = choice(roots)

        #  randomly choose the stem of the move
        if(not WCA):
            chance = randint(1, 100)
            if(roots == POSSIBLE_FACE_MOVE_ROOTS):
                if(chance <= 10):
                    root = root.lower()
                elif(chance <= 20):
                    root += "w"
            elif((roots == POSSIBLE_CUBE_ROTATION_ROOTS) and (chance <= 25)):
                root = root.upper()

        return root + choice(POSSIBLE_MOVE_STEMS)

#  Generates a sequence of random moves, given a move count. Specifying WCA as False will make it possible to generate more complex
#  moves in the sequence that are not allowed in official WCA tournament scrambles (wide moves, slice moves, and cube rotations).
#  With WCA specified as False, there is a 70% chance to generate a face move, a 20% chance to generate a slice move, and a 10%
#  chance to generate a cube rotation. If WCA is specified as False and a face move is generated, there is a 20% chance that it is
#  a wide move (a 10% chance to make its root lowercase, and a 10% chance to otherwise append a "w" to its root). All cube rotations have a
#  75% chance of being lowercase, and a 25% chance of being uppercase.
def generateRandomMoves(moveCount: int, WCA: bool = True) -> str:
    if(type(moveCount) != int):
        raise TypeError(f"generateRandomMoves:\n\tparameter moveCount: \"{str(moveCount)}\" is not an int.")
    elif(moveCount < 0):
        raise ValueError(f"generateRandomMoves:\n\tparameter moveCount: \"{str(moveCount)}\" is not a non-negative integer.")
    elif(type(WCA) != bool):
        raise TypeError(f"generateRandomMoves:\n\tparameter WCA: \"{str(WCA)}\" is not a bool.")
    else:
        result: str = ""
        simplifier: Callable[[str], str] = combineMoves if WCA else simplifyMoves

        while(len(result.split()) < moveCount):
            result = simplifier(result + " " + generateRandomMove(WCA))
        
        return result.strip()


#  Returns whether two integers represent a valid edge on the cube.
def isValidEdge(color0: int, color1: int) -> bool:
    if(type(color0) != int):
        raise TypeError(f"isValidEdge:\n\tparameter color0: \"{str(color0)}\" is not an integer.")
    elif(color0 not in range(6)):
        raise ValueError(f"isValidEdge:\n\tparameter color0: \"{str(color0)}\" is not a valid integer.")
    elif(type(color1) != int):
        raise TypeError(f"isValidEdge:\n\tparameter color1: \"{str(color1)}\" is not an integer.")
    elif(color1 not in range(6)):
        raise ValueError(f"isValidEdge:\n\tparameter color1: \"{str(color1)}\" is not a valid integer.")
    else:
        return (color0 != color1) and (color0 != FLIP_COLOR[color1])

#  Returns whether three integers represent a valid corner on the cube. The order of the integers
#  matters, since colors on the corners of the cube are read clockwise; for example, if
#  (a, b, c) is a valid corner, then so is (b, c, a), but not (a, c, b).
def isValidCorner(color0: int, color1: int, color2: int) -> bool:
    if(type(color0) != int):
        raise TypeError(f"isValidCorner:\n\tparameter color0: \"{str(color0)}\" is not an integer.")
    elif(color0 not in range(6)):
        raise ValueError(f"isValidCorner:\n\tparameter color0: \"{str(color0)}\" is not a valid integer.")
    elif(type(color1) != int):
        raise TypeError(f"isValidCorner:\n\tparameter color1: \"{str(color1)}\" is not an integer.")
    elif(color1 not in range(6)):
        raise ValueError(f"isValidCorner:\n\tparameter color1: \"{str(color1)}\" is not a valid integer.")
    elif(type(color2) != int):
        raise TypeError(f"isValidCorner:\n\tparameter color2: \"{str(color2)}\" is not an integer.")
    elif(color2 not in range(6)):
        raise ValueError(f"isValidCorner:\n\tparameter color2: \"{str(color2)}\" is not a valid integer.")
    else:
        def allCyclesList(L: list) -> list[list]:
            if(type(L) != list):
                raise TypeError(f"allCyclesList:\n\tparameter L: \"{str(L)}\" is not a list.")
            else:
                result: list = []
                for item in L:
                    result.append(L)
                    L = L[1:] + [item]
                return max(result, [[]])
        
        cycles: list[list[int]] = allCyclesList([color0, color1, color2])
        return (tuple(cycles[0]) in CORNERS) or (tuple(cycles[1]) in CORNERS) or (tuple(cycles[2]) in CORNERS)


#  Given two sequences of moves, conjugates the first sequence with the second sequence.
#  This means that this function returns the sequence of moves consisting of the first
#  sequence, followed by the second sequence, followed by the inverse of the first sequence.
def conjugation(moves0: str, moves1: str) -> str:
    if(not areValidMoves(moves0)):
        raise ValueError(f"conjugate:\n\tparameter moves0: \"{str(moves0)}\" are not valid moves.")
    elif(not areValidMoves(moves1)):
        raise ValueError(f"conjugate:\n\tparameter moves1: \"{str(moves1)}\" are not valid moves.")
    else:
        m0: str = cleanUpSpacing(moves0)
        m1: str = cleanUpSpacing(moves1)
        return cleanUpSpacing(f"({m0}) ({m1}) ({invertMoves(m0)})")

#  Given two sequences of moves, returns the commutator of the first sequence with the second
#  sequence. This means that this function returns the sequence of moves consisting of the first
#  sequence, followed by the second sequence, followed by the inverse of the first sequence, followed
#  by the inverse of the second sequence.
def commutator(moves0: str, moves1: str) -> str:
    if(not areValidMoves(moves0)):
        raise ValueError(f"commutator:\n\tparameter moves0: \"{str(moves0)}\" are not valid moves.")
    elif(not areValidMoves(moves1)):
        raise ValueError(f"commutator:\n\tparameter moves1: \"{str(moves1)}\" are not valid moves.")
    else:
        m0: str = cleanUpSpacing(moves0)
        m1: str = cleanUpSpacing(moves1)
        return cleanUpSpacing(f"({m0}) ({m1}) ({invertMoves(m0)}) ({invertMoves(m1)})")


#  Each Rubik's Cube is represented by an instance of the object class "Cube"
class Cube:
    #  Initializes a cube object (its state, edges, corners, and centers attributes).
    def __init__(self, moves: str = "") -> None:
        #  The state of the cube is initially solved
        self.__state: list[list[int]] = (s := deepcopy(SOLVED_CUBE))


        #  The following three attributes are "two-way" dictionaries, so that the location of every piece on the cube
        #  is stored, but also what piece is currently at every specific location on the cube.

        #  In other words, the following two actions can be used with a cube object's attributes:
        #       - Give me a piece on the cube, and I can immediately tell you where that piece is
        #       - Give me a location on the cube, and I can immediately tell you what piece is at that location
        #  In these two ways, the unique locations of all (3**2 * 6) = 54 stickers on every cube are accounted for.

        self.__edges: dict[str, tuple[int]] = \
        {
            "edgeA": (s[UP][1]   , s[BACK][1]),
            "edgeB": (s[UP][5]   , s[RIGHT][1]),
            "edgeC": (s[UP][7]   , s[FRONT][1]),
            "edgeD": (s[UP][3]   , s[LEFT][1]),

            "edgeE": (s[LEFT][1] , s[UP][3]),
            "edgeF": (s[LEFT][5] , s[FRONT][3]),
            "edgeG": (s[LEFT][7] , s[DOWN][3]),
            "edgeH": (s[LEFT][3] , s[BACK][5]),

            "edgeI": (s[FRONT][1], s[UP][7]),
            "edgeJ": (s[FRONT][5], s[RIGHT][3]),
            "edgeK": (s[FRONT][7], s[DOWN][1]),
            "edgeL": (s[FRONT][3], s[LEFT][5]),

            "edgeM": (s[RIGHT][1], s[UP][5]),
            "edgeN": (s[RIGHT][5], s[BACK][3]),
            "edgeO": (s[RIGHT][7], s[DOWN][5]),
            "edgeP": (s[RIGHT][3], s[FRONT][5]),

            "edgeQ": (s[BACK][1] , s[UP][1]),
            "edgeR": (s[BACK][5] , s[LEFT][3]),
            "edgeS": (s[BACK][7] , s[DOWN][7]),
            "edgeT": (s[BACK][3] , s[RIGHT][5]),

            "edgeU": (s[DOWN][1] , s[FRONT][7]),
            "edgeV": (s[DOWN][5] , s[RIGHT][7]),
            "edgeW": (s[DOWN][7] , s[BACK][7]),
            "edgeX": (s[DOWN][3] , s[LEFT][7])
        }
        
        self.__corners: dict[str, tuple[int]] = \
        {
            "cornerA": (s[UP][0]   , s[LEFT][0] , s[BACK][2]),
            "cornerB": (s[UP][2]   , s[BACK][0] , s[RIGHT][2]),
            "cornerC": (s[UP][8]   , s[RIGHT][0], s[FRONT][2]),
            "cornerD": (s[UP][6]   , s[FRONT][0], s[LEFT][2]),

            "cornerE": (s[LEFT][0] , s[BACK][2] , s[UP][0]),
            "cornerF": (s[LEFT][2] , s[UP][6]   , s[FRONT][0]),
            "cornerG": (s[LEFT][8] , s[FRONT][6], s[DOWN][0]),
            "cornerH": (s[LEFT][6] , s[DOWN][6] , s[BACK][8]),

            "cornerI": (s[FRONT][0], s[LEFT][2] , s[UP][6]),
            "cornerJ": (s[FRONT][2], s[UP][8]   , s[RIGHT][0]),
            "cornerK": (s[FRONT][8], s[RIGHT][6], s[DOWN][2]),
            "cornerL": (s[FRONT][6], s[DOWN][0] , s[LEFT][8]),

            "cornerM": (s[RIGHT][0], s[FRONT][2], s[UP][8]),
            "cornerN": (s[RIGHT][2], s[UP][2]   , s[BACK][0]),
            "cornerO": (s[RIGHT][8], s[BACK][6] , s[DOWN][8]),
            "cornerP": (s[RIGHT][6], s[DOWN][2] , s[FRONT][8]),

            "cornerQ": (s[BACK][0] , s[RIGHT][2], s[UP][2]),
            "cornerR": (s[BACK][2] , s[UP][0]   , s[LEFT][0]),
            "cornerS": (s[BACK][8] , s[LEFT][6] , s[DOWN][6]),
            "cornerT": (s[BACK][6] , s[DOWN][8] , s[RIGHT][8]),

            "cornerU": (s[DOWN][0] , s[LEFT][8] , s[FRONT][6]),
            "cornerV": (s[DOWN][2] , s[FRONT][8], s[RIGHT][6]),
            "cornerW": (s[DOWN][8] , s[RIGHT][8], s[BACK][6]),
            "cornerX": (s[DOWN][6] , s[BACK][8] , s[LEFT][8])
        }
        
        self.__centers: dict[str, int] = \
        {
            "centerUP"   : s[UP][4],
            "centerLEFT" : s[LEFT][4],
            "centerFRONT": s[FRONT][4],
            "centerRIGHT": s[RIGHT][4],
            "centerBACK" : s[BACK][4],
            "centerDOWN" : s[DOWN][4]
        }

        #  The following three for-loops make the three attribute dictionaries go
        #  from regular "one-sided" dicitonaries to "two-sided" dictionaries.
        for key in self.__edges.copy():
            self.__edges[self.__edges[key]] = key
        for key in self.__corners.copy():
            self.__corners[self.__corners[key]] = key
        for key in self.__centers.copy():
            self.__centers[self.__centers[key]] = key
            

        #  Perform the moves on the cube that were specified during initalization, if any.
        #  Its attributes are automatically updated if needed, in the performMoves() function.
        self.performMoves(moves)
        return


    #  Validates a cube object, checking that its state, edges, corners, and centers attributes are of the correct form.
    def validate(self) -> bool:
        s: list[list[int]] = self.__state
        if(type(self.__state) != list):
            raise TypeError(f"validate:\n\tself.__state: \"{str(self.__state)}\" is not a list.")
        elif(len(self.__state) != 6):
            raise ValueError(f"validate:\n\tself.__state: \"{str(self.__state)}\" does not have a length of 6.")
        else:
            for face in self.__state:
                if(type(face) != list):
                    raise TypeError(f"validate:\n\tin self.__state: \"{str(face)}\" is not a list.")
                elif(len(face) != 9):
                    raise ValueError(f"validate:\n\tin self.__state: \"{str(face)}\" does not have a length of 9.")
                else:
                    for sticker in face:
                        if(type(sticker) != int):
                            raise TypeError(f"validate:\n\tin self.__state, in \"{str(face)}\": \"{str(sticker)}\" is not an integer.")
                        elif(sticker not in range(6)):
                            raise ValueError(f"validate:\n\tin self.__state, in \"{str(face)}\": \"{str(sticker)}\" is not a valid integer.")
            

            if(type(self.__edges) != dict):
                raise TypeError(f"validate:\n\tself.__edges: \"{str(self.__edges)}\" is not a dictionary.")
            elif(set(self.__edges.keys()) != \
                                             set(
                                                    [("edge" + chr(letter)) for letter in range(65, 89)] + \
                                                    [
                                                        (s[UP][1]   , s[BACK][1]),
                                                        (s[UP][5]   , s[RIGHT][1]),
                                                        (s[UP][7]   , s[FRONT][1]),
                                                        (s[UP][3]   , s[LEFT][1]),

                                                        (s[LEFT][1] , s[UP][3]),
                                                        (s[LEFT][5] , s[FRONT][3]),
                                                        (s[LEFT][7] , s[DOWN][3]),
                                                        (s[LEFT][3] , s[BACK][5]),

                                                        (s[FRONT][1], s[UP][7]),
                                                        (s[FRONT][5], s[RIGHT][3]),
                                                        (s[FRONT][7], s[DOWN][1]),
                                                        (s[FRONT][3], s[LEFT][5]),

                                                        (s[RIGHT][1], s[UP][5]),
                                                        (s[RIGHT][5], s[BACK][3]),
                                                        (s[RIGHT][7], s[DOWN][5]),
                                                        (s[RIGHT][3], s[FRONT][5]),

                                                        (s[BACK][1] , s[UP][1]),
                                                        (s[BACK][5] , s[LEFT][3]),
                                                        (s[BACK][7] , s[DOWN][7]),
                                                        (s[BACK][3] , s[RIGHT][5]),

                                                        (s[DOWN][1] , s[FRONT][7]),
                                                        (s[DOWN][5] , s[RIGHT][7]),
                                                        (s[DOWN][7] , s[BACK][7]),
                                                        (s[DOWN][3] , s[LEFT][7])
                                                    ]
                                                )
                ):
                raise ValueError(f"validate:\n\self.__edges: \"{str(self.__edges)}\" does not have valid dictionary keys.")
            elif(set(self.__edges.keys()) != set(self.__edges.values())):
                raise ValueError(f"validate:\n\self.__edges: \"{str(self.__edges)}\" does not have valid dictionary values.")

            
            elif(type(self.__corners) != dict):
                raise TypeError(f"validate:\n\tself.__corners: \"{str(self.__corners)}\" is not a dictionary.")
            elif(set(self.__corners.keys()) != \
                                               set(
                                                      [("corner" + chr(letter)) for letter in range(65, 89)] + \
                                                      [
                                                          (s[UP][0]   , s[LEFT][0] , s[BACK][2]),
                                                          (s[UP][2]   , s[BACK][0] , s[RIGHT][2]),
                                                          (s[UP][8]   , s[RIGHT][0], s[FRONT][2]),
                                                          (s[UP][6]   , s[FRONT][0], s[LEFT][2]),

                                                          (s[LEFT][0] , s[BACK][2] , s[UP][0]),
                                                          (s[LEFT][2] , s[UP][6]   , s[FRONT][0]),
                                                          (s[LEFT][8] , s[FRONT][6], s[DOWN][0]),
                                                          (s[LEFT][6] , s[DOWN][6] , s[BACK][8]),

                                                          (s[FRONT][0], s[LEFT][2] , s[UP][6]),
                                                          (s[FRONT][2], s[UP][8]   , s[RIGHT][0]),
                                                          (s[FRONT][8], s[RIGHT][6], s[DOWN][2]),
                                                          (s[FRONT][6], s[DOWN][0] , s[LEFT][8]),

                                                          (s[RIGHT][0], s[FRONT][2], s[UP][8]),
                                                          (s[RIGHT][2], s[UP][2]   , s[BACK][0]),
                                                          (s[RIGHT][8], s[BACK][6] , s[DOWN][8]),
                                                          (s[RIGHT][6], s[DOWN][2] , s[FRONT][8]),

                                                          (s[BACK][0] , s[RIGHT][2], s[UP][2]),
                                                          (s[BACK][2] , s[UP][0]   , s[LEFT][0]),
                                                          (s[BACK][8] , s[LEFT][6] , s[DOWN][6]),
                                                          (s[BACK][6] , s[DOWN][8] , s[RIGHT][8]),

                                                          (s[DOWN][0] , s[LEFT][8] , s[FRONT][6]),
                                                          (s[DOWN][2] , s[FRONT][8], s[RIGHT][6]),
                                                          (s[DOWN][8] , s[RIGHT][8], s[BACK][6]),
                                                          (s[DOWN][6] , s[BACK][8] , s[LEFT][8])
                                                      ]
                                                  )
                ):
                raise ValueError(f"validate:\n\tself.__corners: \"{str(self.__corners)}\" does not have valid dictionary keys.")
            elif(set(self.__corners.keys()) != set(self.__corners.values())):
                raise ValueError(f"validate:\n\tself.__corners: \"{str(self.__edges)}\" does not have valid dictionary values.")


            elif(type(self.__centers) != dict):
                raise TypeError(f"validate:\n\tself.__centers: \"{str(self.__centers)}\" is not a dictionary.")
            elif(set(self.__centers.keys()) != set([(f"center{SIDE}") for SIDE in ("UP", "LEFT", "FRONT", "RIGHT", "BACK", "DOWN")]   +   [s[SIDE][4] for SIDE in range(6)])):
                raise ValueError(f"validate:\n\tself.__centers: \"{str(self.__centers)}\" does not have valid dictionary keys.")
            elif(set(self.__centers.keys()) != set(self.__centers.values())):
                raise ValueError(f"validate:\n\tself.__centers: \"{str(self.__centers)}\" does not have valid dictionary values.")


    #  Prints out the state of the cube, printing out colored letters instead if colorBlindMode is set to True.
    def printCube(self, colorBlindMode: bool = False) -> None:
        self.validate()

        if(type(colorBlindMode) != bool):
            raise TypeError(f"printCube:\n\tparameter colorBlindMode: \"{str(colorBlindMode)}\" is not a bool.")
        else:
            print(DEFAULT, end = "")

            if(not colorBlindMode):
                for i in range(len(self.__state)):
                    print(FACES[i] + " face:")
                    for j in range(len(self.__state[i])):
                        cc: int = self.__state[i][j]   #  current color
                        print(
                                (" " if(j % 3 == 0) else "") + EMOJI_SQUARES[cc],
                                end = (" " if(((j + 1) % 3) != 0) else "\n")
                             )
                    print(end = ("\n" if(i < len(self.__state) - 1) else ""))
            else:
                for i in range(len(self.__state)):
                    print(FACES[i] + " face:" + BOLD)
                    for j in range(len(self.__state[i])):
                        cc: int = self.__state[i][j]   #  current color
                        print(
                                (" " if(j % 3 == 0) else "") + (RGB_COLORS[cc] + STR_COLORS[cc]),
                                end = (" " if(((j + 1) % 3) != 0) else "\n")
                             )
                    print(DEFAULT, end = ("\n" if(i < len(self.__state) - 1) else ""))

            return


    #  Returns whether or not a cube object is solved (each side has the same color).
    def isSolved(self) -> bool:
        self.validate()
        return (self.__state == SOLVED_CUBE)


    #  Performs a sequence of moves (a string) on a Cube.
    #  On success, the function returns the entire sequence of given moves that were performed on the Cube.
    def performMoves(self, moves: str) -> str:

        #  The helper function below is recursive, but the entire function only validates once to save some time.
        self.validate()

        def performMovesHelper(self, moves: str) -> str:
            #  First, check that moves is actually of type string.
            if(type(moves) != str):
                raise TypeError(f"performMovesHelper:\n\tparameter moves: \"{str(moves)}\" is not a string.")
            
            #  Check that all the moves are valid.
            for move in (tokens := moves.replace("(", " ").replace(")", " ").split()):
                if(not isValidMove(move)):
                    raise ValueError(f"performMovesHelper:\n\tin parameter moves: \"{move}\" is not a valid move.")

            #  This is a mutually recursive helper function inside this helper function that performs a single move on
            #  a cube object.
            def performMove(self, move: str) -> str:                    
                if(type(move) != str):
                    raise TypeError(f"performMove:\n\tparameter move: \"{str(move)}\" is not a string.")
                elif(not isValidMove(move)):
                    raise ValueError(f"performMove:\n\tparameter move: \"{move}\" is not a valid move.")
                elif(((m := move.strip()) != "") and (m[0] + m[-1] == "()")):
                    return performMove(self, m[1: -1])
                elif(m != ""):

                    #  Helper function that rotates all of the stickers on a face of a cube by some increment of 90 degrees.
                    #  Turns is any of {-1, 0, 1, 2}.
                    def rotateFace(face: int, turns: int) -> None:
                        if(type(face) != int):
                            raise TypeError(f"rotateFace:\n\tparameter face: \"{str(move)}\" is not an int.")
                        elif(type(turns) != int):
                            raise TypeError(f"rotateFace:\n\tparameter turns: \"{str(turns)}\" is not an int.")
                        st: list[list[int]] = deepcopy(self.__state)
                        match turns:
                            case 1:
                                for i in range(len(self.__state[face])):
                                    self.__state[face][i] = st[face][((-3 * i) + 6) % 10]
                            case -1:
                                for i in range(len(self.__state[face])):
                                    self.__state[face][((-3 * i) + 6) % 10] = st[face][i]
                            case 2:
                                for i in range(len(self.__state[face])):
                                    self.__state[face][i] = st[face][8 - i]
                            case _:
                                if(turns != 0):
                                    raise ValueError(f"rotateFace:\n\tparameter turns: \"{str(turns)}\" is not a valid number of turns.")
                        return
                    

                    s        : list[list[int]] = deepcopy(self.__state)
                    reduced  : str             = reduceMove(m)
                    moveList : str             = moveSplit(reduced)
                    root     : str             = moveList[0]
                    stem     : str             = moveList[1]

                    match root:
                        case "R":
                            #  All moves internally reduce to some combination of R moves and cube rotations.
                            match stem:
                                case "":
                                    self.__state[UP][2] = s[FRONT][2]
                                    self.__state[UP][5] = s[FRONT][5]
                                    self.__state[UP][8] = s[FRONT][8]

                                    self.__state[FRONT][2] = s[DOWN][2]
                                    self.__state[FRONT][5] = s[DOWN][5]
                                    self.__state[FRONT][8] = s[DOWN][8]

                                    rotateFace(RIGHT, 1)
                                    
                                    self.__state[BACK][0] = s[UP][8]
                                    self.__state[BACK][3] = s[UP][5]
                                    self.__state[BACK][6] = s[UP][2]

                                    self.__state[DOWN][2] = s[BACK][6]
                                    self.__state[DOWN][5] = s[BACK][3]
                                    self.__state[DOWN][8] = s[BACK][0]
                                case "'":
                                    self.__state[UP][2] = s[BACK][6]
                                    self.__state[UP][5] = s[BACK][3]
                                    self.__state[UP][8] = s[BACK][0]

                                    self.__state[FRONT][2] = s[UP][2]
                                    self.__state[FRONT][5] = s[UP][5]
                                    self.__state[FRONT][8] = s[UP][8]

                                    rotateFace(RIGHT, -1)

                                    self.__state[BACK][0] = s[DOWN][8]
                                    self.__state[BACK][3] = s[DOWN][5]
                                    self.__state[BACK][6] = s[DOWN][2]

                                    self.__state[DOWN][2] = s[FRONT][2]
                                    self.__state[DOWN][5] = s[FRONT][5]
                                    self.__state[DOWN][8] = s[FRONT][8]
                                case _:     #  case "2":
                                    self.__state[UP][2] = s[DOWN][2]
                                    self.__state[UP][5] = s[DOWN][5]
                                    self.__state[UP][8] = s[DOWN][8]

                                    self.__state[FRONT][2] = s[BACK][6]
                                    self.__state[FRONT][5] = s[BACK][3]
                                    self.__state[FRONT][8] = s[BACK][0]

                                    rotateFace(RIGHT, 2)

                                    self.__state[BACK][0] = s[FRONT][8]
                                    self.__state[BACK][3] = s[FRONT][5]
                                    self.__state[BACK][6] = s[FRONT][2]

                                    self.__state[DOWN][2] = s[UP][2]
                                    self.__state[DOWN][5] = s[UP][5]
                                    self.__state[DOWN][8] = s[UP][8]
                        
                        case "L":
                            performMovesHelper(self, f"y2 R{stem} y2")
                        case "U":
                            performMovesHelper(self, f"z R{stem} z'")
                        case "D":
                            performMovesHelper(self, f"z' R{stem} z")
                        case "F":
                            performMovesHelper(self, f"y' R{stem} y")
                        case "B":
                            performMovesHelper(self, f"y R{stem} y'")


                        case "r" | "Rw":
                            performMovesHelper(self, f"L{stem} x{stem}")
                        case "l" | "Lw":
                            performMovesHelper(self, f"R{stem} " + invertMove(f"x{stem}"))
                        case "u" | "Uw":
                            performMovesHelper(self, f"D{stem} y{stem}")
                        case "d" | "Dw":
                            performMovesHelper(self, "U" + stem + " " + invertMove(f"y{stem}"))
                        case "f" | "Fw":
                            performMovesHelper(self, f"B{stem} z{stem}")
                        case "b" | "Bw":
                            performMovesHelper(self, "F" + stem + " " + invertMove(f"z{stem}"))


                        case "M":
                            performMovesHelper(self, "Lw" + stem + " " + invertMove(f"L{stem}"))
                        case "E":
                            performMovesHelper(self, "d" + stem + " " + invertMove(f"D{stem}"))
                        case "S":
                            performMovesHelper(self, invertMove(f"b{stem}") + f" B{stem}")


                        case _:
                            match reduced.lower():
                                case "x":
                                    self.__state = [s[FRONT], s[LEFT], s[DOWN], s[RIGHT], s[UP], s[BACK]]
                                    rotateFace(LEFT, -1)
                                    rotateFace(RIGHT, 1)
                                    rotateFace(BACK,  2)
                                    rotateFace(DOWN,  2)
                                case "x'":
                                    self.__state = [s[BACK], s[LEFT], s[UP], s[RIGHT], s[DOWN], s[FRONT]]
                                    rotateFace(LEFT,   1)
                                    rotateFace(RIGHT, -1)
                                    rotateFace(UP,     2)
                                    rotateFace(BACK,   2)
                                case "x2":
                                    self.__state = [s[DOWN], s[LEFT], s[BACK], s[RIGHT], s[FRONT], s[UP]]
                                    rotateFace(LEFT,  2)
                                    rotateFace(RIGHT, 2)
                                    rotateFace(BACK,  2)
                                    rotateFace(FRONT,  2)
                                
                                case "y":
                                    self.__state = [s[UP], s[FRONT], s[RIGHT], s[BACK], s[LEFT], s[DOWN]]
                                    rotateFace(UP,    1)
                                    rotateFace(DOWN, -1)
                                case "y'":
                                    self.__state = [s[UP], s[BACK], s[LEFT], s[FRONT], s[RIGHT], s[DOWN]]
                                    rotateFace(UP,  -1)
                                    rotateFace(DOWN, 1)
                                case "y2":
                                    self.__state = [s[UP], s[RIGHT], s[BACK], s[LEFT], s[FRONT], s[DOWN]]
                                    rotateFace(UP,   2)
                                    rotateFace(DOWN, 2)
                                
                                case "z":
                                    self.__state = [s[LEFT], s[DOWN], s[FRONT], s[UP], s[BACK], s[RIGHT]]
                                    for face in range(6):
                                        rotateFace(face, 1)
                                    rotateFace(BACK, 2)
                                case "z'":
                                    self.__state = [s[RIGHT], s[UP], s[FRONT], s[DOWN], s[BACK], s[LEFT]]
                                    for face in range(6):
                                        rotateFace(face, -1)
                                    rotateFace(BACK, 2)
                                case _:    #  case "z2":
                                    self.__state = [s[DOWN], s[RIGHT], s[FRONT], s[LEFT], s[BACK], s[UP]]
                                    for face in range(6):
                                        rotateFace(face, 2)

                return

            #  If a non-zero number of moves were performed on the Cube, update its attributes
            if(tokens != []):
                for move in tokens:
                    performMove(self, move)
                    
                s: list[list[int]] = self.__state

                self.__edges = \
                {
                    "edgeA": (s[UP][1]   , s[BACK][1]),
                    "edgeB": (s[UP][5]   , s[RIGHT][1]),
                    "edgeC": (s[UP][7]   , s[FRONT][1]),
                    "edgeD": (s[UP][3]   , s[LEFT][1]),

                    "edgeE": (s[LEFT][1] , s[UP][3]),
                    "edgeF": (s[LEFT][5] , s[FRONT][3]),
                    "edgeG": (s[LEFT][7] , s[DOWN][3]),
                    "edgeH": (s[LEFT][3] , s[BACK][5]),

                    "edgeI": (s[FRONT][1], s[UP][7]),
                    "edgeJ": (s[FRONT][5], s[RIGHT][3]),
                    "edgeK": (s[FRONT][7], s[DOWN][1]),
                    "edgeL": (s[FRONT][3], s[LEFT][5]),

                    "edgeM": (s[RIGHT][1], s[UP][5]),
                    "edgeN": (s[RIGHT][5], s[BACK][3]),
                    "edgeO": (s[RIGHT][7], s[DOWN][5]),
                    "edgeP": (s[RIGHT][3], s[FRONT][5]),

                    "edgeQ": (s[BACK][1] , s[UP][1]),
                    "edgeR": (s[BACK][5] , s[LEFT][3]),
                    "edgeS": (s[BACK][7] , s[DOWN][7]),
                    "edgeT": (s[BACK][3] , s[RIGHT][5]),

                    "edgeU": (s[DOWN][1] , s[FRONT][7]),
                    "edgeV": (s[DOWN][5] , s[RIGHT][7]),
                    "edgeW": (s[DOWN][7] , s[BACK][7]),
                    "edgeX": (s[DOWN][3] , s[LEFT][7])
                }

                self.__corners = \
                {
                    "cornerA": (s[UP][0]   , s[LEFT][0] , s[BACK][2]),
                    "cornerB": (s[UP][2]   , s[BACK][0] , s[RIGHT][2]),
                    "cornerC": (s[UP][8]   , s[RIGHT][0], s[FRONT][2]),
                    "cornerD": (s[UP][6]   , s[FRONT][0], s[LEFT][2]),

                    "cornerE": (s[LEFT][0] , s[BACK][2] , s[UP][0]),
                    "cornerF": (s[LEFT][2] , s[UP][6]   , s[FRONT][0]),
                    "cornerG": (s[LEFT][8] , s[FRONT][6], s[DOWN][0]),
                    "cornerH": (s[LEFT][6] , s[DOWN][6] , s[BACK][8]),

                    "cornerI": (s[FRONT][0], s[LEFT][2] , s[UP][6]),
                    "cornerJ": (s[FRONT][2], s[UP][8]   , s[RIGHT][0]),
                    "cornerK": (s[FRONT][8], s[RIGHT][6], s[DOWN][2]),
                    "cornerL": (s[FRONT][6], s[DOWN][0] , s[LEFT][8]),

                    "cornerM": (s[RIGHT][0], s[FRONT][2], s[UP][8]),
                    "cornerN": (s[RIGHT][2], s[UP][2]   , s[BACK][0]),
                    "cornerO": (s[RIGHT][8], s[BACK][6] , s[DOWN][8]),
                    "cornerP": (s[RIGHT][6], s[DOWN][2] , s[FRONT][8]),

                    "cornerQ": (s[BACK][0] , s[RIGHT][2], s[UP][2]),
                    "cornerR": (s[BACK][2] , s[UP][0]   , s[LEFT][0]),
                    "cornerS": (s[BACK][8] , s[LEFT][6] , s[DOWN][6]),
                    "cornerT": (s[BACK][6] , s[DOWN][8] , s[RIGHT][8]),

                    "cornerU": (s[DOWN][0] , s[LEFT][8] , s[FRONT][6]),
                    "cornerV": (s[DOWN][2] , s[FRONT][8], s[RIGHT][6]),
                    "cornerW": (s[DOWN][8] , s[RIGHT][8], s[BACK][6]),
                    "cornerX": (s[DOWN][6] , s[BACK][8] , s[LEFT][8])
                }

                self.__centers: dict[str, int] = \
                {
                    "centerUP"   : s[UP][4],
                    "centerLEFT" : s[LEFT][4],
                    "centerFRONT": s[FRONT][4],
                    "centerRIGHT": s[RIGHT][4],
                    "centerBACK" : s[BACK][4],
                    "centerDOWN" : s[DOWN][4]
                }

                for key in self.__edges.copy():
                    self.__edges[self.__edges[key]] = key
                for key in self.__corners.copy():
                    self.__corners[self.__corners[key]] = key
                for key in self.__centers.copy():
                    self.__centers[self.__centers[key]] = key
            
            return
        
        #  Call the helper in the wrapper function
        performMovesHelper(self, moves)
        return moves

    #  Returns the string of cube rotations needed to rotate the cube such that the color0 face is on top,
    #  and the color1 face is on the front. color0 and color1 must be distinct adjacent faces on the cube.
    #  The color of a face is entirely determined by the color of the center piece of that face.
    def rotatePosition(self, color0: int, color1: int) -> str:
        if(color0 not in range(6)):
            raise ValueError(f"rotatePosition:\n\tparameter color0 \"{str(color0)}\" is not a valid integer.")
        elif(color1 not in range(6)):
            raise ValueError(f"rotatePosition:\n\tparameter color1 \"{str(color1)}\" is not a valid integer.")
        elif(FLIP_COLOR[color0] == FLIP_COLOR[color1]):
            raise ValueError(f"rotatePosition:\n\tparameters color0 and color1 \"({color0}, {color1})\" are not adjacent colors.")
        else:
            result: str = ""

            #  Rotate the cube so the desired color is on the top using only x and z rotations.
            match self.__centers[color0].split("r")[1]:
                case "UP":
                    pass
                case "LEFT":
                    result += "z"
                case "FRONT":
                    result += "x"
                case "RIGHT":
                    result += "z'"
                case "BACK":
                    result += "x'"
                case _:   #  case "DOWN":
                    result += "x2"

            firstRotation: str = result
            self.performMoves(firstRotation)

            #  Rotate the cube so the desired color is on the front using only y rotations, preserving the color on the top.
            match self.__centers[color1].split("r")[1]:
                case "LEFT":
                    result += " y'"
                case "FRONT":
                    pass
                case "RIGHT":
                    result += " y"
                case _:   #  case "BACK":
                    result += " y2"
            
            self.performMoves(invertMove(firstRotation))
            return result.strip()


    #  Returns the string of moves needed to insert the edge with the two given colors (ints) into the right edge
    #  slot on the bottom face of the cube. This is for solving the first layer, other solved cross pieces would be
    #  preserved. After performing this sequence of moves on the cube, crossColor would be at the edgeV position,
    #  and adjColor would be at the edgeO position. Returns -1 if the given edge is not found on the cube.
    def insertCrossEdge(self, crossColor: int, adjColor: int) -> str | int:
        self.validate()
        if(not isValidEdge(crossColor, adjColor)):
            raise ValueError(f"insertCrossPiece:\n\parameters color0 and color1: \"({crossColor}, {adjColor})\" is not a valid edge.")
        else:
            match self.__edges[crossColor, adjColor][-1]:
                case "A":
                    return "U R2"
                case "B":
                    return "R2"
                case "C":
                    return "U' R2"
                case "D":
                    return "U2 R2"
                
                case "E":
                    return "U' (F R' F')"
                case "F":
                    return "D' F' D"
                case "G":
                    return "L' (D' F' D)"
                case "H":
                    return "D B D'"
                
                case "I":
                    return "F R' F'"
                case "J":
                    return "R'"
                case "K":
                    return "F' R'"
                case "L":
                    return "D2 L D2"
                
                case "M":
                    return "U (F R' F')"
                case "N":
                    return "D B' D'"
                case "O":
                    return "R (D' F D)"
                case "P":
                    return "D' F D"
                
                case "Q":
                    return "B' R B"
                case "R":
                    return "D2 L' D2"
                case "S":
                    return "B R"
                case "T":
                    return "R"
                
                case "U":
                    return "F' (D' F D)"
                case "V":
                    return ""
                case "W":
                    return "B (D B' D')"
                case "X":
                    return "L2 U2 R2"
                case _:
                    return -1

    #  Returns the string of moves needed to insert the corner with the three given colors (ints) into the top right
    #  slot on the bottom face of the cube. This is for solving the first layer, the rest of the solved first layer would
    #  be preserved. After performing this sequence of moves on the cube, color0 would be at the cornerV position,
    #  color1 would be at the cornerK position, and color2 would be at the cornerP position. Returns -1 if the given edge is
    #  not found on the cube.
    def insertFirstCorner(self, color0: int, color1: int, color2: int) -> str | int:
        self.validate()
        if(not isValidCorner(color0, color1, color2)):
            raise ValueError(f"insertCrossPiece:\n\parameters color0 and color1: \"({color0}, {color1}, {color2})\" is not a valid corner.")
        else:
            match self.__corners[color0, color1, color2][-1]:
                case "A":
                    return "(L U' L') (R U R')"
                case "B":
                    return "R' U R2 U' R'"
                case "C":
                    return "(R U' R') (F' U2 F)"
                case "D":
                    return "U2 R' U R2 U' R'"
                
                case "E":
                    return "F' U2 F"
                case "F":
                    return "R U' R'"
                case "G":
                    return "L' R U' R' L"
                case "H":
                    return "L F' U2 F L'"
                
                case "I":
                    return "U' (R U R')"
                case "J":
                    return "F' U' F"
                case "K":
                    return "(R U' R') (F' U' F)"
                case "L":
                    return "F U F2 U2 F"
                
                case "M":
                    return "R U R'"
                case "N":
                    return "U (F' U' F)"
                case "O":
                    return "R' U2 R2 U' R'"
                case "P":
                    return "(R U R' U') (R U R')"
                
                case "Q":
                    return "F' U F"
                case "R":
                    return "R U2 R'"
                case "S":
                    return "(L U' L') (R U2 R')"
                case "T":
                    return "(R' U R) (F' U F)"
                
                case "U":
                    return "(L' U' L) (R U R')"
                case "V":
                    return ""
                case "W":
                    return "(B U B') (F' U' F)"
                case "X":
                    return "(L U2 L') (F' U' F)"
                case _:
                    return -1


#  end: class Cube






#  The first function called when the main program is run
def runMain() -> None:
    CCN: str = STR_COLORS_FULL.index("green".strip().lower())   #  Cross Color Number

    myCube         : Cube = Cube(moves := generateRandomMoves(10))
    isValidScramble: bool = True

    for i in range(1):
        if(not
           (
               myCube._Cube__centers["centerUP"   ] == FLIP_COLOR[myCube._Cube__centers["centerDOWN"]] and  \
               myCube._Cube__centers["centerRIGHT"] == FLIP_COLOR[myCube._Cube__centers["centerLEFT"]] and  \
               myCube._Cube__centers["centerFRONT"] == FLIP_COLOR[myCube._Cube__centers["centerBACK"]] and  \
               isValidCorner(myCube._Cube__centers["centerUP"   ],
                             myCube._Cube__centers["centerRIGHT"],
                             myCube._Cube__centers["centerFRONT"])
           )
        ):
            isValidScramble = False
            print("Sorry, the colors you entered don't make a valid Rubik's cube, the center pieces are incorrect.\n" +  \
                  "Remember that this program only solves Rubik's cubes that use the standard western (\"BOY\") color scheme.\nTry again:")
            break
        
        initialRotations: str = myCube.rotatePosition(FLIP_COLOR[CCN], BLUE if(CCN not in [BLUE, GREEN]) else WHITE)
        print(f"{moves} {initialRotations}".strip())
        myCube.performMoves(initialRotations)       #  rotate the cube so that the cross color is on the bottom
        myCube.printCube()
        print("\n" * 5)

        COLOR_SCHEME: dict[str, list[Any]] = {
            "integer": [
                CCN,
                myCube._Cube__centers["centerRIGHT"],
                myCube._Cube__centers["centerBACK"],
                myCube._Cube__centers["centerLEFT"],
                myCube._Cube__centers["centerFRONT"],
                FLIP_COLOR[CCN]
            ]
        }
        COLOR_SCHEME["word"]: list[str] = [STR_COLORS_FULL[x] for x in COLOR_SCHEME["integer"]]
        COLOR_SCHEME["RGB" ]: list[str] = [RGB_COLORS     [x] for x in COLOR_SCHEME["integer"]]
        
        solveBreakdown: list[str]  = [f"{BOLD}{UNDERLINE}Solve Breakdown{DEFAULT}{BOLD}:{DEFAULT}\n"]
        fullSolution  : str        = ""
        indent        : int        = 0

        solveBreakdown.append(f"{BOLD}Rotate the entire cube so that the face with the cross color is on the bottom:{DEFAULT} {initialRotations}\n\n" +  \
                            f"{BOLD}The first (bottom) layer:")
        indent += 1
        solveBreakdown.append(("   " * indent) + f"{ITALICS}Solving the cross:{DEFAULT}")
        indent += 1


        #  Solving the cross of the first layer
        for i in range(len(COLOR_SCHEME["integer"][1: 5])):
            if((newPart := myCube.insertCrossEdge(CCN, COLOR_SCHEME["integer"][i + 1])) == -1):
                isValidScramble = False
                print("Sorry, the colors you entered don't make a valid Rubik's cube, the edge pieces are incorrect.\n" +  \
                      "Remember that this program only solves Rubik's cubes that use the standard western (\"BOY\") color scheme.\nTry again:")
                break
            fullSolution += f"{newPart} D' "
            myCube.performMoves(newPart + " D'")
            solveBreakdown.append(
                ("   " * indent) + "Insert the " + COLOR_SCHEME["RGB"][0] + COLOR_SCHEME["word"][0] + DEFAULT + "-" +  \
                COLOR_SCHEME["RGB"][i + 1] + (COLOR_SCHEME["word"][i + 1] + "    ")[:7] + DEFAULT + f"cross piece:   " + cleanUpSpacing(f"({newPart}) D'")
            )

        if(not isValidScramble):
            break

        #  Solving the corners of the first layer
        0




    myCube.printCube()
    print("\n" * 3)




    if(isValidScramble):
        #  Print out the final results of the solve
        solveBreakdown.append(CROSSED + (177 * " ") + DEFAULT)
        solveBreakdown.append(f"\nHolding the cube with the {G}{BOLD}GREEN{DEFAULT} side on the {BOLD}{UNDERLINE}BOTTOM{DEFAULT} and the " +  \
                            f"{BOLD}WHITE{DEFAULT} side in {BOLD}{UNDERLINE}FRONT{DEFAULT} (facing you), here is the solution to solve your cube!" +  \
                            "\nRemember that the color of a side is determined by the color of its center.")
        solveBreakdown.append(f"{BOLD}{UNDERLINE}Full (simplified) solution{DEFAULT}{BOLD}:    {simplifyMoves(fullSolution)}{DEFAULT}")
        for i in range(len(solveBreakdown)):
            print(solveBreakdown[i])

    return

    

#  The main program! This is what runs first when the program is started.
if __name__ == "__main__":
    runMain()
    exit()    #  After running the program, exit successfully.
