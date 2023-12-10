import encryption.table as t


def text_to_binary(text):
    binary_result = ""
    for char in text:
        binary_char = bin(ord(char))[2:].zfill(8)
        binary_result += binary_char

    # Pad the binary result with zeros to make it a multiple of 64 bits
    padding_size = (64 - len(binary_result) % 64) % 64
    binary_result += '0' * padding_size

    return [binary_result[i:i+64] for i in range(0, len(binary_result), 64)]


def binary_to_text(binary_list):
    binary_str = ''.join(binary_list)
    text = ""
    for i in range(0, len(binary_str), 8):
        char_binary = binary_str[i:i+8]
        try:
            char = chr(int(char_binary, 2))
            # Check if the character is printable ASCII
            if not (32 <= ord(char) <= 126):
                text += ' '  # Replace non-printable characters with empty space
            else:
                text += char
        except ValueError:
            text += ' '  # Replace invalid characters with empty space
    return text



def binary_to_hex(binary_str):
    # Convert decimal to hexadecimal
    hexadecimal_number = format(int(binary_str, 2), 'X')

    return hexadecimal_number


def permute(source, table):
    result = ""
    for i in table:
        result += source[i - 1]
    return result


def left_shift_binary(binary_str, n):
    return binary_str[n:] + binary_str[:n]


def binary_xor(bin_str1, bin_str2):
    # Ensure both binary strings have the same length
    max_len = max(len(bin_str1), len(bin_str2))
    bin_str1 = bin_str1.zfill(max_len)
    bin_str2 = bin_str2.zfill(max_len)

    result = ''
    for i in range(max_len):
        if bin_str1[i] == bin_str2[i]:
            result += '0'
        else:
            result += '1'

    return result


def decimal_to_binary(decimal):
    if decimal == 0:
        return "0000"

    binary_str = ""
    while decimal > 0:
        binary_str = str(decimal % 2) + binary_str
        decimal //= 2

    while len(binary_str) < 4:
        binary_str = '0' + binary_str

    return binary_str


def generateKeys(key):
    round_keys = []

    # 64 bits to 56 bits
    pc1_key = permute(key, t.pc1)

    left = pc1_key[0:28]
    right = pc1_key[28:56]

    for i in range(0, 8):
        left = left_shift_binary(left, t.shift_round[i])
        right = left_shift_binary(right, t.shift_round[i])

        # 56 bits to 48 bits
        round_key = permute(left + right, t.pc2)

        round_keys.append(round_key)

    return round_keys


def encrypt(plaintext, round_keys):
    # initial permutation
    ip_plaintext = permute(plaintext, t.initial_perm)
    left = ip_plaintext[0:32]
    right = ip_plaintext[32:64]
    for i in range(0, 8):
        # print("Round Key: ", i + 1, " = ", binary_to_hex(left), " ; ", binary_to_hex(right), " ; " , binary_to_hex(round_keys[i]))
        # right 32 bit to 48 bit
        right_expanded = permute(right, t.exp_perm)

        right_xored = binary_xor(right_expanded, round_keys[i])

        # back from right 48 bit to 32 bit
        right_sboxed = ""
        for j in range(0, 48, 6):
            chunk = right_xored[j:j + 6]
            row = int(chunk[0] + chunk[5], 2)
            col = int(chunk[1:5], 2)

            # Get the value from the S-Box
            right_sboxed += decimal_to_binary(t.sbox_perm[j//6][row][col])

        right_pboxed = permute(right_sboxed, t.pbox_perm)
        right_result = binary_xor(left, right_pboxed)

        left = right
        right = right_result

    cipher_text = permute((right + left), t.inverse_initial_perm)
    return cipher_text


def decrypt(ciphertext, round_keys):
    rev_round_keys = round_keys[::-1]
    return encrypt(ciphertext, rev_round_keys)
