"""
house_rules.py

Pygame recreation of Rose Finn-Kelcey "House Rules" LED sign (dot-matrix).
Updated: flashing now pauses scrolling, clears screen, flashes word, then resumes.
"""

import pygame
import sys
import time

# ---------------- CONFIG ----------------
MATRIX_HEIGHT = 7
MATRIX_WIDTH = 7 * 5
LED_ON_COLOR = (239, 69, 44)
LED_OFF_COLOR = (52, 52, 52)
DISPLAY_BG_COLOR = (20, 20, 20)
LETTERBOX_COLOR = (0, 0, 0)

WINDOW_DEFAULT_SIZE = (800, 300)
FPS = 60
SCROLL_SPEED_COLS_PER_SEC = 45.0  # columns scrolled per second when not flashing

# Ticks: discrete time unit controlling scheduling. Set to what you prefer.
TICKS_PER_SEC = 10  # how many ticks in one real second

# Ordered schedule for flashes. This is the single source of truth for flash
# timing. No randomness.
# Each entry: {'word': <str>, 'delay': <int ticks after previous flash>, 'duration': <int ticks to display>}
# Example: first flash will occur at tick = schedule[0]['delay'] (since tick starts at 0)
FLASH_SCHEDULE = [
    {'word': 'fuck!', 'delay': 5000000, 'duration': 6},
    {'word': 'bored!', 'delay': 4, 'duration': 5},
    {'word': 'whatever!', 'delay': 6, 'duration': 6},
    {'word': 'what?', 'delay': 8, 'duration': 4},
    {'word': 'wow!', 'delay': 10, 'duration': 5},
]

