"""
house_rules_recreation.py

Working Pygame recreation of Rose Finn-Kelcey "House Rules" LED sign (dot-matrix).
Follows the schedule structure you supplied: sequential commands, no shared state.
"""

import pygame
import sys

# ---------------- CONFIG ----------------
MATRIX_HEIGHT = 7
MATRIX_WIDTH = 7 * 5  # 35 by default; matches your descriptions
LED_ON_COLOR = (255, 0, 0)
LED_OFF_COLOR = (52, 52, 52)
DISPLAY_BG_COLOR = (20, 20, 20)
LETTERBOX_COLOR = (0, 0, 0)
WINDOW_WIDTH_MM = 100 # Real width of the sign in mm is 88.9mm (3.5 inches)

"""
# Variables to change per your screen
# M1 MacBook Air 2020 Retina display example
real_screen_res = (2560, 1600)
real_screen_diagonal_inch = 13.3
scaling_factor = 0.761904761904761904761904 # 2560/3360
is_HiDPI = True
#####################################
# """

# Variables to change per your screen
real_screen_res = (3840, 2160)
real_screen_diagonal_inch = 27
scaling_factor = 1.25
is_HiDPI = False
#####################################

# ---------- Calculate effective PPI and window size ----------
effective_screen_size = (real_screen_res[0] / (scaling_factor/2), real_screen_res[1] / (scaling_factor/2)) if is_HiDPI else (real_screen_res[0] / scaling_factor, real_screen_res[1] / scaling_factor)

aspect_ratio = real_screen_res[0] / real_screen_res[1]

real_screen_horizontal_inch = (real_screen_diagonal_inch ** 2 / (1 + (1 / aspect_ratio) ** 2)) ** 0.5
real_screen_vertical_inch = real_screen_horizontal_inch / aspect_ratio

effective_ppi = (effective_screen_size[0]) / real_screen_horizontal_inch

effective_pixels_per_mm = effective_ppi / 25.4

WINDOW_WIDTH = WINDOW_WIDTH_MM * effective_pixels_per_mm
# -------------------------------------------------------------

WINDOW_DEFAULT_SIZE = (int(WINDOW_WIDTH), (WINDOW_WIDTH*(MATRIX_HEIGHT/MATRIX_WIDTH)))
FPS = 60
SCROLL_SPEED_COLS_PER_SEC = 47.5  # columns scrolled per second when not flashing
#SCROLL_SPEED_COLS_PER_SEC = 1

PHRASE_GAP = 8
INTER_CHAR_BLANKS = 1
LED_CIRCLE_RATIO = 0.95

# ---------- FONT ----------
FONT = {
    'a': ["0000","0000","0110","0001","0111","1001","0111"], # Confirmed correct
    'b': ["1000","1000","1110","1001","1001","1001","0110"], # Confirmed correct
    'c': ["000","000","011","100","100","100","011"], # Confirmed correct
    'd': ["0001","0001","0111","1001","1001","1001","0110"], # Confirmed correct
    'e': ["0000","0000","0110","1001","1111","1000","0111"], # Confirmed correct
    'f': ["011","100","111","100","100","100","100"], # Confirmed correct
    'g': ["0000","0000","0110","1001","1111","0001","1110"], # Confirmed correct
    'h': ["1000","1000","1110","1001","1001","1001","1001"], # Confirmed correct
    'i': ["1","0","1","1","1","1","1"], # Confirmed correct
    'j': ["01","00","01","01","01","01","11"], # Confirmed correct
    'k': ["1000","1000","1001","1010","1100","1010","1001"], # Confirmed correct
    'l': ["1","1","1","1","1","1","1"], # Confirmed correct
    'm': ["00000","00000","01010","10101","10101","10101","10101"], # Confirmed correct
    'n': ["0000","0000","0110","1001","1001","1001","1001"], # Confirmed correct
    'o': ["0000","0000","0110","1001","1001","1001","0110"], # Confirmed correct
    'p': ["0000","0000","0110","1001","1001","1110","1000"], # Confirmed correct
    'q': ["0000","0000","0110","1001","1001","0111","0001"], # Confirmed correct
    'r': ["000","000","011","100","100","100","100"], # Confirmed correct
    's': ["0000","0000","0111","1000","0110","0001","1110"], # Confirmed correct
    't': ["100","100","111","100","100","100","011"], # Confirmed correct
    'u': ["0000","0000","1001","1001","1001","1001","0110"], # Confirmed correct
    'v': ["00000","00000","10001","10001","10001","01010","00100"], # Confirmed correct
    'w': ["00000","00000","10101","10101","10101","10101","01010"], # Confirmed correct
    'x': ["00000","00000","10001","01010","00100","01010","10001"], # Confirmed correct
    'y': ["0000","0000","1001","1001","0111","0001","1110"], # Confirmed correct
    'z': ["0000","0000","1111","0001","0110","1000","1111"], # Confirmed correct
    '!': ["1","1","1","1","0","1","1"], # Confirmed correct
    '?': ["01110","10001","00001","00010","00100","00000","00100"], # Confirmed correct
    ' ': ["0"] * 7,
} 


