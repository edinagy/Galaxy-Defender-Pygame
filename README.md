# Galaxy Defender

Galaxy Defender este un joc 2D de tip space shooter realizat în Python cu biblioteca Pygame. Proiectul combină o campanie cinematică, lupte pe wave-uri, evenimente spațiale și un boss final cu mai multe faze.

# Poveste

Jucătorul părăsește planeta natală, traversează un vortex și un câmp de asteroizi, intră într-un wormhole și ajunge în sistemul ostil Dead Star. După încheierea secvențelor cinematice începe lupta principală pentru apărarea galaxiei.

# Funcționalități principale

- intro cinematic alcătuit din mai multe scene;
- salvarea progresului și opțiuni `CONTINUE` / `NEW GAME`;
- wave-uri cu dificultate progresivă;
- inamici scout, fighter, tank și elite;
- tipuri diferite de proiectile și comportamente de atac;
- nouă evenimente spațiale prezentate într-o ordine stabilită;
- sistem de upgrade al armei cu patru niveluri;
- abilitate specială `Energy Pulse`;
- power-up-uri pentru armă, scut și viață;
- combo, multiplicator de scor și leaderboard;
- boss final cu trei faze, generatoare, proiectile și lasere;
- muzică, ambianțe și efecte sonore;
- meniu, pauză, setări audio, fullscreen și selector de rezoluție.

# Controale

| Acțiune | Taste |
|---|---|
| Mișcare | `WASD` |
| Tragere automată | Ține apăsat `SPACE` |
| Energy Pulse | `E`, când bara este încărcată |
| Pauză / revenire | `ESC` |
| Retry după Game Over | `R` |

# Instalare și rulare

Este recomandat Python 3.12.

```bash
python -m venv .venv
```

Activarea mediului virtual pe Windows:

```bash
.venv\Scripts\activate
```

Instalarea dependențelor:

```bash
pip install -r requirements.txt
```

Pornirea jocului:

```bash
python main.py
```

# Structura proiectului

- `main.py` — pornește jocul și coordonează meniurile și scenele;
- `gameplay.py` — gestionează lupta, coliziunile, wave-urile și scorul;
- `player.py` — controlează nava jucătorului;
- `enemy.py` și `enemy_bullet.py` — definesc inamicii și atacurile lor;
- `boss.py` — conține bossul final și cele trei faze;
- `space_events.py` — coordonează evenimentele speciale;
- `save_manager.py` — salvează progresul și setările;
- `display_manager.py` — gestionează rezoluția și modul fullscreen;
- `intro/` — conține scenele cinematice;
- `assets/` — conține imaginile, muzica, sunetele și fonturile.

# Starea proiectului

Proiectul este funcțional și se află în dezvoltare. Versiunea curentă este pregătită pentru prezentarea progresului realizat până în acest moment.