COMMANDS = ["no lingering", "no snacking", "no cycling",
            "no molesting", "no phoning", "no tampering",
            "no humping", "no waiting", "no serving",
            "no shaming", "no busting", "no crying",
            "no stealing", "no knocking", "no shouting",
            "no littering", "no trucking", "no spitting",
            "no fixing", "no oiling", "no throwing",
            "no canvassing", "no conoodling", "no worshipping",
            "no stopping", "no pleasing", "no groveling", # [3]fuck off[0]
            "no weeping", "no bribing", "no dumping",
            "no stewing", "no pushing", "no stirring",
            "no baking", "no farting", "no drinking",
            "no playing", "no fighting", "no gutting",
            "no demanding", "no hitting", "no dying",
            "no flirting", "no moaning", "no joking",
            "no tensing", "no flipping", "no biting", # [6]sod it[7]
            "no punching", "no trashing", "no bellowing",
            "no smoking", "no kicking", "no meddling",
            "no stamping", "no folding", "no stabbing",
            "no bellowing", "no shoving", # [6]what?[5]
            "no leaking", "no bruising", "no teasing",
            "no licking", "no flossing", "no baiting",
            "no chasing", "no plastering", "no gyrating",
            "no saucing", "no sloshing", "no cooling",
            "no battering", "no taming", "no dissecting",
            "no arguing", "no driving", "no killing",
            "no soliciting", "no drawing", "no joining",
            "no blasting", "no voting", "no protesting",
            "no beating", "no eating", # [11]eh?[9]
            "no eating", "no fondling", # [11]eh?[9]
            "no eating", "no fondling", "no yawning",
            "no hating", "no loitering", "no sneering",
            "no touting", "no watering", "no lying",
            "no dragging", "no pointing", "no lifting",
            "no picking", "no grassing", "no parking",
            "no standing", "no snorting", "no queuing",
            "no elbowing", "no sniffing", "no relaxing",
            "no fluffing", # [4]jeezus![2]
            "no jamming", "no undressing", "no clamping",
            "no snogging", "no tripping", "no cuddling",
            "no drooling", "no staring", "no mugging",
            "no fixating", "no tailing", "no blaming",
            "no crushing", "no dancing", "no mounting",
            "no creeping", "no brewing", "no festering",
            "no breeding", "no pumping", "no peeling",
            "no lusting", "no dissing", "no dropping",
            "no jerking", "no crumpling", "no looking", # [7]whoa![6]
            "no carting", "no necking", "no abducting",
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
            "no accelerating", "no dawdling", # [5]fuck it[4]
            "no fathering", "no hanging", "no filming",
            "no rushing", "no watching", "no kidding",
            "no perverting", "no nipping", "no cruising",
            "no pinching", "no fidgeting", "no kissing",
            "no cheating", "no speeding", "no blocking", # [9]huh?[6]
            "no shirking", "no brushing", "no hurting",
            "no dirtying", "no whispering", "no snoring",
            "no running", "no fingering", "no blackmailing",
            "no snorting", "no frowning", "no laughing",
            "no stalking", "no yawning", "no flannelling",
            "no trading", "no jabbing", "no chasing",
            "no hoarding", "no trafficking", "no bullying",
            "no tiptoeing", "no smarting", "no groaning",
            "no feuding", "no circling", "no groping",
            "no bawling", "no jumping", # [8]wait![8]
            "no laundering", "no gawping", "no spiking",
            "no weeding", "no touching", "no aiding",
            "no charging", "no limping", "no abetting",
            "no smuggling", "no drooping", "no mouthing",
            "no jawing", "no climbing", "no faking",
            "no leaving", "no rioting", "no breathing",
            "no stealing", "no boring", "no sweating",
            "no crawling", "no creeping", # [5]hnnh?[4]
            "no pouting", "no wrestling", "no knifing",
            "no pummelling", "no shouting", "no fainting",
            "no loafing", "no squeezing", "no vamping",
            "no straying", "no hitching", "no picketing",
            "no streaking", "no joyriding", "no rabbiting",
            "no pleading", "no smiling", "no battling",
            "no slimming", "no jeering", "no peeping",
            "no blaming", "no stuffing", "no curating",
            "no dating", "no pickling", "no crossing",
            "no punching", # [4]stuff it[2]
            "no screwing", "no bleeding", "no smearing",
            "no stroking", "no hoping", "no voting",
            "no signing", "no crediting", "no accounting",
            "no rolling", "no sacking", "no drafting",
            "no ticketing", "no troubling", "no bargaining",
            "no fingering", "no helping", "no plotting", # [6]yeah?[4]
            "no clapping", "no following", "no scribbling",
            "no rioting", "no shipping", "no ravaging",
            "no aiming", "no painting", "no carving",
            "no scalping", "no flying", "no landing",
            "no sterilising", "no robbing", "no trawling",
            "no looting", "no leaping", "no terrorising",
            "no spewing", "no kicking", "no kidnapping",
            "no preaching", "no moonlighting", "no cycling",
            "no networking", "no speeding", # [4]pleeze![2]
            "no colouring", "no perming", "no rapping",
            "no crowding", "no aging", "no dribbling",
            "no pausing", "no controlling", "no panicking",
            "no freewheeling", "no carpeting", "no fuming",
            "no blazing", "no steaming", "no craving",
            "no tricking", "no daring", "no moping",
            "no operating", "no training", "no pilfering",
            "no tresspassing", "no dillydallying", # [2]aaaaah![2]
            "no straining", "no commenting", "no fundraising",
            "no developing", "no heating", "no sluicing",
            "no judging", "no limiting", "no sweeping",
            "no drawing", "no smacking", "no scrubbing",
            "no roping", "no worming", "no splashing",
            "no prowling", "no feeling", "no scoring",
            "no embezzling", "no chasing", "no tossing",
            "no undertaking", "no holding", "no crisscrossing",
            "no unravelling", "no crawling", # [3]sod off[3]
            "no swiping", "no smudging", "no whistling",
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
            "no nothing", # [7]stop![8]
            "no nothing", "no sponging", # [6]stop![9]
            "no sedating", "no itching", # # [7]stop![8]
            "no quoting", "no ending"] 

# How many blank columns between phrases
PHRASE_GAP = 6

# Between each character there should be one blank column
INTER_CHAR_BLANKS = 1
# Visual tuning: what fraction of the cell is the LED circle
LED_CIRCLE_RATIO = 0.95

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
    '!': ["001","001","001","001","000","001","001"], # Confirmed correct
    '?': ["01110","10001","00001","00010","00100","00000","00100"], # Confirmed correct
    ' ': ["00"] * 7,
} 

# ------------------------------------------------------------------------------

def char_to_columns(ch):
    ch = ch.lower()
    if ch not in FONT:
        rows = FONT[' ']
    else:
        rows = FONT[ch]

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


def build_phrase_columns(phrase):
    return text_to_columns(phrase)


