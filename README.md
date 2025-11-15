# MML, DNF et Transmission Morse Moderne

## Vue d'ensemble du système

Ce projet présente une architecture innovante pour la transmission de documents structurés dans des environnements contraints, combinant un langage de balisage minimal (MML), un framework réseau distribué (DNF), et le code Morse comme couche de transport finale.

Imaginez que vous voulez envoyer une page web complète à quelqu'un qui n'a accès qu'à une connexion radio amateur ou un réseau mesh local. Traditionnellement, cela nécessiterait des bandes passantes importantes et des protocoles complexes. Notre système transforme cette page web en une séquence Morse optimisée, transmissible même sur les canaux les plus étroits.

## Architecture en couches

```
┌─────────────────┐
│   Documents     │ ← HTML, Markdown, texte structuré
│     source      │
└─────────────────┘
         ↓
┌─────────────────┐
│   MML (Minimal  │ ← Langage de balisage intermédiaire
│ Markup Language)│
└─────────────────┘
         ↓
┌─────────────────┐
│  Compression    │ ← MML-C avec tokens lexicaux
│    avancée      │
└─────────────────┘
         ↓
┌─────────────────┐
│   Code Morse    │ ← Mapping optimisé ASCII→Morse
│   optimisé      │
└─────────────────┘
         ↓
┌─────────────────┐
│ Transmission    │ ← CW, JS8Call, APRS, Bluetooth
│    physique     │
└─────────────────┘
```

## Objectifs du système

### Robustesse
- Transmission fiable même avec des taux d'erreur élevés
- Récupération automatique des erreurs via redondance
- Tolérance aux interruptions de signal

### Faible bande passante
- Compression extrême des données textuelles
- Optimisation du mapping Morse
- Utilisation efficiente des fréquences radio

### Universalité
- Compatible avec tous les protocoles de transmission existants
- Indépendant de l'infrastructure réseau
- Accessible aux radioamateurs et systèmes embarqués

## Table des matières

### 1. Introduction générale
- [1.1 Vision du système](docs/introduction/1.1-vision-systeme.md)
- [1.2 Pourquoi un langage intermédiaire ?](docs/introduction/1.2-langage-intermediaire.md)
- [1.3 Objectifs : robustesse, faible bande passante, universalité](docs/introduction/1.3-objectifs.md)

### 2. Fondations techniques
- [2.1 Le protocole DNF (Distributed Network Framework)](docs/fondations/2.1-protocole-dnf.md)
- [2.2 Transmission hors-réseau](docs/fondations/2.2-transmission-hors-reseau.md)
- [2.3 Pourquoi le Morse reste pertinent](docs/fondations/2.3-morse-pertinent.md)

### 3. Le langage MML (Minimal Markup Language)
- [3.1 Philosophie du MML](docs/mml/3.1-philosophie-mml.md)
- [3.2 Syntaxe complète](docs/mml/3.2-syntaxe-complete.md)
- [3.3 Balises standardisées](docs/mml/3.3-balises-standardisees.md)
- [3.4 Variantes compressées](docs/mml/3.4-variantes-comprimees.md)

### 4. Transmission de documents HTML via MML
- [4.1 Cartographie HTML → MML](docs/transmission_html/4.1-cartographie-html-mml.md)
- [4.2 Gestion des titres, paragraphes, liens](docs/transmission_html/4.2-gestion-contenu.md)
- [4.3 Exemple complet : page HTML convertie](docs/transmission_html/4.3-exemple-complet.md)

### 5. Compression avancée
- [5.1 Codes courts pour les balises](docs/compression/5.1-codes-courts.md)
- [5.2 Tokens lexicaux](docs/compression/5.2-tokens-lexicaux.md)
- [5.3 MML-C (MML Compressed)](docs/compression/5.3-mml-compressed.md)

### 6. Conversion en Morse
- [6.1 Rappels du Morse international](docs/morse/6.1-rappels-morse.md)
- [6.2 Mapping optimisé pour MML-C](docs/morse/6.2-mapping-optimise.md)
- [6.3 Séquences d'émission pour DNF](docs/morse/6.3-sequences-emission.md)

### 7. Transmission radio
- [7.1 CW (Morse manual/automatique)](docs/radio/7.1-cw-transmission.md)
- [7.2 JS8Call](docs/radio/7.2-js8call.md)
- [7.3 APRS/Packet](docs/radio/7.3-aprs-packet.md)
- [7.4 Intégration radioamateurs](docs/radio/7.4-integration-radio.md)

### 8. Le client DNF-MML
- [8.1 Architecture](docs/client/8.1-architecture.md)
- [8.2 Pipeline : Texte → MML → Compression → Morse](docs/client/8.2-pipeline-direct.md)
- [8.3 Pipeline inverse : Morse → Décompression → MML → Rendu HTML](docs/client/8.3-pipeline-inverse.md)

### 9. Cas d'usage
- [9.1 Zones sans réseau](docs/cas_usage/9.1-zones-sans-reseau.md)
- [9.2 Communications de crise](docs/cas_usage/9.2-communications-crise.md)
- [9.3 Réseaux clandestins/résilients](docs/cas_usage/9.3-reseaux-clandestins.md)
- [9.4 Micro-pages web transmises localement](docs/cas_usage/9.4-micro-pages.md)

### 10. Sécurité et intégrité
- [10.1 Hash léger intégré au MML](docs/securite/10.1-hash-leger.md)
- [10.2 Signatures volontaires](docs/securite/10.2-signatures.md)
- [10.3 Protection contre la déformation du signal](docs/securite/10.3-protection-signal.md)

### 11. Spécification officielle MML (RFC)
- [11.1 Structure](docs/specification/11.1-structure.md)
- [11.2 Déclarations](docs/specification/11.2-declarations.md)
- [11.3 Exemples conformes](docs/specification/11.3-exemples.md)

### 12. Annexes
- [12.1 Tables Morse optimisées](docs/annexes/12.1-tables-morse.md)
- [12.2 Dictionnaire de tokens](docs/annexes/12.2-dictionnaire-tokens.md)
- [12.3 Cartes ASCII → Morse](docs/annexes/12.3-cartes-ascii-morse.md)
- [12.4 Exemple d'implémentation Python](docs/annexes/12.4-implementation-python.md)

## Démarrage rapide

```bash
# Installation des dépendances
pip install -r requirements.txt

# Exemple simple : convertir du HTML en Morse
python -m src.mml.converter examples/sample.html

# Transmission via interface radio
python -m src.transmission.radio_interface --mode cw --frequency 7.030
```

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

---

*Ce système représente une fusion moderne entre les techniques de compression de données ancestrales et les protocoles de communication contemporains, permettant la transmission fiable d'informations structurées même dans les environnements les plus hostiles.*
