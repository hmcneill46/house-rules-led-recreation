"""
house_rules.py

Pygame recreation of Rose Finn-Kelcey "House Rules" LED sign (dot-matrix).
Updated: flashing now pauses scrolling, clears screen, flashes word, then resumes.
"""

import pygame, sys, random, time

# ---------------- CONFIG ----------------
MATRIX_HEIGHT = 7
MATRIX_WIDTH = 7 * 5
LED_ON_COLOR = (239, 69, 44)
LED_OFF_COLOR = (52, 52, 52)
DISPLAY_BG_COLOR = (20, 20, 20)
LETTERBOX_COLOR = (0, 0, 0)

WINDOW_DEFAULT_SIZE = (800, 300)
FPS = 60
SCROLL_SPEED_COLS_PER_SEC = 20.0

FLASH_WORDS = ["fuck!", "bored!", "whatever!", "what?", "wow!"]
FLASH_MIN_INTERVAL = 6.0
FLASH_MAX_INTERVAL = 18.0
FLASH_DURATION = 0.9

COMMANDS = ["no dying", "no flirting", "no moaning",
            "no joking", "no flipping", "no biting",
            "no punching", "no trashing", "no bellowing",
            "no smoking", "no kicking", "no meddling",
            "no stamping", "no folding", "no shoving",
            "no leaking", "no bruising", "no teasing",
            "no licking", "no flossing", "no baiting",
            "no chasing", "no plastering", "no gyrating",
            "no saucing", "no sloshing", "no cooling",
            "no battering", "no taming", "no dissecting",
            "no beating", "no fondling", "no hating",
            "no loitering", "no watering", "no lying",
            "no snorting", "no relaxing", "no undressing",
            "no clamping"]

# NEW variable: how many blank columns between phrases
PHRASE_GAP = 6  # increase this to separate phrases further apart visually

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
    'r': ["000","000","011","100","100","100","100"], # Confirmed correct
    's': ["0000","0000","0111","1000","0110","0001","1110"], # Confirmed correct
    't': ["100","100","111","100","100","100","011"], # Confirmed correct
    'u': ["0000","0000","1001","1001","1001","1001","0110"], # Confirmed correct
    'v': ["00000","00000","10001","10001","10001","01010","00100"], # Confirmed correct
    'w': ["00000","00000","10101","10101","10101","10101","01010"], # Confirmed correct
    'x': ["00000","00000","10001","01010","00100","01010","10001"], # Confirmed correct
    'y': ["0000","0000","1001","1001","0111","0001","1110"], # Confirmed correct
    'z': ["0000","0000","1111","0001","0110","1000","1111"], # Confirmed correct
    '!': ["001","001","001","001","000","001","001"], # Confirmed correct
    '?': ["01110","10001","00001","00010","00100","00000","00100"], # Confirmed correct
    ' ': ["00"] * 7,
} # Q missing from letters, will try and add later

q_options = {1:["0000","0000","0110","1001","1001","0111","0001"], # Decent, flipped p
             2:["0000","0000","0110","1001","1001","0110","0001"], # Decent, like 'o' with tail
             }

chosen_q = random.randint(1, len(q_options))
FONT['q'] = q_options[chosen_q]
print(f"Chosen 'q' pattern: {chosen_q}")

# Between each character there should be one blank column
INTER_CHAR_BLANKS = 1

# Visual tuning: what fraction of the cell is the LED circle
LED_CIRCLE_RATIO = 0.95

# ------------------------------------------------------------------------------

def char_to_columns(ch):
    ch = ch.lower()
    if ch not in FONT:
        rows = FONT[' ']
    else:
        rows = FONT[ch]

    if len(rows) < MATRIX_HEIGHT:
        pad_top = MATRIX_HEIGHT - len(rows)
        rows = (["0" * len(rows[0])] * pad_top) + rows

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

def build_phrase_columns(phrase):
    """Convert one full phrase (e.g. 'no dying') into column data."""
    return text_to_columns(phrase)

def build_full_scroll_buffer(commands, phrase_gap):
    """Builds one continuous column buffer of all commands, each separated by blanks."""
    all_cols = []
    gap = [[0]*MATRIX_HEIGHT for _ in range(phrase_gap)]
    randomised = commands[:]  # shuffle so order changes each time
    random.shuffle(randomised)
    for phrase in randomised:
        all_cols.extend(build_phrase_columns(phrase))
        all_cols.extend(gap)
    # Repeat once to ensure wrap continuity
    all_cols.extend(all_cols[:MATRIX_WIDTH])
    return all_cols

pygame.init()
clock = pygame.time.Clock()
screen = pygame.display.set_mode(WINDOW_DEFAULT_SIZE, pygame.RESIZABLE)
pygame.display.set_caption("House Rules — LED Dot Matrix Recreation")

