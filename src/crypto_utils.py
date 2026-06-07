from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

# ==========================================
# Generate RSA Key Pair
# ==========================================

def generate_key_pair():

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    public_key = private_key.public_key()

    return private_key, public_key

# ==========================================
# Sign Message
# ==========================================

def sign_message(private_key, message):

    signature = private_key.sign(
        message.encode(),
        padding.PKCS1v15(),
        hashes.SHA256()
    )

    return signature

# ==========================================
# Verify Signature
# ==========================================

def verify_signature(
    public_key,
    message,
    signature
):

    try:

        public_key.verify(
            signature,
            message.encode(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )

        return True

    except Exception:

        return False