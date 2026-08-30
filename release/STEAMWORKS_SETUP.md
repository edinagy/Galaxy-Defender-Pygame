# Configurare Steamworks

Codul jocului are fallback local și nu cere Steam pentru a porni. Activarea reală
se face după ce există AppID și acces la Steamworks SDK.

## 1. Achievements

Creează următoarele API names în Steamworks, exact cu majusculele de mai jos:

| API name | Nume afișat | Condiție |
|---|---|---|
| `FIRST_BLOOD` | First Blood | primul inamic distrus |
| `STORY_COMPLETE` | Beyond the Wormhole | ajunge în enemy territory |
| `UNTOUCHABLE` | Untouchable | combo 25 |
| `DAREDEVIL` | Daredevil | Graze Chain 25 |
| `SOVEREIGN_SLAYER` | Sovereign Slayer | primul Sovereign distrus |
| `DEEP_SPACE` | Deep Space | Stage 3 |
| `ACE_PILOT` | Ace Pilot | 100.000 puncte într-o rundă |
| `IMMORTAL_RUN` | Immortal Run | boss învins fără hull damage |

Adaugă iconiță locked/unlocked pentru fiecare și publică schimbările din backend.

## 2. Leaderboard

- API name: `GLOBAL_SCORE`
- sortare: Descending
- display: Numeric
- upload method: Keep Best
- scor: integer pe 32 biți; jocul limitează valoarea trimisă la `2.147.483.647`
- details, în ordine: `stage`, `wave`, `best_combo`, `best_graze`, `duration_seconds`

Jocul validează sumarul rundei înainte de upload și păstrează maximum 25 operații
offline în `%LOCALAPPDATA%\GalaxyDefender\platform_queue.json`.

## 3. Bridge nativ

Adaugă în build un modul `steam_bridge` care expune clasa `SteamBridge` din
`release/STEAM_BRIDGE_CONTRACT.md`. Include DLL-ul Steamworks necesar în spec și
reconstruiește executabilul. Nu distribui `steam_appid.txt`; acesta este numai
pentru testare locală.

## 4. Steam Cloud

Configurează Auto-Cloud pentru Windows:

- root: `WinAppDataLocal`
- subdirectory: `GalaxyDefender`
- files recomandate: `save.json` și `leaderboard.txt`
- platform: Windows

`platform_queue.json` nu trebuie sincronizat: conține doar operații temporare
care sunt trimise când clientul Steam revine online.
`settings.json` rămâne local, ca rezoluția, fullscreen-ul și volumele să nu fie
copiate între PC-uri diferite.

## 5. Build și depot

Conținutul depotului este folderul `dist/GalaxyDefender/`. Executabilul de launch
este `GalaxyDefender.exe`, fără argumente. Înainte de setarea branch-ului public,
rulează checklist-ul QA și Steamworks release process pentru store page și build.

## 6. Pași care cer contul proprietarului

AppID-ul, SDK-ul, imaginile achievement, Steam Cloud, prețul, taxele, chestionarele,
store page review și build review nu pot fi publicate din cod. Acestea trebuie
confirmate în contul Steamworks al proprietarului.