def build_scrolling_columns_for_command(cmd_text):
    cols = text_to_columns(cmd_text)
    gap = [[0] * MATRIX_HEIGHT for _ in range(MATRIX_WIDTH // 2)]
    return cols + gap

def command_generator():
    pool = COMMANDS[:]
    random.shuffle(pool)
    while True:
        if not pool:
            pool = COMMANDS[:]
            random.shuffle(pool)
        yield pool.pop()

cmd_gen = command_generator()
current_cmd = next(cmd_gen)
scrolling_columns = build_scrolling_columns_for_command(current_cmd)
scroll_offset = 0.0
looping_buffer = scrolling_columns + scrolling_columns

next_flash_time = time.time() + random.uniform(FLASH_MIN_INTERVAL, FLASH_MAX_INTERVAL)
is_flashing = False
flash_start_time = 0.0
current_flash_word = ""
saved_scroll_offset = 0.0  # where we paused for the flash

def schedule_next_flash():
    global next_flash_time
    next_flash_time = time.time() + random.uniform(FLASH_MIN_INTERVAL, FLASH_MAX_INTERVAL)

schedule_next_flash()

def get_visible_columns(buffer_cols, offset):
    start_idx = int(offset) % len(buffer_cols)
    out = []
    for i in range(MATRIX_WIDTH):
        out.append(buffer_cols[(start_idx + i) % len(buffer_cols)])
    return out

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

            # If only_flash True, we show only the flash_word pixels as ON; everything else is OFF
            if only_flash:
                color = LED_ON_COLOR if flash_bit else LED_OFF_COLOR
            else:
                # Normal behaviour: flashing could overlay, but we don't use overlay now (kept for completeness)
                if flash_bit:
                    color = LED_ON_COLOR
                else:
                    color = LED_ON_COLOR if bit else LED_OFF_COLOR

            cx = start_x + col_idx * cell_size + cell_size / 2.0
            cy = start_y + row_idx * cell_size + cell_size / 2.0
            pygame.draw.circle(surface, color, (int(cx), int(cy)), int(radius))

def build_flash_columns(word):
    cols = text_to_columns(word)
    cols = cols[:MATRIX_WIDTH]
    left_pad = max(0, (MATRIX_WIDTH - len(cols)) // 2)
    full = [[0] * MATRIX_HEIGHT for _ in range(left_pad)] + cols
    if len(full) < MATRIX_WIDTH:
        full += [[0] * MATRIX_HEIGHT for _ in range(MATRIX_WIDTH - len(full))]
    return full[:MATRIX_WIDTH]

def main():
    global screen
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_DEFAULT_SIZE, pygame.RESIZABLE)
    pygame.display.set_caption('Recreation of "House Rules" — Rose Finn-Kelcey')
    clock = pygame.time.Clock()

    # Build long scrolling buffer
    full_buffer = build_full_scroll_buffer(COMMANDS, PHRASE_GAP)
    scroll_offset = 0.0

    next_flash_time = time.time() + random.uniform(FLASH_MIN_INTERVAL, FLASH_MAX_INTERVAL)
    is_flashing = False
    flash_start = 0.0
    flash_word = ""
    saved_scroll_offset = 0.0

    last_time = time.time()
    running = True

    while running:
        now = time.time()
        dt = now - last_time
        last_time = now

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)

        # --- Flash control (unchanged) ---
        if not is_flashing and now >= next_flash_time:
            is_flashing = True
            flash_start = now
            flash_word = random.choice(FLASH_WORDS)
            saved_scroll_offset = scroll_offset
        elif is_flashing and (now - flash_start) >= FLASH_DURATION:
            is_flashing = False
            flash_word = ""
            next_flash_time = time.time() + random.uniform(FLASH_MIN_INTERVAL, FLASH_MAX_INTERVAL)

        # --- Scroll logic ---
        if not is_flashing:
            scroll_offset += SCROLL_SPEED_COLS_PER_SEC * dt
        else:
            scroll_offset = saved_scroll_offset

        # --- Drawing ---
        window_w, window_h = screen.get_size()
        screen.fill(LETTERBOX_COLOR)
        disp_rect = compute_display_area(window_w, window_h)

        if is_flashing:
            flash_cols = build_flash_columns(flash_word)
            empty_visible = [[0]*MATRIX_HEIGHT for _ in range(MATRIX_WIDTH)]
            render_matrix(screen, disp_rect, empty_visible, flash_columns=flash_cols, only_flash=True)
        else:
            visible = get_visible_columns(full_buffer, scroll_offset)
            render_matrix(screen, disp_rect, clip_columns_to_matrix(visible))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()