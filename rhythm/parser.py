import music21 as m21

###############################################################################
# Helpers and classes
###############################################################################

class MyPart():
    def __init__(self, instrument, notes):
        self.instrument = instrument
        self.notes = notes

###############################################################################
# Lexer
###############################################################################
import ply.lex as lex
import re

tokens = (
        'SPACE',
        'INT',
        'LETTER',
        'TAG_INSTRUMENT',
        'STRING'
        )

t_SPACE = r'[ \t\n]+'
t_LETTER = r'[a-zA-Z]'
# t_TAG = r'\\[a-zA-Z][a-zA-Z0-9_]*'
t_TAG_INSTRUMENT = r'\\instrument'
t_STRING = r'".*"'

def t_INT(t):
    # TODO support decimals
    r'\d+'
    try:
        t.value = int(t.value)
    except ValueError:
        print("Integer value too large %d", t.value)
        t.value = 0
    return t

literals = [
        '/', '\\',
        '#', '-',
        '*',
        '%',
        '.',
        '[', ']',
        '<', '>',
        '(', ')',
        '{', '}'
        ]

# Build lexer
lexer = lex.lex()

################################################################################
# Parser
################################################################################
import ply.yacc as yacc

def p_main(t):
    """
    main : part_list
    """
    t[0] = t[1]

def p_part_list(t):
    """
    part_list : 
              | part
              | part_list SPACE part
    """
    # empty
    if len(t) == 1:
        t[0] = []
    # single
    elif len(t) == 2:
        t[0] = [ t[1] ]
    else:
        t[0] = t[1]
        t[0].append(t[3])

def p_part_default(t):
    """
    part : '[' SPACE note_series SPACE ']'
    """
    t[0] = MyPart('piano', t[5])

def p_part(t):
    """
    part : tag_instrument SPACE '[' SPACE note_series SPACE ']'
    """
    t[0] = MyPart(t[1], t[5])

def p_note_series(t):
    """
    note_series : 
                | note
                | note_series SPACE note
    """
    # empty
    if len(t) == 1:
        t[0] = []
    # single
    elif len(t) == 2:
        t[0] = [ t[1] ]
    else:
        t[0] = t[1]
        t[0].append(t[3])

def p_note(t):
    """
    note : pitch duration
    """
    t[0] = m21.note.Note(t[1], duration=t[2])

def p_pitch_natural(t):
    """
    pitch : pitch_letter
          | pitch_letter octave
    """
    if len(t) == 2:
        octave = 4
    else:
        octave = t[2]
    print(octave)
    t[0] = m21.pitch.Pitch(t[1] + str(octave))

def p_pitch_accidental(t):
    """
    pitch : pitch_letter accidental
          | pitch_letter accidental octave
    """
    if len(t) == 3:
        octave = 4
    else:
        octave = t[3]
    t[0] = m21.pitch.Pitch(t[1] + t[2] + str(octave))

def p_pitch_letter(t):
    """
    pitch_letter : LETTER
    """
    if not re.match(r"[a-gA-GxX]", t[1]):
        raise yacc.YaccError("Invalid pitch letter")
    t[0] = t[1]

def p_accidental(t):
    """
    accidental : '#'
               | '-'
    """
    t[0] = t[1]

def p_octave(t):
    """
    octave : INT
    """
    t[0] = t[1]

def p_duration_empty(t):
    "duration : "
    t[0] = m21.duration.Duration(quarterLength=1)

def p_duration_enum_denom(t):
    """
    duration : '*' enum '/' denom
             | '*' enum '/' denom dotting
    """
    # No dots
    if len(t) == 5:
        dots = 0
    # Dots
    else:
        dots = t[3]
    quarterLength = 4 * t[2] / t[4]
    t[0] = m21.duration.Duration(quarterLength=quarterLength, dots=dots)


def p_duration_enum(t):
    """
    duration : '*' enum
             | '*' enum dotting
    """
    # No dots
    if len(t) == 3:
        dots = 0
    # Dots
    else:
        dots = t[3]
    quarterLength = 4 * t[2]
    t[0] = m21.duration.Duration(quarterLength=quarterLength, dots=dots)

def p_duration_denom(t):
    """
    duration : '/' denom
             | '/' denom dotting
    """
    # No dots
    if len(t) == 3:
        dots = 0
    # Dots
    else:
        dots = t[3]
    quarterLength = 4 / t[2]
    t[0] = m21.duration.Duration(quarterLength=quarterLength, dots=dots)

def p_enum(t):
    """
    enum : INT
    """
    t[0] = t[1]

def p_denom(t):
    """
    denom : INT
    """
    t[0] = t[1]

def p_dotting_one(t):
    "dotting : '.'" # *3/2
    t[0] = 1

def p_dotting_two(t):
    "dotting : '.' '.'" # *7/4
    t[0] = 2

## def p_tag(t):
##     """
##     tag : '\\' tag_name
##         | '\\' tag_name '<' param_list '>'
##         | '\\' tag_name '(' note_series ')'
##         | '\\' tag_name '<' param_list '>' '(' note_series ')'
##     """

def p_tag_instrument(t):
    """
    tag_instrument : TAG_INSTRUMENT '<' STRING '>'
    """
    t[0] = t[3]

##
## def p_tag_id(t):
##     """
##     tag_name : 'instrument'
##              | 'key'
##              | 'meter'
##              | 'slur'
##     """
##
## param_list:
##     ''
##     param
##     param ',' param_list
## param: string

# Build parser
parser = yacc.yacc()

################################################################################
# Runner
################################################################################
while True:
    try:
        line = input('> ')
    except EOFError:
        break
    ast = parser.parse(line)

    # Create score
    score = m21.stream.Score()

    # Create parts
    for p in ast:
        part = m21.stream.Part()
        # Add instrument 
        part.insert(m21.instrument.fromString(p.instrument))
        for note in p.notes:
            part.append(note)
        score.append(part)

    # Set tempo
    tm = m21.tempo.MetronomeMark(number=60)
    score.insert(0, tm)

    print(score.show('text'))

    # Play score
    score.show('midi')
