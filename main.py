import pygame
import random
import sys

# --- CONFIG ---------------------------------------------------
LED_ON_COLOR =  (239,69,44)     # bright red
LED_OFF_COLOR = (52, 52, 52)        # dim/off 
MATRIX_HEIGHT = 7
MATRIX_WIDTH = 7 * 5
SCROLL_SPEED = 1  # frames per column shift (1 = fastest)
GAP = 1
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
random.shuffle(COMMANDS)
SCROLL_TEXT = " ".join(COMMANDS)
#SCROLL_TEXT = " the quick brown fox jumps over the lazy dog! or does it? "

FLASH_WORDS = ["zap?", "bored!", "whatever!", "wow!", "ouch!", "what?"]
MIN_FLASH_DELAY = 200  # min number of scroll steps before next flash
MAX_FLASH_DELAY = 200  # max number of scroll steps before next flash
FLASH_DURATION = 40     # frames the flash stays visible

# --- FONT DEFINITION -----------------------------------------

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

# Randomly select one of the 'q' patterns and print which one was chosen

chosen_q = random.randint(1, len(q_options))
FONT['q'] = q_options[chosen_q]
print(f"Chosen 'q' {chosen_q}")

Letter_lengths = {char: len(pattern[0]) for char, pattern in FONT.items()}

# --- TEXT CONVERSION ------------------------------------------
def text_to_columns(text):
    """Convert text to a list of columns for the LED matrix."""
    columns = []
    for char in text:
        pattern = FONT.get(char.lower(), FONT[' '])
        char_width = Letter_lengths.get(char.lower(), 5)
        for x in range(char_width):
            col = []
            for y in range(MATRIX_HEIGHT):
                on = pattern[y][x] == '1'
                col.append(on)
            columns.append(col)
        # Add gap column
        gap_col = [False] * MATRIX_HEIGHT
        columns.append(gap_col)
    return columns

# --- DRAWING --------------------------------------------------
def draw_led(surface, x, y, diameter, on):
    """Draw a single circular LED."""
    colour = LED_ON_COLOR if on else LED_OFF_COLOR
    pygame.draw.circle(surface, colour, (x, y), diameter//2)

def draw_matrix(surface, columns, offset, visible_cols, led_size, x_offset, y_offset):
    """Draw visible section of the text with LEDs."""
    surface.fill((0, 0, 0))
    for x in range(visible_cols):
        col_index = (offset + x) % len(columns)
        for y in range(MATRIX_HEIGHT):
            on = columns[col_index][y]
            cx = x_offset + x * led_size + led_size // 2
            cy = y_offset + y * led_size + led_size // 2
            draw_led(surface, cx, cy, led_size - 2, on)

def draw_flash(surface, word, led_size, x_offset, y_offset):
    """Render a flash word using the LED effect."""
    columns = text_to_columns(word)
    visible_cols = len(columns)
    surface.fill((0, 0, 0))
    for x in range(visible_cols):
        for y in range(MATRIX_HEIGHT):
            on = columns[x][y]
            cx = x_offset + x * led_size + led_size // 2
            cy = y_offset + y * led_size + led_size // 2
            draw_led(surface, cx, cy, led_size - 2, on)

# --- MAIN LOOP ------------------------------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 200), pygame.RESIZABLE)
    pygame.display.set_caption("LED Matrix Emulator")

    columns = text_to_columns(SCROLL_TEXT)
    offset = 0
    frame_count = 0
    next_flash_in = random.randint(MIN_FLASH_DELAY, MAX_FLASH_DELAY)
    flashing = False
    flash_timer = 0
    flash_word = ""

    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

        # --- compute scaling and aspect ratio ---
        w, h = screen.get_size()
        aspect_ratio = MATRIX_WIDTH / MATRIX_HEIGHT
        target_width = w
        target_height = int(w / aspect_ratio)
        if target_height > h:
            target_height = h
            target_width = int(h * aspect_ratio)
        x_offset = (w - target_width) // 2
        y_offset = (h - target_height) // 2
        led_size = target_width // MATRIX_WIDTH

        visible_cols = MATRIX_WIDTH

        # --- drawing logic ---
        if flashing:
            draw_flash(screen, flash_word, led_size, x_offset, y_offset)
            flash_timer += 1
            if flash_timer > FLASH_DURATION:
                flashing = False
                next_flash_in = random.randint(MIN_FLASH_DELAY, MAX_FLASH_DELAY)
        else:
            draw_matrix(screen, columns, offset, visible_cols, led_size, x_offset, y_offset)
            frame_count += 1
            if frame_count % SCROLL_SPEED == 0:
                offset = (offset + 1) % len(columns)
                next_flash_in -= 1
                if next_flash_in <= 0:
                    flashing = True
                    flash_timer = 0
                    flash_word = random.choice(FLASH_WORDS)

        pygame.display.flip()
        clock.tick(40)

if __name__ == "__main__":
    main()
