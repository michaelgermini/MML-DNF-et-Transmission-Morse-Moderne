#!/usr/bin/env python3
"""
Démonstration de la sécurité avancée DNF-MML-Morse

Montre le chiffrement AES-GCM, les signatures numériques RSA,
et les transmissions sécurisées.
"""

import sys
import json
from pathlib import Path

# Ajout du répertoire src au path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def demo_encryption():
    """Démonstration du chiffrement AES-GCM"""
    print("[AES] Démonstration du chiffrement AES-GCM")
    print("=" * 60)

    from dnf_mml_morse.security import EncryptionManager

    enc = EncryptionManager()

    # Texte à chiffrer
    secret_message = b"Ceci est un message secret pour transmission securisee!"
    print(f"Message original: {secret_message.decode()}")

    # Chiffrement
    key = enc.generate_key()  # Clé aléatoire
    associated_data = b"metadata_importante"

    encrypted = enc.encrypt(secret_message, key, associated_data)
    print("
Message chiffré:"    print(f"  Algorithme: {encrypted['algorithm']}")
    print(f"  Ciphertext: {encrypted['ciphertext'][:50]}...")
    print(f"  IV: {encrypted['iv']}")
    print(f"  Tag: {encrypted['tag']}")

    # Déchiffrement
    decrypted = enc.decrypt(encrypted, key)
    print(f"\nMessage déchiffré: {decrypted.decode()}")
    print(f"Intégrité: {'✓ OK' if decrypted == secret_message else '✗ ERREUR'}")

    print()

def demo_signatures():
    """Démonstration des signatures numériques RSA"""
    print("[RSA] Démonstration des signatures numériques RSA-PSS")
    print("=" * 60)

    from dnf_mml_morse.security import SignatureManager

    sig = SignatureManager()

    # Génération de clés
    private_key, public_key = sig.generate_keypair()

    # Message à signer
    message = b"Document officiel pour transmission securisee"
    print(f"Message à signer: {message.decode()}")

    # Signature
    signature = sig.sign_data(message, private_key)
    print(f"\nSignature créée: {signature[:50]}...")

    # Vérification
    is_valid = sig.verify_signature(message, signature, public_key)
    print(f"Vérification de signature: {'✓ VALIDE' if is_valid else '✗ INVALIDE'}")

    # Tentative de vérification avec message modifié
    modified_message = b"Document officiel MODIFIE pour transmission securisee"
    is_valid_modified = sig.verify_signature(modified_message, signature, public_key)
    print(f"Vérification avec message modifié: {'✓ VALIDE' if is_valid_modified else '✗ INVALIDE (normal)'}")

    print()

def demo_secure_transmission():
    """Démonstration de transmission sécurisée complète"""
    print("[SECURE] Démonstration de transmission sécurisée")
    print("=" * 60)

    from dnf_mml_morse.security import SecureTransmissionManager, KeyManager

    # Configuration des identités
    alice_km = KeyManager()
    bob_km = KeyManager()

    alice_identity = alice_km.generate_identity("alice")
    bob_identity = bob_km.generate_identity("bob")

    print("Identités créées:")
    print(f"  Alice: {alice_identity['name']}")
    print(f"  Bob: {bob_identity['name']}")

    # Gestionnaire sécurisé pour Alice
    alice_secure = SecureTransmissionManager(alice_km)

    # Message à transmettre
    message = b"Hello Bob! Ceci est un message securise de Alice."
    print(f"\nMessage à transmettre: {message.decode()}")

    # Création du message sécurisé
    secure_message = alice_secure.create_secure_message(
        message,
        sender_identity="alice",
        recipient_identity="bob",
        encrypt=True,
        sign=True
    )

    print("
Message sécurisé créé:"    print(f"  Expéditeur: {secure_message['sender']}")
    print(f"  Chiffré: {secure_message['encrypted']}")
    print(f"  Signé: {secure_message['signed']}")
    print(f"  Timestamp: {secure_message['timestamp']}")
    print(f"  Taille: {len(json.dumps(secure_message))} caractères")

    # Simulation de transmission (sérialisation JSON)
    transmitted_data = json.dumps(secure_message)
    print(f"\nTransmission simulée: {len(transmitted_data)} caractères")

    # Réception et vérification par Bob
    received_message = json.loads(transmitted_data)

    # Gestionnaire sécurisé pour Bob
    bob_secure = SecureTransmissionManager(bob_km)

    success, decrypted_data = bob_secure.verify_secure_message(
        received_message,
        expected_sender="alice"
    )

    print("
Réception et vérification:"    print(f"  Succès: {'✓ OUI' if success else '✗ NON'}")
    if success:
        print(f"  Message déchiffré: {decrypted_data.decode()}")
        print(f"  Intégrité: {'✓ OK' if decrypted_data == message else '✗ ERREUR'}")

    print()

def demo_identity_management():
    """Démonstration de gestion des identités"""
    print("[IDENTITY] Démonstration de gestion des identités")
    print("=" * 60)

    from dnf_mml_morse.security import KeyManager

    km = KeyManager()

    # Création d'identités
    identities = ["operator1", "station_alpha", "emergency_ops"]

    print("Création d'identités:")
    for name in identities:
        identity = km.generate_identity(name)
        print(f"  ✓ {name}: créée le {identity['created'][:19]}")

    # Liste des identités
    available = km.list_identities()
    print(f"\nIdentités disponibles: {len(available)}")
    for identity in available:
        print(f"  - {identity}")

    # Export d'une identité publique
    public_data = km.load_identity("operator1")
    print(f"\nExport de l'identité 'operator1':")
    print(f"  Nom: {public_data['identity']['name']}")
    print(f"  Créée: {public_data['identity']['created']}")
    print(f"  Clé publique: {public_data['identity']['public_key'][:50]}...")

    print()

def demo_performance():
    """Démonstration des performances de sécurité"""
    print("[PERFORMANCE] Performance du chiffrement et signatures")
    print("=" * 60)

    import time
    from dnf_mml_morse.security import EncryptionManager, SignatureManager

    # Préparation
    enc = EncryptionManager()
    sig = SignatureManager()
    private_key, public_key = sig.generate_keypair()

    # Données de test
    test_data = b"A" * 10000  # 10KB de données
    key = enc.generate_key()

    print(f"Test avec {len(test_data)} octets de données")

    # Test chiffrement
    start_time = time.time()
    encrypted = enc.encrypt(test_data, key)
    encrypt_time = time.time() - start_time

    start_time = time.time()
    decrypted = enc.decrypt(encrypted, key)
    decrypt_time = time.time() - start_time

    print("
Chiffrement AES-256-GCM:"    print(f"  Chiffrement: {encrypt_time:.4f}s ({len(test_data)/encrypt_time/1024:.1f} KB/s)")
    print(f"  Déchiffrement: {decrypt_time:.4f}s ({len(test_data)/decrypt_time/1024:.1f} KB/s)")
    print(f"  Intégrité: {'✓ OK' if decrypted == test_data else '✗ ERREUR'}")

    # Test signature
    start_time = time.time()
    signature = sig.sign_data(test_data, private_key)
    sign_time = time.time() - start_time

    start_time = time.time()
    is_valid = sig.verify_signature(test_data, signature, public_key)
    verify_time = time.time() - start_time

    print("
Signature RSA-PSS:"    print(f"  Signature: {sign_time:.4f}s")
    print(f"  Vérification: {verify_time:.4f}s")
    print(f"  Validité: {'✓ OK' if is_valid else '✗ ERREUR'}")

    print()

def main():
    """Fonction principale de démonstration"""
    print("🔐 Démonstration de la sécurité avancée - DNF-MML-Morse")
    print("=" * 80)
    print()

    try:
        demo_encryption()
        demo_signatures()
        demo_secure_transmission()
        demo_identity_management()
        demo_performance()

        print("🎉 Démonstration sécurité terminée!")
        print()
        print("💡 Fonctionnalités de sécurité implémentées:")
        print("   • Chiffrement AES-256-GCM authentifié")
        print("   • Signatures numériques RSA-PSS")
        print("   • Gestion d'identités avec keystore")
        print("   • Transmissions sécurisées end-to-end")
        print("   • Vérification d'intégrité et authenticité")
        print("   • Performance optimisée pour la transmission")

    except Exception as e:
        print(f"❌ Erreur lors de la démonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