# ---------- Sequence (from user's data) ----------

sequence = [
    {"type": "scrolling",
     "content": ["no lingering", "no snacking", "no cycling",
                 "no molesting", "no phoning", "no tampering",
                 "no humping", "no waiting", "no serving",
                 "no shaming", "no busting", "no crying",
                 "no stealing", "no knocking", "no shouting",
                 "no littering", "no trucking", "no spitting",
                 "no fixing", "no oiling", "no throwing",
                 "no canvassing", "no conoodling", "no worshipping",
                 "no stopping", "no pleasing", "no groveling"],
     "start-pos": 35, # this will be just off screen, so the first time it scrolls in it appears from the right
     "end-gap": 5},

    {"type": "flash",
     "word": "fuck off",
     "word-pos": 3,
     "punctuation": "",
     "punctuation_pos": -1,
     "flash-duration": 12},  # [3]fuck off[0]

    {"type": "scrolling",
     "content": ["no weeping", "no bribing", "no dumping",
                 "no stewing", "no pushing", "no stirring",
                 "no baking", "no farting", "no drinking",
                 "no playing", "no fighting", "no gutting",
                 "no demanding", "no hitting", "no dying",
                 "no flirting", "no moaning", "no joking",
                 "no tensing", "no flipping", "no biting"],
     "start-pos": 8,
     "end-gap": 1},

    {"type": "flash",
     "word": "sod it",
     "word-pos": 6,
     "punctuation": "",
     "punctuation_pos": -1,
     "flash-duration": 12}, # [6]sod it[7]

    {"type": "scrolling",
     "content": ["no punching", "no trashing", "no bellowing",
                 "no smoking", "no kicking", "no meddling",
                 "no stamping", "no folding", "no stabbing",
                 "no bellowing", "no shoving"],
     "start-pos": 0,
     "end-gap": 1},

    {"type": "flash",
     "word": "what",
     "word-pos": 6,
     "punctuation": "?",
     "punctuation_pos": 26,
     "flash-duration": 25}, # [6]what?[5]

    {"type": "scrolling",
     "content": ["no leaking", "no bruising", "no teasing",
                 "no licking", "no flossing", "no baiting",
                 "no chasing", "no plastering", "no gyrating",
                 "no saucing", "no sloshing", "no cooling",
                 "no battering", "no taming", "no dissecting",
                 "no arguing", "no driving", "no killing",
                 "no soliciting", "no drawing", "no joining",
                 "no blasting", "no voting", "no protesting",
                 "no beating", "no eating"],
     "start-pos": 1,
     "end-gap": 1},

    {"type": "flash",
     "word": "eh",
     "word-pos": 11,
     "punctuation": "?",
     "punctuation_pos": 22,
     "flash-duration": 26}, # [11]eh?[9]

    {"type": "scrolling",
     "content": ["no eating", "no fondling"],
     "start-pos": 25,
     "end-gap": 19},

    {"type": "flash",
     "word": "eh",
     "word-pos": 12,
     "punctuation": "?",
     "punctuation_pos": 23,
     "flash-duration": 25}, # [12]eh?[10]

    {"type": "scrolling",
     "content": ["no eating", "no fondling", "no yawning",
                 "no hating", "no loitering", "no sneering",
                 "no touting", "no watering", "no lying",
                 "no dragging", "no pointing", "no lifting",
                 "no picking", "no grassing", "no parking",
                 "no standing", "no snorting", "no queuing",
                 "no elbowing", "no sniffing", "no relaxing",
                 "no fluffing"],
     "start-pos": 21,
     "end-gap": 15},

    {"type": "flash",
     "word": "jeezus",
     "word-pos": 4,
     "punctuation": "!",
     "punctuation_pos": 32,
     "flash-duration": 49}, # [4]jeezus![2]

    {"type": "scrolling",
     "content": ["no jamming", "no undressing", "no clamping",
                 "no snogging", "no tripping", "no cuddling",
                 "no drooling", "no staring", "no mugging",
                 "no fixating", "no tailing", "no blaming",
                 "no crushing", "no dancing", "no mounting",
                 "no creeping", "no brewing", "no festering",
                 "no breeding", "no pumping", "no peeling",
                 "no lusting", "no dissing", "no dropping",
                 "no jerking", "no crumpling", "no looking"],
     "start-pos": 41, # this is off screen (on standard 35 wide screen) so the screen will start blank until the text scrolls in
     "end-gap": 2}, 

    {"type": "flash",
     "word": "whoa",
     "word-pos": 6,
     "punctuation": "!",
     "punctuation_pos": 28,
     "flash-duration": 49}, # [6]whoa![6]

    {"type": "scrolling",
     "content": ["no carting", "no necking", "no abducting",
                 "no blowing", "no fagging", "no deserting",
                 "no invading", "no retouching", "no fumbling",
                 "no chewing", "no defacing", "no slipping",
                 "no whitewashing", "no relapsing", "no nodding",
                 "no dodging", "no gossiping", "no blanking",
                 "no needling", "no floating", "no spanking",
                 "no gaming", "no kneeing", "no stretching",
                 "no trusting", "no harassing", "no toasting",
                 "no sampling", "no washing", "no exposing",
                 "no listening", "no fibbing", "no bossing",
                 "no accelerating", "no dawdling"],
     "start-pos": 2,
     "end-gap": 1},

    {"type": "flash",
     "word": "fuck it",
     "word-pos": 5,
     "punctuation": "",
     "punctuation_pos": -1,
     "flash-duration": 12}, # [5]fuck it[4]

    {"type": "scrolling",
     "content": ["no fathering", "no hanging", "no filming",
                 "no rushing", "no watching", "no kidding",
                 "no perverting", "no nipping", "no cruising",
                 "no pinching", "no fidgeting", "no kissing",
                 "no cheating", "no speeding", "no blocking"],
     "start-pos": 1,
     "end-gap": 1},

    {"type": "flash",
     "word": "huh",
     "word-pos": 9,
     "punctuation": "?",
     "punctuation_pos": 25,
     "flash-duration": 26}, # [9]huh?[6]

    {"type": "scrolling",
     "content": ["no shirking", "no brushing", "no hurting",
                 "no dirtying", "no whispering", "no snoring",
                 "no running", "no fingering", "no blackmailing",
                 "no snorting", "no frowning", "no laughing",
                 "no stalking", "no yawning", "no flannelling",
                 "no trading", "no jabbing", "no chasing",
                 "no hoarding", "no trafficking", "no bullying",
                 "no tiptoeing", "no smarting", "no groaning",
                 "no feuding", "no circling", "no groping",
                 "no bawling", "no jumping"],
     "start-pos": 15,
     "end-gap": 1},

    {"type": "flash",
     "word": "wait",
     "word-pos": 8,
     "punctuation": "!",
     "punctuation_pos": 26,
     "flash-duration": 49}, # [8]wait![8]

    {"type": "scrolling",
     "content": ["no laundering", "no gawping", "no spiking",
                 "no weeding", "no touching", "no aiding",
                 "no charging", "no limping", "no abetting",
                 "no smuggling", "no drooping", "no mouthing",
                 "no jawing", "no climbing", "no faking",
                 "no leaving", "no rioting", "no breathing",
                 "no stealing", "no boring", "no sweating",
                 "no crawling", "no creeping"],
     "start-pos": 3,
     "end-gap": 0},

    {"type": "flash",
     "word": "hnnh",
     "word-pos": 5,
     "punctuation": "?",
     "punctuation_pos": 27,
     "flash-duration": 50}, # [5]hnnh?[4]

    {"type": "scrolling",
     "content": ["no pouting", "no wrestling", "no knifing",
                 "no pummelling", "no shouting", "no fainting",
                 "no loafing", "no squeezing", "no vamping",
                 "no straying", "no hitching", "no picketing",
                 "no streaking", "no joyriding", "no rabbiting",
                 "no pleading", "no smiling", "no battling",
                 "no slimming", "no jeering", "no peeping",
                 "no blaming", "no stuffing", "no curating",
                 "no dating", "no pickling", "no crossing",
                 "no punching"],
     "start-pos": 1,
     "end-gap": 1},

    {"type": "flash",
     "word": "stuff it",
     "word-pos": 4,
     "punctuation": "",
     "punctuation_pos": -1,
     "flash-duration": 13}, # [4]stuff it[2]

    {"type": "scrolling",
     "content": ["no screwing", "no bleeding", "no smearing",
                 "no stroking", "no hoping", "no voting",
                 "no signing", "no crediting", "no accounting",
                 "no rolling", "no sacking", "no drafting",
                 "no ticketing", "no troubling", "no bargaining",
                 "no fingering", "no helping", "no plotting"],
     "start-pos": 5,
     "end-gap": 1},

    {"type": "flash",
     "word": "yeah",
     "word-pos": 6,
     "punctuation": "?",
     "punctuation_pos": 27,
     "flash-duration": 26}, # [6]yeah?[4]

    {"type": "scrolling",
     "content": ["no clapping", "no following", "no scribbling",
                 "no rioting", "no shipping", "no ravaging",
                 "no aiming", "no painting", "no carving",
                 "no scalping", "no flying", "no landing",
                 "no sterilising", "no robbing", "no trawling",
                 "no looting", "no leaping", "no terrorising",
                 "no spewing", "no kicking", "no kidnapping",
                 "no preaching", "no moonlighting", "no cycling",
                 "no networking", "no speeding"],
     "start-pos": 3,
     "end-gap": 1},

    {"type": "flash",
     "word": "pleeze",
     "word-pos": 4,
     "punctuation": "!",
     "punctuation_pos": 32,
     "flash-duration": 51}, # [4]pleeze![2]

    {"type": "scrolling",
     "content": ["no colouring", "no perming", "no rapping",
                 "no crowding", "no aging", "no dribbling",
                 "no pausing", "no controlling", "no panicking",
                 "no freewheeling", "no carpeting", "no fuming",
                 "no blazing", "no steaming", "no craving",
                 "no tricking", "no daring", "no moping",
                 "no operating", "no training", "no pilfering",
                 "no tresspassing", "no dillydallying"],
     "start-pos": 19,
     "end-gap": 1},

    {"type": "flash",
     "word": "aaaaah",
     "word-pos": 2,
     "punctuation": "!",
     "punctuation_pos": 32,
     "flash-duration": 49}, # [2]aaaaah![2]

    {"type": "scrolling",
     "content": ["no straining", "no commenting", "no fundraising",
                 "no developing", "no heating", "no sluicing",
                 "no judging", "no limiting", "no sweeping",
                 "no drawing", "no smacking", "no scrubbing",
                 "no roping", "no worming", "no splashing",
                 "no prowling", "no feeling", "no scoring",
                 "no embezzling", "no chasing", "no tossing",
                 "no undertaking", "no holding", "no crisscrossing",
                 "no unravelling", "no crawling"],
     "start-pos": 8,
     "end-gap": 1},

    {"type": "flash",
     "word": "sod off",
     "word-pos": 3,
     "punctuation": "",
     "punctuation_pos": -1,
     "flash-duration": 25}, # [3]sod off[3]

    {"type": "scrolling",
     "content": ["no swiping", "no smudging", "no whistling",
                 "no camping", "no delaying", "no dumping",
                 "no praying", "no grilling", "no nailing",
                 "no sliding", "no spoiling", "no breaking",
                 "no warning", "no bombing", "no driving",
                 "no backing", "no trailing", "no whoring",
                 "no railing", "no loading", "no skipping",
                 "no boating", "no milking", "no nursing",
                 "no posing", "no malarking", "no entering",
                 "no promising", "no parking", "no talking",
                 "no singing", "no policing", "no busking",
                 "no nothing"],
     "start-pos": 2,
     "end-gap": 1},

    {"type": "flash",
     "word": "stop",
     "word-pos": 7,
     "punctuation": "!",
     "punctuation_pos": 26,
     "flash-duration": 13}, # [7]stop![8]

    {"type": "scrolling",
     "content": ["no nothing", "no sponging"],
     "start-pos": 5,
     "end-gap": 1},

    {"type": "flash",
     "word": "stop",
     "word-pos": 6,
     "punctuation": "!",
     "punctuation_pos": 25,
     "flash-duration": 13}, # [6]stop![9]

    {"type": "scrolling",
     "content": ["no sedating", "no itching"],
     "start-pos": 2,
     "end-gap": 1},

    {"type": "flash",
     "word": "stop",
     "word-pos": 7,
     "punctuation": "!",
     "punctuation_pos": 26,
     "flash-duration": 13}, # [7]stop![8]

    {"type": "scrolling",
     "content": ["no quoting", "no ending"],
     "start-pos": 0,
     "end-gap": 5}
]


