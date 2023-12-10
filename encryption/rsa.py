import random
import math


def setkeys():
    prime1 = 7  # First prime number
    prime2 = 11  # Second prime number

    n = prime1 * prime2
    phi_n = (prime1 - 1) * (prime2 - 1)

    possible_e_values = [e for e in range(2, phi_n) if math.gcd(e, phi_n) == 1]
    e = random.choice(possible_e_values)

    # d = (k*Φ(n) + 1) / e for some integer k
    public_key = e

    d = 2
    while True:
        if (d * e) % phi_n == 1:
            break
        d += 1

    private_key = d

    return public_key, private_key, n


# To encrypt the given number
def encrypt(message, public_key, n):
    e = public_key
    encrypted_text = 1
    while e > 0:
        encrypted_text *= message
        encrypted_text %= n
        e -= 1
    return encrypted_text


# To decrypt the given number
def decrypt(encrypted_text, private_key, n):
    d = private_key
    decrypted = 1
    while d > 0:
        decrypted *= encrypted_text
        decrypted %= n
        d -= 1
    return decrypted


# First converting each character to its ASCII value and
# then encoding it then decoding the number to get the
# ASCII and converting it to character
def encoder(message):
    encoded = []
    # Calling the encrypting function in encoding function
    for letter in message:
        encoded.append(encrypt(ord(letter)))
    return encoded


def decoder(encoded):
    s = ''
    # Calling the decrypting function decoding function
    for num in encoded:
        s += chr(decrypt(num))
    return s
