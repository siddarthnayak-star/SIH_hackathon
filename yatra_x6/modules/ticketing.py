import qrcode, io, base64

def generate_ticket_qr(ticket_id):
    qr = qrcode.make(ticket_id)  # encode the ticket UUID
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()