# ---------------- Helper functions ----------------
def char_to_columns(ch):
    ch = ch.lower()
    if ch not in FONT:
        rows = FONT[' ']
    else:
        rows = FONT[ch]

    # pad top if needed
    if len(rows) < MATRIX_HEIGHT:
        pad_top = MATRIX_HEIGHT - len(rows)
        rows = ([("0" * len(rows[0]))] * pad_top) + rows

    char_width = len(rows[0])
    cols = []
    for c in range(char_width):
        col = []
        for r in range(MATRIX_HEIGHT):
            bit = rows[r][c] if c < len(rows[r]) else "0"
            col.append(1 if bit == "1" else 0)
        cols.append(col)
    return cols


def text_to_columns(text):
    all_cols = []
    for i, ch in enumerate(text):
        ch_cols = char_to_columns(ch)
        all_cols.extend(ch_cols)
        for _ in range(INTER_CHAR_BLANKS):
            all_cols.append([0] * MATRIX_HEIGHT)
    return all_cols

def clip_columns_to_matrix(cols):
    if len(cols) >= MATRIX_WIDTH:
        return cols[:MATRIX_WIDTH]
    pad = [[0] * MATRIX_HEIGHT for _ in range(MATRIX_WIDTH - len(cols))]
    return cols + pad


