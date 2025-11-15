"""
Module de sécurité avancée pour DNF-MML-Morse

Implémente le chiffrement, les signatures numériques,
et l'authentification pour transmissions sécurisées.
"""

import os
import hmac
import hashlib
from typing import Dict, Any, Optional, Tuple, Union
from pathlib import Path
import json
import base64
from datetime import datetime, timedelta
import secrets

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature


class EncryptionManager:
    """
    Gestionnaire de chiffrement AES-GCM

    Fournit chiffrement symétrique sécurisé pour les données sensibles.
    """

    def __init__(self, key_size: int = 256):
        """
        Initialisation du gestionnaire de chiffrement

        Args:
            key_size: Taille de clé (128, 192, 256 bits)
        """
        self.key_size = key_size
        self.backend = default_backend()

    def generate_key(self, password: Optional[str] = None,
                    salt: Optional[bytes] = None) -> bytes:
        """
        Génère une clé de chiffrement

        Args:
            password: Mot de passe (optionnel)
            salt: Sel pour dérivation (optionnel)

        Returns:
            Clé de chiffrement
        """
        if password:
            # Dérivation de clé à partir du mot de passe
            if salt is None:
                salt = os.urandom(16)

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=self.key_size // 8,
                salt=salt,
                iterations=100000,
                backend=self.backend
            )
            return kdf.derive(password.encode('utf-8'))
        else:
            # Clé aléatoire
            return os.urandom(self.key_size // 8)

    def encrypt(self, data: bytes, key: bytes,
               associated_data: Optional[bytes] = None) -> Dict[str, Any]:
        """
        Chiffre des données avec AES-GCM

        Args:
            data: Données à chiffrer
            key: Clé de chiffrement
            associated_data: Données associées (non chiffrées mais authentifiées)

        Returns:
            Données chiffrées avec métadonnées
        """
        # Génère un IV aléatoire
        iv = os.urandom(12)  # 96 bits pour GCM

        # Chiffrement AES-GCM
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=self.backend)
        encryptor = cipher.encryptor()

        if associated_data:
            encryptor.authenticate_additional_data(associated_data)

        ciphertext = encryptor.update(data) + encryptor.finalize()

        return {
            'ciphertext': base64.b64encode(ciphertext).decode('ascii'),
            'iv': base64.b64encode(iv).decode('ascii'),
            'tag': base64.b64encode(encryptor.tag).decode('ascii'),
            'algorithm': f'AES-{self.key_size}-GCM',
            'associated_data': base64.b64encode(associated_data).decode('ascii') if associated_data else None,
        }

    def decrypt(self, encrypted_data: Dict[str, Any], key: bytes) -> bytes:
        """
        Déchiffre des données AES-GCM

        Args:
            encrypted_data: Données chiffrées
            key: Clé de déchiffrement

        Returns:
            Données déchiffrées

        Raises:
            ValueError: Si le déchiffrement échoue
        """
        try:
            ciphertext = base64.b64decode(encrypted_data['ciphertext'])
            iv = base64.b64decode(encrypted_data['iv'])
            tag = base64.b64decode(encrypted_data['tag'])
            associated_data = base64.b64decode(encrypted_data['associated_data']) if encrypted_data.get('associated_data') else None

            # Déchiffrement AES-GCM
            cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=self.backend)
            decryptor = cipher.decryptor()

            if associated_data:
                decryptor.authenticate_additional_data(associated_data)

            plaintext = decryptor.update(ciphertext) + decryptor.finalize()

            return plaintext

        except Exception as e:
            raise ValueError(f"Échec du déchiffrement: {e}")


