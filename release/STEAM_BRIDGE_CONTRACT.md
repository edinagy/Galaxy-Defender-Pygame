# Contract `steam_bridge`

`platform_services.py` detectează automat modulul opțional. Implementarea nativă
trebuie să ofere:

```python
class SteamBridge:
    def initialize(self) -> bool: ...
    def run_callbacks(self) -> None: ...
    def set_achievement(self, achievement_id: str) -> bool: ...
    def upload_score(
        self,
        leaderboard_name: str,
        score: int,
        details: list[int],
    ) -> bool: ...
    def shutdown(self) -> None: ...
```

Reguli:

- `initialize()` întoarce `False` dacă Steam nu poate fi inițializat;
- `run_callbacks()` este chemat în fiecare frame;
- `set_achievement()` trebuie să seteze achievement-ul și să salveze stats;
- `upload_score()` trebuie să găsească/creeze handle-ul pentru leaderboard și să
  folosească metoda Keep Best;
- metodele întorc `True` numai după ce operația a fost acceptată;
- excepțiile nu trebuie să închidă jocul; fallback-ul local rămâne activ.

Bridge-ul nu este inclus până când proiectul primește AppID-ul și Steamworks SDK.
