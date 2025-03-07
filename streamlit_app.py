import streamlit.elements.image as image_module
import base64, io

def dummy_image_to_url(*args, **kwargs):
    # Assume the first argument is the PIL image.
    image = args[0]
    fmt = kwargs.get("format", "PNG")
    buffered = io.BytesIO()
    image.save(buffered, format=fmt)
    img_bytes = buffered.getvalue()
    b64 = base64.b64encode(img_bytes).decode("utf-8")
    return f"data:image/{fmt.lower()};base64,{b64}"

if not hasattr(image_module, "image_to_url"):
    image_module.image_to_url = dummy_image_to_url


import streamlit as st
from streamlit_drawable_canvas import st_canvas
import pygame, sys, random, time, json
import numpy as np
from PIL import Image
import streamlit.elements.image as image_module
if not hasattr(image_module, "image_to_url"):
    image_module.image_to_url = lambda image: image

# ─────────────────────────────
# Constants & Configuration
# ─────────────────────────────

# Screen dimensions
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768

# Grid settings
GRID_ROWS = 10  # 10
GRID_COLS = 10  # 10
TILE_SIZE = 60  # 60
GRID_ORIGIN = (50, 50)

# Inventory settings
INVENTORY_SLOTS = 9
INVENTORY_SLOT_SIZE = 80
INVENTORY_ORIGIN = (50, SCREEN_HEIGHT - INVENTORY_SLOT_SIZE - 20)
STARTING_CASH = 500  # 500

# Time settings
MINUTE_DURATION = 0.25  # seconds per in-game hour
DAY_HOURS = 24  # or 1440 minutes
DAY_DURATION = (MINUTE_DURATION * 60) * DAY_HOURS  # 720 seconds per day

# Colours (RGB)
COLOR_BG = (206, 206, 206)
COLOR_TILE_UNTILLED = (120, 72, 48)
COLOR_TILE_TILLED = (200, 170, 120)
COLOR_WATERED_OVERLAY = (0, 0, 255, 50)  # Blue overlay with alpha
COLOR_SPRINKLER = (0, 191, 255)
COLOR_WEED = (34, 139, 34)
COLOR_FERTILIZER = (152, 245, 249)
COLOR_PROGRESS_BG = (50, 50, 50)
COLOR_PROGRESS_FG = (255, 200, 0)  # (254, 217, 7)
COLOR_PROGRESS_INACTIVE = (195, 195, 195)
COLOR_PROGRESS_COMPLETE = (0, 255, 0)
COLOR_PROGRESS_FERTILIZED_INCOMPLETE = (0, 240, 255)
COLOR_PROGRESS_FERTILIZED_COMPLETE = (0, 150, 255)
COLOR_INVENTORY_BG = (150, 150, 150)
COLOR_SELECTED_SLOT = (255, 255, 0)
COLOR_TEXT = (0, 0, 0)
BLACK = (0, 0, 0)

