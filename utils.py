import qrcode

def generate_qr(roll_no):

    img = qrcode.make(roll_no)

    file_path = f"qr_codes/{roll_no}.png"

    img.save(file_path)

    return file_path