import asyncio
import argparse
import base64
from pathlib import Path
from tkinter import Tk, filedialog, messagebox
from meshcore import MeshCore, EventType

MAX_SIZE = 1 * 1024 * 1024  # 1MB

async def main():
    parser = argparse.ArgumentParser(
        description="Send an image over MeshCore via BLE using a GUI file picker"
    )
    parser.add_argument(
        "device", help="BLE address or name of the MeshCore radio"
    )
    parser.add_argument("contact", help="Destination contact name")
    parser.add_argument(
        "--chunk", type=int, default=200, help="Chunk size in bytes of base64 data"
    )
    args = parser.parse_args()

    root = Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title="Select Image File")
    root.destroy()
    if not file_path:
        print("No image selected")
        return

    image_path = Path(file_path)
    if image_path.stat().st_size > MAX_SIZE:
        messagebox.showerror(
            "File Too Large", "Selected image exceeds the 1MB size limit"
        )
        return

    # Connect via BLE
    meshcore = await MeshCore.create_ble(args.device)
    await meshcore.ensure_contacts()

    contact = meshcore.get_contact_by_name(args.contact)
    if not contact:
        print(f"Contact '{args.contact}' not found")
        await meshcore.disconnect()
        return

    data = base64.b64encode(image_path.read_bytes()).decode("ascii")
    chunk_size = args.chunk
    total = (len(data) + chunk_size - 1) // chunk_size
    print(f"Sending {total} chunks")

    for i in range(total):
        part = data[i*chunk_size:(i+1)*chunk_size]
        text = f"IMG {i+1}/{total}:{part}"
        result = await meshcore.commands.send_msg(contact, text)
        if result.type == EventType.ERROR:
            print(f"Failed to send chunk {i+1}: {result.payload}")
            break
        await asyncio.sleep(0.5)

    await meshcore.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
