# Galaxy Defender

Galaxy Defender este un arcade space shooter 2D pentru Windows, construit în
Python/Pygame. Campania cinematică duce jucătorul până în teritoriul Dead Star,
apoi lupta devine o rundă endless axată pe scor și leaderboard.

## Ce conține jocul

- campanie cinematică în opt scene, cu incident orbital, dialoguri radio,
  Commander Vale și o tranziție coerentă spre teritoriul Dead Star;
- `NEW GAME` pornește povestea completă, iar `CONTINUE` reia checkpoint-ul salvat;
- tutorial contextual la prima intrare în luptă, cu opțiune de replay din Settings;
- rundă endless: fiecare Sovereign învins deschide următorul stage;
- dificultate, viteză, recompense și evenimente crescute în stage-urile adânci;
- scout, fighter, tank, elite, Shield Carrier și Phase Hunter;
- zece evenimente spațiale, inclusiv Phase Storm;
- boss Sovereign cu trei faze și atacuri suplimentare după Stage 1;
- combo care se pierde numai la damage real și Graze Chain pentru joc riscant;
- patru niveluri de armă, Energy Pulse, scut și power-up-uri;
- cinci vieți la începutul fiecărei runde competitive;
- opt achievements persistente și leaderboard local;
- integrare Steam pregătită printr-un bridge opțional, cu fallback local;
- tastatură, mouse și controller (Xbox-style) în meniu și gameplay;
- rezoluție adaptivă, fullscreen, setări audio, pauză și Game Over.

## Controale

| Acțiune | Tastatură | Controller |
|---|---|---|
| Mișcare / navigare | `WASD` / săgeți | stick stânga / D-pad |
| Foc automat / confirmare | `SPACE` / `ENTER` | `A` / `RT` |
| Energy Pulse | `E` | `X` |
| Omitere tutorial | `F1` | `Y` |
| Pauză / înapoi | `ESC` | `START` / `B` |
| Retry după Game Over | `R` / `ENTER` | `A` |

## Rulare din surse

Este recomandat Python 3.12.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Testele automate:

```powershell
python -m unittest discover -s tests -v
```

Buildul Windows:

```powershell
pip install -r requirements-build.txt
.\scripts\build_windows.ps1
```

Executabilul este generat în `dist/GalaxyDefender/GalaxyDefender.exe`.
`python main.py --smoke-test` verifică inițializarea și randarea fără a porni
bucla interactivă.

## Date locale

În dezvoltare, progresul se salvează în `data/`. În buildul Windows, fișierele
sunt păstrate în `%LOCALAPPDATA%\GalaxyDefender`, separat de executabil, astfel
încât update-urile să nu șteargă progresul.

## Release

Instrucțiunile de Steamworks, checklist-ul QA și textul pentru pagina magazinului
sunt în folderul `release/`. Codul funcționează complet fără Steam; publicarea
achievements/leaderboard necesită AppID, Steamworks SDK și configurarea aplicației
în contul partenerului.