def compute_display_area(window_w, window_h):
    target_ratio = MATRIX_WIDTH / MATRIX_HEIGHT
    win_ratio = window_w / window_h
    if win_ratio > target_ratio:
        h = window_h
        w = int(h * target_ratio)
    else:
        w = window_w
        h = int(w / target_ratio)
    x = (window_w - w) // 2
    y = (window_h - h) // 2
    return pygame.Rect(x, y, w, h)


def render_matrix(surface, disp_rect, visible_columns, flash_columns=None, only_flash=False):
    surface.fill(DISPLAY_BG_COLOR, disp_rect)

    cell_w = disp_rect.width / MATRIX_WIDTH
    cell_h = disp_rect.height / MATRIX_HEIGHT
    cell_size = min(cell_w, cell_h)
    circle_diam = cell_size * LED_CIRCLE_RATIO
    circle_diam = min(circle_diam, cell_size * 0.98)
    radius = circle_diam / 2.0

    total_grid_w = cell_size * MATRIX_WIDTH
    total_grid_h = cell_size * MATRIX_HEIGHT
    start_x = disp_rect.x + (disp_rect.width - total_grid_w) / 2.0
    start_y = disp_rect.y + (disp_rect.height - total_grid_h) / 2.0

    for col_idx in range(MATRIX_WIDTH):
        col = visible_columns[col_idx]
        for row_idx in range(MATRIX_HEIGHT):
            bit = col[row_idx]
            if flash_columns:
                flash_bit = flash_columns[col_idx][row_idx]
            else:
                flash_bit = 0

            if only_flash:
                color = LED_ON_COLOR if flash_bit else LED_OFF_COLOR
            else:
                if flash_bit:
                    color = LED_ON_COLOR
                else:
                    color = LED_ON_COLOR if bit else LED_OFF_COLOR

            cx = start_x + col_idx * cell_size + cell_size / 2.0
            cy = start_y + row_idx * cell_size + cell_size / 2.0
            pygame.draw.circle(surface, color, (int(cx), int(cy)), int(radius))


