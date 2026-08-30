# Galaxy Defender — QA de release

## Validări automate executate

- [x] Toate cele 40 de teste unitare trec.
- [x] Toate modulele principale trec verificarea de sintaxă.
- [x] Jocul din surse trece `--smoke-test` cu drivere video/audio headless.
- [x] Buildul Windows onedir este creat cu iconița finală.
- [x] Executabilul ambalat trece `--smoke-test` cu exit code 0.
- [x] Meniu, Settings, tutorialul, feedbackul de luptă, toate cele opt cadre-cheie
  ale intro-ului și Stage 2 au fost randate și inspectate la 1280×720.
- [x] Benchmark headless: peste 400 FPS neplafonat pentru scena QA Stage 2.
- [x] Salvarea coruptă este înlocuită cu valori sigure.
- [x] Scorurile invalide, negative sau neverosimile sunt refuzate înainte de upload.

## Verificare manuală înainte de Steam review

- [ ] Joacă o rundă de minimum 30 minute cu tastatură și una cu controller real.
- [ ] Verifică fiecare rezoluție suportată, fullscreen și revenirea cu `ESC`/`B`.
- [ ] Scoate controllerul în timpul jocului și reconectează-l.
- [ ] Verifică volumele cu căști și boxe; confirmă că niciun efect nu distorsionează.
- [ ] Deblochează toate cele opt achievements pe un cont Steam de test.
- [ ] Trimite un scor, repornește jocul offline, apoi reconectează Steam și confirmă uploadul.
- [ ] Verifică overlay-ul Steam, capturile F12 și închiderea din client.
- [ ] Instalează buildul într-un folder curat și testează pe un al doilea PC Windows.
- [ ] Confirmă drepturile comerciale pentru fiecare imagine, font, muzică și efect audio.
- [ ] Completează chestionarul Steam privind conținutul generat cu AI, dacă se aplică.

## Criteriu de acceptare

Nu se urcă buildul pe ramura publică până când toate punctele manuale sunt bifate.
Erorile de crash, pierdere de save, controller blocat sau scor incorect sunt P0 și
blochează release-ul.
