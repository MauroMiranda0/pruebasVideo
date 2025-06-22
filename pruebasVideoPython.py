from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import os
import time
import shutil # Make sure shutil is imported


# Configuración
output_video = "escritura_con_cursor.mp4"
codigo = """
Aqui va a ir todo el codigo probablemente tenga que copiar para poner otro tipo
de codigo sin embargo
   por ahoraesta bien si queda asi
      eso espero
"""

# Parámetros visuales
# Cargamos la captura de pantalla de VS Code que servirá de fondo
background_image_path = "vscode_background.png"
background_image = Image.open(background_image_path).convert("RGB")
width, height = background_image.size
bg_color = (25, 25, 25)  # Color de fondo por si se necesita un tono base
# Use a different base color for the code text itself, as the highlight function will apply specific colors
text_color = (200, 200, 200) # Light grey base for general text not highlighted
font_size = 24
cursor_color = (0, 255, 0)
cursor_char = "|"  # Puedes cambiarlo por "_" o "|"
font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
line_spacing = 4
margin_x, margin_y = 50, 50
duracion_por_frame = 0.03 # Define the duration per frame here
fps_salida = int(1 / duracion_por_frame)

# Colores específicos para highlighting (using the updated scheme)
number_color = (128, 128, 128) # Gris para los números de línea
keyword_color = (86, 156, 214) # #569CD6 Azul claro
attribute_color = (220, 204, 170) # #DCDCAA Amarillo dorado
string_color = (78, 201, 176) # #4EC9B0 Turquesa suave
tag_color = (197, 134, 192) # #C586C0 Lavanda/Morado claro
property_color = (156, 220, 254) # #9CDCFE Azul celeste
css_value_color = (206, 145, 120) # #CE9178 Naranja claro
comment_color = (96, 139, 78) # #608B4E Verde oliva apagado


# Función para colorear el código (updated to be more robust and use new colors)
def highlight_code(line, font, base_color, draw, x, y, line_number=None,
                   number_color=(128, 128, 128), # Gris
                   keyword_color=(86, 156, 214), # #569CD6 Azul claro
                   attribute_color=(220, 204, 170), # #DCDCAA Amarillo dorado
                   string_color=(78, 201, 176), # #4EC9B0 Turquesa suave
                   tag_color=(197, 134, 192), # #C586C0 Lavanda/Morado claro
                   property_color=(156, 220, 254), # #9CDCFE Azul celeste
                   css_value_color=(206, 145, 120), # #CE9178 Naranja claro
                   comment_color=(96, 139, 78)): # #608B4E Verde oliva apagado


    current_x = x

    if line_number is not None:
        line_number_str = f"{line_number: >4}  " # Añadir padding y espacio
        try:
            draw.text((current_x, y), line_number_str, font=font, fill=number_color)
            current_x += draw.textlength(line_number_str, font=font)
        except AttributeError:
             # Handle the case where font is the default PIL font or older PIL versions
            draw.text((current_x, y), line_number_str, font=font, fill=number_color)
            # Estimate text length for default font (may not be perfectly accurate)
            # Fallback for older PIL versions or default font
            try:
                char_width = font.getbbox(" ")[2] - font.getbbox(" ")[0] # Approximate width of a character
            except IndexError: # Handle case where space might not have a valid bounding box
                 char_width = font_size // 2 # Rough estimate
            current_x += len(line_number_str) * char_width


    # More robust tokenization and highlighting
    # This is still a simplified approach and might not handle all edge cases of HTML/CSS
    tokens = []
    buffer = ""
    in_string = False
    in_tag = False
    in_css_rule = False # Simple flag for CSS rules

    css_properties = ['color', 'background-color', 'font-family', 'font-size'] # Example CSS properties

    for char in line:
        if char == '"':
            if buffer:
                tokens.append(('text', buffer))
            tokens.append(('string_quote', '"'))
            buffer = ""
            in_string = not in_string
        elif in_string:
            buffer += char
        elif char in ['<', '>']:
            if buffer:
                tokens.append(('text', buffer))
            tokens.append(('tag_bracket', char))
            buffer = ""
            if char == '<':
                in_tag = True
            elif char == '>':
                in_tag = False
        elif char in [':', ';', '{', '}'] and not in_tag: # Simple CSS delimiters
             if buffer:
                tokens.append(('text', buffer))
             tokens.append(('css_delimiter', char))
             buffer = ""
             if char == '{':
                 in_css_rule = True
             if char == '}':
                 in_css_rule = False
        elif char.isspace():
             if buffer:
                tokens.append(('text', buffer))
             tokens.append(('whitespace', char))
             buffer = ""
        else:
            buffer += char

    if buffer:
        tokens.append(('text', buffer))

    for token_type, token_value in tokens:
        color = base_color

        if token_type == 'string_quote' or (token_type == 'text' and in_string):
            color = string_color
        elif token_type == 'tag_bracket':
            color = tag_color # Treat brackets as part of the tag structure
        elif token_type == 'text':
            # Simple keyword/tag/attribute check
            if token_value.lower() in ['!doctype', 'html', 'head', 'title', 'style', 'body', 'h1', 'p']:
                 color = tag_color # Tag names
            elif token_value.lower() in ['class', 'id', 'href', 'ul', 'li']: # More HTML keywords/tags
                 color = keyword_color
            elif '=' in token_value and in_tag: # Simple attribute check
                 color = attribute_color
            elif token_value.lower() in css_properties and in_css_rule:
                color = property_color
            # Basic check for CSS values (might need refinement)
            elif in_css_rule and not any(css_prop in token_value.lower() for css_prop in css_properties) and ':' in line.split(token_value, 1)[0]:
                 color = css_value_color

        # For simplicity, whitespace and other delimiters keep the base color or are just spaces
        if token_type == 'whitespace' or token_type == 'css_delimiter':
             pass # Keep base color or handle as space

        try:
            draw.text((current_x, y), token_value, font=font, fill=color)
            current_x += draw.textlength(token_value, font=font)
        except AttributeError:
            draw.text((current_x, y), token_value, font=font, fill=color)
            # Fallback for older PIL versions or default font
            try:
                char_width = font.getbbox(" ")[2] - font.getbbox(" ")[0]
            except IndexError:
                 char_width = font_size // 2
            current_x += len(token_value) * char_width


