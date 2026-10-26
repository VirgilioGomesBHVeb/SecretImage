from pathlib import Path

from PIL import Image

END_MARKER = b"SI2_END_v1"


def _bytes_to_bits(data: bytes):
    for byte in data:
        for shift in range(7, -1, -1):
            yield (byte >> shift) & 1


def _bits_to_bytes(bits):
    result = bytearray()
    value = 0
    count = 0

    for bit in bits:
        value = (value << 1) | bit
        count += 1

        if count == 8:
            result.append(value)
            value = 0
            count = 0

    return bytes(result)


def _validate_image(path: Path):
    try:
        with Image.open(path) as img:
            img.verify()
    except Exception as exc:
        raise ValueError("O ficheiro enviado não é uma imagem válida.") from exc


def hide_payload(input_path, payload: bytes, output_path):
    input_path = Path(input_path)
    output_path = Path(output_path)

    _validate_image(input_path)

    with Image.open(input_path) as source:
        image = source.convert("RGB")

    data = payload + END_MARKER
    required_bits = len(data) * 8
    capacity_bits = image.width * image.height * 3

    if required_bits > capacity_bits:
        raise ValueError(
            f"A mensagem é grande demais para esta imagem. "
            f"Capacidade aproximada: {capacity_bits // 8} bytes."
        )

    bits = _bytes_to_bits(data)
    pixels = list(image.getdata())
    new_pixels = []
    finished = False

    for pixel in pixels:
        channels = list(pixel)

        for channel in range(3):
            if finished:
                break

            try:
                bit = next(bits)
            except StopIteration:
                finished = True
                break

            channels[channel] = (channels[channel] & 0xFE) | bit

        new_pixels.append(tuple(channels))

    image.putdata(new_pixels)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, "PNG")


def extract_payload(image_path) -> bytes:
    image_path = Path(image_path)
    _validate_image(image_path)

    with Image.open(image_path) as source:
        image = source.convert("RGB")

    bits = []
    for pixel in image.getdata():
        bits.extend(channel & 1 for channel in pixel)

    data = _bits_to_bytes(bits)
    marker_position = data.find(END_MARKER)

    if marker_position == -1:
        raise ValueError(
            "Nenhuma mensagem SecretImage 2.0 foi encontrada."
        )

    return data[:marker_position]