# ─────────────────────────────
# Crop Definitions
# ─────────────────────────────
CROP_TYPES = {
    "Parsnip":      {"growth_time": 4,  "sell_price": 20,   "yield": 1,   "allowed_seasons": ["Spring"],
                     "color": (255, 200, 0),     "shape": "circle",  "multi_harvest": False},
    
    "Strawberry":   {"growth_time": 6,  "sell_price": 35,   "yield": 1,   "allowed_seasons": ["Spring"],
                     "color": (255, 0, 0),       "shape": "square",  "multi_harvest": False},
    
    "Cauliflower":  {"growth_time": 8,  "sell_price": 50,   "yield": 1,   "allowed_seasons": ["Spring"],
                     "color": (240, 240, 240),   "shape": "circle",  "multi_harvest": False},
    
    "Potato":       {"growth_time": 5,  "sell_price": 25,   "yield": 1,   "allowed_seasons": ["Spring"],
                     "color": (210, 180, 140),   "shape": "square",  "multi_harvest": False},
    
    "Tomato":       {"growth_time": 8,  "sell_price": 40,   "yield": 1,   "allowed_seasons": ["Summer"],
                     "color": (255, 80, 80),     "shape": "circle",  "multi_harvest": False},
    
    "Blueberry":    {"growth_time": 10,  "sell_price": 60,   "yield": 2,   "allowed_seasons": ["Summer"],
                     "color": (100, 149, 237),   "shape": "square",  "multi_harvest": True},
    
    "Corn":         {"growth_time": 10, "sell_price": 45,   "yield": 1,   "allowed_seasons": ["Summer"],
                     "color": (255, 215, 0),     "shape": "circle",  "multi_harvest": False},
    
    "HotPepper":    {"growth_time": 6,  "sell_price": 30,   "yield": 1,   "allowed_seasons": ["Summer"],
                     "color": (255, 69, 0),      "shape": "square",  "multi_harvest": False},
    
    "Pumpkin":      {"growth_time": 8,  "sell_price": 80,   "yield": 1,   "allowed_seasons": ["Fall"],
                     "color": (255, 140, 0),     "shape": "circle",  "multi_harvest": False},
    
    "Cranberry":    {"growth_time": 8,  "sell_price": 40,   "yield": 2,   "allowed_seasons": ["Fall"],
                     "color": (220, 20, 60),     "shape": "square",  "multi_harvest": True},
    
    "Eggplant":     {"growth_time": 6,  "sell_price": 35,   "yield": 1,   "allowed_seasons": ["Fall"],
                     "color": (128, 0, 128),     "shape": "circle",  "multi_harvest": False},
    
    "Yam":          {"growth_time": 6,  "sell_price": 30,   "yield": 1,   "allowed_seasons": ["Fall"],
                     "color": (160, 82, 45),     "shape": "square",  "multi_harvest": False},

    "Thyme":        {"growth_time": 2,  "sell_price": 15,   "yield": 1,   "allowed_seasons": ["Fall"],
                     "color": (160, 82, 45),     "shape": "square",  "multi_harvest": True},
    
    "WinterRoot":   {"growth_time": 8,  "sell_price": 50,   "yield": 1,   "allowed_seasons": ["Winter"],
                     "color": (255, 250, 250),   "shape": "circle",  "multi_harvest": False},
    
    "SnowYam":      {"growth_time": 6,  "sell_price": 40,   "yield": 1,   "allowed_seasons": ["Winter"],
                     "color": (240, 248, 255),   "shape": "square",  "multi_harvest": False},
    
    "CrystalFruit": {"growth_time": 8,  "sell_price": 70,   "yield": 1,   "allowed_seasons": ["Winter"],
                     "color": (175, 238, 238),   "shape": "circle",  "multi_harvest": False},
    
    "FrostApple":   {"growth_time": 6,  "sell_price": 55,   "yield": 1,   "allowed_seasons": ["Winter"],
                     "color": (255, 99, 71),     "shape": "square",  "multi_harvest": True},
    
    # Multi‑season crops:
    "GreenBean":    {"growth_time": 6,  "sell_price": 30,   "yield": 2,   "allowed_seasons": ["Spring", "Summer"],
                     "color": (34, 139, 34),  "shape": "circle",  "multi_harvest": True},

    "Grass":    {"growth_time": 2,  "sell_price": 10,   "yield": 1,   "allowed_seasons": ["Summer", "Fall"],
                     "color": (2, 249, 36),  "shape": "square",  "multi_harvest": True},
    
    "AncientFruit": {"growth_time": 20, "sell_price": 100,  "yield": 3,   "allowed_seasons": ["Spring", "Summer", "Fall"],
                     "color": (255, 20, 147), "shape": "square",  "multi_harvest": False}
}

# Extra shop items (available every season)
SHOP_EXTRA = {
    "Sprinkler": {"price": 50, "type": "sprinkler"},
    "Fertilizer": {"price": 20, "type": "fertilizer"}
}

# ─────────────────────────────
# Class Definitions
# ─────────────────────────────

class Tile:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilled = False
        self.crop = None         # Instance of CropInstance (if planted)
        self.watered = False
        self.sprinkler = False
        self.fertilizer = False
        self.weed = False