# Crear carpeta temporal
os.makedirs("frames", exist_ok=True)

# Inicializar contenido
frames = []
contenido_actual = ""

# 1. Pausa inicial en blanco (or with empty editor screen)
for i in range(int(3 / duracion_por_frame)):  # Pausa de 3 segundos
    img = background_image.copy()
    img.save(f"frames/inicio_{i:03d}.png")
    frames.append(f"frames/inicio_{i:03d}.png")

# 2. Escritura letter by letter with blinking cursor and highlighting
mostrar_cursor = True
lineas_completadas = ""
linea_actual_en_escritura = ""
line_number = 1
# Ensure code ends with a newline to process the last line
if not codigo.endswith('\n'):
    codigo += '\n'

for i, letra in enumerate(codigo):
    linea_actual_en_escritura += letra

    if letra == '\n':
        lineas_completadas += linea_actual_en_escritura
        linea_actual_en_escritura = ""
        line_number += 1

    for parpadeo in range(2):  # Two frames per letter (one with cursor, one without)
        img = background_image.copy()
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype(font_path, font_size)
        except (IOError, OSError):
            font = ImageFont.load_default()
            # print(f"Advertencia: Fuente '{font_path}' no encontrada. Usando fuente por defecto.")
        except Exception as e:
            font = ImageFont.load_default()
            # print(f"Error al cargar la fuente '{font_path}': {e}. Usando fuente por defecto.")


        # Draw completed lines with highlighting
        y_offset = margin_y
        for j, completed_line in enumerate(lineas_completadas.splitlines()):
            highlight_code(completed_line, font, text_color, draw, margin_x, y_offset,
                           line_number=j+1, number_color=number_color, keyword_color=keyword_color,
                           tag_color=tag_color, attribute_color=attribute_color, string_color=string_color,
                           property_color=property_color, css_value_color=css_value_color, comment_color=comment_color)
            # Calculate line height based on font metrics
            try:
                y_offset += font.getbbox("A")[3] - font.getbbox("A")[1] + line_spacing
            except (AttributeError, IndexError):
                # Approximate line height for default font
                y_offset += font.getbbox("A")[3] + line_spacing if hasattr(font, 'getbbox') else font_size + line_spacing


        # Draw the current line being typed
        texto_linea_actual = linea_actual_en_escritura
        if mostrar_cursor and parpadeo % 2 == 0:
             texto_linea_actual += cursor_char

        highlight_code(texto_linea_actual, font, text_color, draw, margin_x, y_offset,
                       line_number=line_number, number_color=number_color, keyword_color=keyword_color,
                       tag_color=tag_color, attribute_color=attribute_color, string_color=string_color,
                       property_color=property_color, css_value_color=css_value_color, comment_color=comment_color)


        frame_path = f"frames/frame_{i:04d}_{parpadeo}.png"
        img.save(frame_path)
        frames.append(frame_path)

# 3. Final pause (static screen with complete code and blinking cursor)
contenido_final = lineas_completadas + linea_actual_en_escritura # All code at the end

for i in range(int(4.5 / duracion_por_frame)): # 4.5 second pause
    img = background_image.copy()
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(font_path, font_size)
    except (IOError, OSError):
        font = ImageFont.load_default()
        # print(f"Advertencia: Fuente '{font_path}' no encontrada para la pausa final. Usando fuente por defecto.")
    except Exception as e:
        font = ImageFont.load_default()
        # print(f"Error al cargar la fuente '{font_path}' para la pausa final: {e}. Usando fuente por defecto.")


    y_offset = margin_y
    for j, final_line in enumerate(contenido_final.splitlines()):
        # Add cursor to the last line of content_final during the final pause if i is even
        line_to_highlight = final_line
        if j == len(contenido_final.splitlines()) - 1 and i % 2 == 0:
             line_to_highlight += cursor_char

        highlight_code(line_to_highlight, font, text_color, draw, margin_x, y_offset,
                       line_number=j+1, number_color=number_color, keyword_color=keyword_color,
                       tag_color=tag_color, attribute_color=attribute_color, string_color=string_color,
                       property_color=property_color, css_value_color=css_value_color, comment_color=comment_color)
        try:
            y_offset += font.getbbox("A")[3] - font.getbbox("A")[1] + line_spacing
        except (AttributeError, IndexError):
             y_offset += font.getbbox("A")[3] + line_spacing if hasattr(font, 'getbbox') else font_size + line_spacing


    frame_path = f"frames/final_{i:03d}.png"
    img.save(frame_path)
    frames.append(frame_path)


# 4. Create video
clips = [ImageClip(f).set_duration(duracion_por_frame) for f in frames]
video = concatenate_videoclips(clips, method="compose")
video.write_videofile(output_video, fps=fps_salida)

# Cleanup
shutil.rmtree("frames")