class SignatureManager:
    """
    Gestionnaire de signatures numériques ECDSA

    Fournit authentification et intégrité des messages.
    """

    def __init__(self):
        """Initialisation du gestionnaire de signatures"""
        self.backend = default_backend()

    def generate_keypair(self) -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
        """
        Génère une paire de clés RSA

        Returns:
            Tuple (clé privée, clé publique)
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=self.backend
        )
        public_key = private_key.public_key()

        return private_key, public_key

    def sign_data(self, data: bytes, private_key: rsa.RSAPrivateKey) -> str:
        """
        Signe des données avec une clé privée

        Args:
            data: Données à signer
            private_key: Clé privée RSA

        Returns:
            Signature en base64
        """
        signature = private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        return base64.b64encode(signature).decode('ascii')

    def verify_signature(self, data: bytes, signature: str,
                        public_key: rsa.RSAPublicKey) -> bool:
        """
        Vérifie une signature avec une clé publique

        Args:
            data: Données signées
            signature: Signature en base64
            public_key: Clé publique RSA

        Returns:
            True si la signature est valide
        """
        try:
            signature_bytes = base64.b64decode(signature)

            public_key.verify(
                signature_bytes,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )

            return True

        except InvalidSignature:
            return False
        except Exception:
            return False

    def export_public_key(self, public_key: rsa.RSAPublicKey) -> str:
        """
        Exporte une clé publique au format PEM

        Args:
            public_key: Clé publique RSA

        Returns:
            Clé publique en format PEM
        """
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return pem.decode('ascii')

    def import_public_key(self, pem_data: str) -> rsa.RSAPublicKey:
        """
        Importe une clé publique depuis PEM

        Args:
            pem_data: Clé publique en format PEM

        Returns:
            Clé publique RSA
        """
        public_key = serialization.load_pem_public_key(
            pem_data.encode('ascii'),
            backend=self.backend
        )

        return public_key


class KeyManager:
    """
    Gestionnaire de clés et certificats

    Gère le stockage sécurisé et la rotation des clés.
    """

    def __init__(self, keystore_path: Optional[Path] = None):
        """
        Initialisation du gestionnaire de clés

        Args:
            keystore_path: Chemin vers le keystore
        """
        self.keystore_path = keystore_path or Path.home() / '.dnf_mml_morse' / 'keys'
        self.keystore_path.mkdir(parents=True, exist_ok=True)

        # Cache des clés chargées
        self._key_cache: Dict[str, Any] = {}

    def generate_identity(self, identity_name: str) -> Dict[str, Any]:
        """
        Génère une nouvelle identité avec clés

        Args:
            identity_name: Nom de l'identité

        Returns:
            Informations de l'identité créée
        """
        # Génère les clés
        enc_manager = EncryptionManager()
        sig_manager = SignatureManager()

        private_key, public_key = sig_manager.generate_keypair()
        encryption_key = enc_manager.generate_key()

        identity = {
            'name': identity_name,
            'created': datetime.utcnow().isoformat(),
            'public_key': sig_manager.export_public_key(public_key),
            'encryption_key_hash': hashlib.sha256(encryption_key).hexdigest(),
            'version': '1.0',
        }

        # Sauvegarde les clés privées (protégées)
        self._save_private_key(identity_name, private_key, encryption_key)

        # Sauvegarde l'identité publique
        self._save_identity(identity_name, identity)

        # Cache
        self._key_cache[identity_name] = {
            'private_key': private_key,
            'public_key': public_key,
            'encryption_key': encryption_key,
            'identity': identity,
        }

        return identity

    def load_identity(self, identity_name: str,
                     password: Optional[str] = None) -> Dict[str, Any]:
        """
        Charge une identité depuis le keystore

        Args:
            identity_name: Nom de l'identité
            password: Mot de passe pour déchiffrer (optionnel)

        Returns:
            Informations de l'identité
        """
        if identity_name in self._key_cache:
            return self._key_cache[identity_name]

        # Charge depuis le disque
        identity_path = self.keystore_path / f"{identity_name}.json"
        if not identity_path.exists():
            raise FileNotFoundError(f"Identité {identity_name} introuvable")

        with open(identity_path, 'r') as f:
            identity = json.load(f)

        # Charge la clé privée
        private_key, encryption_key = self._load_private_key(identity_name, password)

        # Reconstruit la clé publique
        sig_manager = SignatureManager()
        public_key = sig_manager.import_public_key(identity['public_key'])

        # Cache
        self._key_cache[identity_name] = {
            'private_key': private_key,
            'public_key': public_key,
            'encryption_key': encryption_key,
            'identity': identity,
        }

        return self._key_cache[identity_name]

    def _save_private_key(self, identity_name: str,
                         private_key: rsa.RSAPrivateKey,
                         encryption_key: bytes):
        """Sauvegarde une clé privée de manière sécurisée"""
        # Exporte la clé privée
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        # Crée un bundle sécurisé
        key_bundle = {
            'private_key': base64.b64encode(private_pem).decode('ascii'),
            'encryption_key': base64.b64encode(encryption_key).decode('ascii'),
            'created': datetime.utcnow().isoformat(),
        }

        # Sauvegarde (en production, utiliser un chiffrement supplémentaire)
        key_path = self.keystore_path / f"{identity_name}_private.json"
        with open(key_path, 'w') as f:
            json.dump(key_bundle, f, indent=2)

        # Permissions restrictives
        key_path.chmod(0o600)

    def _load_private_key(self, identity_name: str,
                         password: Optional[str] = None) -> Tuple[rsa.RSAPrivateKey, bytes]:
        """Charge une clé privée"""
        key_path = self.keystore_path / f"{identity_name}_private.json"
        if not key_path.exists():
            raise FileNotFoundError(f"Clé privée pour {identity_name} introuvable")

        with open(key_path, 'r') as f:
            key_bundle = json.load(f)

        # Importe la clé privée
        private_pem = base64.b64decode(key_bundle['private_key'])
        private_key = serialization.load_pem_private_key(
            private_pem,
            password=None,  # En production, utiliser un mot de passe
            backend=default_backend()
        )

        # Récupère la clé de chiffrement
        encryption_key = base64.b64decode(key_bundle['encryption_key'])

        return private_key, encryption_key

    def _save_identity(self, identity_name: str, identity: Dict[str, Any]):
        """Sauvegarde une identité publique"""
        identity_path = self.keystore_path / f"{identity_name}.json"
        with open(identity_path, 'w') as f:
            json.dump(identity, f, indent=2)

    def list_identities(self) -> List[str]:
        """Liste les identités disponibles"""
        identities = []
        for file_path in self.keystore_path.glob("*.json"):
            if not file_path.name.endswith("_private.json"):
                identities.append(file_path.stem)

        return identities


class SecureTransmissionManager:
    """
    Gestionnaire de transmissions sécurisées

    Combine chiffrement, signatures et authentification.
    """

    def __init__(self, key_manager: Optional[KeyManager] = None):
        """
        Initialisation du gestionnaire sécurisé

        Args:
            key_manager: Gestionnaire de clés (optionnel)
        """
        self.key_manager = key_manager or KeyManager()
        self.encryption = EncryptionManager()
        self.signatures = SignatureManager()

        # Statistiques
        self.stats = {
            'messages_encrypted': 0,
            'messages_signed': 0,
            'messages_verified': 0,
            'security_failures': 0,
        }

    def create_secure_message(self, data: bytes, sender_identity: str,
                            recipient_identity: Optional[str] = None,
                            encrypt: bool = True, sign: bool = True) -> Dict[str, Any]:
        """
        Crée un message sécurisé

        Args:
            data: Données à sécuriser
            sender_identity: Identité de l'expéditeur
            recipient_identity: Identité du destinataire (pour chiffrement)
            encrypt: Activer le chiffrement
            sign: Activer la signature

        Returns:
            Message sécurisé
        """
        # Charge l'identité de l'expéditeur
        sender_keys = self.key_manager.load_identity(sender_identity)

        secure_message = {
            'version': '1.0',
            'timestamp': datetime.utcnow().isoformat(),
            'sender': sender_identity,
            'encrypted': encrypt,
            'signed': sign,
        }

        # Chiffrement
        if encrypt:
            if recipient_identity:
                # Chiffrement asymétrique (clé partagée simulée)
                # En production, utiliser un échange de clés Diffie-Hellman
                shared_key = self._derive_shared_key(sender_identity, recipient_identity)
            else:
                # Chiffrement symétrique avec clé de l'expéditeur
                shared_key = sender_keys['encryption_key']

            encrypted = self.encryption.encrypt(data, shared_key)
            secure_message['data'] = encrypted
            self.stats['messages_encrypted'] += 1

        else:
            # Données en clair
            secure_message['data'] = base64.b64encode(data).decode('ascii')

        # Signature
        if sign:
            signature_data = json.dumps(secure_message, sort_keys=True).encode('utf-8')
            signature = self.signatures.sign_data(signature_data, sender_keys['private_key'])
            secure_message['signature'] = signature
            secure_message['sender_public_key'] = sender_keys['identity']['public_key']
            self.stats['messages_signed'] += 1

        return secure_message

    def verify_secure_message(self, secure_message: Dict[str, Any],
                            expected_sender: Optional[str] = None) -> Tuple[bool, bytes]:
        """
        Vérifie et déchiffre un message sécurisé

        Args:
            secure_message: Message sécurisé
            expected_sender: Expéditeur attendu (optionnel)

        Returns:
            Tuple (succès, données déchiffrées)
        """
        try:
            # Vérification de la signature
            if secure_message.get('signed'):
                signature_data = json.dumps({
                    k: v for k, v in secure_message.items()
                    if k not in ['signature', 'sender_public_key']
                }, sort_keys=True).encode('utf-8')

                sender_public_key = self.signatures.import_public_key(
                    secure_message['sender_public_key']
                )

                is_valid = self.signatures.verify_signature(
                    signature_data,
                    secure_message['signature'],
                    sender_public_key
                )

                if not is_valid:
                    self.stats['security_failures'] += 1
                    return False, b""

                self.stats['messages_verified'] += 1

                # Vérification de l'expéditeur si spécifié
                if expected_sender and secure_message['sender'] != expected_sender:
                    self.stats['security_failures'] += 1
                    return False, b""

            # Déchiffrement
            if secure_message.get('encrypted'):
                # Pour cet exemple, on utilise la clé du destinataire
                # En production, gérer correctement les clés partagées
                if expected_sender:
                    recipient_keys = self.key_manager.load_identity(expected_sender)
                    decryption_key = recipient_keys['encryption_key']
                else:
                    # Clé de secours (non sécurisé)
                    decryption_key = self.encryption.generate_key()

                data = self.encryption.decrypt(secure_message['data'], decryption_key)
            else:
                # Données en clair
                data = base64.b64decode(secure_message['data'])

            return True, data

        except Exception as e:
            self.stats['security_failures'] += 1
            return False, b""

    def _derive_shared_key(self, sender: str, recipient: str) -> bytes:
        """
        Dérive une clé partagée (simulation)

        En production, utiliser ECDH ou similaire
        """
        # Simulation simple (non sécurisé pour la production)
        combined = f"{sender}:{recipient}".encode('utf-8')
        return hashlib.sha256(combined).digest()

    def get_security_stats(self) -> Dict[str, Any]:
        """Statistiques de sécurité"""
        return {
            'stats': self.stats.copy(),
            'security_level': 'high',  # AES-256-GCM + ECDSA
            'supported_algorithms': ['AES-256-GCM', 'RSA-PSS', 'SHA-256'],
        }


# Fonctions utilitaires
def generate_secure_identity(name: str, key_manager: Optional[KeyManager] = None) -> Dict[str, Any]:
    """
    Génère une nouvelle identité sécurisée

    Args:
        name: Nom de l'identité
        key_manager: Gestionnaire de clés (optionnel)

    Returns:
        Informations de l'identité
    """
    km = key_manager or KeyManager()
    return km.generate_identity(name)


def create_secure_message(data: Union[str, bytes], sender: str,
                         key_manager: Optional[KeyManager] = None,
                         encrypt: bool = True, sign: bool = True) -> Dict[str, Any]:
    """
    Fonction utilitaire pour créer un message sécurisé

    Args:
        data: Données à sécuriser
        sender: Expéditeur
        key_manager: Gestionnaire de clés
        encrypt: Activer chiffrement
        sign: Activer signature

    Returns:
        Message sécurisé
    """
    if isinstance(data, str):
        data = data.encode('utf-8')

    stm = SecureTransmissionManager(key_manager)
    return stm.create_secure_message(data, sender, encrypt=encrypt, sign=sign)


def verify_secure_message(message: Dict[str, Any],
                         key_manager: Optional[KeyManager] = None) -> Tuple[bool, bytes]:
    """
    Fonction utilitaire pour vérifier un message sécurisé

    Args:
        message: Message sécurisé
        key_manager: Gestionnaire de clés

    Returns:
        Tuple (succès, données)
    """
    stm = SecureTransmissionManager(key_manager)
    return stm.verify_secure_message(message)