class CropInstance:
    def __init__(self, crop_name):
        self.crop_name = crop_name
        self.data = CROP_TYPES[crop_name]
        self.age = 0           # Number of days grown
        self.progress = 0.0    # Fraction of the current day’s growth (0 to 1)
        self.fertilized = False
        self.growtime = self.data["growth_time"]

    def is_mature(self):
        return self.age >= self.data["growth_time"]

    def update_growth(self, growth_factor):
        # growth_factor is normally 1.0; fertilizer gives a bonus (e.g. 1.5)
        self.progress += growth_factor
        self.age += self.progress
        self.progress = 0.0
        if self.age > self.growtime:
            self.age = self.growtime

    def get_color(self):
        # As the crop matures, its colour lightens.
        base_color = self.data["color"]
        ratio = min(self.age / self.data["growth_time"], 1.0)
        factor = 0.5 + 0.5 * ratio  # from 50% brightness to full
        return tuple(min(255, int(c * factor)) for c in base_color)

class Game:
    def __init__(self):
        # Instead of opening a pygame window, create an off-screen surface.
        self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("We have farming at home")
        self.clock = pygame.time.Clock()
        self.grid = [[Tile(x, y) for x in range(GRID_COLS)] for y in range(GRID_ROWS)]
        # Inventory: 9 slots; first two are reserved for tools.
        self.inventory = [
            {"item": "Hoe", "quantity": 1, "type": "tool"},
            {"item": "Can", "quantity": 1, "type": "tool"}
        ]
        for _ in range(INVENTORY_SLOTS - 2):
            self.inventory.append({"item": None, "quantity": 0, "type": None})
        self.selected_inventory = 0

        # Game state variables
        self.money = STARTING_CASH
        self.mode = "farm"  # either "farm" or "shop"
        self.current_hour = 6  # start at 06:00
        self.current_minute = 0
        self.minute_timer = 0.0
        self.day = 1
        self.season = "Spring"
        self.year = 1
        self.shop_items = self.generate_shop_items()
        self.dragging = False
        self.dragged_tiles = set()

    def generate_shop_items(self):
        # Create a list of shop items (seed items for crops allowed in the current season plus extras)
        shop_list = []
        for crop_name, data in CROP_TYPES.items():
            if self.season in data["allowed_seasons"]:
                shop_list.append({
                    "name": crop_name + " Seed",
                    "price": data["sell_price"] // 2,  # arbitrary seed price
                    "growth_time": data["growth_time"],
                    "type": "seed",
                    "crop_name": crop_name
                })
        for extra_name, extra_data in SHOP_EXTRA.items():
            shop_list.append({
                "name": extra_name,
                "price": extra_data["price"],
                "type": extra_data["type"]
            })
        return shop_list

    def toggle_shop_mode(self):
        self.mode = "shop" if self.mode == "farm" else "farm"

    def handle_mouse_click(self, pos):
        x, y = pos
        # First, check if the click is in the inventory bar.
        if y >= INVENTORY_ORIGIN[1]:
            self.handle_inventory_click(pos)
            return

        # In shop mode, check if clicking on the shop panel.
        if self.mode == "shop":
            shop_panel = pygame.Rect(800, 50, 200, 600)
            if shop_panel.collidepoint(pos):
                self.handle_shop_click(pos, shop_panel)
                return
            # In shop mode, clicking on the grid sells mature crops.
            grid_rect = pygame.Rect(GRID_ORIGIN[0], GRID_ORIGIN[1], GRID_COLS * TILE_SIZE, GRID_ROWS * TILE_SIZE)
            if grid_rect.collidepoint(pos):
                grid_x = (x - GRID_ORIGIN[0]) // TILE_SIZE
                grid_y = (y - GRID_ORIGIN[1]) // TILE_SIZE
                self.sell_crop(grid_x, grid_y)
                return

        # In farm mode, if clicking on the grid, apply the selected tool.
        grid_rect = pygame.Rect(GRID_ORIGIN[0], GRID_ORIGIN[1], GRID_COLS * TILE_SIZE, GRID_ROWS * TILE_SIZE)
        if grid_rect.collidepoint(pos):
            grid_x = (x - GRID_ORIGIN[0]) // TILE_SIZE
            grid_y = (y - GRID_ORIGIN[1]) // TILE_SIZE
            self.apply_tool(grid_x, grid_y)
            return

    def handle_mouse_drag(self, pos):
        x, y = pos
        grid_rect = pygame.Rect(GRID_ORIGIN[0], GRID_ORIGIN[1], GRID_COLS * TILE_SIZE, GRID_ROWS * TILE_SIZE)
        if grid_rect.collidepoint(pos):
            grid_x = (x - GRID_ORIGIN[0]) // TILE_SIZE
            grid_y = (y - GRID_ORIGIN[1]) // TILE_SIZE
            if (grid_x, grid_y) not in self.dragged_tiles:
                self.dragged_tiles.add((grid_x, grid_y))
                self.apply_tool(grid_x, grid_y)

    def handle_inventory_click(self, pos):
        x, y = pos
        for i in range(INVENTORY_SLOTS):
            slot_rect = pygame.Rect(INVENTORY_ORIGIN[0] + i * (INVENTORY_SLOT_SIZE + 5),
                                    INVENTORY_ORIGIN[1], INVENTORY_SLOT_SIZE, INVENTORY_SLOT_SIZE)
            if slot_rect.collidepoint(pos):
                self.selected_inventory = i
                break

    def handle_shop_click(self, pos, shop_panel):
        # Each shop item is drawn in a 40-pixel–tall row.
        x, y = pos
        relative_y = y - shop_panel.y
        index = relative_y // 40
        if index < len(self.shop_items):
            item = self.shop_items[index]
            if self.money >= item["price"]:
                added = False
                # Try stacking the item.
                for slot in self.inventory:
                    if slot["item"] == item["name"]:
                        slot["quantity"] += 1
                        added = True
                        break
                # Otherwise, add to an empty slot (slots 2+ only).
                if not added:
                    for i in range(2, INVENTORY_SLOTS):
                        if self.inventory[i]["item"] is None:
                            self.inventory[i]["item"] = item["name"]
                            self.inventory[i]["quantity"] = 1
                            self.inventory[i]["type"] = item["type"]
                            if item["type"] == "seed":
                                self.inventory[i]["crop_name"] = item["crop_name"]
                            added = True
                            break
                if added:
                    self.money -= item["price"]

    def sell_crop(self, grid_x, grid_y):  # markerselling
        tile = self.grid[grid_y][grid_x]
        if tile.crop and tile.crop.is_mature():
            crop_name = tile.crop.crop_name
            regrowth = CROP_TYPES[crop_name]["multi_harvest"]
            sell_price = CROP_TYPES[crop_name]["sell_price"]
            yield_amount = CROP_TYPES[crop_name]["yield"]
            self.money += sell_price * yield_amount
            if regrowth == True:
                # Regrow the crop
                tile.crop = CropInstance(crop_name)
                tile.tilled = True
            else:
                # Remove the crop
                tile.crop = None
                tile.tilled = True

    def apply_tool(self, grid_x, grid_y):
        tile = self.grid[grid_y][grid_x]
        current = self.inventory[self.selected_inventory]
        if current["item"] is None:
            return

        # Hoe: tills untilled ground or uproots crops/sprinklers (also removes weeds)
        if current["item"] == "Hoe":
            if not tile.tilled:
                tile.tilled = True
            else:
                tile.crop = None
                tile.sprinkler = False
            tile.weed = False
            return

        # Can: waters the tile.
        if current["item"] == "Can":
            if not tile.sprinkler:
                tile.watered = True
                return
            return

        # Seed items (item name ends with "Seed")
        if current["type"] == "seed":
            if tile.tilled and tile.crop is None and not tile.sprinkler:
                crop_name = current.get("crop_name", None)
                if crop_name:
                    if self.season in CROP_TYPES[crop_name]["allowed_seasons"]:
                        tile.crop = CropInstance(crop_name)
                        # Remove one seed from inventory.
                        current["quantity"] -= 1
                        if current["quantity"] <= 0:
                            current["item"] = None
                    else:
                        print("This crop cannot be planted in the current season!")
            return

        # Fertilizer: if a crop is present, apply fertilizer.
        if current["type"] == "fertilizer":
            if tile.crop and not tile.fertilizer:
                tile.fertilizer = True
                tile.crop.fertilized = True
                current["quantity"] -= 1
                if current["quantity"] <= 0:
                    current["item"] = None
            return

        # Sprinkler: place a sprinkler on tilled, empty tile.
        if current["type"] == "sprinkler":
            if tile.crop is None and not tile.sprinkler:
                tile.sprinkler = True
                current["quantity"] -= 1
                if current["quantity"] <= 0:
                    current["item"] = None
            return

    def update_time(self, dt):
        self.minute_timer += dt
        if self.minute_timer >= MINUTE_DURATION:
            self.minute_timer -= MINUTE_DURATION
            self.current_minute += 1
            if self.current_minute >= 60:
                self.current_hour += 1
                self.current_minute = 0
                if self.current_hour >= 24:
                    self.end_of_day()
                    self.current_hour = 0
                    self.current_minute = 0

    def end_of_day(self):
        # Process each tile:
        for y in range(GRID_ROWS):
            for x in range(GRID_COLS):
                tile = self.grid[y][x]
                if tile.crop:
                    if tile.watered:
                        growth = 2 if (tile.fertilizer or tile.crop.fertilized) else 1.0
                        tile.crop.update_growth(growth)
                    # If crop is out of season, it withers.
                    if self.season not in CROP_TYPES[tile.crop.crop_name]["allowed_seasons"]:
                        tile.crop = None
                        tile.tilled = True
                # Untended tilled soil decays, fertilized decays slower
                if tile.tilled and tile.crop is None and not tile.sprinkler:
                    if tile.fertilizer:
                        if random.random() < 0.1:
                            tile.tilled = False
                            tile.fertilizer = False
                    elif random.random() < 0.2:
                        tile.tilled = False
                        tile.fertilizer = False
                # Reset water and fertilizer flags.
                tile.watered = False
        # Sprinkler automation: each sprinkler waters its four adjacent tiles.
        for y in range(GRID_ROWS):
            for x in range(GRID_COLS):
                tile = self.grid[y][x]
                if tile.sprinkler:
                    for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0), (1,1), (1,-1), (-1,-1), (-1,1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < GRID_COLS and 0 <= ny < GRID_ROWS:
                            self.grid[ny][nx].watered = True
        # Weeds and weed spreading (commented out in original)
        spread_list = []
        for y in range(GRID_ROWS):
            for x in range(GRID_COLS):
                tile = self.grid[y][x]
                if tile.weed:
                    dx, dy = random.choice([(0, -1), (0, 1), (-1, 0), (1, 0)])
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < GRID_COLS and 0 <= ny < GRID_ROWS:
                        neighbor = self.grid[ny][nx]
                        if not neighbor.tilled and neighbor.crop is None and not neighbor.sprinkler:
                            spread_list.append((nx, ny))
        for (nx, ny) in spread_list:
            self.grid[ny][nx].weed = True

        # Advance day/season/year counters.
        self.day += 1
        if self.day > 28:
            self.day = 1
            seasons = ["Spring", "Summer", "Fall", "Winter"]
            idx = seasons.index(self.season)
            if idx == len(seasons) - 1:
                self.season = "Spring"
                self.year += 1
            else:
                self.season = seasons[idx + 1]
            self.shop_items = self.generate_shop_items()

    def draw(self):
        self.screen.fill(COLOR_BG)
        # Draw grid and tiles.
        for y in range(GRID_ROWS):
            for x in range(GRID_COLS):
                tile = self.grid[y][x]
                screen_x = GRID_ORIGIN[0] + x * TILE_SIZE
                screen_y = GRID_ORIGIN[1] + y * TILE_SIZE
                rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
                base_color = COLOR_TILE_TILLED if tile.tilled else COLOR_TILE_UNTILLED
                pygame.draw.rect(self.screen, base_color, rect)
                # Draw sprinkler if present.
                if tile.sprinkler:
                    pygame.draw.circle(self.screen, COLOR_SPRINKLER,
                                       (screen_x + TILE_SIZE // 2, screen_y + TILE_SIZE // 2), TILE_SIZE // 3)
                # Draw crop if present.
                if tile.crop:
                    crop_color = tile.crop.get_color()
                    shape = CROP_TYPES[tile.crop.crop_name]["shape"]
                    if shape == "circle":
                        pygame.draw.circle(self.screen, crop_color,
                                           (screen_x + TILE_SIZE // 2, screen_y + TILE_SIZE // 2), TILE_SIZE // 4)
                    else:
                        crop_rect = pygame.Rect(screen_x + 10, screen_y + 10, TILE_SIZE - 20, TILE_SIZE - 20)
                        pygame.draw.rect(self.screen, crop_color, crop_rect)
                    # Draw progress bar below the crop.
                    pb_width = TILE_SIZE - 4
                    pb_height = 6
                    pb_x = screen_x + 2
                    pb_y = screen_y + TILE_SIZE - pb_height - 2
                    pygame.draw.rect(self.screen, COLOR_PROGRESS_BG, (pb_x, pb_y, pb_width, pb_height))
                    if tile.crop.is_mature():
                        if tile.fertilizer:
                            pygame.draw.rect(self.screen, COLOR_PROGRESS_FERTILIZED_COMPLETE, (pb_x, pb_y, int(pb_width*(1)), pb_height))
                        else:
                            pygame.draw.rect(self.screen, COLOR_PROGRESS_COMPLETE, (pb_x, pb_y, int(pb_width*(1)), pb_height))
                    elif tile.fertilizer and tile.watered:
                        pygame.draw.rect(self.screen, COLOR_PROGRESS_FERTILIZED_INCOMPLETE, (pb_x, pb_y, int(pb_width *
                                                                    ((((tile.crop.age * 720) + ((self.current_hour * 60)+self.current_minute)) / (tile.crop.growtime * 720)))),
                                                                      pb_height))
                    elif tile.watered:
                        pygame.draw.rect(self.screen, COLOR_PROGRESS_FG, (pb_x, pb_y, int(pb_width *
                                                                    ((((tile.crop.age * 1440) + ((self.current_hour * 60)+self.current_minute)) / (tile.crop.growtime * 1440)))),
                                                                      pb_height))
                    else:
                        pygame.draw.rect(self.screen, COLOR_PROGRESS_INACTIVE, (pb_x, pb_y, int(pb_width * (tile.crop.age / tile.crop.growtime)), pb_height))
                # Show fertilizer marker.
                if tile.fertilizer:
                    pygame.draw.rect(self.screen, COLOR_FERTILIZER, (screen_x + TILE_SIZE - 15, screen_y + 5, 10, 10))
                # Draw weed (a small circle in the corner).
                if tile.weed:
                    pygame.draw.circle(self.screen, COLOR_WEED, (screen_x + TILE_SIZE - 10, screen_y + 10), 5)
                # If watered, overlay a translucent blue.
                if tile.watered:
                    overlay = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    overlay.fill(COLOR_WATERED_OVERLAY)
                    self.screen.blit(overlay, (screen_x, screen_y))
                pygame.draw.rect(self.screen, BLACK, rect, 1)
        # Draw inventory bar (hotbar).
        inv_bar = pygame.Rect(INVENTORY_ORIGIN[0], INVENTORY_ORIGIN[1],
                                INVENTORY_SLOTS * (INVENTORY_SLOT_SIZE + 5), INVENTORY_SLOT_SIZE)
        pygame.draw.rect(self.screen, COLOR_INVENTORY_BG, inv_bar)
        for i in range(INVENTORY_SLOTS):
            slot_rect = pygame.Rect(INVENTORY_ORIGIN[0] + i*(INVENTORY_SLOT_SIZE+5),
                                    INVENTORY_ORIGIN[1], INVENTORY_SLOT_SIZE, INVENTORY_SLOT_SIZE)
            pygame.draw.rect(self.screen, BLACK, slot_rect, 2)
            if i == self.selected_inventory:
                pygame.draw.rect(self.screen, COLOR_SELECTED_SLOT, slot_rect, 3)
            slot = self.inventory[i]
            if slot["item"]:
                font = pygame.font.Font(None, 24)
                # For seeds, draw an icon (a filled rectangle in the crop’s colour).
                if slot["type"] == "seed":
                    crop_name = slot.get("crop_name", "")
                    icon_color = CROP_TYPES[crop_name]["color"] if crop_name in CROP_TYPES else (200, 200, 200)
                    pygame.draw.rect(self.screen, icon_color, (slot_rect.x+5, slot_rect.y+5, INVENTORY_SLOT_SIZE-10, INVENTORY_SLOT_SIZE-10))
                else:
                    text = font.render(slot["item"], True, BLACK)
                    self.screen.blit(text, (slot_rect.x+5, slot_rect.y+5))
                # Draw quantity at bottom left of slot.
                qty_font = pygame.font.Font(None, 20)
                qty_text = qty_font.render(str(slot["quantity"]), True, BLACK)
                self.screen.blit(qty_text, (slot_rect.x+2, slot_rect.y+INVENTORY_SLOT_SIZE-18))
        # Draw shop panel if in shop mode.
        if self.mode == "shop":
            shop_panel = pygame.Rect(800, 50, 200, 600)
            pygame.draw.rect(self.screen, (180, 180, 180), shop_panel)
            font = pygame.font.Font(None, 20)
            y_offset = 0
            for item in self.shop_items:
                if item["type"] == "seed":
                    text_str = f"{item['name']} ($ {item['price']}, {item['growth_time']}d)"
                else:
                    text_str = f"{item['name']} ($ {item['price']})"
                text = font.render(text_str, True, BLACK)
                self.screen.blit(text, (shop_panel.x + 5, shop_panel.y + y_offset))
                y_offset += 40
        # Draw UI info: Time, Day, Season, Year, Money.
        font = pygame.font.Font(None, 24)
        self.screen.blit(font.render(f"Time: {self.current_hour:02d}:{self.current_minute:02d} Day: {self.day}/28  Season: {self.season}", True, COLOR_TEXT), (50, 10))
        self.screen.blit(font.render(f"Year: {self.year} Money: ${self.money}", True, COLOR_TEXT), (50, 30))
        # Note: pygame.display.flip() is not called here since we use the off-screen surface.

# ─────────────────────────────
# Streamlit Integration
# ─────────────────────────────

def main():
    # Initialize session state variables if not already set.
    if 'game' not in st.session_state:
        st.session_state.game = Game()
        st.session_state.last_time = time.time()
        st.session_state.dragging = False
        st.session_state.previous_points = []  # to track previous canvas points

    game = st.session_state.game

    # Compute dt based on elapsed time.
    current_time = time.time()
    dt = current_time - st.session_state.last_time
    st.session_state.last_time = current_time

    # Sidebar button to toggle shop mode (preserves original key binding 's').
    if st.sidebar.button("Toggle Shop Mode"):
        game.toggle_shop_mode()

    # Update game time and redraw game.
    game.update_time(dt)
    game.draw()

    # Convert the pygame off-screen surface to a NumPy array, then to a PIL Image.
    arr = pygame.surfarray.array3d(game.screen)
    arr = np.transpose(arr, (1, 0, 2))
    game_image = Image.fromarray(arr)

    # Display the canvas with the game image as background.
    canvas_result = dummy_image_to_url(
        fill_color="rgba(0,0,0,0)",
        stroke_width=5,
        stroke_color="#000000",
        background_image=game_image,
        update_streamlit=True,
        height=SCREEN_HEIGHT,
        width=SCREEN_WIDTH,
        drawing_mode="point",
        key="game_canvas"
    )

    # Process mouse events from the canvas.
    if canvas_result.json_data is not None:
        data = json.loads(canvas_result.json_data)
        if "objects" in data:
            objects = data["objects"]
            # Process each drawn object as a mouse event.
            for obj in objects:
                if "left" in obj and "top" in obj:
                    x = obj["left"]
                    y = obj["top"]
                    # On first point (simulate MOUSEBUTTONDOWN).
                    if not st.session_state.dragging:
                        game.handle_mouse_click((x, y))
                        st.session_state.dragging = True
                    else:
                        # Subsequent points simulate dragging.
                        game.handle_mouse_drag((x, y))
            # If no objects and dragging was active, simulate MOUSEBUTTONUP.
            if len(objects) == 0 and st.session_state.dragging:
                st.session_state.dragging = False
                game.dragged_tiles.clear()

    # Display the updated game image.
    import io
    buf = io.BytesIO()
    game_image.save(buf, format='PNG')
    img_bytes = buf.getvalue()
    st.image(img_bytes, caption="Farming Game", use_column_width=True)


# Optionally, you can enable auto‑refresh (for example, every 100 ms) to simulate a real‑time game loop.
# Uncomment the following lines if you wish to enable auto‑refresh.
# from streamlit_autorefresh import st_autorefresh
# st_autorefresh(interval=100, key="game_autorefresh")

if __name__ == '__main__':
    pygame.init()
    main()