def build_scrolling_buffer_for_cmd(cmd):
    """Return list of columns for this scrolling command, taking into account:
       - start-pos blank columns (initial offset to the right)
       - each phrase separated by PHRASE_GAP blank columns
       - end-gap blank columns at the end
    """
    start_pos = int(cmd.get("start-pos", 0))
    end_gap = int(cmd.get("end-gap", 0))
    buffer_cols = []

    # start-pos: blank columns on the *left* of the buffer so the text will appear from the right as we scroll
    for _ in range(start_pos):
        buffer_cols.append([0] * MATRIX_HEIGHT)

    # add each phrase
    for i, phrase in enumerate(cmd.get("content", [])):
        buffer_cols.extend(text_to_columns(phrase))
        # phrase gap after each phrase
        for _ in range(PHRASE_GAP):
            buffer_cols.append([0] * MATRIX_HEIGHT)

    # append end-gap blanks
    for _ in range(end_gap):
        buffer_cols.append([0] * MATRIX_HEIGHT)

    return buffer_cols


def build_flash_columns(word, word_pos=0, punctuation="", punctuation_pos=-1):
    """Construct columns for a flash screen of width MATRIX_WIDTH.
       - word_pos is the left padding (0 means touching left edge).
       - punctuation_pos is an absolute column position on display (0..MATRIX_WIDTH-1). If -1, ignore.
    """
    cols = text_to_columns(word)
    # Clip the word to the width if it's too wide
    if len(cols) > MATRIX_WIDTH:
        cols = cols[:MATRIX_WIDTH]

    # Build left padding
    left_pad = max(0, word_pos)
    full = [[0] * MATRIX_HEIGHT for _ in range(left_pad)] + cols

    # Ensure full is at least MATRIX_WIDTH; pad right if needed
    if len(full) < MATRIX_WIDTH:
        full += [[0] * MATRIX_HEIGHT for _ in range(MATRIX_WIDTH - len(full))]
    else:
        full = full[:MATRIX_WIDTH]

    # Add punctuation (if provided and in FONT)
    if punctuation and 0 <= punctuation_pos < MATRIX_WIDTH:
        pcols = text_to_columns(punctuation)
        # place punctuation columns starting at punctuation_pos (replace existing)
        for i, pcol in enumerate(pcols):
            idx = punctuation_pos + i
            if 0 <= idx < MATRIX_WIDTH:
                full[idx] = pcol

    return full


