import gradio as gr
import sqlite3
import os
from PIL import Image, ImageDraw

# =====================================
# DATABASE FILE
# =====================================

DB_FILE = r"C:\Users\LENOVO\Desktop\darshan\ClassRoomNavigation\NAVIGO_DATA.db"

# =====================================
# DIRECTIONS
# =====================================


# =====================================
# GET ROUTE IMAGES FROM SQLITE
# =====================================

def get_route_images(room_code):

    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT image_folder
        FROM Rooms
        WHERE room_code=?
    """, (room_code,))

    result = cursor.fetchone()

    conn.close()

    if result is None:
        return None

    folder_path = result[0]

    if not os.path.exists(folder_path):
        return None

    image_paths = []

    for file in sorted(os.listdir(folder_path)):

        if file.lower().endswith((".jpg", ".jpeg", ".png")):

            image_paths.append(os.path.join(folder_path, file))

    return image_paths

def get_room_directions(room_code):

    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT direction
        FROM RoomDirections
        WHERE room_code = ?
        ORDER BY step_no
    """, (room_code,))

    rows = cursor.fetchall()

    conn.close()

    if not rows:
        return []

    return [row[0] for row in rows]

# =====================================
# DRAW NAVIGATION ARROW
# =====================================

def add_navigation_arrow(image_path, direction):

    img = Image.open(image_path).convert("RGBA")

    draw = ImageDraw.Draw(img)

    w, h = img.size

    color = (0, 140, 255, 230)

    mid_x = w // 2
    base_y = h - 60

    # STRAIGHT
    if direction == "straight":

        body = [
            (mid_x - 40, base_y),
            (mid_x + 40, base_y),
            (mid_x + 20, base_y - 220),
            (mid_x - 20, base_y - 220),
        ]

        head = [
            (mid_x - 80, base_y - 220),
            (mid_x + 80, base_y - 220),
            (mid_x, base_y - 320),
        ]

        draw.polygon(body, fill=color)
        draw.polygon(head, fill=color)

    # LEFT
    elif direction == "straight-left":

        draw.polygon([
            (mid_x - 40, base_y),
            (mid_x + 40, base_y),
            (mid_x + 20, base_y - 180),
            (mid_x - 20, base_y - 180),
        ], fill=color)

        draw.polygon([
            (mid_x - 20, base_y - 180),
            (mid_x - 180, base_y - 180),
            (mid_x - 180, base_y - 140),
            (mid_x - 20, base_y - 140),
        ], fill=color)

        draw.polygon([
            (mid_x - 180, base_y - 220),
            (mid_x - 180, base_y - 100),
            (mid_x - 260, base_y - 160),
        ], fill=color)

    # RIGHT
    elif direction == "straight-right":

        draw.polygon([
            (mid_x - 40, base_y),
            (mid_x + 40, base_y),
            (mid_x + 20, base_y - 180),
            (mid_x - 20, base_y - 180),
        ], fill=color)

        draw.polygon([
            (mid_x + 20, base_y - 180),
            (mid_x + 180, base_y - 180),
            (mid_x + 180, base_y - 140),
            (mid_x + 20, base_y - 140),
        ], fill=color)

        draw.polygon([
            (mid_x + 180, base_y - 220),
            (mid_x + 180, base_y - 100),
            (mid_x + 260, base_y - 160),
        ], fill=color)

    return img


# =====================================
# FIND LOCATION
# =====================================

def find_location(room_code):

    image_paths = get_route_images(room_code)

    directions = get_room_directions(room_code)

    if image_paths is None or len(image_paths) == 0:

        return (
            None,
            "❌ Room not found",
            0,
            [],
            [],
            gr.update(visible=False),
            gr.update(visible=False)
        )

    if len(directions) == 0:

        return (
            None,
            "❌ Directions not found",
            0,
            [],
            [],
            gr.update(visible=False),
            gr.update(visible=False)
        )

    img = add_navigation_arrow(
        image_paths[0],
        directions[0]
    )

    return (
        img,
        f"Step 1 of {len(image_paths)}",
        0,
        image_paths,
        directions,
        gr.update(visible=True),
        gr.update(visible=False)
    )


# =====================================
# NEXT STEP
# =====================================

def next_step(step, image_paths, directions):

    step += 1

    if step >= len(image_paths):

        return (
            None,
            "✅ Destination Reached",
            step,
            image_paths,
            directions,
            gr.update(visible=False),
            gr.update(visible=True)
        )

    direction = directions[
        min(step, len(directions)-1)
    ]

    img = add_navigation_arrow(
        image_paths[step],
        direction
    )

    return (
        img,
        f"Step {step+1} of {len(image_paths)}",
        step,
        image_paths,
        directions,
        gr.update(visible=True),
        gr.update(visible=True)
    )


# =====================================
# PREVIOUS STEP
# =====================================

def previous_step(step, image_paths, directions):

    step -= 1

    if step < 0:
        step = 0

    direction = directions[
        min(step, len(directions)-1)
    ]

    img = add_navigation_arrow(
        image_paths[step],
        direction
    )

    return (
        img,
        f"Step {step+1} of {len(image_paths)}",
        step,
        image_paths,
        directions,
        gr.update(visible=True)
    )


# =====================================
# UI
# =====================================

with gr.Blocks(theme=gr.themes.Soft()) as app:

    gr.Markdown(
        """
        # NAVIGO
        ### Smart Indoor Navigation
        """
    )

    room_input = gr.Textbox(
        label="Enter Room Code",
        placeholder="AI034F03"
    )

    search_btn = gr.Button(
        "Find Route",
        variant="primary"
    )

    image_output = gr.Image(
        label="Navigation View"
    )

    status_output = gr.Textbox(
        label="Status"
    )

    step_state = gr.State(0)

    image_paths_state = gr.State([])
    directions_state=gr.State([])

    with gr.Row():

        back_btn = gr.Button(
            "⬅ Back",
            visible=False
        )

        next_btn = gr.Button(
            "Next ➡",
            visible=False
        )

    # SEARCH
    search_btn.click(
    find_location,
    inputs=room_input,
    outputs=[
        image_output,
        status_output,
        step_state,
        image_paths_state,
        directions_state,
        next_btn,
        back_btn
    ]
)

    # NEXT
    next_btn.click(
    next_step,
    inputs=[
        step_state,
        image_paths_state,
        directions_state
    ],
    outputs=[
        image_output,
        status_output,
        step_state,
        image_paths_state,
        directions_state,
        next_btn,
        back_btn
    ]
)

    # BACK
    back_btn.click(
    previous_step,
    inputs=[
        step_state,
        image_paths_state,
        directions_state
    ],
    outputs=[
        image_output,
        status_output,
        step_state,
        image_paths_state,
        directions_state,
        next_btn
    ]
)

# =====================================
# RUN
# =====================================

app.launch(

    share=True,

    allowed_paths=[
        r"C:\Users\LENOVO\Desktop\darshan\ClassRoomNavigation\routes"
    ]

)