def build_full_scroll_buffer(commands, phrase_gap):
    """Builds one continuous column buffer of all commands, each separated by blanks,
    in the exact order provided in `commands` (no shuffling).
    """
    all_cols = []
    gap = [[0]*MATRIX_HEIGHT for _ in range(phrase_gap)]
    for phrase in commands:
        all_cols.extend(build_phrase_columns(phrase))
        all_cols.extend(gap)
    # Repeat once to ensure wrap continuity
    all_cols.extend(all_cols[:MATRIX_WIDTH])
    return all_cols


def build_scrolling_columns_for_command(cmd_text):
    cols = text_to_columns(cmd_text)
    gap = [[0] * MATRIX_HEIGHT for _ in range(MATRIX_WIDTH // 2)]
    return cols + gap


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


def build_flash_columns(word):
    cols = text_to_columns(word)
    cols = cols[:MATRIX_WIDTH]
    left_pad = max(0, (MATRIX_WIDTH - len(cols)) // 2)
    full = [[0] * MATRIX_HEIGHT for _ in range(left_pad)] + cols
    if len(full) < MATRIX_WIDTH:
        full += [[0] * MATRIX_HEIGHT for _ in range(MATRIX_WIDTH - len(full))]
    return full[:MATRIX_WIDTH]


def main():
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_DEFAULT_SIZE, pygame.RESIZABLE)
    pygame.display.set_caption('Recreation of "House Rules" — No Randomness')
    clock = pygame.time.Clock()

    # Build long scrolling buffer (in order)
    full_buffer = build_full_scroll_buffer(COMMANDS, PHRASE_GAP)
    scroll_offset = 0.0

    # Tick counter and accumulator
    tick_counter = 0
    tick_acc = 0.0

    # Prepare schedule: convert delays into absolute trigger ticks (relative to start/tick 0).
    schedule = []
    absolute = 0
    for entry in FLASH_SCHEDULE:
        # Delay is number of ticks after previous flash ended. For first entry, counted from tick 0.
        absolute += int(entry.get('delay', 0))
        schedule.append({'word': entry['word'], 'trigger_tick': absolute, 'duration': int(entry.get('duration', 1))})
        # After we schedule the start, the next trigger's delays count after this flash ends,
        # so we add the duration to the absolute time so "delay" in the next entry is after flash end.
        absolute += int(entry.get('duration', 1))

    # Index to next scheduled flash
    next_schedule_idx = 0
    is_flashing = False
    flash_end_tick = None
    saved_scroll_offset = 0.0
    current_flash_word = ""

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

        # --- Tick update ---
        tick_acc += dt * TICKS_PER_SEC
        while tick_acc >= 1.0:
            tick_counter += 1
            tick_acc -= 1.0

        # --- Flash scheduling (deterministic) ---
        if not is_flashing and schedule:
            next_item = schedule[next_schedule_idx]
            if tick_counter >= next_item['trigger_tick']:
                # Start the flash
                is_flashing = True
                current_flash_word = next_item['word']
                flash_end_tick = tick_counter + next_item['duration']
                saved_scroll_offset = scroll_offset
        elif is_flashing:
            # End flash when its duration has passed
            if tick_counter >= flash_end_tick:
                is_flashing = False
                current_flash_word = ""
                # Advance to next scheduled item (loop around)
                next_schedule_idx = (next_schedule_idx + 1) % len(schedule)
                # If we've looped to the start, we must shift all trigger_ticks forward so they stay in the future.
                # Easiest deterministic behaviour: when we loop, add the total cycle length to all trigger ticks.
                if next_schedule_idx == 0:
                    # compute cycle length as trigger of first after we finish the last flash minus current tick
                    # but simpler: compute total time of one schedule cycle as the last trigger_tick + its duration
                    cycle_length = schedule[-1]['trigger_tick'] + schedule[-1]['duration']
                    for item in schedule:
                        item['trigger_tick'] += cycle_length

        # --- Scrolling ---
        if not is_flashing:
            scroll_offset += SCROLL_SPEED_COLS_PER_SEC * dt
        else:
            scroll_offset = saved_scroll_offset

        # --- Drawing ---
        window_w, window_h = screen.get_size()
        screen.fill(LETTERBOX_COLOR)
        disp_rect = compute_display_area(window_w, window_h)

        if is_flashing and current_flash_word:
            flash_cols = build_flash_columns(current_flash_word)
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