def get_visible_columns_from_buffer(buffer_cols, offset):
    """Return MATRIX_WIDTH columns: slice from buffer starting at int(offset).
       If beyond the end, pad with zero columns.
    """
    start_idx = int(offset)
    out = []
    for i in range(MATRIX_WIDTH):
        idx = start_idx + i
        if 0 <= idx < len(buffer_cols):
            out.append(buffer_cols[idx])
        else:
            out.append([0] * MATRIX_HEIGHT)
    return out


# ---------------- Main program ----------------
def main(seq):
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_DEFAULT_SIZE, pygame.RESIZABLE)
    pygame.display.set_caption('Recreation of "House Rules" — Deterministic Schedule')
    clock = pygame.time.Clock()

    cmd_idx = 0
    scroll_offset = 0.0  # in columns
    is_flashing = False
    flash_frame_counter = 0
    current_flash_cols = None

    # For the current scrolling command store its buffer once created
    current_scroll_buffer = None

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # seconds elapsed since last frame

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((ev.w, ev.h), pygame.RESIZABLE)
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False

        if not seq:
            # nothing to do
            screen.fill(LETTERBOX_COLOR)
            pygame.display.flip()
            continue

        cmd = seq[cmd_idx]

        if cmd["type"] == "scrolling":
            # If we just moved to this command, build its buffer and reset offset
            if current_scroll_buffer is None:
                current_scroll_buffer = build_scrolling_buffer_for_cmd(cmd)
                scroll_offset = 0.0

            # advance scroll offset
            scroll_offset += SCROLL_SPEED_COLS_PER_SEC * dt

            # get visible slice and draw
            visible = get_visible_columns_from_buffer(current_scroll_buffer, scroll_offset)
            window_w, window_h = screen.get_size()
            screen.fill(LETTERBOX_COLOR)
            disp_rect = compute_display_area(window_w, window_h)
            render_matrix(screen, disp_rect, clip_columns_to_matrix(visible))

            # check if we've reached the end of the buffer (all columns scrolled past)
            # Once scroll_offset >= len(buffer) we have shown all columns (including any trailing end-gap)
            """if scroll_offset >= len(current_scroll_buffer):
                # move to next command
                cmd_idx = (cmd_idx + 1) % len(seq)
                current_scroll_buffer = None
                scroll_offset = 0.0
                is_flashing = False
                current_flash_cols = None
                flash_frame_counter = 0"""
                
            # check if we've reached the end of the buffer (all columns scrolled past)
            end_gap = int(cmd.get("end-gap", 0))
            if scroll_offset >= len(current_scroll_buffer) - MATRIX_WIDTH - end_gap:
                cmd_idx = (cmd_idx + 1) % len(seq)
                current_scroll_buffer = None
                scroll_offset = 0.0
                is_flashing = False
                current_flash_cols = None
                flash_frame_counter = 0


            


        elif cmd["type"] == "flash":
            # If just entered flash, build flash columns and set counters
            if not is_flashing:
                word = cmd.get("word", "")
                word_pos = int(cmd.get("word-pos", 0))
                punctuation = cmd.get("punctuation", "")
                punctuation_pos = int(cmd.get("punctuation_pos", cmd.get("punctuation_pos", -1)) if cmd.get("punctuation_pos", None) is not None else cmd.get("punctuation_pos", -1))
                flash_duration_frames = int(cmd.get("flash-duration", 1))
                # Build flash columns using absolute word_pos and punctuation_pos semantics
                current_flash_cols = build_flash_columns(word, word_pos=word_pos, punctuation=punctuation, punctuation_pos=punctuation_pos)
                is_flashing = True
                flash_frame_counter = 0
                # Clear any scrolling buffer (no memory)
                current_scroll_buffer = None
                scroll_offset = 0.0

            # Render the flash screen
            window_w, window_h = screen.get_size()
            screen.fill(LETTERBOX_COLOR)
            disp_rect = compute_display_area(window_w, window_h)
            empty_visible = [[0] * MATRIX_HEIGHT for _ in range(MATRIX_WIDTH)]
            # Only the flash columns should be visible; use only_flash=True to show only flash pixels
            render_matrix(screen, disp_rect, empty_visible, flash_columns=current_flash_cols, only_flash=True)

            flash_frame_counter += 1
            if flash_frame_counter >= int(cmd.get("flash-duration", 1)):
                # finished flashing; go to next command
                cmd_idx = (cmd_idx + 1) % len(seq)
                is_flashing = False
                current_flash_cols = None
                flash_frame_counter = 0
                current_scroll_buffer = None
                scroll_offset = 0.0

        else:
            # unsupported command type: skip forward
            cmd_idx = (cmd_idx + 1) % len(seq)
            current_scroll_buffer = None
            is_flashing = False
            current_flash_cols = None
            flash_frame_counter = 0
            scroll_offset = 0.0

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    # run
    main(sequence)
